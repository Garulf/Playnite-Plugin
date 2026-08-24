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
