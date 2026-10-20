# tests/test_performance.py
from datetime import datetime, timezone
from pathlib import Path
import time

from matcher import EMPTY_QUERY_LIMIT, SEARCH_QUERY_LIMIT, match_and_rank_games
from playnite import Game
from results import build_result

TYPING_SEQUENCE = ["", "r", "ra", "rav", "rave", "raven", "ravens", "ravenswatch"]


def _build_synthetic_library(tmp_path: Path, *, include_hidden: bool) -> tuple[list[Game], Path]:
    files_dir = tmp_path / "Playnite" / "library" / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    synthetic_games = [
        Game(
            id=f"00000000-0000-0000-0000-{index:012d}",
            name="Ravenswatch" if index == 0 else f"Sample Game Title {index:04d}: Edition {index % 17}",
            is_installed=(index < 15),
            hidden=(index % 250 == 0),
            install_directory=rf"C:\Games\Game_{index}",
            icon=rf"00000000-0000-0000-0000-{index:012d}\icon.ico",
            cover_image=rf"00000000-0000-0000-0000-{index:012d}\cover.jpg",
            playtime=index * 60,
            last_activity=datetime(2026, 10, 19, tzinfo=timezone.utc) if index < 350 else None,
            links=[{"name": "Steam", "url": "https://store.steampowered.com"}],
            source="Steam",
        )
        for index in range(1725)
    ]
    if not include_hidden:
        synthetic_games = [game for game in synthetic_games if not game.hidden]
    return synthetic_games, files_dir


def test_typing_sequence_performance_across_full_library(tmp_path):
    candidate_games, files_dir = _build_synthetic_library(tmp_path, include_hidden=True)
    assert len(candidate_games) == 1725

    start_time = time.perf_counter()
    for query_text in TYPING_SEQUENCE:
        ranked = match_and_rank_games(candidate_games, query_text)
        results = [build_result(game, files_dir, score) for game, score in ranked]
        if not query_text:
            assert len(results) == EMPTY_QUERY_LIMIT
        else:
            assert len(results) <= SEARCH_QUERY_LIMIT
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert elapsed_ms < 100.0, f"8-keystroke typing sequence took {elapsed_ms:.2f}ms (expected < 100ms)"


def test_typing_sequence_performance_installed_only(tmp_path):
    candidate_games, files_dir = _build_synthetic_library(tmp_path, include_hidden=False)
    installed_games = [game for game in candidate_games if game.is_installed]

    start_time = time.perf_counter()
    for query_text in TYPING_SEQUENCE:
        ranked = match_and_rank_games(installed_games, query_text)
        results = [build_result(game, files_dir, score) for game, score in ranked]
        assert len(results) <= EMPTY_QUERY_LIMIT if not query_text else len(results) <= SEARCH_QUERY_LIMIT
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert elapsed_ms < 25.0, f"Installed-only 8-keystroke sequence took {elapsed_ms:.2f}ms (expected < 25ms)"
