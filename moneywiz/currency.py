from logging import Logger
from typing import Self

from moneywiz.scheme import MwCurrency
from storage.scheme import Currency


class CurrencyAnalyzer:
    """Analyze currency data."""

    __logger: Logger
    __currencies: list[Currency]

    def __init__(self, logger: Logger, currencies: list[Currency]) -> None:
        self.__logger = logger
        self.__currencies = currencies

    def analyze(self, currencies: list[MwCurrency]) -> Self:
        """Analyze currency data."""

        self.__logger.info("Analyzing currencies...")
        hashset = {c.name for c in self.__currencies}
        self.__currencies.extend([Currency(name=c.name) for c in currencies if c.name not in hashset])
        self.__logger.info("Analyzing currencies... Done")
        return self

    def get(self) -> list[Currency]:
        """Get currency data."""

        return self.__currencies
