# tests/test_library_server.py
import json
import urllib.error

import pytest

from library_server import LibraryServerUnavailable, fetch_games

GAME_ID = "033b6530-47a6-4179-a8fa-c1197ea4f335"


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def game_payload(**overrides):
    base = {
        "id": GAME_ID,
        "name": "Doom",
        "isInstalled": True,
        "hidden": False,
        "installDirectory": r"F:\Games\Doom",
        "icon": None,
        "coverImage": None,
        "playtime": 0,
        "lastActivity": None,
        "links": [],
        "source": "Steam",
    }
    base.update(overrides)
    return base


def test_fetch_games_returns_parsed_games(monkeypatch):
    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: FakeResponse(200, [game_payload()]),
    )
    games = fetch_games(port=38217, include_hidden=False)
    assert len(games) == 1
    assert games[0].id == GAME_ID
    assert games[0].name == "Doom"


def test_fetch_games_raises_on_connection_refused(monkeypatch):
    def raise_refused(url, timeout):
        raise urllib.error.URLError(ConnectionRefusedError())

    monkeypatch.setattr("library_server.urllib.request.urlopen", raise_refused)
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_raises_on_timeout(monkeypatch):
    def raise_timeout(url, timeout):
        raise TimeoutError()

    monkeypatch.setattr("library_server.urllib.request.urlopen", raise_timeout)
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_raises_on_non_200(monkeypatch):
    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: FakeResponse(500, {"error": "boom"}),
    )
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_raises_on_bad_json(monkeypatch):
    class BadJsonResponse(FakeResponse):
        def read(self):
            return b"not json"

    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: BadJsonResponse(200, {}),
    )
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_raises_on_wrong_shaped_payload(monkeypatch):
    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: FakeResponse(200, {"error": "boom"}),
    )
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_raises_on_game_missing_id(monkeypatch):
    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: FakeResponse(200, [{"name": "Doom"}]),
    )
    with pytest.raises(LibraryServerUnavailable):
        fetch_games(port=38217, include_hidden=False)


def test_fetch_games_filters_hidden_games_client_side(monkeypatch):
    monkeypatch.setattr(
        "library_server.urllib.request.urlopen",
        lambda url, timeout: FakeResponse(200, [game_payload(hidden=True)]),
    )
    games = fetch_games(port=38217, include_hidden=False)
    assert games == []


def test_fetch_games_passes_hidden_query_param(monkeypatch):
    captured = {}

    def capture(url, timeout):
        captured["url"] = url
        return FakeResponse(200, [])

    monkeypatch.setattr("library_server.urllib.request.urlopen", capture)
    fetch_games(port=38217, include_hidden=True)
    assert "hidden=true" in captured["url"]
    assert "127.0.0.1" in captured["url"]
