from logging import Logger
from pathlib import Path
from typing import List

from sqlalchemy import Engine, event, create_engine, select
from sqlalchemy.orm import Session

from storage.scheme import Base, Currency, Account, Transfer, Payment

DB_NAME = 'MoneyWiz.sqlite'


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


class TransactionsDB:
    """Transactions database."""

    __logger: Logger
    __engine: Engine

    def __init__(self, logger: Logger, path: str) -> None:
        self.__logger = logger
        self.__conn = None

        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        self.__engine = create_engine(f'sqlite:///{p.joinpath(DB_NAME)}')

    def init(self) -> None:
        """Initialize database scheme."""

        self.__logger.info(f'Initializing database')
        Base.metadata.create_all(self.__engine)
        self.__logger.info(f'Initialization finished')

    def get_currencies(self) -> List[Currency]:
        """Get all currencies from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Currency)).all()]

    def get_accounts(self) -> List[Account]:
        """Get all accounts from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Account)).all()]

    def get_transfers(self) -> List[Transfer]:
        """Get all transfers from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Transfer)).all()]

    def get_payments(self) -> List[Payment]:
        """Get all payments from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Payment)).all()]

    def add_currencies(self, currencies: List[Currency]) -> None:
        """Add new currencies to DB."""

        with Session(self.__engine) as session:
            for currency in currencies:
                session.add(currency)
            session.commit()

    def add_accounts(self, accounts: List[Account]) -> None:
        """Add new accounts to DB."""

        with Session(self.__engine) as session:
            for account in accounts:
                session.add(account)
            session.commit()

    def add_transfers(self, transfers: List[Transfer]) -> None:
        """Add new transfers to DB."""

        with Session(self.__engine) as session:
            for transfer in transfers:
                session.add(transfer)
            session.commit()

    def add_payments(self, payments: List[Payment]) -> None:
        """Add new payments to DB."""

        with Session(self.__engine) as session:
            for payment in payments:
                session.add(payment)
            session.commit()
