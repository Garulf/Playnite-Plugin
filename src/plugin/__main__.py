from litedb_py import LiteDbError
from pyflowlauncher import Plugin

from playnite import DEFAULT_DATA_DIR, LibraryNotFound, PlayniteLibrary, PlayniteNotFound
from results import build_context_menu, build_result, error_result
from settings import as_bool

plugin = Plugin()


def library() -> PlayniteLibrary:
    return PlayniteLibrary(plugin.settings.get("playnite_path") or DEFAULT_DATA_DIR)


@plugin.on_method
async def query(query: str):
    lib = library()
    try:
        games = lib.games(include_hidden=as_bool(plugin.settings.get("show_hidden")))
    except PlayniteNotFound as error:
        yield error_result("Playnite not found", f"Nothing at {error.path}. Set the data directory in settings.")
        return
    except LibraryNotFound as error:
        yield error_result("Playnite library not found", f"No database at {error.path}.")
        return
    except LiteDbError as error:
        yield error_result("Could not read the Playnite library", str(error))
        return
    except OSError as error:
        yield error_result("Could not read the Playnite library", str(error))
        return
    for game in games:
        score = 0
        if query:
            match = await plugin.launcher.api.fuzzy_search(query, game.name)
            if match.score < match.score_cutoff:
                continue
            score = int(match.score)
        yield build_result(game, lib.files_dir, score)


@plugin.on_method
def context_menu(data: list):
    if not data:
        return []
    return build_context_menu(data[0])


plugin.run()
