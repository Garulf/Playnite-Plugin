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
