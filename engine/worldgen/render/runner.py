"""Запуск Blender подпроцессом.

`bpy` живёт только внутри процесса Blender, поэтому пакет `worldgen` никогда его не
импортирует: он собирает командную строку и разбирает результат. Скрипты для
исполнения внутри Blender лежат в `worldgen/render/blender/`.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from worldgen.paths import ENGINE_ROOT

BLENDER_ENV_VAR = "WORLDGEN_BLENDER"
BLENDER_SCRIPTS_DIR = Path(__file__).resolve().parent / "blender"

# Минимум, на котором проверено: EEVEE отдаёт Cryptomatte, Depth и Normal в один
# multilayer EXR, а формат вывода требует media_type="MULTI_LAYER_IMAGE" (5.x API).
MIN_BLENDER_VERSION = (5, 0)


class BlenderNotFoundError(RuntimeError):
    """Не удалось найти исполняемый файл Blender."""


def _steam_blender_candidates() -> list[Path]:
    """Blender, поставленный через Steam, лежит в произвольной библиотеке."""
    vdf = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    vdf = vdf / "Steam" / "steamapps" / "libraryfolders.vdf"
    if not vdf.is_file():
        return []
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    roots = [Path(m) for m in re.findall(r'"path"\s+"([^"]+)"', text.replace("\\\\", "\\"))]
    return [root / "steamapps" / "common" / "Blender" / "blender.exe" for root in roots]


def _default_candidates() -> list[Path]:
    candidates: list[Path] = []
    on_path = shutil.which("blender")
    if on_path:
        candidates.append(Path(on_path))
    if sys.platform == "win32":
        for env in ("ProgramFiles", "ProgramW6432"):
            base = os.environ.get(env)
            if base:
                candidates += sorted(
                    Path(base).glob("Blender Foundation/Blender */blender.exe"), reverse=True
                )
        candidates += _steam_blender_candidates()
    else:
        candidates += [Path("/usr/bin/blender"), Path("/usr/local/bin/blender")]
    return candidates


def find_blender(explicit: str | Path | None = None) -> Path:
    """Найти blender: явный путь → переменная окружения → PATH → штатные места установки."""
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise BlenderNotFoundError(f"указанный blender не найден: {path}")
        return path

    from_env = os.environ.get(BLENDER_ENV_VAR)
    if from_env:
        path = Path(from_env)
        if not path.is_file():
            raise BlenderNotFoundError(f"{BLENDER_ENV_VAR}={from_env}, но файла нет")
        return path

    for candidate in _default_candidates():
        if candidate.is_file():
            return candidate

    raise BlenderNotFoundError(
        "blender не найден. Укажите путь через переменную окружения "
        f"{BLENDER_ENV_VAR} или аргумент --blender."
    )


def blender_version(executable: Path) -> tuple[int, int, int]:
    result = subprocess.run(
        [str(executable), "--version"], capture_output=True, text=True, timeout=120, check=False
    )
    match = re.search(r"Blender\s+(\d+)\.(\d+)\.(\d+)", result.stdout)
    if not match:
        raise BlenderNotFoundError(f"не удалось прочитать версию Blender из вывода {executable}")
    return (int(match[1]), int(match[2]), int(match[3]))


def run_blender_script(
    script: str | Path,
    script_args: list[str],
    *,
    blender: str | Path | None = None,
    factory_startup: bool = True,
    timeout: float = 1800.0,
) -> subprocess.CompletedProcess[str]:
    """Выполнить скрипт внутри headless-Blender.

    `factory_startup` включён по умолчанию: пользовательские настройки и аддоны не
    должны влиять на результат прогона. Отключать только когда нужен аддон
    (например, импортёр VRM).
    """
    executable = find_blender(blender)
    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = BLENDER_SCRIPTS_DIR / script_path
    if not script_path.is_file():
        raise FileNotFoundError(f"скрипт для Blender не найден: {script_path}")

    command = [str(executable), "--background"]
    if factory_startup:
        command.append("--factory-startup")
    command += ["--python-exit-code", "1", "--python", str(script_path), "--", *script_args]

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        cwd=str(ENGINE_ROOT),
    )


__all__ = [
    "BLENDER_ENV_VAR",
    "BLENDER_SCRIPTS_DIR",
    "MIN_BLENDER_VERSION",
    "BlenderNotFoundError",
    "blender_version",
    "find_blender",
    "run_blender_script",
]
