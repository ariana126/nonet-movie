import urllib.parse

from nonet_movie.application.subtitle import SubtitleSource
from nonet_movie.domain import Series, Subtitle, Movie


class SubzoneSource(SubtitleSource):
    def __init__(self):
        self.base_url = 'https://subzone.ir'
        self.search_path = 'subtitles/searchbytitle'

    def get_subtitles_for_movie(self, movie: Movie) -> list[Subtitle]:
        query = f"{movie.title} {movie.year}"
        encoded_query = urllib.parse.urlencode({"query": query})
        search_url = f"{self.base_url}/{self.search_path}?{encoded_query}"
        return [Subtitle(search_url, 'Subzone')]

    def get_subtitles_for_series(self, series: Series) -> list[Subtitle]:
        encoded_query = urllib.parse.urlencode({"query": series.title})
        search_url = f"{self.base_url}/{self.search_path}?{encoded_query}"
        return [Subtitle(search_url, 'Subzone')]
