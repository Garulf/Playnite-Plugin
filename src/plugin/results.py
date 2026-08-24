from __future__ import annotations

from pathlib import Path

from pyflowlauncher import Result, api
from pyflowlauncher.icons import SETTINGS as SETTINGS_ICON
from pyflowlauncher.models.result import PreviewInfo

from playnite import Game, game_subtitle, media_path, show_game_uri, start_uri


def context_payload(game: Game, files_dir: Path) -> dict:
    icon = media_path(files_dir, game.icon)
    return {
        "id": game.id,
        "name": game.name,
        "is_installed": game.is_installed,
        "install_directory": game.install_directory,
        "links": game.links,
        "icon": str(icon) if icon else None,
    }


def build_result(game: Game, files_dir: Path, score: int = 0) -> Result:
    uri = game.start_uri if game.is_installed else game.show_game_uri
    cover = media_path(files_dir, game.cover_image)
    preview = PreviewInfo(
        PreviewImagePath=str(cover) if cover else None,
        Description=game.name,
        IsMedia=True,
        PreviewDeligate="",
    )
    return Result(
        title=game.name,
        subtitle=game_subtitle(game),
        icon=media_path(files_dir, game.icon),
        score=score,
        preview=preview,
        json_rpc_action=api.open_uri(uri),
        context_data=[context_payload(game, files_dir)],
    )


def build_context_menu(payload: dict) -> list[Result]:
    icon = payload.get("icon")
    installed = payload["is_installed"]
    game_id = payload["id"]
    results = [
        Result(
            title="Launch" if installed else "Install",
            subtitle=f"{'Launch' if installed else 'Install'} {payload['name']} with Playnite",
            icon=icon,
            json_rpc_action=api.open_uri(start_uri(game_id)),
        ),
        Result(
            title="Show in Playnite",
            subtitle="Open the game's detail page",
            icon=icon,
            json_rpc_action=api.open_uri(show_game_uri(game_id)),
        ),
    ]
    if installed and payload.get("install_directory") and Path(payload["install_directory"]).is_dir():
        results.append(
            Result(
                title="Open install folder",
                subtitle=payload["install_directory"],
                icon=icon,
                json_rpc_action=api.open_directory(payload["install_directory"]),
            )
        )
    for link in payload.get("links") or []:
        results.append(
            Result(
                title=link["name"],
                subtitle=link["url"],
                icon=icon,
                json_rpc_action=api.open_url(link["url"]),
            )
        )
    results.append(
        Result(
            title="Copy game Id",
            subtitle=game_id,
            icon=icon,
            json_rpc_action=api.copy_to_clipboard(game_id),
        )
    )
    return results


def error_result(title: str, subtitle: str) -> Result:
    return Result(
        title=title,
        subtitle=subtitle,
        icon=SETTINGS_ICON,
        json_rpc_action=api.open_setting_dialog(),
    )
