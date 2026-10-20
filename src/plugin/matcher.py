# src/plugin/matcher.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from pyflowlauncher.string_matcher import string_matcher

from playnite import Game, _compute_sort_key

EMPTY_QUERY_LIMIT = 10
SEARCH_QUERY_LIMIT = 25

# Bypass the 128-entry lru_cache wrapper on pyflowlauncher.string_matcher:
# scanning 1,000+ games per keystroke would otherwise thrash the 128-entry cache
# with a 0% hit rate while paying lock and dictionary eviction overhead on every game.
_unwrapped_string_matcher = getattr(string_matcher, "__wrapped__", string_matcher)


def has_ordered_characters(needle: str, haystack: str) -> bool:
    """Return True if every character of ``needle`` appears in order in ``haystack``.

    Both substring matching and acronym matching in Flow Launcher's algorithm
    require all non-space query characters to appear in sequence in the candidate
    title. Checking this in C via ``str.find`` filters out non-matches before
    invoking the full Python scorer.
    """
    position = 0
    find_next = haystack.find
    for character in needle:
        position = find_next(character, position)
        if position < 0:
            return False
        position += 1
    return True


def empty_query_sort_key(game: Game) -> tuple[int, float, int, str]:
    """Order games for an empty query: most recently played first, then playtime, then name."""
    precomputed = getattr(game, "sort_key", None)
    if isinstance(precomputed, tuple):
        return precomputed

    last_activity = getattr(game, "last_activity", None)
    raw_playtime = getattr(game, "playtime", 0)
    playtime = int(raw_playtime) if isinstance(raw_playtime, (int, float)) else 0
    raw_name = getattr(game, "name", "")
    normalized_name = raw_name.lower() if isinstance(raw_name, str) else str(raw_name).lower()
    return _compute_sort_key(
        normalized_name,
        playtime,
        last_activity if isinstance(last_activity, datetime) else None,
    )


def match_and_rank_games(
    games: Iterable[Game],
    query: str,
    *,
    empty_limit: int = EMPTY_QUERY_LIMIT,
    search_limit: int = SEARCH_QUERY_LIMIT,
) -> list[tuple[Game, int]]:
    """Filter, score, sort, and cap ``games`` for ``query`` before building UI results."""
    stripped_query = query.strip() if query else ""
    if not stripped_query:
        ordered_games = sorted(games, key=empty_query_sort_key)
        return [(game, 0) for game in ordered_games[:empty_limit]]

    subsequence_needle = stripped_query.lower().replace(" ", "")
    scored_matches: list[tuple[Game, int]] = []

    if len(subsequence_needle) == 1:
        single_char = subsequence_needle
        for game in games:
            name_lower = getattr(game, "name_lower", None)
            if not isinstance(name_lower, str):
                name_lower = str(getattr(game, "name", "")).lower()
            if single_char not in name_lower:
                continue
            game_name = game.name if isinstance(game.name, str) else str(game.name)
            match = _unwrapped_string_matcher(stripped_query, game_name)
            if match.matched and match.score >= match.score_cutoff:
                scored_matches.append((game, int(match.score)))
    else:
        for game in games:
            name_lower = getattr(game, "name_lower", None)
            if not isinstance(name_lower, str):
                name_lower = str(getattr(game, "name", "")).lower()
            if not has_ordered_characters(subsequence_needle, name_lower):
                continue
            game_name = game.name if isinstance(game.name, str) else str(game.name)
            match = _unwrapped_string_matcher(stripped_query, game_name)
            if match.matched and match.score >= match.score_cutoff:
                scored_matches.append((game, int(match.score)))

    scored_matches.sort(key=lambda item: (-item[1], empty_query_sort_key(item[0])))
    return scored_matches[:search_limit]
