from logging import Logger
from typing import Self

from moneywiz.scheme import MwCategory
from storage.scheme import Category


class CategoryAnalyzer:
    """Analyze category data."""

    __logger: Logger
    __categories: list[Category]

    def __init__(self, logger: Logger, categories: list[Category]) -> None:
        self.__logger = logger
        self.__categories = categories

    def analyze(self, categories: list[MwCategory]) -> Self:
        """Analyze category data."""

        self.__logger.info('Analyzing categories...')
        hashset = {c.name for c in self.__categories}
        self.__categories.extend([Category(name=c.name) for c in categories if c.name and c.name not in hashset])
        self.__logger.info('Analyzing categories... Done')
        return self

    def get(self) -> list[Category]:
        """Get category data."""

        return self.__categories
