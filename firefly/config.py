from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class AccountConfig:
    """Account configuration."""

    name: str
    """Account name."""

    type: str | None = None
    """Account type."""

    role: str | None = None
    """Account role."""

    payment_date: int | None = None
    """Credit card payment date."""

    liability_type: str | None = ''
    """Account liability type."""

    interest: str | None = ''
    """Account interest rate."""

    opening_balance_date: str | None = ''
    """Account opening balance date."""

    opening_balance: str | None = ''
    """Account opening balance."""

    active: bool | None = False
    """Is account active."""

    ignore: bool | None = False
    """Should we ignore this account."""


@dataclass_json
@dataclass
class SettingsConfig:
    """Settings configuration."""

    default_account_type: str
    """Default account type."""

    default_account_role: str
    """Default account role."""

    loan_payment_category: str
    """Name of the loan payment category."""

    loan_interest_category: str
    """Name of the loan interest category."""


@dataclass_json
@dataclass
class Config:
    """Export configuration file."""

    accounts: list[AccountConfig]
    """Accounts configuration."""

    settings: SettingsConfig
    """Settings configuration."""


def load_config(logger: Logger, filename: str) -> Config:
    """Load configuration from file."""

    if not filename:
        return Config(accounts=[],
                      settings=SettingsConfig(default_account_type="asset", default_account_role="defaultAsset"))

    logger.info(f'Load configuration {filename}')
    json = Path(filename).read_text()
    cfg = Config.from_json(json)
    logger.info('Configuration loaded')
    return cfg
