from ddd.domain import AggregateRoot
from ddd.domain.value import Identity

from nonet_movie.domain import Link
from nonet_movie.domain import Subtitle


class Movie(AggregateRoot):
    def __init__(self, title: str, year: int, links: list[Link], subtitles: list[Subtitle]|None = None) -> None:
        super().__init__(Identity.from_string(f"{title} - {year}"))
        self.__title = title
        if 1901 >= year:
            raise ValueError('There is no movie existed in the given year')
        self.__year = year
        self.__links = links
        self.__subtitles = subtitles if not subtitles is None else []

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

    @property
    def subtitles(self) -> list['Subtitle']:
        return self.__subtitles

    def add_links(self, links: list[Link]) -> None:
        for link in links:
            self.__add_link(link)

    def __add_link(self, link: Link) -> None:
        for existing_link in self.__links:
            if link.url == existing_link.url:
                return
        self.__links.append(link)

    def add_subtitles(self, subtitles: list[Subtitle]) -> None:
        for subtitle in subtitles:
            self.__add_subtitle(subtitle)

    def __add_subtitle(self, subtitle: Subtitle) -> None:
        for existing_subtitle in self.__subtitles:
            if subtitle.url == existing_subtitle.url:
                return
        self.__subtitles.append(subtitle)