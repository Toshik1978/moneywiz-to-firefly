from logging import Logger
from typing import List, Self

from moneywiz.scheme import MwCurrency
from storage.scheme import Currency


class CurrencyAnalyzer:
    """Analyze currency data."""

    __logger: Logger
    __currencies: List[Currency]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger
        self.__currencies = []

    def analyze(self, currencies: List[MwCurrency]) -> Self:
        """Analyze currency data."""

        self.__currencies = [Currency(name=c.name) for c in currencies]
        return self

    def get(self) -> List[Currency]:
        """Get currency data."""

        return self.__currencies
