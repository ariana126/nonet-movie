from pydm import ServiceContainer

from nonet_movie.infrastructure.boot import boot
from nonet_movie.infrastructure.console.app import ConsoleApplication


def main() -> None:
    boot()
    ServiceContainer.get_instance().get_service(ConsoleApplication).run()


if __name__ == "__main__":
    main()
