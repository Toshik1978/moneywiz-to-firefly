from itertools import filterfalse
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
    __db: TransactionsDB
    __currencies: List[Currency]
    __payees: List[Payee]
    __categories: List[Category]
    __tags: List[Tag]
    __accounts: List[Account]
    __transfers: List[Transfer]
    __payments: List[Payment]

    def __init__(self, logger: Logger, db: TransactionsDB) -> None:
        self.__logger = logger
        self.__db = db

    def analyze(self, mw: MwData, dedup: bool) -> None:
        """Run data analysis."""

        self.__logger.info('Analyzing MoneyWiz CSV...')

        self.__currencies = CurrencyAnalyzer(self.__logger, self.__db.get_currencies()).analyze(mw.currencies).get()
        self.__payees = PayeeAnalyzer(self.__logger, self.__db.get_payees()).analyze(mw.payees).get()
        self.__categories = CategoryAnalyzer(self.__logger, self.__db.get_categories()).analyze(mw.categories).get()
        self.__tags = TagAnalyzer(self.__logger, self.__db.get_tags()).analyze(mw.tags).get()
        self.__accounts = AccountAnalyzer(self.__logger, self.__currencies, self.__db.get_accounts()).analyze(
            mw.accounts).get()

        self.__transfers = TransferAnalyzer(self.__logger, self.__currencies, self.__payees, self.__categories,
                                            self.__accounts).analyze(mw.transfers).get()
        self.__payments = PaymentAnalyzer(self.__logger, self.__payees, self.__categories, self.__tags,
                                          self.__accounts).analyze(mw.payments).get()

        if dedup:
            self.__deduplicate_transfers()
            self.__deduplicate_payments()

        self.__logger.info('Analyzing MoneyWiz CSV... Done')

    def commit(self) -> None:
        """Commit changes."""

        self.__logger.info(f'Committing changes')
        self.__db.add_currencies(self.__currencies)
        self.__db.add_payees(self.__payees)
        self.__db.add_categories(self.__categories)
        self.__db.add_tags(self.__tags)
        self.__db.add_accounts(self.__accounts)
        self.__db.add_transfers(self.__transfers)
        self.__db.add_payments(self.__payments)
        self.__logger.info(f'Committed changes')

    def __deduplicate_transfers(self) -> None:
        """Deduplicate transfers."""

        # Check if we have transfers in DB already and remove them
        def is_duplicate(t: Transfer) -> bool:
            dup = self.__db.check_transfer(t)
            if dup:
                self.__logger.info(f'Duplicate transfer {t.description} found. Id={t.firefly_id}')
            return dup
        self.__transfers[:] = filterfalse(is_duplicate, self.__transfers)

    def __deduplicate_payments(self) -> None:
        """Deduplicate payments."""

        # Check if we have payments in DB already and remove them
        def is_duplicate(p: Payment) -> bool:
            dup = self.__db.check_payment(p)
            if dup:
                self.__logger.info(f'Duplicate payment {p.description} found. Id={p.firefly_id}')
            return dup
        self.__payments[:] = filterfalse(is_duplicate, self.__payments)
