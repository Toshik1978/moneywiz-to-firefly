from logging import Logger
from typing import List

from storage.scheme import Currency, Account, Transfer, Payment, Payee, Category, Tag
from storage.transactions import TransactionsDB


class Exporter:
    """Exporter to Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __currencies: List[Currency]
    __payees: List[Payee]
    __categories: List[Category]
    __tags: List[Tag]
    __accounts: List[Account]
    __transfers: List[Transfer]
    __payments: List[Payment]

    def __init__(self, logger: Logger, db: TransactionsDB):
        self.__logger = logger
        self.__db = db

    def export(self) -> None:
        """Run export."""

        self.__logger.info("Export financial data to Firefly III...")
        self.__load()
        self.__logger.info('Export finished')

    def __load(self) -> None:
        self.__logger.info('Loading database')
        self.__currencies = self.__db.get_currencies()
        self.__payees = self.__db.get_payees()
        self.__categories = self.__db.get_categories()
        self.__tags = self.__db.get_tags()
        self.__accounts = self.__db.get_accounts()
        self.__transfers = self.__db.get_transfers()
        self.__payments = self.__db.get_payments()
        self.__logger.info('Loaded database')
