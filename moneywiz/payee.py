from logging import Logger
from typing import List, Self

from moneywiz.scheme import MwPayee
from storage.scheme import Payee


class PayeeAnalyzer:
    """Analyze payee data."""

    __logger: Logger
    __payees: List[Payee]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger
        self.__payees = []

    def analyze(self, payees: List[MwPayee]) -> Self:
        """Analyze payee data."""

        self.__payees = [Payee(name=p.name) for p in payees if p.name]
        return self

    def get(self) -> List[Payee]:
        """Get payee data."""

        return self.__payees
