from __future__ import annotations

import json
from pathlib import Path
import os
import webbrowser
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import TypedDict, List
from filters import LibraryFilter, filter_game, IsID


PLAYNITE_DIR_NAME = 'Playnite'
SCRIPT_NAME = 'FlowLauncherExporter'
DEFAULT_PLAYNITE_DIR = Path(os.getenv('APPDATA'), PLAYNITE_DIR_NAME)
EXTENSION_DATA = 'ExtensionsData'
LIBRARY_FILE = 'library.json'
PLUGIN_NAME = 'FlowLauncherExporter'
PLAYNITE_SCHEME = 'playnite://'

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

    def game(self, id: str) -> Game | None:
        """Returns a Game object by ID from the Playnite library."""
        filter = IsID(id)
        try:
            return self.search('', [filter])[0]
        except IndexError:
            return None

    def _acronym(self, text):
        return ''.join([word[0] for word in text.split()])

class ReleaseDate(TypedDict):
    """Release date of the game"""
    Day: int
    Month: int
    Year: int

class Source(TypedDict):
    """Source library of the game"""
    Name: str
    Id: str

@dataclass
class Game:
    """Playnite Game"""
    Id: str
    Name: str
    Playtime: int
    IsInstalled: bool
    InstallDirectory: str
    Icon: str
    Hidden: bool
    ReleaseDate: ReleaseDate | None 
    Source: Source | None
    Playnite: Playnite = field(repr=False)


    def _build_uri(self, action, scheme=PLAYNITE_SCHEME) -> str:
        return f"{scheme}playnite/{action}/{self.Id}"

    def get_release_date(self) -> datetime | None:
        if self.ReleaseDate:
            return datetime(self.ReleaseDate.Year, self.ReleaseDate.Month, self.ReleaseDate.Day)
        return None

    @property
    def start_uri(self) -> str:
        return self._build_uri('start')

    @property
    def show_game_uri(self) -> str:
        return self._build_uri('showgame')

    @property
    def icon_path(self) -> Path | None:
        if self.Icon:
            path = Path(self.Playnite.path, 'library', 'files', self.Icon)
            if path.is_file():
                return path
        return None

    def start(self) -> None:
        webbrowser.open(self.start_uri)

    def show_game(self) -> None:
        webbrowser.open(self.show_game_uri)

