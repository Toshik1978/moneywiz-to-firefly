from collections.abc import Mapping
from logging import Logger
from typing import Self

from moneywiz.exception import AnalyzerException
from moneywiz.scheme import MwAccount
from storage.scheme import Account, Currency


class AccountAnalyzer:
    """Analyze account data."""

    __logger: Logger
    __currencies: Mapping[str, Currency]
    __accounts: list[Account]

    def __init__(self, logger: Logger, currencies: list[Currency], accounts: list[Account]) -> None:
        self.__logger = logger
        self.__currencies = {currency.name: currency for currency in currencies}
        self.__accounts = accounts

    def analyze(self, accounts: list[MwAccount]) -> Self:
        """Analyze account data."""

        self.__logger.info('Analyzing accounts...')
        mapping = {a.name: a for a in self.__accounts}

        # Update balances for existing accounts
        for a in accounts:
            if a.name in mapping:
                mapping[a.name].balance = a.balance
        # Add new accounts
        self.__accounts.extend(
            [Account(name=a.name, currency_id=self.__currencies.get(a.currency).id, balance=a.balance) for a in accounts if
             a.name not in mapping])

        self.__validate()
        self.__logger.info('Analyzing accounts... Done')
        return self

    def get(self) -> list[Account]:
        """Get account data."""

        return self.__accounts

    def __validate(self) -> None:
        accounts = [account.name for account in self.__accounts if account.currency_id is None]
        if accounts:
            raise AnalyzerException(f'Orphaned accounts detected: {accounts}')
