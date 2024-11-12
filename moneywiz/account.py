from logging import Logger
from typing import List, Mapping, Self

from moneywiz.exception import AnalyzerException
from moneywiz.scheme import MwAccount
from storage.scheme import Currency, Account


class AccountAnalyzer:
    """Analyze account data."""

    __logger: Logger
    __currencies: Mapping[str, Currency]
    __accounts: List[Account]

    def __init__(self, logger: Logger, currencies: List[Currency], accounts: List[Account]) -> None:
        self.__logger = logger
        self.__currencies = {currency.name: currency for currency in currencies}
        self.__accounts = accounts

    def analyze(self, accounts: List[MwAccount]) -> Self:
        """Analyze account data."""

        hashset = {a.name for a in self.__accounts}
        self.__accounts.extend(
            [Account(name=a.name, currency=self.__currencies.get(a.currency)) for a in accounts if
             a.name not in hashset])
        self.__validate()
        return self

    def get(self) -> List[Account]:
        """Get account data."""

        return self.__accounts

    def __validate(self) -> None:
        accounts = [account.name for account in self.__accounts if account.currency is None]
        if accounts:
            raise AnalyzerException(f'Orphaned accounts detected: {accounts}')
