from urllib.parse import urlparse

from ddd.domain import ValueObject
from ddd.domain import Entity
from ddd.domain.value import Identity

class Link(ValueObject):
    def __init__(self, url: str, quality: str, size: str):
        # TODO: Use pydantic package for url validation.
        self.__validate_url(url)
        self.__url = url
        self.__quality = quality
        self.__size = size

    @staticmethod
    def __validate_url(url: str) -> None:
        try:
            urlparse(url)
        except Exception:
            raise ValueError('Invalid URL')

    def __repr__(self):
        return f'Link(url={self.__url}, quality={self.__quality}, size={self.__size})'

    @property
    def url(self) -> str:
        return self.__url

    @property
    def quality(self) -> str:
        return self.__quality

    @property
    def size(self) -> str:
        return self.__size


class Movie(Entity):
    def __init__(self, title: str, year: int, links: list[Link]) -> None:
        super().__init__(Identity.from_string(f"{title} - {year}"))
        self.__title = title
        if 1901 >= year:
            raise ValueError('There is no movie existed in the given year')
        self.__year = year
        self.__links = links

    def __repr__(self):
        return f'Movie(title={self.__title}, year={self.__year}, links={self.__links})'

    @property
    def title(self) -> str:
        return self.__title

    @property
    def year(self) -> int:
        return self.__year

    @property
    def links(self) -> list['Link']:
        return self.__links

    def add_link(self, link: Link) -> None:
        for existing_link in self.__links:
            if link.equals(existing_link):
                return
        self.__links.append(link)