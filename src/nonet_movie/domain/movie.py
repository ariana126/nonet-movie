from ddd.domain import AggregateRoot
from ddd.domain.value import Identity

from nonet_movie.domain import Link


class Movie(AggregateRoot):
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
            if link.url == existing_link.url:
                return
        self.__links.append(link)