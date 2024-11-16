from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class AccountConfig:
    """Account configuration."""

    name: str
    """Account name."""

    type: Optional[str] = None
    """Account type."""

    role: Optional[str] = None
    """Account role."""

    payment_date: Optional[int] = None
    """Credit card payment date."""

    liability_type: Optional[str] = ''
    """Account liability type."""

    interest: Optional[str] = ''
    """Account interest rate."""


@dataclass_json
@dataclass
class SettingsConfig:
    """Settings configuration."""

    default_account_type: str
    """Default account type."""

    default_account_role: str
    """Default account role."""


@dataclass_json
@dataclass
class Config:
    """Export configuration file."""

    accounts: List[AccountConfig]
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
