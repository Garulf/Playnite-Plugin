from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import webbrowser
from typing import TypedDict, TYPE_CHECKING, Union

PLAYNITE_SCHEME = 'playnite://'

if TYPE_CHECKING:
    from playnite import PlayniteApp

class ReleaseDate(TypedDict):
    """Release date of the game"""
    Day: int
    Month: int
    Year: int

class Source(TypedDict):
    """Source library of the game"""
    Name: str
    Id: str

ID = str
NAME = str
PLAYTIME = int
IS_INSTALLED = bool
INSTALL_DIRECTORY = str
ICON = str
HIDDEN = bool
RELEASE_DATE = Union[ReleaseDate, None]
SOURCE = Union[Source, None]
PLAYNITE = 'PlayniteApp'

@dataclass
class Game:
    """Playnite Game"""
    Id: ID
    Name: NAME
    Playtime: PLAYTIME
    IsInstalled: IS_INSTALLED
    InstallDirectory: INSTALL_DIRECTORY
    Icon: ICON
    Hidden: HIDDEN
    ReleaseDate: RELEASE_DATE 
    Source: SOURCE
    Playnite: PLAYNITE = field(repr=False)


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