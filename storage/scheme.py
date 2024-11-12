from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Currency(Base):
    """Currency record in DB."""

    __tablename__ = 'currencies'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Currency ID."""

    name: Mapped[str] = mapped_column(String(12))
    """Currency name."""

    firefly_id: Mapped[Optional[int]]
    """Firefly currency ID."""

    def __repr__(self) -> str:
        return f'Currency(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})'


class Payee(Base):
    """Payee record in DB."""

    __tablename__ = 'payees'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Payee ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Payee name."""

    firefly_id: Mapped[Optional[int]]
    """Firefly payee ID."""

    def __repr__(self) -> str:
        return f'Payee(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})'


class Category(Base):
    """Category record in DB."""

    __tablename__ = 'categories'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Category ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Category name."""

    firefly_id: Mapped[Optional[int]]
    """Firefly category ID."""

    def __repr__(self) -> str:
        return f'Category(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})'


class Tag(Base):
    """Tag record in DB."""

    __tablename__ = 'tags'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Tag ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Tag name."""

    firefly_id: Mapped[Optional[int]]
    """Firefly tag ID."""

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})'


class Account(Base):
    """Account record in DB."""

    __tablename__ = 'accounts'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Account ID."""

    name: Mapped[str] = mapped_column(String(256))
    """Account name."""

    currency_id: Mapped[int] = mapped_column(ForeignKey('currencies.id'))
    """Currency ID."""

    firefly_id: Mapped[Optional[int]]
    """Firefly currency ID."""

    currency: Mapped['Currency'] = relationship()

    def __repr__(self) -> str:
        return f'Account(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})'


class Transfer(Base):
    """Money transfer record in DB."""

    __tablename__ = 'transfers'

    id: Mapped[int] = mapped_column(primary_key=True)
    """Transfer ID."""

    source_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))
    """Source account ID."""

    target_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))
    """Target account ID."""

    description: Mapped[Optional[str]] = mapped_column(String(1024))
    """Description."""

    date: Mapped[datetime] = mapped_column(DateTime)
    """Date of transfer."""

    source_amount: Mapped[str] = mapped_column(String(64))
    """Amount of transfer for the source account."""

    source_currency_id: Mapped[int] = mapped_column(ForeignKey('currencies.id'))
    """Currency ID."""

    target_amount: Mapped[str] = mapped_column(String(64))
    """Amount of transfer for the target account."""

    target_currency_id: Mapped[int] = mapped_column(ForeignKey('currencies.id'))
    """Currency ID."""

    firefly_id: Mapped[Optional[int]]
    """Firefly currency ID."""

    source: Mapped['Account'] = relationship('Account', foreign_keys=[source_id])

    target: Mapped['Account'] = relationship('Account', foreign_keys=[target_id])

    source_currency: Mapped['Currency'] = relationship('Currency', foreign_keys=[source_currency_id])

    target_currency: Mapped['Currency'] = relationship('Currency', foreign_keys=[target_currency_id])

    def __repr__(self) -> str:
        return f'Transfer(id={self.id!r}, name={self.get_name()!r}, firefly_id={self.firefly_id!r})'

    def get_name(self) -> str:
        """Generate name for a transfer."""

        return f'{self.source.name}-{self.target.name}-{self.date}'


class Payment(Base):
    """Payment record in DB."""

    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True)
    """Payment ID."""

    account_id: Mapped[int] = mapped_column(ForeignKey('accounts.id'))
    """Account ID."""

    payee_id: Mapped[Optional[int]] = mapped_column(ForeignKey('payees.id'))
    """Payee."""

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'))
    """Category."""

    description: Mapped[Optional[str]] = mapped_column(String(1024))
    """Description."""

    date: Mapped[datetime] = mapped_column(DateTime)
    """Date of payment."""

    amount: Mapped[str] = mapped_column(String(64))
    """Amount of payment."""

    tag_id: Mapped[Optional[int]] = mapped_column(ForeignKey('tags.id'))
    """Tag."""

    firefly_id: Mapped[Optional[int]]
    """Firefly currency ID."""

    account: Mapped['Account'] = relationship('Account')

    payee: Mapped['Payee'] = relationship('Payee')

    category: Mapped['Category'] = relationship('Category')

    tag: Mapped['Tag'] = relationship('Tag')

    def __repr__(self) -> str:
        return f'Payment(id={self.id!r}, description={self.description!r}, firefly_id={self.firefly_id!r})'
