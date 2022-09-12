from __future__ import annotations

import json
from pathlib import Path
import os
import webbrowser
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import TypedDict, List
from filters import LibraryFilter, filter_game, IsID
from game import Game, ID


PLAYNITE_DIR_NAME = 'Playnite'
SCRIPT_NAME = 'FlowLauncherExporter'
DEFAULT_PLAYNITE_DIR = Path(os.getenv('APPDATA'), PLAYNITE_DIR_NAME)
EXTENSION_DATA = 'ExtensionsData'
LIBRARY_FILE = 'library.json'
PLUGIN_NAME = 'FlowLauncherExporter'

EPIC = 'Epic'
STEAM = 'Steam'
SOURCES = [EPIC, STEAM]

class PlayniteApp:

    def __init__(self, path: Path | str = DEFAULT_PLAYNITE_DIR):
        self._path = Path(os.path.expandvars(path))

    @property
    def path(self) -> Path:
        if self._path.is_dir():
            return self._path
        elif str(self._path).endswith(LIBRARY_FILE):
            return self._path.parent.parent.parent

    @property
    def library_path(self) -> Path:
        return self.path.joinpath(EXTENSION_DATA, PLUGIN_NAME, LIBRARY_FILE)

    def get_games(self, filter=None) -> List[Game]:
        games = []
        with open(self.library_path, encoding='utf-8-sig') as f:
            data = json.load(f)
        for game in data:
            games.append(Game(Playnite=self, **game))
        return games

    def search(self, query: str, filters: list[LibraryFilter] = []) -> List[Game]:
        """Searches the Playnite library for games matching the query."""
        games = self.get_games()
        return [game for game in games if (query.lower() in game.Name.lower() or query.lower() == self._acronym(game.Name.lower())) and filter_game(filters, game, query)]

    def game(self, id: ID) -> Game | None:
        """Returns a Game object by ID from the Playnite library."""
        filter = IsID(id)
        try:
            return self.search('', [filter])[0]
        except IndexError:
            return None

    def _acronym(self, text):
        return ''.join([word[0] for word in text.split()])