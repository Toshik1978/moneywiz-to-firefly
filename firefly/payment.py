from logging import Logger
from typing import List, Mapping

from firefly_iii_client import TransactionStore, TransactionSplitStore, TransactionTypeProperty

from firefly.client import FireflyClient
from firefly.helpers import to_amount
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
        for p in db:
            if p.firefly_id is None:
                # Create transaction and update database object
                p.firefly_id = self.__client.create_transaction(self.__to_ff(p))
                self.__logger.debug(f'Payment created. Id={p.firefly_id}')
        self.__db.add_payments(db)

    def __to_ff(self, p: Payment) -> TransactionStore:
        withdrawal = p.amount[0] == '-'
        account_id = self.__accounts[p.account_id]
        payee_id = self.__payees[p.payee_id] if p.payee_id else None
        return TransactionStore(transactions=[
            TransactionSplitStore(
                type=TransactionTypeProperty.WITHDRAWAL if withdrawal else TransactionTypeProperty.DEPOSIT,
                var_date=p.date,
                amount=to_amount(p.amount),
                source_id=account_id if withdrawal else payee_id,
                destination_id=payee_id if withdrawal else account_id,
                category_id=self.__categories[p.category_id] if p.category_id else None,
                tags=[p.tag.name] if p.tag else None,
                description=p.description,
                external_id=str(p.id),
            )
        ])
