# tests/test_library_source.py
from unittest.mock import Mock

import pytest

from library_server import LibraryServerUnavailable
from library_source import games
from playnite import Game

GAME_ID = "033b6530-47a6-4179-a8fa-c1197ea4f335"


def make_game(name):
    return Game(id=GAME_ID, name=name)


def test_uses_server_games_when_available(monkeypatch):
    server_games = [make_game("From Server")]
    monkeypatch.setattr("library_source.fetch_games", lambda port, include_hidden: server_games)

    fallback = Mock()
    result = games(server_port=38217, include_hidden=False, fallback=fallback)

    assert result == server_games
    fallback.games.assert_not_called()


def test_skips_server_when_use_server_is_false(monkeypatch):
    fetch_mock = Mock()
    monkeypatch.setattr("library_source.fetch_games", fetch_mock)

    fallback = Mock()
    fallback.games.return_value = [make_game("From File")]

    result = games(server_port=38217, include_hidden=True, fallback=fallback, use_server=False)

    assert result == [make_game("From File")]
    fetch_mock.assert_not_called()
    fallback.games.assert_called_once_with(include_hidden=True)


def test_falls_back_when_server_unavailable(monkeypatch):
    def raise_unavailable(port, include_hidden):
        raise LibraryServerUnavailable("connection refused")

    monkeypatch.setattr("library_source.fetch_games", raise_unavailable)

    fallback = Mock()
    fallback.games.return_value = [make_game("From File")]

    result = games(server_port=38217, include_hidden=True, fallback=fallback)

    assert result == [make_game("From File")]
    fallback.games.assert_called_once_with(include_hidden=True)


def test_fallback_exceptions_propagate(monkeypatch):
    monkeypatch.setattr(
        "library_source.fetch_games",
        lambda port, include_hidden: (_ for _ in ()).throw(LibraryServerUnavailable("down")),
    )

    fallback = Mock()
    fallback.games.side_effect = OSError("permission denied")

    with pytest.raises(OSError):
        games(server_port=38217, include_hidden=False, fallback=fallback)
