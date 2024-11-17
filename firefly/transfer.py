from logging import Logger
from typing import List, Mapping

from firefly_iii_client import TransactionStore, TransactionSplitStore, TransactionTypeProperty

from firefly.client import FireflyClient
from firefly.helpers import to_amount
from storage.scheme import Transfer
from storage.transactions import TransactionsDB


class TransferExporter:
    """Export transfers into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, str]
    __currencies: Mapping[int, str]

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the transfers in the database and Firefly III."""

        self.__logger.info('Sync transfers...')
        self.__accounts = {a.id: str(a.firefly_id) for a in self.__db.get_accounts()}
        self.__currencies = {c.id: str(c.firefly_id) for c in self.__db.get_currencies()}
        self.__sync_ff(self.__db.get_transfers())
        self.__logger.info('Sync transfers... Done')

    def __sync_ff(self, db: List[Transfer]) -> None:
        # Create transfer in Firefly
        index = 0
        for t in db:
            if t.firefly_id is None:
                # Create transaction and update database object
                t.firefly_id = self.__client.create_transaction(self.__to_ff(t))
                self.__logger.debug(f'Transfer created. Id={t.firefly_id}')

                index += 1
                if index % 100 == 0:
                    self.__logger.info(f'\t...{index} transfers created...')
        self.__db.add_transfers(db)

    def __to_ff(self, t: Transfer) -> TransactionStore:
        return TransactionStore(transactions=[
            TransactionSplitStore(
                type=TransactionTypeProperty.TRANSFER,
                var_date=t.date,
                amount=to_amount(t.source_amount),
                currency_id=self.__currencies[t.source_currency_id],
                source_id=self.__accounts[t.source_id],
                destination_id=self.__accounts[t.target_id],
                foreign_currency_id=self.__currencies[t.target_currency_id] if t.source_currency_id != t.target_currency_id else None,
                foreign_amount=to_amount(t.target_amount) if t.source_currency_id != t.target_currency_id else None,
                description=t.description,
                external_id=str(t.id),
            )
        ])
