from __future__ import annotations

import json
from pathlib import Path
import os
import webbrowser
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import TypedDict
from filters import LibraryFilter, filter_game, IsHidden, IsInstalled, IsSource


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


def camel_to_snake(text):
    return ''.join(['_'+char.lower() if char.isupper() else char for char in text]).lstrip('_')



class PlayniteApp:

    def __init__(self, path: Path | str = DEFAULT_PLAYNITE_DIR):
        self._path = Path(os.path.expandvars(path))

    @property
    def path(self):
        if self._path.is_dir():
            return self._path
        elif str(self._path).endswith(LIBRARY_FILE):
            return self._path.parent.parent.parent

    @property
    def library_path(self):
        return self.path.joinpath(EXTENSION_DATA, PLUGIN_NAME, LIBRARY_FILE)

    def filter_installed(self, game):
        return game['IsInstalled']

    def get_games(self, filter=None):
        games = []
        with open(self.library_path, encoding='utf-8-sig') as f:
            data = json.load(f)
        for game in data:
            games.append(Game(Playnite=self, **game))
        return games

    def search(self, query: str, filters: list[LibraryFilter] = []):
        games = self.get_games()
        return [game for game in games if (query.lower() in game.Name.lower() or query.lower() == self._acronym(game.Name.lower())) and filter_game(filters, game, query)]

    def game(self, id: str):
        games = self.get_games()
        for game in games:
            if game.Id == id:
                return game
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


    def _build_uri(self, action, scheme=PLAYNITE_SCHEME):
        return f"{scheme}playnite/{action}/{self.Id}"

    def get_release_date(self):
        if self.ReleaseDate:
            return datetime(self.ReleaseDate.Year, self.ReleaseDate.Month, self.ReleaseDate.Day)
        return None

    @property
    def start_uri(self):
        return self._build_uri('start')

    @property
    def show_game_uri(self):
        return self._build_uri('showgame')

    @property
    def icon_path(self):
        if self.Icon:
            path = Path(self.Playnite.path, 'library', 'files', self.Icon)
            if path.is_file():
                return path
        return ''

    def start(self):
        webbrowser.open(self.start_uri)

    def show_game(self):
        webbrowser.open(self.show_game_uri)


if __name__ == "__main__":
    pn = PlayniteApp()
    games = pn.search(None, [IsSource('Epic')])
    print(games)
    print(len(games))
