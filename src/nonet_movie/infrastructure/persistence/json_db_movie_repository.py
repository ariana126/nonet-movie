import json
import os

from ddd.domain.value import Identity

from ...domain.movie import Movie, FileSize
from ...domain.movie import Link
from ...domain.service.MovieRepositoy import MovieRepository


class JsonDBMovieRepository(MovieRepository):
    def __init__(self, db_path: str):
        self.__db_path = db_path
        self.__loaded_records = {}
        self.__records_are_loaded = False
        self.__is_transaction_open = False

    def flush(self) -> None:
        os.makedirs(os.path.dirname(self.__db_path), exist_ok=True)
        with open(self.__db_path, "w", encoding="utf-8") as file:
            json.dump(self.__load(), file, indent=2, ensure_ascii=False)
        self.__loaded_records = {}
        self.__records_are_loaded = False
        self.__is_transaction_open = False

    def open_transaction(self) -> None:
        self.__is_transaction_open = True

    def search_in_title(self, title: str) -> list[Movie]:
        records = self.__load()
        matches: list[Movie] = []
        for record in records.values():
            if title.lower() in record["title"].lower():
                matches.append(self.__deserialize(record))
        return matches

    def find(self, id_: Identity) -> Movie|None:
        records = self.__load()
        if not id_.id() in records:
            return None
        return self.__deserialize(records[id_.id()])

    def save(self, movie: Movie) -> None:
        records = self.__load()
        key = movie.id().id()
        records[key] = self.__serialize(movie)
        self.__persist(records)

    def __load(self) -> dict:
        if self.__records_are_loaded:
            return self.__loaded_records
        if not os.path.exists(self.__db_path) or os.path.getsize(self.__db_path) == 0:
            return {}
        with open(self.__db_path, "r", encoding="utf-8") as file:
            records = json.load(file)
            self.__loaded_records = records
            self.__records_are_loaded = True
            return records

    def __persist(self, records: dict) -> None:
        self.__loaded_records = records
        if not self.__is_transaction_open:
            self.flush()

    @staticmethod
    def __serialize(movie: Movie) -> dict:
        return {
            "title": movie.title,
            "year": movie.year,
            "links": [
                {
                    "url": link.url,
                    "quality": link.quality,
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
                quality=link_data["quality"],
                size=FileSize.from_string(link_data["size"]),
            )
            for link_data in record["links"]
        ]
        return Movie(record["title"], record["year"], links)
