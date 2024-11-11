from logging import Logger
from typing import List, Mapping, Self

from moneywiz.exception import AnalyzerException
from moneywiz.helpers import to_datetime
from moneywiz.scheme import MwPayment
from storage.scheme import Currency, Account, Payment


class PaymentAnalyzer:
    """Analyze payment data."""

    __logger: Logger
    __accounts: Mapping[str, Account]
    __payments: List[Payment]

    def __init__(self, logger: Logger, accounts: List[Account]) -> None:
        self.__logger = logger
        self.__accounts = {account.name: account for account in accounts}
        self.__payments = []

    def analyze(self, payments: List[MwPayment]) -> Self:
        """Analyze payment data."""

        self.__payments = [
            Payment(
                account=self.__accounts.get(p.account),
                payee=p.payee,
                category=p.category,
                description=p.description,
                tags=p.tags,
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
