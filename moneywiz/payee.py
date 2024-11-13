from logging import Logger
from typing import List, Self

from moneywiz.helpers import hash_key
from moneywiz.scheme import MwPayee
from storage.scheme import Payee


class PayeeAnalyzer:
    """Analyze payee data."""

    __logger: Logger
    __payees: List[Payee]

    def __init__(self, logger: Logger, payees: List[Payee]) -> None:
        self.__logger = logger
        self.__payees = payees

    def analyze(self, payees: List[MwPayee]) -> Self:
        """Analyze payee data."""

        hashset = {hash_key(p.name, str(p.expense)) for p in self.__payees}
        self.__payees.extend([Payee(name=p.name, expense=p.expense) for p in payees if
                              p.name and hash_key(p.name, str(p.expense)) not in hashset])
        return self

    def get(self) -> List[Payee]:
        """Get payee data."""

        return self.__payees
