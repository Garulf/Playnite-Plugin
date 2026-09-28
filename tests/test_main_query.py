import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

from playnite import LibraryLocked

MAIN_PATH = Path(__file__).parent.parent / "src" / "plugin" / "__main__.py"


def load_main():
    spec = importlib.util.spec_from_file_location("playnite_plugin_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_query_uses_library_source(monkeypatch, tmp_path):
    main = load_main()

    # lib.files_dir must resolve for real: when games come from the live
    # server, lib.games() is never called, so this is the only thing that
    # would otherwise validate playnite_path (see the PlayniteNotFound note
    # in Step 2).
    (tmp_path / "library").mkdir()

    fake_game = Mock(name="game")
    monkeypatch.setattr(main, "library_source_games", lambda **kwargs: [fake_game])
    monkeypatch.setattr(main, "build_result", lambda game, files_dir, score: f"result-for-{game}")

    # pyflowlauncher's Plugin.settings/.launcher are read-only properties
    # (Plugin.settings returns self._launcher.settings; Launcher.settings
    # returns self._launcher._settings) — pinned pyflowlauncher==1.1.1 has
    # no setter on either. The private `_launcher` attribute itself is a
    # normal, freely-assignable instance attribute, so replace it wholesale
    # with a fake exposing the same shape (.settings, .api.fuzzy_search).
    async def fake_fuzzy_search(query, name):
        return Mock(score=100, score_cutoff=50)

    fake_launcher = Mock()
    fake_launcher.settings = {"playnite_path": str(tmp_path)}
    fake_launcher.api.fuzzy_search = fake_fuzzy_search
    monkeypatch.setattr(main.plugin, "_launcher", fake_launcher)

    results = [item async for item in main.query("")]

    assert results == [f"result-for-{fake_game}"]


@pytest.mark.asyncio
async def test_query_reports_bad_playnite_path_even_when_server_has_data(monkeypatch, tmp_path):
    """lib.files_dir is read eagerly inside the try block specifically so this
    still surfaces as a clean error_result instead of an unhandled exception,
    even though the server path never calls lib.games()."""
    main = load_main()

    monkeypatch.setattr(main, "library_source_games", lambda **kwargs: [Mock(name="game")])

    fake_launcher = Mock()
    fake_launcher.settings = {"playnite_path": str(tmp_path / "does-not-exist")}
    monkeypatch.setattr(main.plugin, "_launcher", fake_launcher)

    results = [item async for item in main.query("")]

    assert len(results) == 1
    assert "not found" in results[0].title.lower()


@pytest.mark.asyncio
async def test_query_suggests_library_server_when_playnite_locks_library(monkeypatch, tmp_path):
    main = load_main()

    def raise_locked(**kwargs):
        raise LibraryLocked(tmp_path / "library" / "games.db")

    monkeypatch.setattr(main, "library_source_games", raise_locked)

    fake_launcher = Mock()
    fake_launcher.settings = {"playnite_path": str(tmp_path)}
    monkeypatch.setattr(main.plugin, "_launcher", fake_launcher)

    results = [item async for item in main.query("")]

    assert len(results) == 1
    assert "playnite-library-server" in results[0].title
