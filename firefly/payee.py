from logging import Logger
from typing import List

from firefly_iii_client import AccountRead, AccountStore, ShortAccountTypeProperty

from firefly.client import FireflyClient
from storage.scheme import Payee
from storage.transactions import TransactionsDB


class PayeeExporter:
    """Export payees into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the payees in the database and Firefly III."""

        self.__logger.info('Sync payees...')
        db = self.__db.get_payees()
        ff = self.__client.get_accounts()

        self.__sync_db(db, ff)
        self.__sync_ff(db, ff)
        self.__logger.info('Sync payees... Done')

    def __sync_db(self, db: List[Payee], ff: List[AccountRead]) -> None:
        # Update firefly_id for all payees exist in Firefly
        mapping = {'-'.join([str(p.attributes.name), str(p.attributes.type)]): p for p in ff}
        for p in db:
            ff_p = mapping.get('-'.join(
                [p.name, str(ShortAccountTypeProperty.EXPENSE if p.expense else ShortAccountTypeProperty.REVENUE)]))
            if ff_p and p.firefly_id is None:
                p.firefly_id = int(ff_p.id)
                self.__logger.debug(f'Payee {p.name} updated in database. Id={p.firefly_id}')
        self.__db.add_payees(db)

    def __sync_ff(self, db: List[Payee], ff: List[AccountRead]) -> None:
        # Create payee in Firefly
        mapping = {'-'.join([str(p.attributes.name), str(p.attributes.type)]): p for p in ff}
        for p in db:
            ff_p = mapping.get('-'.join(
                [p.name, str(ShortAccountTypeProperty.EXPENSE if p.expense else ShortAccountTypeProperty.REVENUE)]))
            if ff_p is None:
                # Create payee and update database object
                p.firefly_id = self.__client.create_account(AccountStore(name=p.name,
                                                                         type=ShortAccountTypeProperty.EXPENSE if p.expense else ShortAccountTypeProperty.REVENUE))
                self.__logger.debug(f'Payee {p.name} created. Id={p.firefly_id}')
        self.__db.add_payees(db)
