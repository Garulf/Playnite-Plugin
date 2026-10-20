# tests/test_settings.py
from settings import (
    as_bool,
    should_show_hidden,
    should_show_uninstalled,
    should_use_library_server,
)


def test_as_bool_accepts_bools_and_strings():
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool("true") is True
    assert as_bool("True") is True
    assert as_bool("false") is False
    assert as_bool("") is False
    assert as_bool(None) is False
    assert as_bool(None, default=True) is True


def test_show_hidden_defaults_to_true():
    assert should_show_hidden({}) is True
    assert should_show_hidden({"show_hidden": "false"}) is False
    assert should_show_hidden({"show_hidden": True}) is True


def test_show_uninstalled_defaults_to_true_and_supports_legacy_hide_setting():
    assert should_show_uninstalled({}) is True
    assert should_show_uninstalled({"show_uninstalled": "false"}) is False
    assert should_show_uninstalled({"show_uninstalled": "true"}) is True
    assert should_show_uninstalled({"hide_uninstalled": "true"}) is False
    assert should_show_uninstalled({"hide_uninstalled": "false"}) is True


def test_use_library_server_defaults_to_false():
    assert should_use_library_server({}) is False
    assert should_use_library_server({"use_library_server": "true"}) is True
    assert should_use_library_server({"use_library_server": False}) is False
