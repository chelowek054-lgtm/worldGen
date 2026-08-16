"""Описание сцены: схема JSON и загрузка. Рендерер эту схему не знает — он её потребляет."""

from worldgen.jsonread import ConfigValidationError
from worldgen.scene.loader import asset_path, check_assets_exist, load_scene, load_scene_dict
from worldgen.scene.schema import (
    SCHEMA_VERSION,
    AssetRef,
    Camera,
    Environment,
    Light,
    Placement,
    RenderSettings,
    Scene,
)

__all__ = [
    "SCHEMA_VERSION",
    "AssetRef",
    "Camera",
    "ConfigValidationError",
    "Environment",
    "Light",
    "Placement",
    "RenderSettings",
    "Scene",
    "asset_path",
    "check_assets_exist",
    "load_scene",
    "load_scene_dict",
]
