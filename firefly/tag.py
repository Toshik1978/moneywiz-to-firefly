from logging import Logger
from typing import List

from firefly_iii_client import TagRead, TagModelStore

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

    def __sync_db(self, db: List[Tag], ff: List[TagRead]) -> None:
        # Update firefly_id for all tags exist in Firefly
        mapping = {c.attributes.tag: c for c in ff}
        for c in db:
            ff_c = mapping.get(c.name)
            if ff_c and c.firefly_id is None:
                c.firefly_id = int(ff_c.id)
                self.__logger.debug(f'Tag {c.name} updated in database. Id={c.firefly_id}')
        self.__db.add_tags(db)

    def __sync_ff(self, db: List[Tag], ff: List[TagRead]) -> None:
        # Create tag in Firefly
        mapping = {c.attributes.tag: c for c in ff}
        for c in db:
            ff_c = mapping.get(c.name)
            if ff_c is None:
                # Create tag and update database object
                c.firefly_id = self.__client.create_tag(TagModelStore(tag=c.name))
                self.__logger.debug(f'Tag {c.name} created. Id={c.firefly_id}')
        self.__db.add_tags(db)
