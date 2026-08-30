import json

import pytest

from playnite import LibraryNotFound, PlayniteLibrary, PlayniteNotFound

GAMES = [
    {"Id": "033b6530-47a6-4179-a8fa-c1197ea4f335", "Name": "Doom", "IsInstalled": True, "Hidden": False},
    {"Id": "7f5440ce-70e1-4c3b-a33f-09ed280284eb", "Name": "Secret", "IsInstalled": False, "Hidden": True},
]


def make_data_dir(tmp_path, payload=GAMES, encoding="utf-8-sig"):
    exporter_dir = tmp_path / "Playnite" / "ExtensionsData" / "FlowLauncherExporter"
    exporter_dir.mkdir(parents=True)
    if payload is not None:
        (exporter_dir / "library.json").write_text(json.dumps(payload), encoding=encoding)
    return tmp_path / "Playnite"


def test_missing_data_dir_raises(tmp_path):
    lib = PlayniteLibrary(tmp_path / "nope")
    with pytest.raises(PlayniteNotFound):
        lib.games()


def test_missing_library_json_raises(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path, payload=None))
    with pytest.raises(LibraryNotFound):
        lib.games()


def test_env_vars_expanded(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYNITE_TEST_HOME", str(tmp_path))
    lib = PlayniteLibrary("$PLAYNITE_TEST_HOME/Playnite")
    assert lib.data_dir == tmp_path / "Playnite"


def test_games_reads_exporter_library(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path))
    games = lib.games(include_hidden=True)
    assert [game.name for game in games] == ["Doom", "Secret"]


def test_games_filters_hidden_by_default(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path))
    assert [game.name for game in lib.games()] == ["Doom"]


def test_games_reads_plain_utf8(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path, encoding="utf-8"))
    assert len(lib.games(include_hidden=True)) == 2


def test_single_game_object_payload(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path, payload=GAMES[0]))
    assert [game.name for game in lib.games()] == ["Doom"]


def test_files_dir_under_library(tmp_path):
    lib = PlayniteLibrary(make_data_dir(tmp_path))
    assert lib.files_dir == tmp_path / "Playnite" / "library" / "files"
