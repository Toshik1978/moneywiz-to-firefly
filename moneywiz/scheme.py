from typing import List


class MwCurrency:
    """MW currency record."""

    name: str
    """Currency name."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwPayee:
    """MW payee record."""

    name: str
    """Payee name."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwCategory:
    """MW category record."""

    name: str
    """Category name."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwTag:
    """MW tag record."""

    name: str
    """Tag name."""

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

    tag: str
    """Tag of payment."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class MwData:
    currencies: List[MwCurrency]
    """All currencies."""

    payees: List[MwPayee]
    """All payees."""

    categories: List[MwCategory]
    """All categories."""

    tags: List[MwTag]
    """All tags."""

    accounts: List[MwAccount]
    """All accounts."""

    transfers: List[MwTransfer]
    """All transfers."""

    payments: List[MwPayment]
    """All payments."""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)
