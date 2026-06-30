from logging import Logger
from typing import Self

from helpers import hash_key
from moneywiz.scheme import MwPayee
from storage.scheme import Payee


class PayeeAnalyzer:
    """Analyze payee data."""

    __logger: Logger
    __payees: list[Payee]

    def __init__(self, logger: Logger, payees: list[Payee]) -> None:
        self.__logger = logger
        self.__payees = payees

    def analyze(self, payees: list[MwPayee]) -> Self:
        """Analyze payee data."""

        self.__logger.info('Analyzing payees...')
        hashset = {hash_key(p.name, str(p.expense)) for p in self.__payees}
        self.__payees.extend([Payee(name=p.name, expense=p.expense) for p in payees if
                              p.name and hash_key(p.name, str(p.expense)) not in hashset])
        self.__logger.info('Analyzing payees... Done')
        return self

    def get(self) -> list[Payee]:
        """Get payee data."""

        return self.__payees
