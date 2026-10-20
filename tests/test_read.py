# tests/test_read.py
import shutil
from pathlib import Path
from uuid import UUID

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


def test_games_uses_in_memory_cache_and_invalidates_on_file_change(tmp_path, monkeypatch):
    lib = make_library(tmp_path, FIXTURE_DB)
    open_calls = []

    class FakeLiteDatabase:
        def __init__(self, path):
            open_calls.append(path)

        def __enter__(self):
            return {
                "Game": [
                    {
                        "_id": UUID("00000000-0000-0000-0000-000000000001"),
                        "Name": "Installed Game",
                        "IsInstalled": True,
                        "Hidden": False,
                    },
                    {
                        "_id": UUID("00000000-0000-0000-0000-000000000002"),
                        "Name": "Hidden Uninstalled Game",
                        "IsInstalled": False,
                        "Hidden": True,
                    },
                ]
            }

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("playnite.LiteDatabase", FakeLiteDatabase)

    all_games = lib.games(include_hidden=True)
    visible_games = lib.games(include_hidden=False)
    installed_games = lib.games(include_hidden=False, include_uninstalled=False)

    assert len(open_calls) == 1
    assert len(all_games) == 2
    assert [game.name for game in visible_games] == ["Installed Game"]
    assert [game.name for game in installed_games] == ["Installed Game"]

    # Modifying games.db on disk invalidates the in-memory cache and reloads
    (tmp_path / "Playnite" / "library" / "games.db").write_bytes(b"updated database bytes")
    _ = lib.games(include_hidden=True)
    assert len(open_calls) == 2


@pytest.mark.skipif(not REAL_DB.is_file(), reason="no real Playnite games.db available")
def test_reads_real_playnite_library(tmp_path):
    lib = make_library(tmp_path, REAL_DB)
    games = lib.games(include_hidden=True)
    assert len(games) > 0
    assert all(game.id and game.name for game in games)
    visible = lib.games(include_hidden=False)
    assert len(visible) <= len(games)
