# src/plugin/library_source.py
from __future__ import annotations

from typing import TYPE_CHECKING

from library_server import LibraryServerUnavailable, fetch_games

if TYPE_CHECKING:
    from playnite import Game, PlayniteLibrary


def games(
    server_port: int,
    include_hidden: bool,
    fallback: "PlayniteLibrary",
    *,
    use_server: bool = True,
) -> "list[Game]":
    """Return games from the live server when ``use_server`` is enabled, falling back to ``fallback.games(...)`` when unavailable."""
    if not use_server:
        return fallback.games(include_hidden=include_hidden)
    try:
        return fetch_games(port=server_port, include_hidden=include_hidden)
    except LibraryServerUnavailable:
        return fallback.games(include_hidden=include_hidden)
