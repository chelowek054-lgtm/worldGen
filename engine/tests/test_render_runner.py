"""Поиск Blender и сборка команды. Сам Blender для этих тестов не нужен."""

from __future__ import annotations

from pathlib import Path

import pytest

from worldgen.render import BLENDER_ENV_VAR, BlenderNotFoundError, find_blender, run_blender_script
from worldgen.render.runner import BLENDER_SCRIPTS_DIR


def test_explicit_path_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "blender.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv(BLENDER_ENV_VAR, str(tmp_path / "другой.exe"))
    assert find_blender(fake) == fake


def test_env_var_used_when_no_explicit_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "blender.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv(BLENDER_ENV_VAR, str(fake))
    assert find_blender() == fake


def test_missing_explicit_path_reported(tmp_path: Path) -> None:
    with pytest.raises(BlenderNotFoundError, match="не найден"):
        find_blender(tmp_path / "нет-такого.exe")


def test_broken_env_var_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(BLENDER_ENV_VAR, str(tmp_path / "нет-такого.exe"))
    with pytest.raises(BlenderNotFoundError, match=BLENDER_ENV_VAR):
        find_blender()


def test_unknown_script_fails_before_launching_blender(tmp_path: Path) -> None:
    """Blender не должен даже стартовать ради опечатки в имени скрипта."""
    fake = tmp_path / "blender.exe"
    fake.write_text("", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="нет-такого.py"):
        run_blender_script("нет-такого.py", [], blender=fake)


def test_shipped_blender_scripts_exist() -> None:
    for name in ("build_scene.py", "make_proxy_asset.py"):
        assert (BLENDER_SCRIPTS_DIR / name).is_file()


def test_blender_scripts_are_not_importable_as_package() -> None:
    """`bpy` вне Blender не существует — каталог не должен быть импортируемым пакетом."""
    assert not (BLENDER_SCRIPTS_DIR / "__init__.py").exists()
