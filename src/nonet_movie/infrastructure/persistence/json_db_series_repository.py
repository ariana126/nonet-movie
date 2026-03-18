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

    def commit(self) -> None:
        self.db.commit()

    def open_transaction(self) -> None:
        self.db.open_transaction()

    def search_in_title(self, title: str) -> list[Series]:
        records = self.db.load(self.__COLLECTION_NAME)
        matches: list[Series] = []
        for id_, record in records.items():
            if title.lower() in record["title"].lower():
                matches.append(self.__deserialize(id_, self.__fetch_relations(record)))
        return matches

    def find(self, id_: Identity) -> Series|None:
        records = self.db.load(self.__COLLECTION_NAME)
        if not id_.as_string in records:
            return None
        rich_record = self.__fetch_relations(records[id_.as_string])
        return self.__deserialize(id_.as_string, rich_record)

    def save(self, series: Series) -> None:
        self.db.open_transaction()

        self.__save_seasons(series.seasons)
        records = self.db.load(self.__COLLECTION_NAME)
        if not series.id.as_string in records:
            records[series.id.as_string] = self.__serialize(series)
        else:
            season_ids = records[series.id.as_string]["seasons_ids"]
            for season in series.seasons:
                if not season.id.as_string in season_ids:
                    season_ids.append(season.id.as_string)
        self.db.persist(records, self.__COLLECTION_NAME)
        
        self.db.commit()

    def __save_seasons(self, seasons: list[Season]) -> None:
        records = self.db.load(self.__SEASONS_COLLECTION_NAME)
        for season in seasons:
            self.__save_episodes(season.episodes)
            if not season.id.as_string in records:
                records[season.id.as_string] = self.__serialize_season(season)
                continue
            episode_ids = records[season.id.as_string]["episodes_ids"]
            for episode in season.episodes:
                if not episode.id.as_string in episode_ids:
                    episode_ids.append(episode.id.as_string)
        self.db.persist(records, self.__SEASONS_COLLECTION_NAME)

    def __save_episodes(self, episodes: list[Episode]) -> None:
        records = self.db.load(self.__EPISODES_COLLECTION_NAME)
        for episode in episodes:
            if not episode.id.as_string in records:
                records[episode.id.as_string] = self.__serialize_episode(episode)
                continue
            persisted_episode: Episode = self.__deserialize_episode(records[episode.id.as_string])
            persisted_episode.add_links(episode.links)
            records[episode.id.as_string] = self.__serialize_episode(persisted_episode)
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
    def __deserialize(id_: str, record: dict) -> Series:
        seasons: list[Season] = [
            Season(Identity.from_string(id_), SeasonNumber.from_string(season_data["number"]), [
                Episode(season_id, EpisodeNumber.from_string(episode_data["number"]), [
                    Link(link_data["url"], link_data["version"], FileSize.from_string(link_data["size"]))
                    for link_data in episode_data["links"]
                ])
                for episode_data in season_data["episodes"].values()
            ])
            for season_id, season_data in record["seasons"].items()
        ]

        return Series(record["title"], seasons)

    @staticmethod
    def __deserialize_episode(record: dict) -> Episode:
        links: list[Link] = [
            Link(link_data["url"], link_data["version"], FileSize.from_string(link_data["size"]))
            for link_data in record["links"]
        ]
        return Episode(Identity.from_string(record["season_id"]), EpisodeNumber.from_string(record["number"]), links)

    @staticmethod
    def __serialize(series: Series) -> JSON:
        return {
            "title": series.title,
            "seasons_ids": [season.id.as_string for season in series.seasons],
        }

    @staticmethod
    def __serialize_season(season: Season) -> JSON:
        return {
            "series_id": season.series_id.as_string,
            "number": season.number.as_string,
            "episodes_ids": [episode.id.as_string for episode in season.episodes],
        }

    @staticmethod
    def __serialize_episode(episode: Episode) -> JSON:
        return {
            "season_id": episode.season_id.as_string,
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