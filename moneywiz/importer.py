import csv
from logging import Logger

from moneywiz.helpers import hash_key
from moneywiz.scheme import MwAccount, MwCurrency, MwTransfer, MwPayment, MwData, MwPayee, MwCategory, MwTag


class CsvImporter:
    """MoneyWiz CSV importer."""

    __logger: Logger
    __currencies: dict[str, MwCurrency]
    __payees: dict[str, MwPayee]
    __categories: dict[str, MwCategory]
    __tags: dict[str, MwTag]
    __accounts: dict[str, MwAccount]
    __transfers: list[MwTransfer]
    __payments: list[MwPayment]

    def __init__(self, logger: Logger):
        self.__logger = logger
        self.__currencies = {}
        self.__payees = {}
        self.__categories = {}
        self.__tags = {}
        self.__accounts = {}
        self.__transfers = []
        self.__payments = []

    def parse(self, filename: str) -> MwData:
        """Parse CSV file."""

        self.__logger.info(f'Parsing {filename}...')
        with open(filename, encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.__parse(row)
        self.__logger.info(f'Parsing {filename}... Done')

        return MwData(
            currencies=list(self.__currencies.values()),
            payees=list(self.__payees.values()),
            categories=list(self.__categories.values()),
            tags=list(self.__tags.values()),
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
                self.__parse_payment(row)
        except KeyError:
            self.__logger.error(f'Parsing failed: {row}')
            pass

    def __parse_account(self, row: dict) -> None:
        self.__logger.debug(f'Parsing account and currency: {row["Name"]}')

        currency = self.__get_currency(row['Account'])
        account = self.__get_account(row['Name'])
        account.currency = currency.name
        account.balance = row['Current balance']
        self.__accounts[account.name] = account

    def __parse_transfer(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transfer: {row["Transfers"]}')

        transfer = MwTransfer(
            source=row['Account'],
            target=row['Transfers'],
            currency=row['Currency'],
            date=row['Date'],
            time=row['Time'],
            category=row['Category'],
            description=row['Description'],
            amount=row['Amount'],
            balance=row['Balance'],
        )
        self.__transfers.append(transfer)

    def __parse_payment(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transaction: {row["Description"]}')

        self.__parse_payee(row['Payee'], row['Amount'][0] == '-')
        self.__parse_category(row['Category'])
        self.__parse_tag(row['Tags'].rstrip('; '))
        payment = MwPayment(
            account=row['Account'],
            payee=row['Payee'],
            category=row['Category'],
            description=row['Description'],
            date=row['Date'],
            time=row['Time'],
            amount=row['Amount'],
            balance=row['Balance'],
            tag=row['Tags'].rstrip('; '),
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
            account = MwAccount(name=name, currency=None, balance=None)
            self.__accounts[name] = account
        else:
            self.__logger.debug(f'Account already exists: {name}')
        return account

    def __parse_payee(self, name: str, expense: bool) -> None:
        payee = self.__payees.get(hash_key(name, str(expense)))
        if payee is None:
            self.__payees[hash_key(name, str(expense))] = MwPayee(name=name, expense=expense)
        else:
            self.__logger.debug(f'Payee already exists: {name}')

    def __parse_category(self, name: str) -> None:
        name = name.replace(b'\xe2\x96\xb6\xef\xb8\x8e'.decode('utf-8'), '-')
        category = self.__categories.get(name)
        if category is None:
            self.__categories[name] = MwCategory(name=name)
        else:
            self.__logger.debug(f'Category already exists: {name}')

    def __parse_tag(self, name: str) -> None:
        tag = self.__tags.get(name)
        if tag is None:
            self.__tags[name] = MwTag(name=name)
        else:
            self.__logger.debug(f'Tag already exists: {name}')
