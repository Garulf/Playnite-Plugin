from __future__ import annotations

import json
import urllib.error
import urllib.request

from playnite import Game

DEFAULT_PORT = 38217
DEFAULT_TIMEOUT = 0.3
EXTENSION_URL = "https://github.com/Garulf/playnite-library-server/releases/latest"


class LibraryServerUnavailable(Exception):
    pass


def fetch_games(port: int = DEFAULT_PORT, include_hidden: bool = False, timeout: float = DEFAULT_TIMEOUT) -> "list[Game]":
    hidden_param = "true" if include_hidden else "false"
    url = f"http://localhost:{port}/games?hidden={hidden_param}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                raise LibraryServerUnavailable(f"unexpected status {response.status}")
            payload = json.loads(response.read())
            games = [Game.from_json_api(doc) for doc in payload]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, KeyError) as error:
        raise LibraryServerUnavailable(str(error)) from error
    return [game for game in games if include_hidden or not game.hidden]
