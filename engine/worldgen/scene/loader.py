"""Загрузка описания сцены из JSON и разрешение путей ассетов.

Отделено от `schema.py` намеренно: схему импортирует и скрипт внутри Blender,
где важно не тянуть лишнего.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from worldgen.jsonread import ConfigValidationError
from worldgen.paths import ENGINE_ROOT
from worldgen.scene.schema import AssetRef, Scene


def load_scene_dict(path: str | Path) -> dict[str, Any]:
    scene_path = Path(path)
    if not scene_path.is_file():
        raise ConfigValidationError(f"описание сцены не найдено: {scene_path}")
    try:
        data = json.loads(scene_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigValidationError(f"{scene_path}: битый JSON — {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigValidationError(f"{scene_path}: на верхнем уровне ожидался объект")
    return data


def load_scene(path: str | Path) -> Scene:
    """Прочитать и провалидировать сцену. Наличие файлов ассетов здесь не проверяется."""
    return Scene.from_dict(load_scene_dict(path))


def asset_path(asset: AssetRef, *, root: Path = ENGINE_ROOT) -> Path:
    """Абсолютный путь до файла ассета. Относительные пути — от корня `engine/`."""
    raw = Path(asset.path)
    return raw if raw.is_absolute() else (root / raw)


def check_assets_exist(scene: Scene, *, root: Path = ENGINE_ROOT) -> list[str]:
    """Вернуть id ассетов, файлов которых нет на диске.

    Отдельно от `validate()`: схема валидна и без файлов — их отсутствие это
    состояние окружения, а не ошибка описания.
    """
    return [a.id for a in scene.assets if not asset_path(a, root=root).is_file()]


__all__ = ["asset_path", "check_assets_exist", "load_scene", "load_scene_dict"]
