from rich.console import Console
from rich.table import Table

from src.nonet_movie.domain import Link


def present_links(title: str, links: list[Link]) -> None:
    console = Console()
    table = Table(title=title)
    table.add_column("version", style="cyan")
    table.add_column("size", style="magenta")
    table.add_column("url", overflow="fold", style="green")
    for link in links:
        table.add_row(link.version, link.size.as_string, link.url)
    console.print(table, justify="center")