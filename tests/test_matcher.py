# tests/test_matcher.py
from datetime import datetime, timezone

from matcher import (
    EMPTY_QUERY_LIMIT,
    SEARCH_QUERY_LIMIT,
    has_ordered_characters,
    match_and_rank_games,
)
from playnite import Game


def make_game(
    game_id: str,
    name: str,
    *,
    playtime: int = 0,
    last_activity: datetime | None = None,
) -> Game:
    return Game(
        id=game_id,
        name=name,
        playtime=playtime,
        last_activity=last_activity,
    )


def test_has_ordered_characters():
    assert has_ordered_characters("rdr2", "red dead redemption 2") is True
    assert has_ordered_characters("rav", "ravenswatch") is True
    assert has_ordered_characters("zxy", "ravenswatch") is False


def test_empty_query_orders_by_last_activity_then_playtime_then_name():
    games = [
        make_game("1", "Zelda", playtime=100, last_activity=None),
        make_game("2", "Alpha", playtime=100, last_activity=None),
        make_game("3", "High Playtime", playtime=5000, last_activity=None),
        make_game("4", "Played Earlier", playtime=10, last_activity=datetime(2026, 9, 1, tzinfo=timezone.utc)),
        make_game("5", "Played Recently", playtime=10, last_activity=datetime(2026, 10, 19, tzinfo=timezone.utc)),
    ]

    ranked = match_and_rank_games(games, "")
    titles = [game.name for game, score in ranked]

    assert titles == [
        "Played Recently",
        "Played Earlier",
        "High Playtime",
        "Alpha",
        "Zelda",
    ]
    assert all(score == 0 for _, score in ranked)


def test_empty_query_caps_at_ten_results():
    games = [make_game(str(index), f"Game {index:02d}") for index in range(30)]
    ranked = match_and_rank_games(games, "")
    assert len(ranked) == EMPTY_QUERY_LIMIT == 10


def test_search_query_caps_at_twenty_five_and_orders_by_score():
    games = [make_game(str(index), f"Star Wars Episode {index:02d}") for index in range(40)]
    games.append(make_game("exact", "Star Wars"))

    ranked = match_and_rank_games(games, "Star Wars")

    assert len(ranked) == SEARCH_QUERY_LIMIT == 25
    assert ranked[0][0].name == "Star Wars"
    scores = [score for _, score in ranked]
    assert scores == sorted(scores, reverse=True)


def test_search_query_matches_acronyms():
    games = [
        make_game("1", "Red Dead Redemption 2"),
        make_game("2", "Hollow Knight"),
    ]
    ranked = match_and_rank_games(games, "rdr2")
    assert [game.name for game, _ in ranked] == ["Red Dead Redemption 2"]
