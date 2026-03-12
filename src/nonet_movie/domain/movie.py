from urllib.parse import urlparse

from ddd.domain import ValueObject
from ddd.domain import Entity
from ddd.domain.value import Identity

class FileSizeUnit(ValueObject):
    __MEGABYTE = 'M'
    __GIGABYTE = 'G'

    def __init__(self, unit: str) -> None:
        self.__unit = unit

    @property
    def as_string(self) -> str:
        return self.__unit

    @property
    def byte_value(self) -> int:
        if self.__MEGABYTE == self.__unit:
            return 1000
        if self.__GIGABYTE == self.__unit:
            return 1000000
        return 0

    @staticmethod
    def from_string(value: str) -> 'FileSizeUnit':
        return FileSizeUnit(value)

class FileSize(ValueObject):
    def __init__(self, quantity: float, unit: FileSizeUnit):
        self.__quantity = quantity
        self.__unit = unit

    @property
    def as_string(self) -> str:
        return f"{self.__quantity}{self.__unit.as_string}"

    @property
    def bytes(self) -> float:
        return self.__unit.byte_value * self.__quantity

    @staticmethod
    def from_string(value: str) -> 'FileSize':
        quantity = float(value[:-1])
        unit = FileSizeUnit.from_string(value[-1:])
        return FileSize(quantity, unit)

class Link(ValueObject):
    def __init__(self, url: str, quality: str, size: FileSize):
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
    def size(self) -> FileSize:
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