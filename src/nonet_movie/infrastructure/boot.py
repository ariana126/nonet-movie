from pydm import ServiceContainer, InMemoryParametersBag

from .console.command import ConsoleCommandHandler
from .console.commands.discover import DiscoverCommandHandler
from .console.commands.search import SearchCommandHandler
from .movie_source.almas_movie import AlmasMovieSource
from .movie_source.factory import MovieSourcesFactoryImpl
from .persistence.json_db_movie_repository import JsonDBMovieRepository
from ..application.movie_source import MovieSourcesFactory
from ..domain.service.MovieRepositoy import MovieRepository

PARAMETERS: dict[str, str] = {
    'CONSOLE_COMMAND_HANDLERS': {
        'search': SearchCommandHandler,
        'discover': DiscoverCommandHandler,
    },
    'JSON_DB_PATH': 'storage/database.json',
    'ALMAS_MOVIE_FILE_SERVERS_BASE_URLS': [
        'https://tokyo.saymyname.website/Movies',
        'https://berlin.saymyname.website/Movies',
        'https://nairobi.saymyname.website/Movies',
    ]
}


def boot():
    service_container = ServiceContainer.get_instance()
    service_container.set_parameters(InMemoryParametersBag(PARAMETERS))

    service_container.bind_parameters(JsonDBMovieRepository, {'db_path': 'JSON_DB_PATH'})
    service_container.bind(MovieRepository, JsonDBMovieRepository)

    service_container.bind_parameters(AlmasMovieSource, {'file_server_base_urls': 'ALMAS_MOVIE_FILE_SERVERS_BASE_URLS'})
    service_container.bind(MovieSourcesFactory, MovieSourcesFactoryImpl)

    service_container.bind_parameters(ConsoleCommandHandler, {'handlers': 'CONSOLE_COMMAND_HANDLERS'})