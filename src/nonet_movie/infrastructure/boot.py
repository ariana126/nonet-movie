from pydm import ServiceContainer, InMemoryParametersBag

from .console.command import ConsoleCommandHandler
from .console.commands.discover import DiscoverCommandHandler
from .console.commands.discovery_series import DiscoverSeriesCommandHandler
from .console.commands.search import SearchCommandHandler
from .console.commands.search_series import SearchSeriesCommandHandler
from .movie_source.almas_movie import AlmasMovieSource
from .movie_source.factory import MovieSourcesFactoryImpl, SeriesSourcesFactoryImpl
from .persistence.json_db import JsonDB
from .persistence.json_db_movie_repository import JsonDBMovieRepository
from .persistence.json_db_series_repository import JsonDBSeriesRepository
from ..application.movie_source import MovieSourcesFactory
from ..application.series_source import SeriesSourcesFactory
from ..domain.service.movie_repositoy import MovieRepository
from ..domain.service.series_repository import SeriesRepository

PARAMETERS: dict[str, str] = {
    'CONSOLE_COMMAND_HANDLERS': {
        'search': SearchCommandHandler,
        'discover': DiscoverCommandHandler,
        'search-series': SearchSeriesCommandHandler,
        'discover-series': DiscoverSeriesCommandHandler,
    },
    'JSON_DB_PATH': 'storage/',
    'ALMAS_MOVIE_MOVIES_FILE_SERVERS_BASE_URLS': [
        'https://tokyo.saymyname.website/Movies',
        'https://berlin.saymyname.website/Movies',
        'https://nairobi.saymyname.website/Movies',
    ],
    'ALMAS_MOVIE_SERIES_FILE_SERVERS_BASE_URLS': [
        'https://rio.ggusers.com/Series',
        'https://tokyo.ggusers.com/Series',
        'https://nairobi.ggusers.com/Series',
    ],
}


def boot():
    service_container = ServiceContainer.get_instance()
    service_container.set_parameters(InMemoryParametersBag(PARAMETERS))

    service_container.bind_parameters(ConsoleCommandHandler, {'handlers': 'CONSOLE_COMMAND_HANDLERS'})

    service_container.bind_parameters(JsonDB, {'db_path': 'JSON_DB_PATH'})

    service_container.bind(MovieRepository, JsonDBMovieRepository)
    service_container.bind(SeriesRepository, JsonDBSeriesRepository)

    service_container.bind(MovieSourcesFactory, MovieSourcesFactoryImpl)
    service_container.bind(SeriesSourcesFactory, SeriesSourcesFactoryImpl)

    service_container.bind_parameters(AlmasMovieSource, {
        'movie_file_servers_base_url': 'ALMAS_MOVIE_MOVIES_FILE_SERVERS_BASE_URLS',
        'series_file_servers_base_url': 'ALMAS_MOVIE_SERIES_FILE_SERVERS_BASE_URLS',
    })