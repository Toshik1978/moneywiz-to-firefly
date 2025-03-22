from logging import Logger
from pathlib import Path
from typing import List, Self

from sqlalchemy import Engine, event, create_engine, select
from sqlalchemy.orm import Session

from storage.scheme import Base, Currency, Payee, Category, Tag, Account, Transfer, Payment

DB_NAME = 'MoneyWiz.sqlite'


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


class TransactionsDB:
    """Transactions database."""

    __logger: Logger
    __path: str
    __engine: Engine

    def __init__(self, logger: Logger, path: str) -> None:
        self.__logger = logger
        self.__path = path

    def init(self) -> Self:
        """Initialize database scheme."""

        self.__logger.info(f'Initializing database')
        p = Path(self.__path)
        p.mkdir(parents=True, exist_ok=True)
        self.__engine = create_engine(f'sqlite:///{p.joinpath(DB_NAME)}')
        Base.metadata.create_all(self.__engine)
        self.__logger.info(f'Initialization finished')
        return self

    def get_currencies(self) -> List[Currency]:
        """Get all currencies from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Currency)).all()]

    def get_payees(self) -> List[Payee]:
        """Get all payees from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Payee)).all()]

    def get_categories(self) -> List[Category]:
        """Get all categories from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Category)).all()]

    def get_tags(self) -> List[Tag]:
        """Get all tags from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Tag)).all()]

    def get_accounts(self) -> List[Account]:
        """Get all accounts from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Account)).all()]

    def get_transfers(self) -> List[Transfer]:
        """Get all new transfers from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Transfer).filter(Transfer.firefly_id.is_(None))).all()]

    def get_payments(self) -> List[Payment]:
        """Get all new payments from DB."""

        with Session(self.__engine) as session:
            return [c for c in session.scalars(select(Payment).filter(Payment.firefly_id.is_(None))).all()]

    def check_transfer(self, t: Transfer) -> bool:
        """Check if transfer exists in DB."""

        source_id = None if t.source is None else t.source.id
        target_id = None if t.target is None else t.target.id
        payee_id = None if t.payee is None else t.payee.id
        category_id = None if t.category is None else t.category.id
        source_currency_id = None if t.source_currency is None else t.source_currency.id
        target_currency_id = None if t.target_currency is None else t.target_currency.id

        with Session(self.__engine) as session:
            return session.scalars(
                select(Transfer)
                .where(Transfer.source_id == source_id)
                .where(Transfer.target_id == target_id)
                .where(Transfer.payee_id == payee_id)
                .where(Transfer.category_id == category_id)
                .where(Transfer.description == t.description)
                .where(Transfer.date == t.date)
                .where(Transfer.source_amount == t.source_amount)
                .where(Transfer.source_currency_id == source_currency_id)
                .where(Transfer.source_balance == t.source_balance)
                .where(Transfer.target_amount == t.target_amount)
                .where(Transfer.target_currency_id == target_currency_id)
                .where(Transfer.target_balance == t.target_balance)
            ).first() is not None

    def check_payment(self, p: Payment) -> bool:
        """Check if payment exists in DB."""

        account_id = None if p.account is None else p.account.id
        payee_id = None if p.payee is None else p.payee.id
        category_id = None if p.category is None else p.category.id
        tag_id = None if p.tag is None else p.tag.id

        with Session(self.__engine) as session:
            return session.scalars(
                select(Payment)
                .where(Payment.account_id == account_id)
                .where(Payment.payee_id == payee_id)
                .where(Payment.category_id == category_id)
                .where(Payment.description == p.description)
                .where(Payment.date == p.date)
                .where(Payment.amount == p.amount)
                .where(Payment.balance == p.balance)
                .where(Payment.tag_id == tag_id)
            ).first() is not None

    def add_currencies(self, currencies: List[Currency]) -> None:
        """Add new currencies to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for currency in currencies:
                session.add(currency)
            session.commit()

    def add_payees(self, payees: List[Payee]) -> None:
        """Add new payees to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for payee in payees:
                session.add(payee)
            session.commit()

    def add_categories(self, categories: List[Category]) -> None:
        """Add new categories to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for category in categories:
                session.add(category)
            session.commit()

    def add_tags(self, tags: List[Tag]) -> None:
        """Add new tags to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for tag in tags:
                session.add(tag)
            session.commit()

    def add_accounts(self, accounts: List[Account]) -> None:
        """Add new accounts to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for account in accounts:
                session.add(account)
            session.commit()

    def add_transfers(self, transfers: List[Transfer]) -> None:
        """Add new transfers to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for transfer in transfers:
                session.merge(transfer)
            session.commit()

    def add_payments(self, payments: List[Payment]) -> None:
        """Add new payments to DB."""

        with Session(self.__engine, expire_on_commit=False) as session:
            for payment in payments:
                session.add(payment)
            session.commit()
