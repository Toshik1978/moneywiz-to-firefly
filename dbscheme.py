from typing import List, Optional
from sqlalchemy import String, ForeignKey, UniqueConstraint

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Currency(Base):
    """Currency definition in DB."""

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

    accounts: Mapped[List['Account']] = relationship(
        back_populates='currency', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"Currency(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Account(Base):
    """Account definition in DB."""

    __tablename__ = 'accounts'
    __table_args__ = (
        UniqueConstraint('name', sqlite_on_conflict='IGNORE'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    """Account ID."""

    name: Mapped[str] = mapped_column(String(256))
    """Account name."""

    currency_id: Mapped[int] = mapped_column(ForeignKey("currencies.id"))
    """Currency ID."""

    firefly_id: Mapped[Optional[int]]
    """Firefly account ID."""

    currency: Mapped['Currency'] = relationship(back_populates="accounts")

    def __repr__(self) -> str:
        return f"Account(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"
