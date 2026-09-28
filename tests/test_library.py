import shutil

import pytest

from playnite import LibraryLocked, LibraryNotFound, PlayniteLibrary, PlayniteNotFound


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


def test_cached_copy_falls_back_to_previous_snapshot_when_source_locked(tmp_path, monkeypatch):
    """Playnite opens games.db with LiteDB Mode=Exclusive for its whole session,
    so copying the live file raises PermissionError the entire time Playnite is
    running. Serve the last snapshot we could read instead of failing outright."""
    data_dir = make_data_dir(tmp_path)
    lib = PlayniteLibrary(data_dir, cache_dir=tmp_path / "cache")
    first = lib.cached_copy(lib.games_db)

    (data_dir / "library" / "games.db").write_bytes(b"changed while locked")

    def locked_copy(src, dst):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(shutil, "copy", locked_copy)
    fallback = lib.cached_copy(lib.games_db)

    assert fallback == first
    assert fallback.read_bytes() == b"original"


def test_cached_copy_raises_when_locked_with_no_previous_snapshot(tmp_path, monkeypatch):
    data_dir = make_data_dir(tmp_path)
    lib = PlayniteLibrary(data_dir, cache_dir=tmp_path / "cache")

    def locked_copy(src, dst):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(shutil, "copy", locked_copy)
    with pytest.raises(LibraryLocked) as raised:
        lib.cached_copy(lib.games_db)
    assert raised.value.path == lib.games_db
