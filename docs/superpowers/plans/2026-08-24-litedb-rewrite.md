# Playnite Plugin LiteDB Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Playnite Flow Launcher plugin as v3.0.0 on pyflowlauncher (`python_v2`), reading Playnite's `games.db` directly with litedb-py, no Playnite-side extension.

**Architecture:** Three flat modules under `src/plugin/` (Flow runs them via a `run.py` shim + `runpy`, so imports are absolute, not package-relative): `playnite.py` owns library location, DB copy/cache, and the `Game` model; `results.py` builds Flow `Result` objects (main results, context menus, error results); `__main__.py` only wires the pyflowlauncher `Plugin` and its `query`/`context_menu` methods. Everything except `__main__.py` is unit-tested on Linux.

**Tech Stack:** Python 3.12, pyflowlauncher 1.1.0, litedb-py 0.1.0, uv, tox + pytest, pre-commit, release-please, readwright.

**Spec:** `docs/superpowers/specs/2026-08-24-litedb-rewrite-design.md`

## Global Constraints

- Plugin identity is fixed, verbatim: ID `625A2812D5364D708582FDD9ACCD8C93`, Name `Playnite`, ActionKeyword `pn`, Version `3.0.0`, Language `python_v2`.
- Runtime deps pinned exactly: `pyflowlauncher==1.1.0`, `litedb-py==0.1.0`.
- Runtime target is Windows (Flow Launcher, Python 3.12); the test suite must pass on this Linux container. Never call `os.startfile` or assume `\\` is `os.sep` — DB media paths use backslashes and are split manually.
- Conventional Commits; no em dashes anywhere in commits, code, or docs; no AI attribution of any kind.
- Work happens on branch `rewrite/litedb` in `~/projects/Playnite-Plugin`.
- All test commands run from the repo root: `uv run pytest ...`.

---

### Task 1: Scaffold v3 layout and toolchain

**Files:**
- Delete: `plugin/` (entire dir), `run.py`, `plugin.json`, `SettingsTemplate.yaml`, `requirements.txt` (all at repo root, v2 leftovers)
- Move: `icon.png` -> `data/icon.png` (`git mv`)
- Create: `data/plugin.json`, `data/SettingsTemplate.yaml`, `src/run.py`, `src/plugin/__init__.py` (empty), `requirements.txt`, `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml`, `LICENSE`, `tests/__init__.py` (empty)

**Interfaces:**
- Produces: repo skeleton every later task builds on; `uv run pytest` works (collects 0 tests); `uv sync` resolves runtime + dev deps.

- [ ] **Step 1: Remove v2 files and move the icon**

```bash
cd ~/projects/Playnite-Plugin
git rm -r plugin run.py plugin.json SettingsTemplate.yaml requirements.txt
mkdir -p data src/plugin tests
git mv icon.png data/icon.png
```

- [ ] **Step 2: Write the manifest** — `data/plugin.json`:

```json
{
  "ID": "625A2812D5364D708582FDD9ACCD8C93",
  "ActionKeyword": "pn",
  "Name": "Playnite",
  "Description": "Search and launch your Playnite library.",
  "Author": "Garulf",
  "Version": "3.0.0",
  "Language": "python_v2",
  "Website": "https://github.com/Garulf/Playnite-Plugin",
  "IcoPath": "icon.png",
  "ExecuteFileName": "run.py"
}
```

- [ ] **Step 3: Write the settings template** — `data/SettingsTemplate.yaml`:

```yaml
body:
  - type: textBlock
    attributes:
      name: description
      description: >
        Search and launch your Playnite library.
  - type: input
    attributes:
      name: playnite_path
      label: "Playnite Data Directory:"
      defaultValue: "%APPDATA%\\Playnite"
      description: Playnite data directory (the folder containing "library"). Change this for portable installs.
  - type: checkbox
    attributes:
      name: show_hidden
      label: "Show Hidden Games"
      defaultValue: "false"
      description: Include games marked hidden in Playnite.
```

- [ ] **Step 4: Write the runner shim** — `src/run.py`, verbatim from Steam-Search:

```python
# run.py — generic shim, identical across all plugins
import runpy
import sys
import os

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin")

sys.path.insert(0, os.path.join(PLUGIN_DIR, "site-packages"))
runpy.run_path(PLUGIN_DIR, run_name="__main__")
```

- [ ] **Step 5: Write dependency and tool config**

`requirements.txt`:

```
pyflowlauncher==1.1.0
litedb-py==0.1.0
```

`pyproject.toml`:

```toml
[project]
name = "playnite-plugin"
version = "3.0.0"
description = "Search and launch your Playnite library from Flow Launcher."
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "pyflowlauncher==1.1.0",
    "litedb-py==0.1.0",
]

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
pythonpath = ["src/plugin"]
testpaths = ["tests"]
```

`tox.ini`:

```ini
[tox]
env_list = py312

[testenv]
deps =
    pytest>=8
    -r requirements.txt
commands = pytest {posargs}
```

- [ ] **Step 6: Write `.pre-commit-config.yaml` and MIT `LICENSE`**

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.3
    hooks:
      - id: gitleaks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json
      - id: check-toml
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        stages: [pre-push]
```

`LICENSE`: standard MIT text, `Copyright (c) 2026 Garulf`.

- [ ] **Step 7: Verify the toolchain**

```bash
uv sync
uv run python -c "import pyflowlauncher, litedb_py; print('ok')"
uv run pytest; echo "exit $?"   # exit 5 (no tests collected) is expected
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Expected: `ok` printed; pytest exits 5; hooks installed. If `litedb-py==0.1.0` fails to resolve from PyPI, stop and report — do not substitute a git dependency silently.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat!: scaffold python_v2 plugin layout, drop FlowLauncherExporter dependency"
```

---

### Task 2: Game model and formatting (`playnite.py`, part 1)

**Files:**
- Create: `src/plugin/playnite.py`
- Test: `tests/test_game.py`

**Interfaces:**
- Produces (consumed by Tasks 3-6):
  - `Game` frozen dataclass: fields `id: str`, `name: str`, `is_installed: bool`, `hidden: bool`, `install_directory: str | None`, `icon: str | None`, `cover_image: str | None`, `playtime: int` (seconds), `last_activity: datetime | None`, `links: list[dict]` (each `{"name": str, "url": str}`), `source: str | None`; properties `start_uri: str`, `show_game_uri: str`; classmethod `Game.from_doc(doc: dict, source_names: dict) -> Game`
  - `start_uri(game_id: str) -> str`, `show_game_uri(game_id: str) -> str`
  - `media_path(files_dir: Path, relative: str | None) -> Path | None`
  - `format_playtime(seconds: int) -> str | None`
  - `game_subtitle(game: Game) -> str`

- [ ] **Step 1: Write failing tests** — `tests/test_game.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from playnite import Game, format_playtime, game_subtitle, media_path

GAME_ID = "033b6530-47a6-4179-a8fa-c1197ea4f335"
SOURCE_ID = UUID("7f5440ce-70e1-4c3b-a33f-09ed280284eb")


def doc(**overrides):
    base = {
        "_id": UUID(GAME_ID),
        "Name": "Grand Theft Auto V Enhanced",
        "IsInstalled": True,
        "Hidden": False,
        "InstallDirectory": r"F:\SteamLibrary\steamapps\common\GTA V",
        "Icon": GAME_ID + r"\icon.ico",
        "CoverImage": GAME_ID + r"\cover.jpg",
        "Playtime": 7200,
        "LastActivity": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "Links": [{"Name": "Steam", "Url": "https://store.steampowered.com/app/3240220"}],
        "SourceId": SOURCE_ID,
    }
    base.update(overrides)
    return base


def test_from_doc_maps_fields():
    game = Game.from_doc(doc(), {SOURCE_ID: "Steam"})
    assert game.id == GAME_ID
    assert game.name == "Grand Theft Auto V Enhanced"
    assert game.is_installed
    assert game.source == "Steam"
    assert game.links == [{"name": "Steam", "url": "https://store.steampowered.com/app/3240220"}]


def test_from_doc_tolerates_missing_optionals():
    minimal = {"_id": UUID(GAME_ID), "Name": "Bare"}
    game = Game.from_doc(minimal, {})
    assert not game.is_installed
    assert game.icon is None
    assert game.last_activity is None
    assert game.links == []
    assert game.source is None
    assert game.playtime == 0


def test_links_without_url_are_dropped():
    game = Game.from_doc(doc(Links=[{"Name": "Broken"}, {"Url": "https://x.example"}]), {})
    assert game.links == [{"name": "Link", "url": "https://x.example"}]


def test_uris():
    game = Game.from_doc(doc(), {})
    assert game.start_uri == f"playnite://playnite/start/{GAME_ID}"
    assert game.show_game_uri == f"playnite://playnite/showgame/{GAME_ID}"


def test_media_path_splits_backslashes(tmp_path):
    target = tmp_path / GAME_ID / "icon.ico"
    target.parent.mkdir()
    target.write_bytes(b"x")
    assert media_path(tmp_path, GAME_ID + r"\icon.ico") == target
    assert media_path(tmp_path, GAME_ID + r"\missing.ico") is None
    assert media_path(tmp_path, None) is None


def test_format_playtime():
    assert format_playtime(0) is None
    assert format_playtime(59) is None
    assert format_playtime(120) == "2m played"
    assert format_playtime(7200) == "2h played"


def test_game_subtitle():
    game = Game.from_doc(doc(), {SOURCE_ID: "Steam"})
    assert game_subtitle(game) == "Steam · Installed · 2h played · last played 2026-08-14"
    bare = Game.from_doc({"_id": UUID(GAME_ID), "Name": "Bare"}, {})
    assert game_subtitle(bare) == "Not installed"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_game.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'playnite'`

- [ ] **Step 3: Implement** — `src/plugin/playnite.py`:

```python
from __future__ import annotations

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
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/test_game.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/plugin/playnite.py tests/test_game.py
git commit -m "feat: add Game model, playnite URIs, and subtitle formatting"
```

---

### Task 3: Library location and DB copy cache (`playnite.py`, part 2)

**Files:**
- Modify: `src/plugin/playnite.py` (append)
- Test: `tests/test_library.py` (new)

**Interfaces:**
- Consumes: Task 2's module contents (same file).
- Produces (consumed by Tasks 4-6):
  - `PlayniteNotFound(Exception)` with `.path`; `LibraryNotFound(Exception)` with `.path`
  - `DEFAULT_DATA_DIR = r"%APPDATA%\Playnite"`
  - `PlayniteLibrary(data_dir=DEFAULT_DATA_DIR, cache_dir=None)` with properties `data_dir: Path` (env vars expanded), `library_dir: Path` (raises `PlayniteNotFound` if data dir missing), `games_db: Path` (raises `LibraryNotFound` if missing), `files_dir: Path`, and method `cached_copy(source: Path) -> Path`

- [ ] **Step 1: Write failing tests** — `tests/test_library.py`:

```python
import pytest

from playnite import LibraryNotFound, PlayniteLibrary, PlayniteNotFound


def make_data_dir(tmp_path, with_db=True):
    library = tmp_path / "Playnite" / "library"
    library.mkdir(parents=True)
    if with_db:
        (library / "games.db").write_bytes(b"original")
    return tmp_path / "Playnite"


def test_missing_data_dir_raises(tmp_path):
    lib = PlayniteLibrary(tmp_path / "nope", cache_dir=tmp_path / "cache")
    with pytest.raises(PlayniteNotFound):
        _ = lib.library_dir


def test_missing_games_db_raises(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path, with_db=False), cache_dir=tmp_path / "cache")
    with pytest.raises(LibraryNotFound):
        _ = lib.games_db


def test_env_vars_expanded(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYNITE_TEST_HOME", str(tmp_path))
    lib = PlayniteLibrary("$PLAYNITE_TEST_HOME/Playnite", cache_dir=tmp_path / "cache")
    assert lib.data_dir == tmp_path / "Playnite"


def test_cached_copy_creates_and_reuses(tmp_path):
    data_dir = make_data_dir(tmp_path)
    lib = PlayniteLibrary(data_dir, cache_dir=tmp_path / "cache")
    first = lib.cached_copy(lib.games_db)
    assert first.read_bytes() == b"original"
    first.write_bytes(b"tampered")
    assert lib.cached_copy(lib.games_db).read_bytes() == b"tampered"  # unchanged source: no re-copy


def test_cached_copy_refreshes_and_prunes_stale(tmp_path):
    data_dir = make_data_dir(tmp_path)
    lib = PlayniteLibrary(data_dir, cache_dir=tmp_path / "cache")
    first = lib.cached_copy(lib.games_db)
    (data_dir / "library" / "games.db").write_bytes(b"changed!!")
    second = lib.cached_copy(lib.games_db)
    assert second.read_bytes() == b"changed!!"
    assert second != first
    assert not first.exists()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_library.py -v`
Expected: FAIL, `ImportError: cannot import name 'PlayniteLibrary'`

- [ ] **Step 3: Implement** — append to `src/plugin/playnite.py` (add `import os`, `import shutil`, `import tempfile` to the imports):

```python
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
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/test_library.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/plugin/playnite.py tests/test_library.py
git commit -m "feat: locate Playnite library and cache a lock-free copy of games.db"
```

---

### Task 4: Reading games and sources through litedb-py (`playnite.py`, part 3)

**Files:**
- Modify: `src/plugin/playnite.py` (append methods to `PlayniteLibrary`)
- Test: `tests/test_read.py` (new)

**Interfaces:**
- Consumes: `litedb_py.LiteDatabase`, `litedb_py.LiteDbError`; Task 2's `Game.from_doc`; Task 3's `cached_copy`/`games_db`.
- Produces (consumed by Task 6):
  - `PlayniteLibrary.source_names() -> dict` mapping source id -> name; `{}` when `library/sources.db` is missing or unreadable
  - `PlayniteLibrary.games(include_hidden: bool = False) -> list[Game]`; propagates `PlayniteNotFound`/`LibraryNotFound`/`LiteDbError`

Test fixture note: unit tests build a real data-dir shape around litedb-py's committed binary fixtures. Copy `~/projects/litedb-py/tests/fixtures/guids.db` into the repo as `tests/fixtures/guids.db` (tiny file; inspect it first with `LiteDatabase` and adapt assertions to its actual collection/field names — the steps below assert only shape, not content, so they hold regardless). The full end-to-end check is an integration test against the real library copy at `~/projects/games.db`, skipped when absent.

- [ ] **Step 1: Copy the fixture and write failing tests** — `tests/test_read.py`:

```bash
mkdir -p tests/fixtures
cp ~/projects/litedb-py/tests/fixtures/guids.db tests/fixtures/guids.db
```

```python
import shutil
from pathlib import Path

import pytest

from playnite import PlayniteLibrary

FIXTURE_DB = Path(__file__).parent / "fixtures" / "guids.db"
REAL_DB = Path.home() / "projects" / "games.db"


def make_library(tmp_path, db_file, sources_file=None):
    library = tmp_path / "Playnite" / "library"
    library.mkdir(parents=True)
    shutil.copy(db_file, library / "games.db")
    if sources_file:
        shutil.copy(sources_file, library / "sources.db")
    return PlayniteLibrary(tmp_path / "Playnite", cache_dir=tmp_path / "cache")


def test_source_names_empty_without_sources_db(tmp_path):
    lib = make_library(tmp_path, FIXTURE_DB)
    assert lib.source_names() == {}


def test_source_names_ignores_corrupt_sources_db(tmp_path):
    library = tmp_path / "Playnite" / "library"
    library.mkdir(parents=True)
    shutil.copy(FIXTURE_DB, library / "games.db")
    (library / "sources.db").write_bytes(b"not a litedb file at all")
    lib = PlayniteLibrary(tmp_path / "Playnite", cache_dir=tmp_path / "cache")
    assert lib.source_names() == {}


@pytest.mark.skipif(not REAL_DB.is_file(), reason="no real Playnite games.db available")
def test_reads_real_playnite_library(tmp_path):
    lib = make_library(tmp_path, REAL_DB)
    games = lib.games(include_hidden=True)
    assert len(games) > 0
    assert all(game.id and game.name for game in games)
    visible = lib.games(include_hidden=False)
    assert len(visible) <= len(games)
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_read.py -v`
Expected: FAIL, `AttributeError: 'PlayniteLibrary' object has no attribute 'source_names'`

- [ ] **Step 3: Implement** — append to `PlayniteLibrary` (add `from litedb_py import LiteDatabase, LiteDbError` to imports):

```python
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
```

- [ ] **Step 4: Run tests, verify they pass (integration test included)**

Run: `uv run pytest tests/test_read.py -v`
Expected: all PASS; `test_reads_real_playnite_library` must run (not skip) on this machine since `~/projects/games.db` exists.

- [ ] **Step 5: Commit**

```bash
git add src/plugin/playnite.py tests/test_read.py tests/fixtures/guids.db
git commit -m "feat: read games and source names from the Playnite database"
```

---

### Task 5: Result builders and context menu (`results.py`)

**Files:**
- Create: `src/plugin/results.py`
- Test: `tests/test_results.py`

**Interfaces:**
- Consumes: Task 2's `Game`, `game_subtitle`, `media_path`, `start_uri`, `show_game_uri`; `pyflowlauncher.Result`, `pyflowlauncher.api` (`open_uri`, `open_url`, `open_directory`, `copy_to_clipboard`, `open_setting_dialog`), `pyflowlauncher.models.result.PreviewInfo`.
- Produces (consumed by Task 6):
  - `build_result(game: Game, files_dir: Path, score: int = 0) -> Result` with `json_rpc_action` set to `api.open_uri(start_uri)` when installed else `api.open_uri(show_game_uri)`, and `context_data=[payload]` where payload is `context_payload(...)`'s dict
  - `context_payload(game: Game, files_dir: Path) -> dict` with keys `id`, `name`, `is_installed`, `install_directory`, `links`, `icon` (resolved path string or None)
  - `build_context_menu(payload: dict) -> list[Result]`
  - `error_result(title: str, subtitle: str) -> Result` with `json_rpc_action = api.open_setting_dialog()`

- [ ] **Step 1: Write failing tests** — `tests/test_results.py`:

```python
from playnite import Game
from results import build_context_menu, build_result, context_payload, error_result


def game(**overrides):
    fields = dict(
        id="033b6530-47a6-4179-a8fa-c1197ea4f335",
        name="Doom",
        is_installed=True,
        install_directory=r"F:\Games\Doom",
        icon="033b6530\\icon.ico",
        links=[{"name": "Steam", "url": "https://store.steampowered.com/app/2280"}],
        source="Steam",
    )
    fields.update(overrides)
    return Game(**fields)


def menu_titles(payload):
    return [result.title for result in build_context_menu(payload)]


def test_build_result_installed_launches(tmp_path):
    result = build_result(game(), tmp_path)
    assert result.title == "Doom"
    assert result.json_rpc_action["Parameters"] == ["playnite://playnite/start/033b6530-47a6-4179-a8fa-c1197ea4f335"]
    assert result.context_data == [context_payload(game(), tmp_path)]


def test_build_result_uninstalled_shows_detail(tmp_path):
    result = build_result(game(is_installed=False), tmp_path)
    assert "showgame" in result.json_rpc_action["Parameters"][0]


def test_preview_uses_cover_when_present(tmp_path):
    cover_rel = "033b6530\\cover.jpg"
    cover = tmp_path / "033b6530" / "cover.jpg"
    cover.parent.mkdir()
    cover.write_bytes(b"x")
    result = build_result(game(cover_image=cover_rel), tmp_path)
    assert result.preview["PreviewImagePath"] == str(cover)


def test_full_context_menu(tmp_path):
    payload = context_payload(game(), tmp_path)
    titles = menu_titles(payload)
    assert titles == ["Launch", "Show in Playnite", "Open install folder", "Steam", "Copy game Id"]


def test_context_menu_is_conditional(tmp_path):
    payload = context_payload(game(is_installed=False, install_directory=None, links=[]), tmp_path)
    titles = menu_titles(payload)
    assert titles == ["Install", "Show in Playnite", "Copy game Id"]


def test_context_menu_actions(tmp_path):
    payload = context_payload(game(), tmp_path)
    menu = {result.title: result.json_rpc_action for result in build_context_menu(payload)}
    assert menu["Open install folder"]["Parameters"][0] == r"F:\Games\Doom"
    assert menu["Steam"]["Parameters"][0] == "https://store.steampowered.com/app/2280"
    assert menu["Copy game Id"]["Parameters"][0] == "033b6530-47a6-4179-a8fa-c1197ea4f335"


def test_error_result_opens_settings():
    result = error_result("Playnite not found", "Set the path in settings")
    assert "SettingDialog" in result.json_rpc_action["Method"] or "setting" in result.json_rpc_action["Method"].lower()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_results.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'results'`

- [ ] **Step 3: Implement** — `src/plugin/results.py`:

```python
from __future__ import annotations

from pathlib import Path

from pyflowlauncher import Result, api
from pyflowlauncher.icons import SETTINGS as SETTINGS_ICON
from pyflowlauncher.models.result import PreviewInfo

from playnite import Game, game_subtitle, media_path, show_game_uri, start_uri


def context_payload(game: Game, files_dir: Path) -> dict:
    icon = media_path(files_dir, game.icon)
    return {
        "id": game.id,
        "name": game.name,
        "is_installed": game.is_installed,
        "install_directory": game.install_directory,
        "links": game.links,
        "icon": str(icon) if icon else None,
    }


def build_result(game: Game, files_dir: Path, score: int = 0) -> Result:
    uri = game.start_uri if game.is_installed else game.show_game_uri
    cover = media_path(files_dir, game.cover_image)
    preview = PreviewInfo(
        PreviewImagePath=str(cover) if cover else None,
        Description=game.name,
        IsMedia=True,
        PreviewDeligate="",
    )
    return Result(
        title=game.name,
        subtitle=game_subtitle(game),
        icon=media_path(files_dir, game.icon),
        score=score,
        preview=preview,
        json_rpc_action=api.open_uri(uri),
        context_data=[context_payload(game, files_dir)],
    )


def build_context_menu(payload: dict) -> list[Result]:
    icon = payload.get("icon")
    installed = payload["is_installed"]
    game_id = payload["id"]
    results = [
        Result(
            title="Launch" if installed else "Install",
            subtitle=f"{'Launch' if installed else 'Install'} {payload['name']} with Playnite",
            icon=icon,
            json_rpc_action=api.open_uri(start_uri(game_id)),
        ),
        Result(
            title="Show in Playnite",
            subtitle="Open the game's detail page",
            icon=icon,
            json_rpc_action=api.open_uri(show_game_uri(game_id)),
        ),
    ]
    if installed and payload.get("install_directory"):
        results.append(
            Result(
                title="Open install folder",
                subtitle=payload["install_directory"],
                icon=icon,
                json_rpc_action=api.open_directory(payload["install_directory"]),
            )
        )
    for link in payload.get("links") or []:
        results.append(
            Result(
                title=link["name"],
                subtitle=link["url"],
                icon=icon,
                json_rpc_action=api.open_url(link["url"]),
            )
        )
    results.append(
        Result(
            title="Copy game Id",
            subtitle=game_id,
            icon=icon,
            json_rpc_action=api.copy_to_clipboard(game_id),
        )
    )
    return results


def error_result(title: str, subtitle: str) -> Result:
    return Result(
        title=title,
        subtitle=subtitle,
        icon=SETTINGS_ICON,
        json_rpc_action=api.open_setting_dialog(),
    )
```

Implementation note: if `pyflowlauncher.icons` has no `SETTINGS` constant, run `uv run python -c "import pyflowlauncher.icons as i; print([n for n in dir(i) if n.isupper()])"` and pick the closest (e.g. `WARNING` or drop the icon argument). Adjust the import, not the test (the test does not assert the icon).

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/test_results.py -v`
Expected: all PASS. If `json_rpc_action["Parameters"]` shape differs, inspect `uv run python -c "from pyflowlauncher import api; print(api.open_uri('x'))"` and fix the TESTS to the actual JsonRPCRequest shape (the api functions are the source of truth), keeping the semantic assertions (URI/path/id values present).

- [ ] **Step 5: Commit**

```bash
git add src/plugin/results.py tests/test_results.py
git commit -m "feat: build query results and rich conditional context menu"
```

---

### Task 6: Plugin wiring (`__main__.py`) and settings

**Files:**
- Create: `src/plugin/__main__.py`, `src/plugin/settings.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Consumes: Task 3's `PlayniteLibrary`, `DEFAULT_DATA_DIR`, `PlayniteNotFound`, `LibraryNotFound`; Task 4's `games()`; Task 5's builders; `litedb_py.LiteDbError`; `pyflowlauncher.Plugin`.
- Produces: the runnable plugin. `settings.py` exposes `as_bool(value, default=False) -> bool`.

- [ ] **Step 1: Write failing tests** — `tests/test_settings.py`:

```python
from settings import as_bool


def test_as_bool_accepts_bools_and_strings():
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool("true") is True
    assert as_bool("True") is True
    assert as_bool("false") is False
    assert as_bool("") is False
    assert as_bool(None) is False
    assert as_bool(None, default=True) is True
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_settings.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'settings'`

- [ ] **Step 3: Implement** — `src/plugin/settings.py`:

```python
def as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default
```

`src/plugin/__main__.py`:

```python
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
```

- [ ] **Step 4: Verify method-return handling for `context_menu`**

`query` yields `Result`s like Steam-Search, which is known-good. `context_menu` returns a list instead. Read the installed handler to confirm a plain iterable of `Result` is serialized the same way:

```bash
uv run python -c "import inspect, pyflowlauncher.method as m; print(inspect.getsource(m))"
```

If a returned list is NOT wrapped like a generator's yields, convert `context_menu` to a generator (`for result in build_context_menu(data[0]): yield result`) and note it in the commit body.

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -v`
Expected: all PASS (test_game, test_library, test_read incl. real-library integration, test_results, test_settings)

- [ ] **Step 6: Commit**

```bash
git add src/plugin/__main__.py src/plugin/settings.py tests/test_settings.py
git commit -m "feat: wire query and context menu into pyflowlauncher plugin"
```

---

### Task 7: CI, packaging, and release automation

**Files:**
- Create: `.github/workflows/tests.yml`, `.github/workflows/release.yml`, `.github/workflows/release-please.yml`, `release-please-config.json`, `.release-please-manifest.json`
- Delete: any leftover v2 workflow files under `.github/workflows/` (check with `ls .github/workflows` first)

**Interfaces:**
- Consumes: Task 1's `requirements.txt`, `data/` layout, tox config.
- Produces: tag-triggered zip release (`Playnite-Plugin-<version>.zip` with `run.py`, `plugin/`, `plugin/site-packages/`, manifest, settings, icon, LICENSE at the zip root) and release-please version management.

- [ ] **Step 1: Write `tests.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - run: uv sync
      - run: uv run pytest -v
```

- [ ] **Step 2: Write `release.yml`** — copy `~/projects/Steam-Search/.github/workflows/release.yml` verbatim (it stages `src/.`, `data/icon.png`, `data/plugin.json`, `data/SettingsTemplate.yaml`, `LICENSE`, pip-installs `requirements.txt` into `plugin/site-packages`, zips as `<repo>-<version>.zip`, and attaches it to the GitHub release). No edits needed; it derives the repo name and version from context.

- [ ] **Step 3: Write release-please config**

`.github/workflows/release-please.yml`:

```yaml
name: release-please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

`release-please-config.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "python",
  "include-component-in-tag": false,
  "packages": {
    ".": {
      "extra-files": [
        {
          "type": "json",
          "path": "data/plugin.json",
          "jsonpath": "$.Version"
        }
      ]
    }
  }
}
```

`.release-please-manifest.json`:

```json
{
  ".": "2.0.0"
}
```

Seeding the manifest at `2.0.0` makes the `feat!` commits on this branch produce a 3.0.0 release PR when merged to main.

- [ ] **Step 4: Validate workflow syntax and commit**

```bash
uv run python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]; print('yaml ok')"
git add .github release-please-config.json .release-please-manifest.json
git commit -m "ci: add test, release, and release-please workflows"
```

(If PyYAML is unavailable in the env, `uv run --with pyyaml python ...`.)

---

### Task 8: README via readwright

**Files:**
- Create: `readme.yaml`, `docs/README.md.j2`
- Modify: `README.md` (generated, replaces the v2 README)

**Interfaces:**
- Consumes: readwright CLI from the local checkout at `~/projects/readwright` (v0.3.0, not yet on PyPI): run it as `uvx --from ~/projects/readwright readwright <command>`.

- [ ] **Step 1: Write `readme.yaml`**

```yaml
template: docs/README.md.j2
project:
  name: Playnite
  owner: Garulf
  repo: Playnite-Plugin
  license: MIT
  tagline: Search and launch your Playnite library. Fully local, no Playnite extension required.
  ci_workflow: tests.yml
badges: [ci, github-release, license]
donate: [buymeacoffee, github-sponsors]
donate_handles:
  buymeacoffee: garulf
  github-sponsors: Garulf
```

- [ ] **Step 2: Create the template** — start from Steam-Search's and adapt:

```bash
mkdir -p docs
cp ~/projects/Steam-Search/docs/README.md.j2 docs/README.md.j2
```

Edit `docs/README.md.j2`, keeping its block structure but replacing Steam-specific prose:

- Features: reads `games.db` directly with litedb-py (no FlowLauncherExporter needed); all sources Playnite knows about; fuzzy matching; icons in results, cover art on `F1`; installed games launch, uninstalled open their Playnite page; rich context menu (open install folder, store links, copy id); hidden games opt-in.
- Usage: `pn` + game name (example: `pn doom`).
- Installation: `pm install playnite` and manual zip instructions pointing at this repo's releases.
- Remove the banner/screenshot includes if the referenced assets do not exist in this repo (check `.github/assets/` first); missing-asset references must not ship.

- [ ] **Step 3: Render and verify**

```bash
uvx --from ~/projects/readwright readwright render
uvx --from ~/projects/readwright readwright check
```

Expected: `README.md` regenerated with the "generated by readwright" header comment; check passes. Read the rendered README top to bottom for stale Steam-Search references.

- [ ] **Step 4: Commit**

```bash
git add readme.yaml docs/README.md.j2 README.md
git commit -m "docs: generate README with readwright"
```

---

### Task 9: README screenshots with flow-render (curated, real Playnite icons)

**Files:**
- Create: `.github/assets/screenshot-config.json` (curated flow-render config), `.github/assets/screenshot.png`, `.github/assets/install.png`
- Modify: `readme.yaml`, `docs/README.md.j2` (reference the new assets), `README.md` (re-render)

**Interfaces:**
- Consumes: [flow-render](https://github.com/Garulf/flow-render) CLI; the real library copy at `~/projects/games.db` for honest names/playtimes; Task 2's `game_subtitle` formatting rules (subtitles in the mockup must match what the plugin actually renders: `Source · Installed · Nh played · last played YYYY-MM-DD`); Task 8's readwright setup.
- Produces: README imagery. Config schema (verified against `example/config.json` in the repo): `{"keyword", "query", "icon" (data URI), "max_results", "selection", "results": [{"title", "subtitle", "icon" (data URI)}], "css", "query_suggestion"}`.

- [ ] **Step 1: Install flow-render**

```bash
uv tool install git+https://github.com/Garulf/flow-render
playwright install chromium
```

If Chromium fails to launch at render time with missing shared libraries, run `sudo playwright install-deps chromium` (passwordless sudo apt works in this container) and retry.

- [ ] **Step 2: Pick showcase games and PAUSE for icon files**

Run this to list candidates and their exact icon paths on the Windows machine:

```bash
cd ~/projects/litedb-py && uv run python - <<'EOF'
from litedb_py import LiteDatabase
with LiteDatabase("/home/Garulf/projects/games.db") as db:
    for doc in db["Game"]:
        if doc.get("IsInstalled") and doc.get("Icon"):
            print(f'{doc["Name"]}  |  %AppData%\\Playnite\\library\\files\\{doc["Icon"]}')
EOF
```

Choose 3 well-known games with good playtime values. Then STOP and ask the user to copy those 3 icon files (plus, optionally, the Playnite app icon for the search bar — the repo's `data/icon.png` works as the fallback) from their Windows machine into `~/projects/playnite-media/`, preserving nothing but the filenames. Do not proceed until the files exist.

- [ ] **Step 3: Build the curated config**

Generate `.github/assets/screenshot-config.json` with a script so the base64 embedding and subtitles are derived, not hand-typed. Subtitles MUST be computed with the plugin's own `game_subtitle()` from real `games.db` documents so the mockup matches genuine output:

```bash
cd ~/projects/Playnite-Plugin && uv run python - <<'EOF'
import base64, json, sys
from pathlib import Path

sys.path.insert(0, "src/plugin")
from litedb_py import LiteDatabase
from playnite import Game, game_subtitle

CHOSEN = {  # game name -> copied icon file (adjust to Step 2's picks)
    "Grand Theft Auto V Enhanced": "9cca7a5a-icon.ico",
}
MEDIA = Path.home() / "projects" / "playnite-media"

def data_uri(path: Path) -> str:
    mime = "image/x-icon" if path.suffix == ".ico" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"

results = []
with LiteDatabase(Path.home() / "projects" / "games.db") as db:
    for doc in db["Game"]:
        if doc.get("Name") in CHOSEN:
            game = Game.from_doc(doc, {})
            results.append({
                "title": game.name,
                "subtitle": game_subtitle(game),
                "icon": data_uri(MEDIA / CHOSEN[game.name]),
            })

config = {
    "keyword": "pn",
    "query": next(iter(CHOSEN)).split()[0].lower(),
    "icon": data_uri(Path("data/icon.png")),
    "max_results": len(results),
    "selection": 0,
    "results": results,
    "css": None,
    "query_suggestion": "",
}
Path(".github/assets").mkdir(parents=True, exist_ok=True)
Path(".github/assets/screenshot-config.json").write_text(json.dumps(config, indent=2))
print("wrote", len(results), "results")
EOF
```

Fill `CHOSEN` with the 3 picks from Step 2 and set `query` to a natural partial query that matches the selected (top) game.

- [ ] **Step 4: Render the results screenshot and the install view**

```bash
flow-render -c .github/assets/screenshot-config.json -o .github/assets --hide-caret
# rename the freshly produced output_<timestamp>_<id>.png:
mv .github/assets/output_*.png .github/assets/screenshot.png

# plugin-manager "pm install" view; stage the shipped layout so -p sees a real plugin dir:
stage=$(mktemp -d) && cp -r src/. "$stage/" && cp data/plugin.json data/SettingsTemplate.yaml data/icon.png "$stage/"
flow-render -i -p "$stage" -o .github/assets --hide-caret
mv .github/assets/output_*.png .github/assets/install.png
rm -rf "$stage"
```

View both PNGs (send them to the user) and confirm: correct icons, subtitles matching `game_subtitle` output, no rendering glitches.

- [ ] **Step 5: Wire into the README and re-render**

Add to `readme.yaml`:

```yaml
screenshots:
  dir: .github/assets
```

Reference `screenshot.png` in the Usage section and `install.png` in the Installation section of `docs/README.md.j2` (same placement as Steam-Search's README), then:

```bash
uvx --from ~/projects/readwright readwright render
```

- [ ] **Step 6: Commit**

```bash
git add .github/assets readme.yaml docs/README.md.j2 README.md
git commit -m "docs: add flow-render screenshots to README"
```

---

### Task 10: Final verification

**Files:** none new.

- [ ] **Step 1: Full suite and hooks**

```bash
uv run tox
pre-commit run --all-files
```

Expected: tox py312 passes (integration test against the real library included); pre-commit hooks all pass (fix any trailing-whitespace/EOF autofixes and re-run until clean).

- [ ] **Step 2: Sanity-check the shipped tree**

```bash
uv run python - <<'EOF'
import json
manifest = json.load(open("data/plugin.json"))
assert manifest["ID"] == "625A2812D5364D708582FDD9ACCD8C93"
assert manifest["Language"] == "python_v2"
assert manifest["Version"] == "3.0.0"
print("manifest ok")
EOF
git status --short   # expect: clean
```

- [ ] **Step 3: Commit any stragglers, then stop**

Do not merge or push. Hand off to superpowers:finishing-a-development-branch for integration.
