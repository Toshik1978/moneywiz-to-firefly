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

        self.__logger.info('Analyzing accounts...')
        mapping = {a.name: a for a in self.__accounts}

        # Update balances for existing accounts
        for a in accounts:
            if a.name in mapping:
                mapping[a.name].balance = a.balance
        # Add new accounts
        self.__accounts.extend(
            [Account(name=a.name, currency=self.__currencies.get(a.currency), balance=a.balance) for a in accounts if
             a.name not in mapping])

        self.__validate()
        self.__logger.info('Analyzing accounts... Done')
        return self

    def get(self) -> List[Account]:
        """Get account data."""

        return self.__accounts

    def __validate(self) -> None:
        accounts = [account.name for account in self.__accounts if account.currency is None]
        if accounts:
            raise AnalyzerException(f'Orphaned accounts detected: {accounts}')
