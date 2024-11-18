from logging import Logger
from typing import List, Mapping

from firefly_iii_client import TransactionStore, TransactionSplitStore, TransactionTypeProperty, \
    ShortAccountTypeProperty

from firefly.config import Config
from helpers import to_amount
from firefly.client import FireflyClient
from storage.scheme import Transfer, Account
from storage.transactions import TransactionsDB


class TransferExporter:
    """Export transfers into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, Account]
    __currencies: Mapping[int, str]
    __loan_category: str
    __loan_category_id: str

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient, config: Config):
        self.__logger = logger
        self.__db = db
        self.__client = client
        self.__loan_category = config.settings.loan_category

    def sync(self) -> None:
        """Synchronize the transfers in the database and Firefly III."""

        self.__logger.info('Sync transfers...')
        self.__accounts = {a.id: a for a in self.__db.get_accounts()}
        self.__currencies = {c.id: str(c.firefly_id) for c in self.__db.get_currencies()}
        self.__loan_category_id = next(str(c.firefly_id) for c in self.__db.get_categories() if c.name == self.__loan_category)
        self.__sync_ff(self.__db.get_transfers())
        self.__logger.info('Sync transfers... Done')

    def __sync_ff(self, db: List[Transfer]) -> None:
        # Create transfer in Firefly
        index = 0
        for t in db:
            if t.firefly_id is None:
                # Create transaction and update database object
                ff_t = self.__to_ff(t)
                if ff_t.transactions[0].amount != '0.00':
                    t.firefly_id = self.__client.create_transaction(ff_t)
                    self.__logger.debug(f'Transfer created. Id={t.firefly_id}')

                    index += 1
                    if index % 100 == 0:
                        self.__logger.info(f'\t...{index} transfers created...')
        self.__logger.info(f'{index} transfers created in total')
        self.__db.add_transfers(db)

    def __to_ff(self, t: Transfer) -> TransactionStore:
        src = self.__accounts[t.source_id]
        dst = self.__accounts[t.target_id]
        category_id = None
        tx_type = TransactionTypeProperty.TRANSFER
        if dst.firefly_type == str(ShortAccountTypeProperty.LIABILITY):
            category_id = self.__loan_category_id
            tx_type = TransactionTypeProperty.WITHDRAWAL

        return TransactionStore(transactions=[
            TransactionSplitStore(
                type=tx_type,
                var_date=t.date,
                amount=to_amount(t.source_amount),
                category_id=category_id,
                currency_id=self.__currencies[t.source_currency_id],
                source_id=str(src.firefly_id),
                destination_id=str(dst.firefly_id),
                foreign_currency_id=self.__currencies[t.target_currency_id] if t.source_currency_id != t.target_currency_id else None,
                foreign_amount=to_amount(t.target_amount) if t.source_currency_id != t.target_currency_id else None,
                description=t.description if t.description else 'No description',
                external_id=str(t.id),
            )
        ])
