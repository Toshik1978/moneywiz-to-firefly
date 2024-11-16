from logging import Logger
from typing import List, Self

from moneywiz.scheme import MwTag
from storage.scheme import Tag


class TagAnalyzer:
    """Analyze tag data."""

    __logger: Logger
    __tags: List[Tag]

    def __init__(self, logger: Logger, tags: List[Tag]) -> None:
        self.__logger = logger
        self.__tags = tags

    def analyze(self, tags: List[MwTag]) -> Self:
        """Analyze tag data."""

        self.__logger.info('Analyzing tags...')
        hashset = {t.name for t in self.__tags}
        self.__tags.extend([Tag(name=t.name) for t in tags if t.name and t.name not in hashset])
        self.__logger.info('Analyzing tags... Done')
        return self

    def get(self) -> List[Tag]:
        """Get tag data."""

        return self.__tags
