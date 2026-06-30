from calendar import monthrange
from collections.abc import Mapping
from datetime import datetime
from logging import Logger

from firefly_iii_client import (
    AccountRead,
    AccountRoleProperty,
    AccountStore,
    AccountUpdate,
    CreditCardTypeProperty,
    InterestPeriodProperty,
    LiabilityDirectionProperty,
    LiabilityTypeProperty,
    ShortAccountTypeProperty,
)

from firefly.client import FireflyClient
from firefly.config import AccountConfig, Config, SettingsConfig
from helpers import to_datetime
from storage.scheme import Account
from storage.transactions import TransactionsDB


class AccountExporter:
    """Export accounts into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[str, AccountConfig]
    __settings: SettingsConfig

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient, config: Config):
        self.__logger = logger
        self.__db = db
        self.__client = client
        self.__accounts = {a.name: a for a in config.accounts}
        self.__settings = config.settings

    def sync(self) -> None:
        """Synchronize the accounts in the database and Firefly III."""

        self.__logger.info('Sync accounts...')
        db = self.__db.get_accounts()
        ff = self.__client.get_accounts()

        self.__sync_db(db, ff)
        self.__sync_ff(db, ff)
        self.__logger.info('Sync accounts... Done')

    def __sync_db(self, db: list[Account], ff: list[AccountRead]) -> None:
        # Update firefly_id for all accounts exist in Firefly
        mapping = {a.attributes.name: a for a in ff}
        for a in db:
            ff_a = mapping.get(a.name)
            if ff_a and a.firefly_id is None:
                a.firefly_id = int(ff_a.id)
                self.__logger.debug(f'Account {a.name} updated in database. Id={a.firefly_id}')
        self.__db.add_accounts(db)

    def __sync_ff(self, db: list[Account], ff: list[AccountRead]) -> None:
        # Create account in Firefly
        index = 0
        try:
            mapping = {a.attributes.name: a for a in ff}
            for a in db:
                ff_a = mapping.get(a.name)
                if ff_a is None:
                    # Create account and update database object
                    ff_a = self.__to_ff(a)
                    if ff_a is not None:
                        a.firefly_id = self.__client.create_account(ff_a)
                        a.firefly_type = str(ff_a.type)
                        self.__logger.debug(f'Account {a.name} created. Id={a.firefly_id}')

                        index += 1
                        if index % 100 == 0:
                            self.__logger.info(f'\t...{index} accounts created...')
                else:
                    # If we have account, let's check if we want to disable it.
                    # We don't want to delete anything, so we will disable ignored accounts, too.
                    config = self.__accounts.get(ff_a.attributes.name)
                    if config is not None:
                        if ff_a.attributes.active and (not config.active or config.ignore):
                            self.__client.update_account(ff_a.id, AccountUpdate(name=ff_a.attributes.name, active=False,
                                                                                include_net_worth=False))
        finally:
            self.__logger.info(f'{index} accounts created in total')
            self.__db.add_accounts(db)

    def __to_ff(self, account: Account) -> AccountStore | None:
        # We have no account type and role in MoneyWiz, so in the db, too.
        # But we can use the config to get it.
        config = self.__accounts.get(account.name)
        if config is None or config.ignore:
            return None

        account_type = ShortAccountTypeProperty(
            config.type if config.type else self.__settings.default_account_type)

        ff = AccountStore(name=account.name, type=account_type, currency_code=account.currency.name)
        ff.active = config.active
        ff.include_net_worth = config.active
        if config.opening_balance_date:
            ff.opening_balance_date = to_datetime(config.opening_balance_date, '00:00')
            ff.opening_balance = config.opening_balance

        if account_type == ShortAccountTypeProperty.ASSET:
            ff.account_role = AccountRoleProperty(
                config.role if config.role else self.__settings.default_account_role)
            if ff.account_role == AccountRoleProperty.CCASSET:
                ff.credit_card_type = CreditCardTypeProperty.MONTHLYFULL
                ff.monthly_payment_date = self.__to_date(config.payment_date)

        if account_type == ShortAccountTypeProperty.LIABILITY:
            ff.liability_type = LiabilityTypeProperty(config.liability_type)
            ff.liability_direction = LiabilityDirectionProperty.DEBIT
            ff.interest = config.interest
            ff.interest_period = InterestPeriodProperty.MONTHLY

        return ff

    def __to_date(self, date: int) -> datetime:
        now = datetime.now()
        # Clamp the configured payment day to a valid day for the current month
        # (e.g. day 31 in a 30-day month would otherwise raise ValueError).
        last_day = monthrange(now.year, now.month)[1]
        return now.replace(day=min(date, last_day))
