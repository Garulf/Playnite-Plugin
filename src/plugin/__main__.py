from litedb_py import LiteDbError
from pyflowlauncher import Plugin

from library_server import DEFAULT_PORT as DEFAULT_LIBRARY_SERVER_PORT
from library_source import games as library_source_games
from playnite import DEFAULT_DATA_DIR, LibraryLocked, LibraryNotFound, PlayniteLibrary, PlayniteNotFound
from results import build_context_menu, build_result, error_result, library_locked_result
from settings import as_bool

plugin = Plugin()


def library() -> PlayniteLibrary:
    return PlayniteLibrary(plugin.settings.get("playnite_path") or DEFAULT_DATA_DIR)


def library_server_port() -> int:
    try:
        return int(plugin.settings.get("library_server_port") or DEFAULT_LIBRARY_SERVER_PORT)
    except (TypeError, ValueError):
        return DEFAULT_LIBRARY_SERVER_PORT


def hide_uninstalled() -> bool:
    return as_bool(plugin.settings.get("hide_uninstalled"), default=True)


@plugin.on_method
async def query(query: str):
    lib = library()
    try:
        games = library_source_games(
            server_port=library_server_port(),
            include_hidden=as_bool(plugin.settings.get("show_hidden")),
            fallback=lib,
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
    if hide_uninstalled():
        games = [game for game in games if game.is_installed]
    for game in games:
        score = 0
        if query:
            match = await plugin.launcher.api.fuzzy_search(query, game.name)
            if match.score < match.score_cutoff:
                continue
            score = int(match.score)
        yield build_result(game, files_dir, score)


@plugin.on_method
def context_menu(data: list):
    if not data:
        return []
    return build_context_menu(data[0])


if __name__ == "__main__":
    plugin.run()
