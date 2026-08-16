"""Рендер: запуск Blender подпроцессом.

Скрипты из `render/blender/` исполняются внутри Blender и отсюда не импортируются —
`bpy` в окружении пакета не существует.
"""

from worldgen.render.runner import (
    BLENDER_ENV_VAR,
    BlenderNotFoundError,
    blender_version,
    find_blender,
    run_blender_script,
)

__all__ = [
    "BLENDER_ENV_VAR",
    "BlenderNotFoundError",
    "blender_version",
    "find_blender",
    "run_blender_script",
]
