import csv
from logging import Logger

from dbscheme import Account, Currency
from txsdb import TxsDatabase


class TxsImporter:
    """MoneyWiz CSV importer."""

    __logger: Logger
    __db: TxsDatabase
    __currencies: dict[str, Currency]
    __accounts: dict[str, Account]

    def __init__(self, logger: Logger, db: TxsDatabase):
        self.__logger = logger
        self.__db = db
        self.__currencies = db.get_currencies()
        self.__accounts = db.get_accounts()

    def parse(self, filename: str) -> None:
        """Parse CSV file."""

        self.__logger.info(f'Parsing {filename}')
        with open(filename, encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.__parse(row)

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

        name = row['Name']
        if self.__accounts.get(name):
            self.__logger.debug(f'Account already exists: {name}')
            return

        currency_name = row['Account']
        currency = self.__currencies.get(currency_name)

        if currency is None:
            currency = Currency(
                name=row['Account']
            )
            self.__currencies[currency_name] = currency
        else:
            self.__logger.debug(f'Currency already exists: {currency_name}')

        account = Account(
            name=name,
            currency=currency,
        )
        self.__db.add_account(account)
        self.__accounts[name] = account

    def __parse_transfer(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transfer: {row["Transfers"]}')

    def __parse_tx(self, row: dict) -> None:
        self.__logger.debug(f'Parsing transaction: {row["Description"]}')
