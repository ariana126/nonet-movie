from ddd.domain import AggregateRoot, Entity, ValueObject
from ddd.domain.value import Identity

from nonet_movie.domain import Link, Subtitle


class EpisodeNumber(ValueObject):
    def __init__(self, number: int) -> None:
        if 0 > number:
            raise ValueError(f"EpisodeNumber({number}) must be greater than 0.")
        self.__number = number

    @property
    def as_int(self) -> int:
        return self.__number

    @property
    def as_string(self) -> str:
        if 10 > self.__number:
            return f'E0{self.__number}'
        return f'E{self.__number}'

    @staticmethod
    def from_string(value: str) -> "EpisodeNumber":
        if not 2 == len(value.split('E')) or not value.split('E')[1].isdigit():
            raise ValueError(f"Invalid episode number: {value}")
        return EpisodeNumber(int(value.split('E')[1]))

    def __str__(self):
        return self.as_string


class SeasonNumber(ValueObject):
    def __init__(self, number: int) -> None:
        if 1 > number:
            raise ValueError(f"SeasonNumber({number}) must be greater than 0.")
        self.__number = number

    @property
    def as_int(self) -> int:
        return self.__number

    @property
    def as_string(self) -> str:
        if 10 > self.__number:
            return f'S0{self.__number}'
        return f'S{self.__number}'

    @staticmethod
    def from_string(value: str) -> 'SeasonNumber':
        if not 2 == len(value.split('S')) or not value.split('S')[1].isdigit():
            raise ValueError(f'Invalid season number: {value}')
        return SeasonNumber(int(value.split('S')[1]))

    def __str__(self):
        return self.as_string


class Episode(Entity):
    def __init__(self, season_id: Identity, number: EpisodeNumber, links: list[Link]):
        super().__init__(Identity.from_string(f'{season_id} - {number}'))
        self.__season_id = season_id
        self.__number = number
        self.__links = links

    @property
    def season_id(self) -> Identity:
        return self.__season_id

    @property
    def number(self) -> EpisodeNumber:
        return self.__number

    @property
    def links(self) -> list[Link]:
        return self.__links

    def add_link(self, link: Link) -> None:
        for existing_link in self.__links:
            if link.url == existing_link.url:
                return
        self.__links.append(link)

    def add_links(self, links: list[Link]) -> None:
        for link in links:
            self.add_link(link)

    def __repr__(self):
        return f'Episode({self.__season_id}, {self.__number}, {self.__links})'


class Season(Entity):
    def __init__(self, series_id: Identity, number: SeasonNumber, episodes: list[Episode]):
        super().__init__(Identity.from_string(f'{series_id} - {number}'))
        self.__series_id = series_id
        self.__number = number
        self.__episodes = episodes

    @property
    def series_id(self) -> Identity:
        return self.__series_id

    @property
    def number(self) -> SeasonNumber:
        return self.__number

    @property
    def episodes(self) -> list[Episode]:
        return self.__episodes

    def add_episode_link(self, episode_number: EpisodeNumber, link: Link) -> None:
        for episode in self.__episodes:
            if episode_number.equals(episode.number):
                episode.add_link(link)
        self.__episodes.append(Episode(self._id, episode_number, [link]))

    def __repr__(self):
        return f'Season({self.__series_id}, {self.__number}, {self.__episodes})'

class Series(AggregateRoot):
    def __init__(self, title: str, seasons: list[Season], subtitles: list[Subtitle]|None = None) -> None:
        super().__init__(Identity.from_string(title))
        self.__title = title
        self.__seasons = seasons
        self.__subtitles = subtitles if not subtitles is None else []

    @property
    def title(self) -> str:
        return self.__title

    @property
    def seasons(self) -> list[Season]:
        return self.__seasons

    @property
    def subtitles(self) -> list[Subtitle]:
        return self.__subtitles

    def add_episode_link(self, season_number: SeasonNumber, episode_number: EpisodeNumber, link: Link) -> None:
        for season in self.__seasons:
            if season_number.equals(season.number):
                season.add_episode_link(episode_number, link)
                return
        season = Season(self._id, season_number, [])
        season.add_episode_link(episode_number, link)
        self.__seasons.append(season)

    def add_subtitles(self, subtitles: list[Subtitle]) -> None:
        for subtitle in subtitles:
            self.__add_subtitle(subtitle)

    def __add_subtitle(self, subtitle: Subtitle) -> None:
        for existing_subtitle in self.__subtitles:
            if subtitle.url == existing_subtitle.url:
                return
        self.__subtitles.append(subtitle)

    def __repr__(self):
        return f'Series(title: {self.title}, seasons: {self.__seasons})'