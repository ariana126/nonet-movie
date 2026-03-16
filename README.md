# nonet-movie

Terminal application for discovering and searching movie/series download links from configured remote file servers.

## Features

- Discover and persist new movies from remote sources
- Discover and persist series, seasons, episodes, and links
- Search movies by title and view links sorted by file size
- Search series by title with season/episode navigation
- Show local library statistics for movies and series

## Requirements

- Python 3.8+
- Internet access (discovery fetches data from remote servers)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Environment variables:

- `JSON_DB_PATH`: directory for JSON storage files (default example: `storage/`)
- `LOG_PATH`: directory for logs (default example: `logs/`)

If directories do not exist, the app creates them automatically.

## Run

Linux/macOS:

```bash
python bin/console
```

Windows (PowerShell or CMD):

```powershell
python scripts/windows_main.py
```

## How It Works

When the app starts, you get an interactive terminal menu with:

- `Search movies`
- `Search series`
- `Add new movies`
- `Add new series`
- `See statistics`

Use discovery options (`Add new movies` / `Add new series`) first to populate local storage, then use search options.

## Local Data

By default, storage is file-based JSON. The app writes collections under `JSON_DB_PATH`, including:

- `movies.json`
- `series.json`
- `seasons.json`
- `episodes.json`

Application logs are written to:

- `LOG_PATH/app.log`

## Packaging

Build scripts are included:

- Debian package: `scripts/build-deb.sh`
- macOS app bundle (`.dmg`): `scripts/build-macos-dmg.sh`
- Windows executable: `scripts/build-windows-exe.ps1`

A GitHub Actions workflow (`.github/workflows/build-installers.yml`) builds installers on tag pushes (`v*`) and publishes a release.

## Development Notes

- Runtime dependencies are defined in `pyproject.toml`
- Dev extras: `pytest`, `assertpy`
- There is currently no test suite in this repository

## License

This project is declared as `MIT` in `pyproject.toml`.
