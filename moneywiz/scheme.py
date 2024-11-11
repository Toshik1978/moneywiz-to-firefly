from typing import List


class MwCurrency:
    """MW currency record."""

    name: str
    """Currency name."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwAccount:
    """MW account record."""

    name: str
    """Account name."""

    currency: str
    """Currency."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwTransfer:
    """MW money transfer record."""

    source: str
    """Source account."""

    target: str
    """Target account."""

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

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


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

    tags: str
    """Tags of payment."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwData:
    currencies: List[MwCurrency]
    """All currencies."""

    accounts: List[MwAccount]
    """All accounts."""

    transfers: List[MwTransfer]
    """All transfers."""

    payments: List[MwPayment]
    """All payments."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)
