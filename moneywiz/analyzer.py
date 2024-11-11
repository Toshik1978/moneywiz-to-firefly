from datetime import datetime
from logging import Logger

from moneywiz.scheme import MwData, MwTransfer
from storage.scheme import Currency, Account, Transfer, Payment
from storage.transactions import TransactionsDB


class CsvAnalyzer:
    """Analyze parsed data from MoneyWiz CSV."""

    __logger: Logger

    __currencies: list[Currency]
    __accounts: list[Account]
    __transfers: list[Transfer]
    __payments: list[Payment]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger

    def run(self, mw: MwData) -> True:
        """Run data analysis."""

        # Prepare sets to detect accounts and currencies
        currencies = {c.name: Currency(name=c.name) for c in mw.currencies}
        accounts = {a.name: Account(name=a.name, currency=currencies.get(a.currency)) for a in mw.accounts}
        transfers = self.__link_transfers(currencies, accounts, mw.transfers)
        payments = [
            Payment(
                account=accounts.get(p.account),
                description=p.description,
                amount=p.amount,
                date=self.__get_date(p.date, p.time),
            )
            for p in mw.payments
        ]

        if not transfers:
            return False
        if not self.__check_orphaned(currencies, accounts, transfers, payments):
            return False

        # Save data
        self.__currencies = [c for c in currencies.values()]
        self.__accounts = [a for a in accounts.values()]
        self.__transfers = transfers
        self.__payments = payments
        return True

    def commit(self, db: TransactionsDB) -> None:
        """Commit changes."""

        self.__logger.info(f'Committing changes')
        db.add_currencies(self.__currencies)
        db.add_accounts(self.__accounts)
        db.add_transfers(self.__transfers)
        db.add_payments(self.__payments)
        self.__logger.info(f'Committed changes')

    def __get_date(self, date: str, time: str) -> datetime:
        dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M").astimezone()
        return dt

    def __link_transfers(self, currencies: dict[str, Currency], accounts: dict[str, Account],
                         transfers: list[MwTransfer]) -> list[Transfer] | None:
        # Build hash table for transfers
        mapping = self.__build_mapping(transfers)

        # And go through all transfers
        processed = set()
        xfers = []
        for transfer in transfers:
            key1 = self.__xfer_key(transfer, False)
            key2 = self.__xfer_key(transfer, True)
            if key1 not in processed and key2 not in processed:
                processed.add(key1)
                processed.add(key2)

                inv = mapping.get(key2)
                if inv is None:
                    self.__logger.error(f'Reverse transaction not found: {key2}')
                    continue
                xfers.append(self.__create_transfer(currencies, accounts, transfer, inv))
        return xfers

    def __build_mapping(self, transfers: list[MwTransfer]) -> dict[str, MwTransfer]:
        mapping = {}
        for transfer in transfers:
            mapping[self.__xfer_key(transfer, False)] = transfer
        return mapping

    def __xfer_key(self, transfer: MwTransfer, reverse: bool) -> str:
        if reverse:
            return f'{transfer.target}-{transfer.source}-{transfer.date}-{transfer.time}'
        else:
            return f'{transfer.source}-{transfer.target}-{transfer.date}-{transfer.time}'

    def __create_transfer(self, currencies: dict[str, Currency], accounts: dict[str, Account],
                          transfer: MwTransfer, inv: MwTransfer) -> Transfer:
        if transfer.amount[0] != '-':
            # Negative means we transfer from transfer to inv, otherwise from inv to transfer
            transfer, inv = inv, transfer

        return Transfer(
            source=accounts.get(transfer.source),
            target=accounts.get(transfer.target),
            description="Transfer between accounts",
            date=self.__get_date(transfer.date, transfer.time),
            source_amount=inv.amount,
            source_currency=currencies.get(inv.currency),
            target_amount=transfer.amount,
            target_currency=currencies.get(transfer.currency),
        )

    def __check_orphaned(self, currencies: dict[str, Currency], accounts: dict[str, Account], transfers: list[Transfer],
                         payments: list[Payment]) -> bool:
        acc_orphaned = [account.name for account in accounts.values() if account.currency is None]
        if acc_orphaned:
            self.__logger.warning(f'Orphaned accounts found: {acc_orphaned}')
            return False

        pmt_orphaned = [payment.description for payment in payments if payment.account is None]
        if pmt_orphaned:
            self.__logger.warning(f'Orphaned payments found: {pmt_orphaned}')
            return False
        return True
