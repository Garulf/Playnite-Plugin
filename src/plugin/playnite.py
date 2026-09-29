from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from litedb_py import LiteDatabase, LiteDbError

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


_LAST_ACTIVITY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)Z$")


def _parse_last_activity(value: str | None) -> datetime | None:
    if not value:
        return None
    match = _LAST_ACTIVITY_RE.match(value)
    if not match:
        return None
    base, fraction = match.groups()
    microseconds = fraction[:6].ljust(6, "0")
    return datetime.fromisoformat(f"{base}.{microseconds}+00:00")


def _normalize_links(raw_links, name_key: str, url_key: str) -> list[dict]:
    return [
        {"name": link.get(name_key) or "Link", "url": link[url_key]}
        for link in raw_links
        if link.get(url_key)
    ]


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
        links = _normalize_links(doc.get("Links") or [], "Name", "Url")
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

    @classmethod
    def from_json_api(cls, payload: dict) -> Game:
        return cls(
            id=str(payload["id"]),
            name=payload.get("name") or "",
            is_installed=bool(payload.get("isInstalled")),
            hidden=bool(payload.get("hidden")),
            install_directory=payload.get("installDirectory") or None,
            icon=payload.get("icon") or None,
            cover_image=payload.get("coverImage") or None,
            playtime=int(payload.get("playtime") or 0),
            last_activity=_parse_last_activity(payload.get("lastActivity")),
            links=_normalize_links(payload.get("links") or [], "name", "url"),
            source=payload.get("source") or None,
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
        None if game.is_installed else "Not installed",
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


class LibraryLocked(Exception):
    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Playnite has locked its library database: {path}")


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
        if cached.is_file():
            return cached
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        stale = sorted(self.cache_dir.glob(f"{source.stem}-*.db"))
        try:
            shutil.copy(source, cached)
        except PermissionError as error:
            # Playnite opens games.db/sources.db with LiteDB's Mode=Exclusive
            # for its entire run, so the file is unreadable the whole time
            # Playnite is open. Serve the last snapshot we could read instead
            # of failing outright.
            if stale:
                return stale[-1]
            raise LibraryLocked(source) from error
        for old in stale:
            old.unlink(missing_ok=True)
        return cached

    def source_names(self) -> dict:
        path = self.library_dir / "sources.db"
        if not path.is_file():
            return {}
        try:
            with LiteDatabase(self.cached_copy(path)) as db:
                return {
                    doc["_id"]: doc["Name"]
                    for name in db.collections
                    for doc in db[name]
                    if "_id" in doc and isinstance(doc.get("Name"), str)
                }
        except LiteDbError:
            return {}

    def games(self, include_hidden: bool = False) -> "list[Game]":
        sources = self.source_names()
        with LiteDatabase(self.cached_copy(self.games_db)) as db:
            games = [Game.from_doc(doc, sources) for doc in db["Game"]]
        return [game for game in games if include_hidden or not game.hidden]
