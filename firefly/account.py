from datetime import datetime
from logging import Logger
from typing import List, Mapping

from firefly_iii_client import AccountRead, AccountStore, ShortAccountTypeProperty, AccountRoleProperty, \
    LiabilityTypeProperty, CreditCardTypeProperty, LiabilityDirectionProperty

from firefly.client import FireflyClient
from firefly.config import Config, SettingsConfig, AccountConfig
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

    def __sync_db(self, db: List[Account], ff: List[AccountRead]) -> None:
        # Update firefly_id for all accounts exist in Firefly
        mapping = {a.attributes.name: a for a in ff}
        for a in db:
            ff_a = mapping.get(a.name)
            if ff_a and a.firefly_id is None:
                a.firefly_id = int(ff_a.id)
                self.__logger.debug(f'Account {a.name} updated in database. Id={a.firefly_id}')
        self.__db.add_accounts(db)

    def __sync_ff(self, db: List[Account], ff: List[AccountRead]) -> None:
        # Create account in Firefly
        index = 0
        mapping = {a.attributes.name: a for a in ff}
        for a in db:
            ff_a = mapping.get(a.name)
            if ff_a is None:
                # Create account and update database object
                a.firefly_id = self.__client.create_account(self.__to_ff(a))
                self.__logger.debug(f'Account {a.name} created. Id={a.firefly_id}')

                index += 1
                if index % 100 == 0:
                    self.__logger.info(f'\t...{index} accounts created...')
        self.__db.add_accounts(db)

    def __to_ff(self, account: Account) -> AccountStore:
        # We have no account type and role in MoneyWiz, so in the db, too.
        # But we can use the config to get it.
        mapping = self.__accounts.get(account.name)
        account_type = ShortAccountTypeProperty(
            mapping.type if mapping is not None and mapping.type else self.__settings.default_account_type)

        ff = AccountStore(name=account.name, type=account_type, currency_code=account.currency.name)

        if account_type == ShortAccountTypeProperty.ASSET:
            ff.account_role = AccountRoleProperty(
                mapping.role if mapping is not None and mapping.role else self.__settings.default_account_role)
            if ff.account_role == AccountRoleProperty.CCASSET:
                ff.credit_card_type = CreditCardTypeProperty.MONTHLYFULL
                ff.monthly_payment_date = self.__to_date(mapping.payment_date)

        if account_type == ShortAccountTypeProperty.LIABILITY:
            ff.liability_type = LiabilityTypeProperty(mapping.liability_type)
            ff.liability_direction = LiabilityDirectionProperty.CREDIT
            ff.interest = mapping.interest

        return ff

    def __to_date(self, date: int) -> datetime:
        return datetime.now().replace(day=date)
