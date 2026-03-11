import json
import os

from ...domain.movie import Movie
from ...domain.movie import Link
from ...domain.service.MovieRepositoy import MovieRepository


class JsonDBMovieRepository(MovieRepository):
    def __init__(self, db_path: str):
        self.__db_path = db_path

    def search_in_title(self, title: str) -> list[Movie]:
        records = self.__load()
        matches: list[Movie] = []
        for record in records.values():
            if title.lower() in record["title"].lower():
                matches.append(self.__deserialize(record))
        return matches

    def save(self, movie: Movie) -> None:
        records = self.__load()
        key = movie.id().id()
        records[key] = self.__serialize(movie)
        self.__persist(records)

    def __load(self) -> dict:
        if not os.path.exists(self.__db_path) or os.path.getsize(self.__db_path) == 0:
            return {}
        with open(self.__db_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def __persist(self, records: dict) -> None:
        os.makedirs(os.path.dirname(self.__db_path), exist_ok=True)
        with open(self.__db_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)

    @staticmethod
    def __serialize(movie: Movie) -> dict:
        return {
            "title": movie.title,
            "year": movie.year,
            "links": [
                {
                    "url": link.url,
                    "quality": link.quality,
                    "size": link.size,
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
                size=link_data["size"],
            )
            for link_data in record["links"]
        ]
        return Movie(record["title"], record["year"], links)
