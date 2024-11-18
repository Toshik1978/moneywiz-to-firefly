from logging import Logger
from typing import List, Mapping, Self, Callable

from moneywiz.exception import AnalyzerException
from helpers import to_datetime, hash_key
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

        self.__logger.info('Analyzing transfers...')

        # Try to link trivial transfers first
        unlinked = self.__link(transfers)
        # And process unlinked
        unlinked = self.__link_complex(unlinked)
        if unlinked:
            raise AnalyzerException(
                f'Orphaned transfers detected: {[hash_key(t.source, t.target, t.date, t.time) for t in unlinked]}')
        if len(transfers) != len(self.__transfers) * 2:
            raise AnalyzerException(
                f'Missing transfers detected: {len(transfers)} vs {len(self.__transfers) * 2}')
        self.__validate()

        self.__logger.info('Analyzing transfers... Done')
        return self

    def __link(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link straightforward transfers and return unlinked list."""

        def hash_func(t: MwTransfer, pair: bool) -> str:
            # t.category can help with loan payments, otherwise it's empty
            if pair:
                return hash_key(t.target, t.source, t.date, t.time, t.category)
            else:
                return hash_key(t.source, t.target, t.date, t.time, t.category)

        return self.__link_generic(transfers, hash_func)

    def __link_complex(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link complex transfers and return still unlinked list."""

        transfers = self.__link_by_date(transfers)
        if transfers:
            transfers = self.__link_by_month(transfers)
        return transfers

    def __link_by_date(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link complex transfers within the same date and return still unlinked list."""

        def hash_func(t: MwTransfer, pair: bool) -> str:
            if pair:
                return hash_key(t.target, t.source, t.date)
            else:
                return hash_key(t.source, t.target, t.date)

        return self.__link_generic(transfers, hash_func)

    def __link_by_month(self, transfers: List[MwTransfer]) -> List[MwTransfer]:
        """Try to link complex transfers within the same month and return still unlinked list."""

        def hash_func(t: MwTransfer, pair: bool) -> str:
            date = '00' + t.date[2:]
            if pair:
                return hash_key(t.target, t.source, date)
            else:
                return hash_key(t.source, t.target, date)

        return self.__link_generic(transfers, hash_func)

    def __link_generic(self, transfers: List[MwTransfer], hash_func: Callable) -> List[MwTransfer]:
        """Try to link transfers using hash function and return unlinked list."""

        mapping = {}
        for t in transfers:
            key = hash_func(t, False)
            if key in mapping:
                self.__logger.error(f'Mapping collision: {key}')
                continue
            mapping[key] = t

        unlinked = []
        excluded = set()

        for transfer in transfers:
            key1 = hash_func(transfer, False)
            key2 = hash_func(transfer, True)
            if key1 not in excluded:
                if key2 in excluded:
                    raise AnalyzerException(f'Wrong transfers symmetry: {key1} / {key2}')

                excluded.add(key1)
                excluded.add(key2)

                # Find pair
                pair = mapping.get(key2)
                if pair is None:
                    unlinked.append(transfer)
                    continue

                self.__transfers.append(self.__xfer(transfer, pair))

        return unlinked

    def __xfer(self, orig: MwTransfer, pair: MwTransfer) -> Transfer:
        if orig.amount[0] != '-':
            # Negative means we transfer from orig to pair
            orig, pair = pair, orig

        return Transfer(
            source=self.__accounts.get(orig.source),
            target=self.__accounts.get(orig.target),
            description=f'{orig.source} -> {orig.target}',
            date=to_datetime(orig.date, orig.time),
            source_amount=orig.amount,
            source_currency=self.__currencies.get(orig.currency),
            source_balance=orig.balance,
            target_amount=pair.amount,
            target_currency=self.__currencies.get(pair.currency),
            target_balance=pair.balance,
        )

    def get(self) -> List[Transfer]:
        """Get transfer data."""

        return self.__transfers

    def __validate(self) -> None:
        # We can check if numbers are equal for the same currencies on both sides.
        transfers = [t for t in self.__transfers if
                     t.source_currency == t.target_currency and t.source_amount != '-' + t.target_amount]
        if transfers:
            raise AnalyzerException(f'Orphaned transfers detected: {transfers}')
