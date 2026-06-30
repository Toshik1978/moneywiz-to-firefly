from logging import Logger

from firefly_iii_client import TagModelStore, TagRead

from firefly.client import FireflyClient
from storage.scheme import Tag
from storage.transactions import TransactionsDB


class TagExporter:
    """Export tags into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the tags in the database and Firefly III."""

        self.__logger.info('Sync tags...')
        db = self.__db.get_tags()
        ff = self.__client.get_tags()

        self.__sync_db(db, ff)
        self.__sync_ff(db, ff)
        self.__logger.info('Sync tags... Done')

    def __sync_db(self, db: list[Tag], ff: list[TagRead]) -> None:
        # Update firefly_id for all tags exist in Firefly
        mapping = {t.attributes.tag: t for t in ff}
        for t in db:
            ff_t = mapping.get(t.name)
            if ff_t and t.firefly_id is None:
                t.firefly_id = int(ff_t.id)
                self.__logger.debug(f'Tag {t.name} updated in database. Id={t.firefly_id}')
        self.__db.add_tags(db)

    def __sync_ff(self, db: list[Tag], ff: list[TagRead]) -> None:
        # Create tag in Firefly
        try:
            mapping = {t.attributes.tag: t for t in ff}
            for t in db:
                ff_t = mapping.get(t.name)
                if ff_t is None:
                    # Create tag and update database object
                    t.firefly_id = self.__client.create_tag(TagModelStore(tag=t.name))
                    self.__logger.debug(f'Tag {t.name} created. Id={t.firefly_id}')
        finally:
            self.__db.add_tags(db)
