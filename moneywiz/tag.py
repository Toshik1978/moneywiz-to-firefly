from logging import Logger
from typing import List, Self

from moneywiz.scheme import MwTag
from storage.scheme import Tag


class TagAnalyzer:
    """Analyze tag data."""

    __logger: Logger
    __tags: List[Tag]

    def __init__(self, logger: Logger) -> None:
        self.__logger = logger
        self.__tags = []

    def analyze(self, tags: List[MwTag]) -> Self:
        """Analyze tag data."""

        self.__tags = [Tag(name=t.name) for t in tags if t.name]
        return self

    def get(self) -> List[Tag]:
        """Get tag data."""

        return self.__tags
