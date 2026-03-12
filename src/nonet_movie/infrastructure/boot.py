from pydm import ServiceContainer, InMemoryParametersBag

from .console.command import ConsoleCommandHandler
from .console.commands.discover import DiscoverCommandHandler
from .console.commands.search import SearchCommandHandler
from .persistence.json_db_movie_repository import JsonDBMovieRepository
from ..application.sources import BerlinSource
from .berlin_source import BerlinSourceImpl
from ..domain.service.MovieRepositoy import MovieRepository

PARAMETERS: dict[str, str] = {
    'CONSOLE_COMMAND_HANDLERS': {
        'search': SearchCommandHandler,
        'discover': DiscoverCommandHandler,
    },
    'JSON_DB_PATH': 'storage/database.json',
    'BERLIN_SOURCE_BASE_URL': 'https://berlin.saymyname.website/Movies',
}


def boot():
    service_container = ServiceContainer.get_instance()
    service_container.set_parameters(InMemoryParametersBag(PARAMETERS))

    service_container.bind_parameters(JsonDBMovieRepository, {'db_path': 'JSON_DB_PATH'})
    service_container.bind(MovieRepository, JsonDBMovieRepository)

    service_container.bind_parameters(BerlinSourceImpl, {'base_url': 'BERLIN_SOURCE_BASE_URL'})
    service_container.bind(BerlinSource, BerlinSourceImpl)

    service_container.bind_parameters(ConsoleCommandHandler, {'handlers': 'CONSOLE_COMMAND_HANDLERS'})