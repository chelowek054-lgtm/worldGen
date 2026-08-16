"""Конфиги MVP грузятся и держат состав среза.

Тесты намеренно проверяют не «какие-то» конфиги, а именно те, что лежат в
`configs/mvp/`: это описание среза, и разъехаться с Roadmap-MVP оно не должно
молча. Blender здесь не нужен — только чтение данных.
"""

from __future__ import annotations

from worldgen.paths import ENGINE_ROOT
from worldgen.scene import asset_path, load_scene
from worldgen.style import load_style_profile

SCENE = ENGINE_ROOT / "configs" / "mvp" / "scene.json"
PROXY_SCENE = ENGINE_ROOT / "configs" / "mvp" / "scene.proxy.json"
STYLE = ENGINE_ROOT / "configs" / "mvp" / "style.json"

# Столбцы и строки матрицы из Roadmap-MVP, раздел 5.
EXPECTED_CAMERAS = ["front", "three_quarter", "profile"]
EXPECTED_LEASH = ["short", "medium", "long"]


def test_scene_config_loads() -> None:
    scene = load_scene(SCENE)
    assert scene.hero.id == "hero"


def test_proxy_scene_differs_from_hero_only_by_asset() -> None:
    """Болванка обязана жить в той же сцене: иначе проверка света ничего не значит."""
    scene, proxy = load_scene(SCENE), load_scene(PROXY_SCENE)
    assert scene.cameras == proxy.cameras
    assert scene.lights == proxy.lights
    assert scene.environment == proxy.environment
    assert scene.render == proxy.render
    assert scene.hero.path != proxy.hero.path


def test_matrix_columns_present() -> None:
    scene = load_scene(SCENE)
    assert [c.id for c in scene.cameras] == EXPECTED_CAMERAS


def test_views_differ_only_by_azimuth() -> None:
    """Между ячейками строки меняется ракурс и ничего больше — иначе строку не сравнить."""
    scene = load_scene(SCENE)
    assert len({(c.fov_deg, c.clip_start, c.clip_end) for c in scene.cameras}) == 1
    assert len({c.placement.location for c in scene.cameras}) == len(EXPECTED_CAMERAS)


def test_lighting_is_not_flat() -> None:
    """Плоский свет даёт скучный кадр и ложный вывод «пайплайн некрасив» (Roadmap-MVP 4.1)."""
    scene = load_scene(SCENE)
    assert len(scene.lights) >= 3
    energies = sorted(light.energy for light in scene.lights)
    assert energies[-1] >= 2 * energies[0]


def test_style_config_carries_full_leash_scale() -> None:
    profile = load_style_profile(STYLE)
    assert profile.levels == EXPECTED_LEASH


def test_scene_points_at_existing_style_profile() -> None:
    scene = load_scene(SCENE)
    assert scene.style_profile is not None
    assert (ENGINE_ROOT / scene.style_profile).is_file()


def test_hero_asset_path_is_inside_data() -> None:
    """Ассеты живут в data/ — она версионируется DVC, а не git (CLAUDE.md)."""
    scene = load_scene(SCENE)
    assert asset_path(scene.hero).is_relative_to(ENGINE_ROOT / "data")
