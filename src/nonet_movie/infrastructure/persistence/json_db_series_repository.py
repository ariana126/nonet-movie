from ddd.domain.value import Identity
from underpy import JSON

from .json_db import JsonDB
from ...domain import Series, Season, SeasonNumber, Episode, EpisodeNumber, Link, FileSize
from ...domain.service.series_repository import SeriesRepository


class JsonDBSeriesRepository(SeriesRepository):
    __COLLECTION_NAME = 'series'
    __SEASONS_COLLECTION_NAME = 'seasons'
    __EPISODES_COLLECTION_NAME = 'episodes'

    def __init__(self, json_db: JsonDB):
        self.db = json_db

    def flush(self) -> None:
        self.db.flush()

    def open_transaction(self) -> None:
        self.db.open_transaction()

    def close_transaction(self) -> None:
        self.db.close_transaction()

    def find(self, id_: Identity) -> Series|None:
        records = self.db.load(self.__COLLECTION_NAME)
        if not id_.as_string in records:
            return None
        rich_record = self.__fetch_relations(records[id_.as_string])
        return self.__deserialize(rich_record)

    def save(self, series: Series) -> None:
        self.db.open_transaction()
        records = self.db.load(self.__COLLECTION_NAME)
        records[series.id.as_string] = self.__serialize(series)
        self.__save_seasons(series.seasons)
        self.db.persist(records, self.__COLLECTION_NAME)
        self.db.close_transaction()

    def __save_seasons(self, seasons: list[Season]) -> None:
        records = self.db.load(self.__SEASONS_COLLECTION_NAME)
        for season in seasons:
            records[season.id.as_string] = self.__serialize_season(season)
            self.__save_episodes(season.episodes)
        self.db.persist(records, self.__SEASONS_COLLECTION_NAME)

    def __save_episodes(self, episodes: list[Episode]) -> None:
        records = self.db.load(self.__EPISODES_COLLECTION_NAME)
        for episode in episodes:
            records[episode.id.as_string] = self.__serialize_episode(episode)
        self.db.persist(records, self.__EPISODES_COLLECTION_NAME)

    def __fetch_relations(self, series_record: JSON) -> JSON:
        season_records = self.db.load(self.__SEASONS_COLLECTION_NAME)
        episodes_records = self.db.load(self.__EPISODES_COLLECTION_NAME)

        series_record["seasons"] = {}
        for season_id in series_record["seasons_ids"]:
            season_record = season_records[season_id]

            season_record["episodes"] = {}
            for episode_id in season_record["episodes_ids"]:
                season_record["episodes"][episode_id] = episodes_records[episode_id]

            series_record["seasons"][season_id] = season_record

        return series_record

    @staticmethod
    def __deserialize(record: dict) -> Series:
        seasons: list[Season] = [
            Season(season_id, SeasonNumber.from_string(season_data["number"]), [
                Episode(episode_id, EpisodeNumber.from_string(episode_data["number"]), [
                    Link(link_data["url"], link_data["version"], FileSize.from_string(link_data["size"]))
                    for link_data in episode_data["links"]
                ])
                for episode_id, episode_data in season_data["episodes"].items()
            ])
            for season_id, season_data in record["seasons"].items()
        ]

        return Series(record["title"], seasons)

    @staticmethod
    def __serialize(series: Series) -> JSON:
        return {
            "title": series.title,
            "seasons_ids": [season.id.as_string for season in series.seasons],
        }

    @staticmethod
    def __serialize_season(season: Season) -> JSON:
        return {
            "number": season.number.as_string,
            "episodes_ids": [episode.id.as_string for episode in season.episodes],
        }

    @staticmethod
    def __serialize_episode(episode: Episode) -> JSON:
        return {
            "number": episode.number.as_string,
            "links": [
                {
                    "url": link.url,
                    "version": link.version,
                    "size": link.size.as_string,
                }
                for link in episode.links
            ]
        }