from logging import Logger
from typing import List, Mapping

from firefly_iii_client import TransactionStore, TransactionSplitStore, TransactionTypeProperty

from helpers import to_amount, hash_key
from firefly.client import FireflyClient
from storage.scheme import Payment
from storage.transactions import TransactionsDB


class PaymentExporter:
    """Export payments into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, str]
    __categories: Mapping[int, str]
    __payees: Mapping[int, str]

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the payments in the database and Firefly III."""

        self.__logger.info('Sync payments...')
        self.__accounts = {a.id: str(a.firefly_id) for a in self.__db.get_accounts()}
        self.__categories = {c.id: str(c.firefly_id) for c in self.__db.get_categories()}
        self.__payees = {p.id: str(p.firefly_id) for p in self.__db.get_payees()}
        self.__sync_ff(self.__db.get_payments())
        self.__logger.info('Sync payments... Done')

    def __sync_ff(self, db: List[Payment]) -> None:
        # Create payments in Firefly
        # We want to create split transactions if it's possible
        # Group by account_id -- payee_id -- date
        index = 0
        try:
            mapping = self.__to_dict(db)
            for l in mapping.values():
                # Add splits to the transaction
                t = TransactionStore(transactions=[])
                for p in l:
                    ff_p = self.__to_ff(p)
                    if ff_p.amount != '0.00':
                        t.transactions.append(ff_p)

                if t.transactions:
                    if len(t.transactions) > 1:
                        t.group_title = l[0].payee.name
                    firefly_id = self.__client.create_transaction(t)
                    self.__logger.debug(f'Payment created. Id={firefly_id}')
                    for p in l:
                        p.firefly_id = firefly_id

                    index += len(t.transactions)
                    if index % 100 == 0:
                        self.__logger.info(f'\t...{index} payments created...')
        finally:
            self.__logger.info(f'{index} payments created in total')
            self.__db.add_payments(db)

    def __to_dict(self, db: List[Payment]) -> Mapping[str, List[Payment]]:
        mapping = {}
        for p in db:
            key = hash_key(str(p.account.name), str(p.payee.name), p.date.strftime('%d-%m-%Y-%H-%M'))
            if mapping.get(key) is None:
                mapping[key] = []
            mapping[key].append(p)
        return mapping

    def __to_ff(self, p: Payment) -> TransactionSplitStore:
        withdrawal = p.amount[0] == '-'
        account_id = self.__accounts[p.account_id]
        payee_id = self.__payees[p.payee_id] if p.payee_id else None
        return TransactionSplitStore(
            type=TransactionTypeProperty.WITHDRAWAL if withdrawal else TransactionTypeProperty.DEPOSIT,
            var_date=p.date,
            amount=to_amount(p.amount),
            source_id=account_id if withdrawal else payee_id,
            destination_id=payee_id if withdrawal else account_id,
            category_id=self.__categories[p.category_id] if p.category_id else None,
            tags=[p.tag.name] if p.tag else None,
            description=p.description if p.description else 'No description',
            external_id=str(p.id),
        )
