from urllib.parse import urlparse

from ddd.domain import ValueObject
from ddd.domain import Entity
from ddd.domain.value import Identity

class Link(ValueObject):
    def __init__(self, url: str, quality: str):
        # TODO: Use pydantic package for url validation.
        self.__validate_url(url)
        self.__url = url
        self.__quality = quality

    @staticmethod
    def __validate_url(url: str) -> None:
        try:
            urlparse(url)
        except Exception:
            raise ValueError('Invalid URL')


class Movie(Entity):
    def __init__(self, title: str, year: int, links: list[Link]) -> None:
        super().__init__(Identity.from_string(f"{title} - {year}"))
        self.__title = title
        if 1906 >= year:
            raise ValueError('There is no movie existed in the given year')
        self.__year = year
        self.__links = links