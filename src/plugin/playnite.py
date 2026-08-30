from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

PLAYNITE_URI_BASE = "playnite://playnite"
EXPORTER_NAME = "FlowLauncherExporter"


def start_uri(game_id: str) -> str:
    return f"{PLAYNITE_URI_BASE}/start/{game_id}"


def show_game_uri(game_id: str) -> str:
    return f"{PLAYNITE_URI_BASE}/showgame/{game_id}"


def media_path(files_dir: Path, relative: str | None) -> Path | None:
    if not relative:
        return None
    path = Path(files_dir, *relative.split("\\"))
    return path if path.is_file() else None


def format_playtime(seconds: int) -> str | None:
    minutes = seconds // 60
    if minutes <= 0:
        return None
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h played" if hours else f"{minutes}m played"


@dataclass(frozen=True)
class Game:
    id: str
    name: str
    is_installed: bool = False
    hidden: bool = False
    install_directory: str | None = None
    icon: str | None = None
    playtime: int = 0
    source: str | None = None

    @classmethod
    def from_export(cls, doc: dict) -> Game:
        source = doc.get("Source") or {}
        return cls(
            id=str(doc["Id"]),
            name=doc.get("Name") or "",
            is_installed=bool(doc.get("IsInstalled")),
            hidden=bool(doc.get("Hidden")),
            install_directory=doc.get("InstallDirectory") or None,
            icon=doc.get("Icon") or None,
            playtime=int(doc.get("Playtime") or 0),
            source=source.get("Name") or None,
        )

    @property
    def start_uri(self) -> str:
        return start_uri(self.id)

    @property
    def show_game_uri(self) -> str:
        return show_game_uri(self.id)


def game_subtitle(game: Game) -> str:
    parts = [
        game.source,
        "Installed" if game.is_installed else "Not installed",
        format_playtime(game.playtime),
    ]
    return " · ".join(part for part in parts if part)


DEFAULT_DATA_DIR = r"%APPDATA%\Playnite"


class PlayniteNotFound(Exception):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Playnite data directory not found: {path}")


class LibraryNotFound(Exception):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Playnite library export not found: {path}")


class PlayniteLibrary:
    def __init__(self, data_dir: "str | os.PathLike" = DEFAULT_DATA_DIR):
        self.data_dir = Path(os.path.expandvars(str(data_dir)))

    @property
    def library_json(self) -> Path:
        if not self.data_dir.is_dir():
            raise PlayniteNotFound(self.data_dir)
        path = self.data_dir / "ExtensionsData" / EXPORTER_NAME / "library.json"
        if not path.is_file():
            raise LibraryNotFound(path)
        return path

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "library" / "files"

    def games(self, include_hidden: bool = False) -> "list[Game]":
        with open(self.library_json, encoding="utf-8-sig") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        games = [Game.from_export(doc) for doc in data]
        return [game for game in games if include_hidden or not game.hidden]
