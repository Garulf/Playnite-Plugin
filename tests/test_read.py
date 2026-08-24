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
