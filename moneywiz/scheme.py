from dataclasses import dataclass


@dataclass
class MwCurrency:
    """MW currency record."""

    name: str
    """Currency name."""


@dataclass
class MwPayee:
    """MW payee record."""

    name: str
    """Payee name."""

    expense: bool
    """Expense payee or not."""


@dataclass
class MwCategory:
    """MW category record."""

    name: str
    """Category name."""


@dataclass
class MwTag:
    """MW tag record."""

    name: str
    """Tag name."""


@dataclass
class MwAccount:
    """MW account record."""

    name: str
    """Account name."""

    currency: str | None
    """Currency."""

    balance: str | None
    """Balance."""


@dataclass
class MwTransfer:
    """MW money transfer record."""

    source: str
    """Source account."""

    target: str
    """Target account."""

    payee: str
    """Payee."""

    category: str
    """Category."""

    description: str
    """Description."""

    date: str
    """Date of transfer."""

    time: str
    """Time of transfer."""

    amount: str
    """Amount of transfer."""

    currency: str
    """Currency."""

    balance: str
    """Balance."""


@dataclass
class MwPayment:
    """MW payment record."""

    account: str
    """Account."""

    payee: str
    """Payee."""

    category: str
    """Category."""

    description: str
    """Description."""

    date: str
    """Date of payment."""

    time: str
    """Time of payment."""

    amount: str
    """Amount of payment."""

    balance: str
    """Balance."""

    tag: str
    """Tag of payment."""


@dataclass
class MwData:
    currencies: list[MwCurrency]
    """All currencies."""

    payees: list[MwPayee]
    """All payees."""

    categories: list[MwCategory]
    """All categories."""

    tags: list[MwTag]
    """All tags."""

    accounts: list[MwAccount]
    """All accounts."""

    transfers: list[MwTransfer]
    """All transfers."""

    payments: list[MwPayment]
    """All payments."""
