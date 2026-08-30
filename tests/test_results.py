from playnite import Game
from results import build_context_menu, build_result, context_payload, error_result, install_exporter_result


def game(**overrides):
    fields = dict(
        id="033b6530-47a6-4179-a8fa-c1197ea4f335",
        name="Doom",
        is_installed=True,
        install_directory=r"F:\Games\Doom",
        icon="033b6530\\icon.ico",
        source="Steam",
    )
    fields.update(overrides)
    return Game(**fields)


def menu_titles(payload):
    return [result.title for result in build_context_menu(payload)]


def test_build_result_installed_launches(tmp_path):
    result = build_result(game(), tmp_path)
    assert result.title == "Doom"
    assert result.json_rpc_action["Parameters"] == ["playnite://playnite/start/033b6530-47a6-4179-a8fa-c1197ea4f335"]
    assert result.context_data == [context_payload(game(), tmp_path)]


def test_build_result_uninstalled_shows_detail(tmp_path):
    result = build_result(game(is_installed=False), tmp_path)
    assert "showgame" in result.json_rpc_action["Parameters"][0]


def test_full_context_menu(tmp_path):
    payload = context_payload(game(install_directory=str(tmp_path)), tmp_path)
    titles = menu_titles(payload)
    assert titles == ["Launch", "Show in Playnite", "Open install folder", "Copy game Id"]


def test_context_menu_omits_missing_install_directory(tmp_path):
    missing = tmp_path / "gone"
    payload = context_payload(game(install_directory=str(missing)), tmp_path)
    assert "Open install folder" not in menu_titles(payload)


def test_context_menu_is_conditional(tmp_path):
    payload = context_payload(game(is_installed=False, install_directory=None), tmp_path)
    titles = menu_titles(payload)
    assert titles == ["Install", "Show in Playnite", "Copy game Id"]


def test_context_menu_actions(tmp_path):
    payload = context_payload(game(install_directory=str(tmp_path)), tmp_path)
    menu = {result.title: result.json_rpc_action for result in build_context_menu(payload)}
    assert menu["Open install folder"]["Parameters"][0] == str(tmp_path)
    assert menu["Copy game Id"]["Parameters"][0] == "033b6530-47a6-4179-a8fa-c1197ea4f335"


def test_error_result_opens_settings():
    result = error_result("Playnite not found", "Set the path in settings")
    assert "SettingDialog" in result.json_rpc_action["Method"] or "setting" in result.json_rpc_action["Method"].lower()


def test_install_exporter_result_opens_addon_page():
    result = install_exporter_result()
    assert result.json_rpc_action["Parameters"] == ["playnite://playnite/installaddon/FlowLauncherExporter"]
