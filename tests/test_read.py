import os
import shutil
from pathlib import Path
from uuid import UUID

import pytest

import playnite
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


GAME_DOCS = [
    {"_id": UUID("00000000-0000-0000-0000-000000000001"), "Name": "Shown", "Hidden": False},
    {"_id": UUID("00000000-0000-0000-0000-000000000002"), "Name": "Hidden", "Hidden": True},
]


@pytest.fixture
def opened_dbs(monkeypatch):
    opened = []

    class RecordingDatabase:
        collections = []

        def __init__(self, path):
            opened.append(Path(path))

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def __getitem__(self, name):
            return GAME_DOCS

    monkeypatch.setattr(playnite, "LiteDatabase", RecordingDatabase)
    return opened


def test_games_reads_the_database_once_while_it_is_unchanged(tmp_path, opened_dbs):
    lib = make_library(tmp_path, FIXTURE_DB)
    every_game = lib.games(include_hidden=True)
    visible = lib.games(include_hidden=False)
    assert lib.games(include_hidden=True) == every_game
    assert [game.name for game in visible] == ["Shown"]
    assert len(opened_dbs) == 1


def test_games_rereads_after_games_db_changes(tmp_path, opened_dbs):
    lib = make_library(tmp_path, FIXTURE_DB)
    lib.games()
    games_db = tmp_path / "Playnite" / "library" / "games.db"
    stat = games_db.stat()
    os.utime(games_db, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    lib.games()
    assert len(opened_dbs) == 2


def test_games_rereads_when_sources_db_appears(tmp_path, opened_dbs):
    lib = make_library(tmp_path, FIXTURE_DB)
    lib.games()
    (tmp_path / "Playnite" / "library" / "sources.db").write_bytes(b"not a litedb file at all")
    lib.games()
    assert [path.stem.split("-")[0] for path in opened_dbs] == ["games", "sources", "games"]


def test_games_returns_a_fresh_list_each_call(tmp_path, opened_dbs):
    lib = make_library(tmp_path, FIXTURE_DB)
    lib.games(include_hidden=True).clear()
    assert lib.games(include_hidden=True)


@pytest.mark.skipif(not REAL_DB.is_file(), reason="no real Playnite games.db available")
def test_reads_real_playnite_library(tmp_path):
    lib = make_library(tmp_path, REAL_DB)
    games = lib.games(include_hidden=True)
    assert len(games) > 0
    assert all(game.id and game.name for game in games)
    visible = lib.games(include_hidden=False)
    assert len(visible) <= len(games)
