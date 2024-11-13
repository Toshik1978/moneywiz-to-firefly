from logging import Logger
from typing import List

from firefly.client import FireflyClient
from firefly.scheme import FfCurrency
from storage.scheme import Currency
from storage.transactions import TransactionsDB


class CurrencyExporter:
    """Export currencies into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the currencies in the database and Firefly III."""

        db = self.__db.get_currencies()
        ff = self.__client.get_currencies()

        self.__sync_db(db, ff)
        self.__sync_ff(db, ff)

    def __sync_db(self, db: List[Currency], ff: List[FfCurrency]) -> None:
        # Update firefly_id for all currencies exist in Firefly
        mapping = {c.code: c for c in ff}
        for c in db:
            ff_c = mapping.get(c.name)
            if ff_c and c.firefly_id is None:
                c.firefly_id = ff_c.id
                self.__logger.debug(f'Currency {c.name} updated in database. Id={c.firefly_id}')
        self.__db.add_currencies(db)

    def __sync_ff(self, db: List[Currency], ff: List[FfCurrency]) -> None:
        # Enable or create currency in Firefly
        mapping = {c.code: c for c in ff}
        for c in db:
            ff_c = mapping.get(c.name)
            if ff_c is None:
                # Create currency and update database object
                c.firefly_id = self.__client.create_currency(FfCurrency(code=c.name, name=c.name, symbol=c.name))
                self.__logger.debug(f'Currency {c.name} created. Id={c.firefly_id}')
            elif ff_c and not ff_c.enabled:
                # Enable currency
                self.__client.enable_currency(ff_c.code)
                self.__logger.debug(f'Currency {c.name} enabled')
        self.__db.add_currencies(db)
