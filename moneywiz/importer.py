import csv
from logging import Logger

from moneywiz.scheme import MwAccount, MwCurrency, MwTransfer, MwPayment, MwData


class CsvImporter:
    """MoneyWiz CSV importer."""

    __logger: Logger
    __currencies: dict[str, MwCurrency]
    __accounts: dict[str, MwAccount]
    __transfers: list[MwTransfer]
    __payments: list[MwPayment]

    def __init__(self, logger: Logger):
        self.__logger = logger
        self.__currencies = {}
        self.__accounts = {}
        self.__transfers = []
        self.__payments = []

    def parse(self, filename: str) -> MwData:
        """Parse CSV file."""

        self.__logger.info(f'Parsing {filename}')
        with open(filename, encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.__parse(row)

        return MwData(
            currencies=list(self.__currencies.values()),
            accounts=list(self.__accounts.values()),
            transfers=self.__transfers,
            payments=self.__payments,
        )

    def __parse(self, row: dict) -> None:
        try:
            if row['Name']:
                self.__parse_account(row)
            elif row['Transfers']:
                self.__parse_transfer(row)
            else:
                self.__parse_tx(row)
        except KeyError:
            self.__logger.error(f'Parsing failed: {row}')
            pass

    def __parse_account(self, row: dict) -> None:
        self.__logger.debug(f'Parsing account and currency: {row["Name"]}')

        currency = self.__get_currency(row['Account'])
        account = self.__get_account(row['Name'])
        account.currency = currency.name
        self.__accounts[account.name] = account

    def __parse_transfer(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transfer: {row["Transfers"]}')

        transfer = MwTransfer(
            source=row['Account'],
            target=row['Transfers'],
            currency=row['Currency'],
            date=row['Date'],
            time=row['Time'],
            description=row['Description'],
            amount=row['Amount'],
        )
        self.__transfers.append(transfer)

    def __parse_tx(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transaction: {row["Description"]}')

        payment = MwPayment(
            account=row['Account'],
            payee=row['Payee'],
            category=row['Category'],
            description=row['Description'],
            date=row['Date'],
            time=row['Time'],
            amount=row['Amount'],
            tags=row['Tags'],
        )
        self.__payments.append(payment)

    def __get_currency(self, name: str) -> MwCurrency:
        currency = self.__currencies.get(name)
        if currency is None:
            currency = MwCurrency(name=name)
            self.__currencies[name] = currency
        else:
            self.__logger.debug(f'Currency already exists: {name}')
        return currency

    def __get_account(self, name: str) -> MwAccount:
        account = self.__accounts.get(name)
        if account is None:
            account = MwAccount(name=name)
            self.__accounts[name] = account
        else:
            self.__logger.debug(f'Account already exists: {name}')
        return account
