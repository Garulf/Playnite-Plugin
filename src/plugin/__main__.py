# src/plugin/__main__.py
from __future__ import annotations

from litedb_py import LiteDbError
from pyflowlauncher import Plugin

from library_server import DEFAULT_PORT as DEFAULT_LIBRARY_SERVER_PORT
from library_source import games as library_source_games
from matcher import match_and_rank_games
from playnite import DEFAULT_DATA_DIR, LibraryLocked, LibraryNotFound, PlayniteLibrary, PlayniteNotFound
from results import build_context_menu, build_result, error_result, library_locked_result
from settings import should_show_hidden, should_show_uninstalled, should_use_library_server

plugin = Plugin()

_cached_library_path: str | None = None
_cached_library: PlayniteLibrary | None = None


def library() -> PlayniteLibrary:
    global _cached_library_path, _cached_library
    configured_path = plugin.settings.get("playnite_path") or DEFAULT_DATA_DIR
    if _cached_library is None or configured_path != _cached_library_path:
        _cached_library = PlayniteLibrary(configured_path)
        _cached_library_path = configured_path
    return _cached_library


def library_server_port() -> int:
    try:
        return int(plugin.settings.get("library_server_port") or DEFAULT_LIBRARY_SERVER_PORT)
    except (TypeError, ValueError):
        return DEFAULT_LIBRARY_SERVER_PORT


def show_uninstalled() -> bool:
    return should_show_uninstalled(plugin.settings)


def show_hidden() -> bool:
    return should_show_hidden(plugin.settings)


def use_library_server() -> bool:
    return should_use_library_server(plugin.settings)


@plugin.on_method
async def query(query: str):
    lib = library()
    try:
        games = library_source_games(
            server_port=library_server_port(),
            include_hidden=show_hidden(),
            fallback=lib,
            use_server=use_library_server(),
        )
        # Read eagerly, inside the try: when games come from the live server,
        # lib.games() is never called, so this is the only place a bad
        # playnite_path setting (PlayniteNotFound) would otherwise surface.
        files_dir = lib.files_dir
    except PlayniteNotFound as error:
        yield error_result("Playnite not found", f"Nothing at {error.path}. Set the data directory in settings.")
        return
    except LibraryNotFound as error:
        yield error_result("Playnite library not found", f"No database at {error.path}.")
        return
    except LibraryLocked:
        yield library_locked_result()
        return
    except LiteDbError as error:
        yield error_result("Could not read the Playnite library", str(error))
        return
    except OSError as error:
        yield error_result("Could not read the Playnite library", str(error))
        return

    if not show_uninstalled():
        games = [game for game in games if game.is_installed]

    for game, score in match_and_rank_games(games, query):
        yield build_result(game, files_dir, score)


@plugin.on_method
def context_menu(data: list):
    if not data:
        return []
    return build_context_menu(data[0])


if __name__ == "__main__":
    plugin.run()
