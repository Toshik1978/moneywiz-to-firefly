from collections.abc import Mapping
from logging import Logger

from firefly_iii_client import (
    ShortAccountTypeProperty,
    TransactionSplitStore,
    TransactionStore,
    TransactionTypeProperty,
)

from firefly.client import FireflyClient
from firefly.config import Config, SettingsConfig
from helpers import to_amount
from storage.scheme import Account, Transfer
from storage.transactions import TransactionsDB


class TransferExporter:
    """Export transfers into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, Account]
    __currencies: Mapping[int, str]
    __payees: Mapping[int, str]

    __settings: SettingsConfig
    __loan_payment_category_id: str
    __loan_interest_category_id: str

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient, config: Config):
        self.__logger = logger
        self.__db = db
        self.__client = client
        self.__settings = config.settings

    def sync(self) -> None:
        """Synchronize the transfers in the database and Firefly III."""

        self.__logger.info('Sync transfers...')
        self.__accounts = {a.id: a for a in self.__db.get_accounts()}
        self.__currencies = {c.id: str(c.firefly_id) for c in self.__db.get_currencies()}
        self.__payees = {p.id: str(p.firefly_id) for p in self.__db.get_payees()}
        self.__loan_payment_category_id = next(
            str(c.firefly_id) for c in self.__db.get_categories() if c.name == self.__settings.loan_payment_category)
        self.__loan_interest_category_id = next(
            str(c.firefly_id) for c in self.__db.get_categories() if c.name == self.__settings.loan_interest_category)
        self.__sync_ff(self.__db.get_transfers())
        self.__logger.info('Sync transfers... Done')

    def __sync_ff(self, db: list[Transfer]) -> None:
        # Create transfer in Firefly
        index = 0
        try:
            for t in db:
                # Create transaction and update database object
                # It's possible to have split transfers, but we don't care and create them separately!
                ff_t = self.__to_ff(t)
                if ff_t.transactions[0].amount != '0.00':
                    t.firefly_id = self.__client.create_transaction(ff_t)
                    self.__logger.debug(f'Transfer created. Id={t.firefly_id}')

                    index += 1
                    if index % 100 == 0:
                        self.__logger.info(f'\t...{index} transfers created...')
        finally:
            self.__logger.info(f'{index} transfers created in total')
            self.__db.add_transfers(db)

    def __to_ff(self, t: Transfer) -> TransactionStore:
        if self.__accounts[t.target_id].firefly_type == str(ShortAccountTypeProperty.LIABILITY):
            return self.__to_ff_liability(t)

        return TransactionStore(transactions=[
            TransactionSplitStore(
                type=TransactionTypeProperty.TRANSFER,
                var_date=t.date,
                amount=to_amount(t.source_amount),
                currency_id=self.__currencies[t.source_currency_id],
                source_id=str(self.__accounts[t.source_id].firefly_id),
                destination_id=str(self.__accounts[t.target_id].firefly_id),
                foreign_currency_id=self.__currencies[
                    t.target_currency_id] if t.source_currency_id != t.target_currency_id else None,
                foreign_amount=to_amount(t.target_amount) if t.source_currency_id != t.target_currency_id else None,
                description=t.description if t.description else 'No description',
                external_id=str(t.id),
            )
        ])

    def __to_ff_liability(self, t: Transfer) -> TransactionStore:
        # It's either withdrawal to liability account or expense (to the bank)
        dst_id = str(self.__accounts[t.target_id].firefly_id)
        category_id = self.__loan_payment_category_id
        if t.category.name == self.__settings.loan_interest_category:
            dst_id = self.__payees[t.payee_id]
            category_id = self.__loan_interest_category_id

        return TransactionStore(transactions=[
            TransactionSplitStore(
                type=TransactionTypeProperty.WITHDRAWAL,
                var_date=t.date,
                amount=to_amount(t.source_amount),
                category_id=category_id,
                currency_id=self.__currencies[t.source_currency_id],
                source_id=str(self.__accounts[t.source_id].firefly_id),
                destination_id=dst_id,
                description=t.description if t.description else 'No description',
                external_id=str(t.id),
            )
        ])
