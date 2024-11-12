from logging import Logger
from typing import List

from moneywiz.account import AccountAnalyzer
from moneywiz.category import CategoryAnalyzer
from moneywiz.currency import CurrencyAnalyzer
from moneywiz.payee import PayeeAnalyzer
from moneywiz.payment import PaymentAnalyzer
from moneywiz.scheme import MwData
from moneywiz.tag import TagAnalyzer
from moneywiz.transfer import TransferAnalyzer
from storage.scheme import Currency, Account, Transfer, Payment, Payee, Category, Tag
from storage.transactions import TransactionsDB


class CsvAnalyzer:
    """Analyze parsed data from MoneyWiz CSV."""

    __logger: Logger
    __currencies: List[Currency]
    __payees: List[Payee]
    __categories: List[Category]
    __tags: List[Tag]
    __accounts: List[Account]
    __transfers: List[Transfer]
    __payments: List[Payment]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger

    def analyze(self, mw: MwData) -> None:
        """Run data analysis."""

        self.__currencies = CurrencyAnalyzer(self.__logger).analyze(mw.currencies).get()
        self.__payees = PayeeAnalyzer(self.__logger).analyze(mw.payees).get()
        self.__categories = CategoryAnalyzer(self.__logger).analyze(mw.categories).get()
        self.__tags = TagAnalyzer(self.__logger).analyze(mw.tags).get()
        self.__accounts = AccountAnalyzer(self.__logger, self.__currencies).analyze(mw.accounts).get()
        self.__transfers = TransferAnalyzer(self.__logger, self.__currencies, self.__accounts).analyze(
            mw.transfers).get()
        self.__payments = PaymentAnalyzer(self.__logger, self.__payees, self.__categories, self.__tags,
                                          self.__accounts).analyze(mw.payments).get()

    def commit(self, db: TransactionsDB) -> None:
        """Commit changes."""

        self.__logger.info(f'Committing changes')
        db.add_currencies(self.__currencies)
        db.add_payees(self.__payees)
        db.add_categories(self.__categories)
        db.add_tags(self.__tags)
        db.add_accounts(self.__accounts)
        db.add_transfers(self.__transfers)
        db.add_payments(self.__payments)
        self.__logger.info(f'Committed changes')
