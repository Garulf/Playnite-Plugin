from playnite import Game, format_playtime, game_subtitle, media_path

GAME_ID = "033b6530-47a6-4179-a8fa-c1197ea4f335"


def export(**overrides):
    base = {
        "Id": GAME_ID,
        "Name": "Grand Theft Auto V Enhanced",
        "IsInstalled": True,
        "Hidden": False,
        "InstallDirectory": r"F:\SteamLibrary\steamapps\common\GTA V",
        "Icon": GAME_ID + r"\icon.ico",
        "Playtime": 7200,
        "Source": {"Id": "7f5440ce-70e1-4c3b-a33f-09ed280284eb", "Name": "Steam"},
        "ReleaseDate": {"Day": 4, "Month": 3, "Year": 2025},
    }
    base.update(overrides)
    return base


def test_from_export_maps_fields():
    game = Game.from_export(export())
    assert game.id == GAME_ID
    assert game.name == "Grand Theft Auto V Enhanced"
    assert game.is_installed
    assert game.playtime == 7200
    assert game.source == "Steam"
    assert game.install_directory == r"F:\SteamLibrary\steamapps\common\GTA V"


def test_from_export_tolerates_missing_optionals():
    game = Game.from_export({"Id": GAME_ID, "Name": "Bare"})
    assert not game.is_installed
    assert not game.hidden
    assert game.icon is None
    assert game.source is None
    assert game.playtime == 0
    assert game.install_directory is None


def test_from_export_tolerates_null_name():
    assert Game.from_export({"Id": GAME_ID, "Name": None}).name == ""


def test_from_export_tolerates_null_source():
    assert Game.from_export(export(Source=None)).source is None


def test_uris():
    game = Game.from_export(export())
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
    game = Game.from_export(export())
    assert game_subtitle(game) == "Steam · Installed · 2h played"
    bare = Game.from_export({"Id": GAME_ID, "Name": "Bare"})
    assert game_subtitle(bare) == "Not installed"
