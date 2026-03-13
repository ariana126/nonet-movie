from ddd.domain.value import Identity

from .json_db import JsonDB
from ...domain import Movie, FileSize, Link
from ...domain.service.movie_repositoy import MovieRepository


class JsonDBMovieRepository(MovieRepository):
    __COLLECTION_NAME = 'movies'

    def __init__(self, json_db: JsonDB):
        self.db = json_db

    def flush(self) -> None:
        self.db.flush()

    def open_transaction(self) -> None:
        self.db.open_transaction()

    def close_transaction(self) -> None:
        self.db.close_transaction()

    def search_in_title(self, title: str) -> list[Movie]:
        records = self.db.load(self.__COLLECTION_NAME)
        matches: list[Movie] = []
        for record in records.values():
            if title.lower() in record["title"].lower():
                matches.append(self.__deserialize(record))
        return matches

    def find(self, id_: Identity) -> Movie|None:
        records = self.db.load(self.__COLLECTION_NAME)
        if not id_.as_string in records:
            return None
        return self.__deserialize(records[id_.as_string])

    def save(self, movie: Movie) -> None:
        records = self.db.load(self.__COLLECTION_NAME)
        records[movie.id.as_string] = self.__serialize(movie)
        self.db.persist(records, self.__COLLECTION_NAME)

    @staticmethod
    def __serialize(movie: Movie) -> dict:
        return {
            "title": movie.title,
            "year": movie.year,
            "links": [
                {
                    "url": link.url,
                    "version": link.version,
                    "size": link.size.as_string,
                }
                for link in movie.links
            ],
        }

    @staticmethod
    def __deserialize(record: dict) -> Movie:
        links = [
            Link(
                url=link_data["url"],
                version=link_data["version"],
                size=FileSize.from_string(link_data["size"]),
            )
            for link_data in record["links"]
        ]
        return Movie(record["title"], record["year"], links)
