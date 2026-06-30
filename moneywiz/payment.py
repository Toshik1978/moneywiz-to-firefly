from collections.abc import Mapping
from logging import Logger
from typing import Self

from helpers import hash_key, to_datetime
from moneywiz.exception import AnalyzerException
from moneywiz.scheme import MwPayment
from storage.scheme import Account, Category, Payee, Payment, Tag


class PaymentAnalyzer:
    """Analyze payment data."""

    __logger: Logger
    __payees: Mapping[str, Payee]
    __categories: Mapping[str, Category]
    __tags: Mapping[str, Tag]
    __accounts: Mapping[str, Account]
    __payments: list[Payment]

    def __init__(self, logger: Logger, payees: list[Payee], categories: list[Category], tags: list[Tag], accounts: list[Account]) -> None:
        self.__logger = logger
        self.__payees = {hash_key(payee.name, str(payee.expense)): payee for payee in payees}
        self.__categories = {category.name: category for category in categories}
        self.__tags = {tag.name: tag for tag in tags}
        self.__accounts = {account.name: account for account in accounts}
        self.__payments = []

    def analyze(self, payments: list[MwPayment]) -> Self:
        """Analyze payment data."""

        self.__logger.info('Analyzing payments...')
        self.__payments = [
            Payment(
                account=self.__accounts.get(p.account),
                payee=self.__payees.get(hash_key(p.payee, str(p.amount[0] == '-'))),
                category=self.__categories.get(p.category),
                description=p.description,
                tag=self.__tags.get(p.tag),
                amount=p.amount,
                balance=p.balance,
                date=to_datetime(p.date, p.time),
            )
            for p in payments
        ]
        self.__validate()
        self.__logger.info('Analyzing payments... Done')
        return self

    def get(self) -> list[Payment]:
        """Get payment data."""

        return self.__payments

    def __validate(self) -> None:
        payments = [payment.description for payment in self.__payments if payment.account is None]
        if payments:
            raise AnalyzerException(f'Orphaned payments detected: {payments}')
