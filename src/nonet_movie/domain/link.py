from urllib.parse import urlparse

from ddd.domain import ValueObject


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

    def __str__(self):
        return self.as_string

class Link(ValueObject):
    def __init__(self, url: str, version: str, size: FileSize):
        # TODO: Use pydantic package for url validation.
        self.__validate_url(url)
        self.__url = url
        self.__version = version
        self.__size = size

    @staticmethod
    def __validate_url(url: str) -> None:
        try:
            urlparse(url)
        except Exception:
            raise ValueError('Invalid URL')

    def __repr__(self):
        return f'Link(url={self.__url}, version={self.__version}, size={self.__size})'

    @property
    def url(self) -> str:
        return self.__url

    @property
    def version(self) -> str:
        return self.__version

    @property
    def size(self) -> FileSize:
        return self.__size
