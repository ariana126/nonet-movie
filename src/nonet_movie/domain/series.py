from ddd.domain import AggregateRoot, Entity, ValueObject
from ddd.domain.value import Identity

from nonet_movie.domain import Link

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

    def has_episode_number(self, episode_number: EpisodeNumber) -> bool:
        for episode in self.__episodes:
            if episode_number.equals(episode.number):
                return True
        return False

    def add_new_episode(self, episode_number: EpisodeNumber) -> None:
        if self.has_episode_number(episode_number):
            raise ValueError(f"Episode number {episode_number} already exists")
        self.__episodes.append(Episode(self.id, episode_number, []))

    def get_episode(self, episode_number: EpisodeNumber) -> Episode:
        for episode in self.__episodes:
            if episode_number.equals(episode.number):
                return episode
        raise ValueError(f"Episode number {episode_number} does not exist")

    def sync_episodes(self, episodes: list[Episode]) -> None:
        for episode in episodes:
            if not self.__has_episode(episode):
                self.__episodes.append(episode)
                continue
            existing_episode: Episode = self.get_episode(episode.number)
            for link in episode.links:
                existing_episode.add_link(link)

    def __has_episode(self, episode: Episode) -> bool:
        for existing_episode in self.__episodes:
            if episode.equals(existing_episode):
                return True
        return False

    def __repr__(self):
        return f'Season({self.__series_id}, {self.__number}, {self.__episodes})'

class Series(AggregateRoot):
    def __init__(self, title: str, seasons: list[Season]):
        super().__init__(Identity.from_string(title))
        self.__title = title
        self.__seasons = seasons

    @property
    def title(self) -> str:
        return self.__title

    @property
    def seasons(self) -> list[Season]:
        return self.__seasons

    def has_season_number(self, season_number: SeasonNumber) -> bool:
        for season in self.__seasons:
            if season_number.equals(season.number):
                return True
        return False

    def add_new_season(self, number: SeasonNumber) -> None:
        if self.has_season_number(number):
            raise ValueError(f'Season number {number} already exists')
        self.__seasons.append(Season(self.id, number, []))

    def get_season(self, number: SeasonNumber) -> Season:
        for season in self.__seasons:
            if number.equals(season.number):
                return season
        raise ValueError(f'Season number {number} does not exist')

    def sync_seasons(self, seasons: list[Season]) -> None:
        for season in seasons:
            if not self.__has_season(season):
                self.__seasons.append(season)
                continue
            existing_season: Season = self.get_season(season.number)
            existing_season.sync_episodes(season.episodes)

    def __has_season(self, season: Season) -> bool:
        for existing_seasons in self.__seasons:
            if season.equals(existing_seasons):
                return True
        return False

    def __repr__(self):
        return f'Series(title: {self.title}, seasons: {self.__seasons})'