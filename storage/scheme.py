from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Currency(Base):
    """Currency record in DB."""

    __tablename__ = "currencies"
    __table_args__ = (UniqueConstraint("name", sqlite_on_conflict="IGNORE"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    """Currency ID."""

    name: Mapped[str] = mapped_column(String(12))
    """Currency name."""

    firefly_id: Mapped[int | None]
    """Firefly currency ID."""

    def __repr__(self) -> str:
        return f"Currency(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Payee(Base):
    """Payee record in DB."""

    __tablename__ = "payees"
    __table_args__ = (UniqueConstraint("name", "expense", sqlite_on_conflict="IGNORE"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    """Payee ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Payee name."""

    expense: Mapped[bool] = mapped_column(Boolean)
    """Expense category or not."""

    firefly_id: Mapped[int | None]
    """Firefly payee ID."""

    def __repr__(self) -> str:
        return f"Payee(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Category(Base):
    """Category record in DB."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", sqlite_on_conflict="IGNORE"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    """Category ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Category name."""

    firefly_id: Mapped[int | None]
    """Firefly category ID."""

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Tag(Base):
    """Tag record in DB."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("name", sqlite_on_conflict="IGNORE"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    """Tag ID."""

    name: Mapped[str] = mapped_column(String(1024))
    """Tag name."""

    firefly_id: Mapped[int | None]
    """Firefly tag ID."""

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Account(Base):
    """Account record in DB."""

    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("name", sqlite_on_conflict="IGNORE"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    """Account ID."""

    name: Mapped[str] = mapped_column(String(256))
    """Account name."""

    currency_id: Mapped[int] = mapped_column(ForeignKey("currencies.id"))
    """Currency ID."""

    balance: Mapped[str] = mapped_column(String(64))
    """Current balance."""

    firefly_id: Mapped[int | None]
    """Firefly account ID."""

    firefly_type: Mapped[str | None] = mapped_column(String(256))
    """Firefly account type."""

    currency: Mapped[Currency] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"Account(id={self.id!r}, name={self.name!r}, firefly_id={self.firefly_id!r})"


class Transfer(Base):
    """Money transfer record in DB."""

    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Transfer ID."""

    source_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    """Source account ID."""

    target_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    """Target account ID."""

    payee_id: Mapped[int | None] = mapped_column(ForeignKey("payees.id"))
    """Payee."""

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    """Category."""

    description: Mapped[str | None] = mapped_column(String(1024))
    """Description."""

    date: Mapped[datetime] = mapped_column(DateTime)
    """Date of transfer."""

    source_amount: Mapped[str] = mapped_column(String(64))
    """Amount of transfer for the source account."""

    source_currency_id: Mapped[int] = mapped_column(ForeignKey("currencies.id"))
    """Currency ID."""

    source_balance: Mapped[str] = mapped_column(String(64))
    """Balance after transfer."""

    target_amount: Mapped[str] = mapped_column(String(64))
    """Amount of transfer for the target account."""

    target_currency_id: Mapped[int] = mapped_column(ForeignKey("currencies.id"))
    """Currency ID."""

    target_balance: Mapped[str] = mapped_column(String(64))
    """Balance after transfer."""

    firefly_id: Mapped[int | None]
    """Firefly transfer ID."""

    source: Mapped[Account] = relationship("Account", foreign_keys=[source_id], lazy="selectin")

    target: Mapped[Account] = relationship("Account", foreign_keys=[target_id], lazy="selectin")

    source_currency: Mapped[Currency] = relationship("Currency", foreign_keys=[source_currency_id], lazy="selectin")

    target_currency: Mapped[Currency] = relationship("Currency", foreign_keys=[target_currency_id], lazy="selectin")

    payee: Mapped[Payee] = relationship("Payee", lazy="selectin")

    category: Mapped[Category] = relationship("Category", lazy="selectin")

    def __repr__(self) -> str:
        return f"Transfer(id={self.id!r}, name={self.get_name()!r}, firefly_id={self.firefly_id!r})"

    def get_name(self) -> str:
        """Generate name for a transfer."""

        return f"{self.source.name}-{self.target.name}-{self.date}"


class Payment(Base):
    """Payment record in DB."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Payment ID."""

    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    """Account ID."""

    payee_id: Mapped[int | None] = mapped_column(ForeignKey("payees.id"))
    """Payee."""

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    """Category."""

    description: Mapped[str | None] = mapped_column(String(1024))
    """Description."""

    date: Mapped[datetime] = mapped_column(DateTime)
    """Date of payment."""

    amount: Mapped[str] = mapped_column(String(64))
    """Amount of payment."""

    balance: Mapped[str] = mapped_column(String(64))
    """Balance after payment."""

    tag_id: Mapped[int | None] = mapped_column(ForeignKey("tags.id"))
    """Tag."""

    firefly_id: Mapped[int | None]
    """Firefly payment ID."""

    account: Mapped[Account] = relationship("Account", lazy="selectin")

    payee: Mapped[Payee] = relationship("Payee", lazy="selectin")

    category: Mapped[Category] = relationship("Category", lazy="selectin")

    tag: Mapped[Tag] = relationship("Tag", lazy="selectin")

    def __repr__(self) -> str:
        return f"Payment(id={self.id!r}, description={self.description!r}, firefly_id={self.firefly_id!r})"
