from logging import Logger
from typing import List

from moneywiz.account import AccountAnalyzer
from moneywiz.currency import CurrencyAnalyzer
from moneywiz.payment import PaymentAnalyzer
from moneywiz.scheme import MwData
from moneywiz.transfer import TransferAnalyzer
from storage.scheme import Currency, Account, Transfer, Payment
from storage.transactions import TransactionsDB


class CsvAnalyzer:
    """Analyze parsed data from MoneyWiz CSV."""

    __logger: Logger
    __currencies: List[Currency]
    __accounts: List[Account]
    __transfers: List[Transfer]
    __payments: List[Payment]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger

    def analyze(self, mw: MwData) -> None:
        """Run data analysis."""

        self.__currencies = CurrencyAnalyzer(self.__logger).analyze(mw.currencies).get()
        self.__accounts = AccountAnalyzer(self.__logger, self.__currencies).analyze(mw.accounts).get()
        self.__transfers =(
            TransferAnalyzer(self.__logger, self.__currencies, self.__accounts).analyze(mw.transfers).get())
        self.__payments = PaymentAnalyzer(self.__logger, self.__accounts).analyze(mw.payments).get()

    def commit(self, db: TransactionsDB) -> None:
        """Commit changes."""

        self.__logger.info(f'Committing changes')
        db.add_currencies(self.__currencies)
        db.add_accounts(self.__accounts)
        db.add_transfers(self.__transfers)
        db.add_payments(self.__payments)
        self.__logger.info(f'Committed changes')
