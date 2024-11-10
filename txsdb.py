from logging import Logger
from pathlib import Path

from sqlalchemy import Engine, event, create_engine, select
from sqlalchemy.orm import Session

from dbscheme import Currency, Account, Base

DB_NAME = 'MoneyWiz.sqlite'


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


class TxsDatabase:
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

    def get_currencies(self) -> dict[str, Currency]:
        """Get all currencies from DB."""

        with Session(self.__engine) as session:
            return {c.name: c for c in session.scalars(select(Currency))}

    def get_accounts(self) -> dict[str, Account]:
        """Get all accounts from DB."""

        with Session(self.__engine) as session:
            return {c.name: c for c in session.scalars(select(Account))}

    def add_account(self, account: Account) -> None:
        """Add new account with currency to DB."""

        with Session(self.__engine) as session:
            session.add(account)
            session.commit()
