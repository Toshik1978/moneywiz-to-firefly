class FfCurrency:
    """Firefly currency object."""

    id: int
    """Currency ID."""

    name: str
    """Currency name."""

    code: str
    """Currency code."""

    symbol: str
    """Currency symbol."""

    enabled: bool
    """Is currency enabled?"""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __repr__(self) -> str:
        return f'FfCurrency(id={self.id!r}, name={self.name!r}, code={self.code!r}, symbol={self.symbol!r}, enabled={self.enabled!r})'
