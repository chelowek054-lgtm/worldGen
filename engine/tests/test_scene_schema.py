"""Схема сцены: соглашение об осях и отказ принимать неоднозначное описание."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from worldgen.jsonread import ConfigValidationError, Reader
from worldgen.scene import Placement, Scene, check_assets_exist, load_scene

MINIMAL: dict[str, Any] = {
    "schema_version": 1,
    "name": "t",
    "assets": [{"id": "hero", "path": "data/assets/hero.glb", "is_hero": True}],
    "lights": [{"id": "key", "type": "AREA", "energy": 100.0, "placement": {"distance": 3.0}}],
    "cameras": [{"id": "front", "placement": {"distance": 3.0}}],
}


def scene_dict(**overrides: Any) -> dict[str, Any]:
    data = deepcopy(MINIMAL)
    data.update(overrides)
    return data


# ------------------------------------------------------------------ соглашение об осях


def test_azimuth_zero_puts_camera_on_minus_y() -> None:
    """Азимут 0 — «вид спереди»: камера на -Y и смотрит в +Y."""
    placement = Placement.from_orbit(
        target=(0.0, 0.0, 0.0), azimuth_deg=0.0, elevation_deg=0.0, distance=3.0
    )
    assert placement.location == pytest.approx((0.0, -3.0, 0.0), abs=1e-9)
    assert placement.rotation_euler == pytest.approx((math.pi / 2, 0.0, 0.0), abs=1e-9)


def test_azimuth_ninety_puts_camera_on_plus_x() -> None:
    placement = Placement.from_orbit(
        target=(0.0, 0.0, 0.0), azimuth_deg=90.0, elevation_deg=0.0, distance=3.0
    )
    assert placement.location == pytest.approx((3.0, 0.0, 0.0), abs=1e-9)


def test_orbit_keeps_distance_to_target() -> None:
    target = (1.0, -2.0, 0.9)
    for azimuth in (0.0, 40.0, 90.0, 170.0, -40.0):
        placement = Placement.from_orbit(
            target=target, azimuth_deg=azimuth, elevation_deg=25.0, distance=3.2
        )
        offset = [a - b for a, b in zip(placement.location, target, strict=True)]
        assert math.dist(offset, (0.0, 0.0, 0.0)) == pytest.approx(3.2, abs=1e-9)


def test_explicit_placement_converts_degrees_to_radians() -> None:
    placement = Placement.from_dict(
        Reader(
            {
                "mode": "explicit",
                "location": [1.0, 2.0, 3.0],
                "rotation_euler_deg": [90.0, 0.0, 45.0],
            }
        )
    )
    assert placement.location == (1.0, 2.0, 3.0)
    assert placement.rotation_euler == pytest.approx((math.pi / 2, 0.0, math.pi / 4), abs=1e-9)


# ---------------------------------------------------------------------- валидация


def test_minimal_scene_is_valid() -> None:
    scene = Scene.from_dict(scene_dict())
    assert scene.hero.id == "hero"
    assert scene.camera("front").fov_deg == 35.0


def test_exactly_one_hero_required() -> None:
    """Маска героя — центральный механизм неоднородного поводка, она обязана быть одна."""
    no_hero = scene_dict(assets=[{"id": "a", "path": "a.glb"}])
    with pytest.raises(ConfigValidationError, match="is_hero"):
        Scene.from_dict(no_hero)

    two_heroes = scene_dict(
        assets=[
            {"id": "a", "path": "a.glb", "is_hero": True},
            {"id": "b", "path": "b.glb", "is_hero": True},
        ]
    )
    with pytest.raises(ConfigValidationError, match="is_hero"):
        Scene.from_dict(two_heroes)


def test_duplicate_ids_rejected() -> None:
    data = scene_dict(
        cameras=[{"id": "front", "placement": {"distance": 3.0}} for _ in range(2)],
    )
    with pytest.raises(ConfigValidationError, match="неуникальные id"):
        Scene.from_dict(data)


def test_unknown_camera_reports_known_ones() -> None:
    scene = Scene.from_dict(scene_dict())
    with pytest.raises(ConfigValidationError, match="front"):
        scene.camera("back")


def test_error_message_points_at_field() -> None:
    data = scene_dict(cameras=[{"id": "front", "fov_deg": 200.0, "placement": {"distance": 3.0}}])
    with pytest.raises(ConfigValidationError, match=r"cameras\[0\]\.fov_deg"):
        Scene.from_dict(data)


def test_unsupported_schema_version_rejected() -> None:
    with pytest.raises(ConfigValidationError, match="schema_version"):
        Scene.from_dict(scene_dict(schema_version=2))


def test_empty_collections_rejected() -> None:
    for key in ("assets", "cameras", "lights"):
        with pytest.raises(ConfigValidationError, match=key):
            Scene.from_dict(scene_dict(**{key: []}))


def test_unknown_keys_are_ignored() -> None:
    """`_note` и прочие пометки в конфигах не должны ломать загрузку."""
    Scene.from_dict(scene_dict(_note="комментарий"))


# ------------------------------------------------------------------------ загрузка


def test_load_scene_reports_broken_json(tmp_path: Path) -> None:
    path = tmp_path / "scene.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="битый JSON"):
        load_scene(path)


def test_load_scene_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigValidationError, match="не найдено"):
        load_scene(tmp_path / "нет-такого.json")


def test_missing_assets_are_reported_separately(tmp_path: Path) -> None:
    """Отсутствие файла ассета — состояние окружения, а не ошибка описания."""
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(scene_dict()), encoding="utf-8")
    scene = load_scene(path)  # валидация проходит
    assert check_assets_exist(scene, root=tmp_path) == ["hero"]
