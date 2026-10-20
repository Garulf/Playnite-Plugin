# src/plugin/settings.py
from __future__ import annotations

from typing import Mapping


def as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        stripped = value.strip().lower()
        if not stripped:
            return False
        return stripped in {"1", "true", "yes", "on"}
    return default


def should_show_hidden(settings: Mapping) -> bool:
    return as_bool(settings.get("show_hidden"), default=True)


def should_show_uninstalled(settings: Mapping) -> bool:
    if "show_uninstalled" in settings and settings.get("show_uninstalled") is not None:
        return as_bool(settings.get("show_uninstalled"), default=True)
    if "hide_uninstalled" in settings and settings.get("hide_uninstalled") is not None:
        return not as_bool(settings.get("hide_uninstalled"), default=False)
    return True


def should_use_library_server(settings: Mapping) -> bool:
    return as_bool(settings.get("use_library_server"), default=False)
