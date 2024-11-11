from logging import Logger
from typing import List, Mapping, Self

from moneywiz.exception import AnalyzerException
from moneywiz.helpers import to_datetime, hash_key
from moneywiz.scheme import MwTransfer
from storage.scheme import Currency, Account, Transfer


class TransferAnalyzer:
    """Analyze transfer data."""

    __logger: Logger
    __currencies: Mapping[str, Currency]
    __accounts: Mapping[str, Account]
    __transfers: List[Transfer]

    def __init__(self, logger: Logger, currencies: List[Currency], accounts: List[Account]) -> None:
        self.__logger = logger
        self.__currencies = {currency.name: currency for currency in currencies}
        self.__accounts = {account.name: account for account in accounts}
        self.__transfers = []

    def analyze(self, transfers: List[MwTransfer]) -> Self:
        """Analyze transfer data."""

        # Try to link trivial transfers first
        unlinked = self.__link(transfers)
        # And process unlinked
        unlinked = self.__link_complex(unlinked)
        if unlinked:
            raise AnalyzerException(
                f'Orphaned transfers detected: {[hash_key(t.source, t.target, t.date, t.time) for t in unlinked]}')
        return self

    def __link(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link straightforward transfers and return unlinked list."""

        mapping = {hash_key(t.source, t.target, t.date, t.time): t for t in transfers}
        unlinked = []
        excluded = set()

        for transfer in transfers:
            key1 = hash_key(transfer.source, transfer.target, transfer.date, transfer.time)
            key2 = hash_key(transfer.target, transfer.source, transfer.date, transfer.time)
            if key1 not in excluded and key2 not in excluded:
                excluded.add(key1)
                excluded.add(key2)

                # Find pair
                pair = mapping.get(key2)
                if pair is None:
                    unlinked.append(transfer)
                    continue

                self.__transfers.append(self.__xfer(transfer, pair))

        return unlinked

    def __link_complex(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link complex transfers and return still unlinked list."""

        return transfers

    def __xfer(self, orig: MwTransfer, pair: MwTransfer) -> Transfer:
        if orig.amount[0] != '-':
            # Negative means we transfer from orig to pair
            orig, pair = pair, orig

        return Transfer(
            source=self.__accounts.get(orig.source),
            target=self.__accounts.get(orig.target),
            description="Transfer between accounts",
            date=to_datetime(orig.date, orig.time),
            source_amount=pair.amount,
            source_currency=self.__currencies.get(pair.currency),
            target_amount=orig.amount,
            target_currency=self.__currencies.get(orig.currency),
        )

    def get(self) -> List[Transfer]:
        """Get transfer data."""

        return self.__transfers
