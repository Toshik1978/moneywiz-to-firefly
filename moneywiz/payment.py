from logging import Logger
from typing import List, Mapping, Self

from moneywiz.exception import AnalyzerException
from moneywiz.helpers import to_datetime
from moneywiz.scheme import MwPayment
from storage.scheme import Payee, Category, Tag, Account, Payment


class PaymentAnalyzer:
    """Analyze payment data."""

    __logger: Logger
    __payees: Mapping[str, Payee]
    __categories: Mapping[str, Category]
    __tags: Mapping[str, Tag]
    __accounts: Mapping[str, Account]
    __payments: List[Payment]

    def __init__(self, logger: Logger, payees: List[Payee], categories: List[Category], tags: List[Tag], accounts: List[Account]) -> None:
        self.__logger = logger
        self.__payees = {payee.name: payee for payee in payees}
        self.__categories = {category.name: category for category in categories}
        self.__tags = {tag.name: tag for tag in tags}
        self.__accounts = {account.name: account for account in accounts}
        self.__payments = []

    def analyze(self, payments: List[MwPayment]) -> Self:
        """Analyze payment data."""

        self.__payments = [
            Payment(
                account=self.__accounts.get(p.account),
                payee=self.__payees.get(p.payee),
                category=self.__categories.get(p.category),
                description=p.description,
                tag=self.__tags.get(p.tag),
                amount=p.amount,
                date=to_datetime(p.date, p.time),
            )
            for p in payments
        ]
        self.__validate()
        return self

    def get(self) -> List[Payment]:
        """Get payment data."""

        return self.__payments

    def __validate(self) -> None:
        payments = [payment.description for payment in self.__payments if payment.account is None]
        if payments:
            raise AnalyzerException(f'Orphaned payments detected: {payments}')
