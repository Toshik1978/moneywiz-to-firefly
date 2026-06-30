from logging import Logger

from firefly_iii_client import CategoryRead, CategoryStore

from firefly.client import FireflyClient
from storage.scheme import Category
from storage.transactions import TransactionsDB


class CategoryExporter:
    """Export categories into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the categories in the database and Firefly III."""

        self.__logger.info("Sync categories...")
        db = self.__db.get_categories()
        ff = self.__client.get_categories()

        self.__sync_db(db, ff)
        self.__sync_ff(db, ff)
        self.__logger.info("Sync categories... Done")

    def __sync_db(self, db: list[Category], ff: list[CategoryRead]) -> None:
        # Update firefly_id for all categories exist in Firefly
        mapping = {c.attributes.name: c for c in ff}
        for c in db:
            ff_c = mapping.get(c.name)
            if ff_c and c.firefly_id is None:
                c.firefly_id = int(ff_c.id)
                self.__logger.debug(f"Category {c.name} updated in database. Id={c.firefly_id}")
        self.__db.add_categories(db)

    def __sync_ff(self, db: list[Category], ff: list[CategoryRead]) -> None:
        # Create category in Firefly
        try:
            mapping = {c.attributes.name: c for c in ff}
            for c in db:
                ff_c = mapping.get(c.name)
                if ff_c is None:
                    # Create category and update database object
                    c.firefly_id = self.__client.create_category(CategoryStore(name=c.name))
                    self.__logger.debug(f"Category {c.name} created. Id={c.firefly_id}")
        finally:
            self.__db.add_categories(db)
