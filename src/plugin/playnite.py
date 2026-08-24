from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PLAYNITE_URI_BASE = "playnite://playnite"


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
    cover_image: str | None = None
    playtime: int = 0
    last_activity: datetime | None = None
    links: list[dict] = field(default_factory=list)
    source: str | None = None

    @classmethod
    def from_doc(cls, doc: dict, source_names: dict) -> Game:
        links = [
            {"name": link.get("Name") or "Link", "url": link["Url"]}
            for link in (doc.get("Links") or [])
            if link.get("Url")
        ]
        return cls(
            id=str(doc["_id"]),
            name=doc.get("Name") or "",
            is_installed=bool(doc.get("IsInstalled")),
            hidden=bool(doc.get("Hidden")),
            install_directory=doc.get("InstallDirectory") or None,
            icon=doc.get("Icon") or None,
            cover_image=doc.get("CoverImage") or None,
            playtime=int(doc.get("Playtime") or 0),
            last_activity=doc.get("LastActivity"),
            links=links,
            source=source_names.get(doc.get("SourceId")),
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
    if game.last_activity:
        parts.append(f"last played {game.last_activity.date().isoformat()}")
    return " · ".join(part for part in parts if part)


DEFAULT_DATA_DIR = r"%APPDATA%\Playnite"
CACHE_DIR_NAME = "flow-playnite-plugin"


class PlayniteNotFound(Exception):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Playnite data directory not found: {path}")


class LibraryNotFound(Exception):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Playnite library database not found: {path}")


class PlayniteLibrary:
    def __init__(self, data_dir: "str | os.PathLike" = DEFAULT_DATA_DIR, cache_dir: "str | os.PathLike | None" = None):
        self.data_dir = Path(os.path.expandvars(str(data_dir)))
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir(), CACHE_DIR_NAME)

    @property
    def library_dir(self) -> Path:
        if not self.data_dir.is_dir():
            raise PlayniteNotFound(self.data_dir)
        return self.data_dir / "library"

    @property
    def games_db(self) -> Path:
        path = self.library_dir / "games.db"
        if not path.is_file():
            raise LibraryNotFound(path)
        return path

    @property
    def files_dir(self) -> Path:
        return self.library_dir / "files"

    def cached_copy(self, source: Path) -> Path:
        stat = source.stat()
        cached = self.cache_dir / f"{source.stem}-{stat.st_mtime_ns}-{stat.st_size}.db"
        if not cached.is_file():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            for stale in self.cache_dir.glob(f"{source.stem}-*.db"):
                stale.unlink(missing_ok=True)
            shutil.copy(source, cached)
        return cached
