from logging import Logger
from typing import List

from firefly.account import AccountExporter
from firefly.client import FireflyClient
from firefly.config import Config
from firefly.currency import CurrencyExporter
from storage.scheme import Currency, Account, Transfer, Payment, Payee, Category, Tag
from storage.transactions import TransactionsDB


class Exporter:
    """Exporter to Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __config: Config
    __currencies: List[Currency]
    __payees: List[Payee]
    __categories: List[Category]
    __tags: List[Tag]
    __accounts: List[Account]
    __transfers: List[Transfer]
    __payments: List[Payment]

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient, config: Config):
        self.__logger = logger
        self.__db = db
        self.__client = client
        self.__config = config

    def export(self) -> None:
        """Run export."""

        self.__logger.info('Export financial data to Firefly III...')
        CurrencyExporter(self.__logger, self.__db, self.__client).sync()
        AccountExporter(self.__logger, self.__db, self.__client, self.__config).sync()
        self.__logger.info('Export financial data to Firefly III... Done')
