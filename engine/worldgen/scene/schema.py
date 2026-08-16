"""Схема JSON-описания сцены.

Сцена — это данные; рендерер их потребляет и ничего не решает сам (Roadmap 13.6).
Поэтому вся семантика сцены — позиции, свет, ракурсы — живёт здесь и в JSON,
а не в скриптах `render/blender/`.

Соглашение об осях — блендеровское: Z вверх, Y вглубь. Азимут `0` ставит камеру
со стороны `-Y` и смотрит в `+Y` («вид спереди»), рост азимута идёт против часовой
стрелки, если смотреть сверху. Персонаж, стало быть, должен быть развёрнут лицом
к `-Y`; если импортированный ассет смотрит иначе, это чинится его
`rotation_euler_deg` в JSON, а не поправкой в рендер-скрипте.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from worldgen.jsonread import ConfigValidationError, Reader, Vec3

SCHEMA_VERSION = 1


# ------------------------------------------------------------------------ размещение


@dataclass(frozen=True)
class Placement:
    """Положение в мире: либо орбита вокруг цели, либо явные координаты.

    Орбита — рабочий режим для матрицы ракурсов: три ячейки строки отличаются одним
    числом `azimuth_deg`, и кадрирование гарантированно не уезжает.
    """

    location: Vec3
    rotation_euler: Vec3  # радианы, XYZ

    @classmethod
    def from_dict(cls, r: Reader) -> Placement:
        mode = r.choice("mode", ("orbit", "explicit"), default="orbit")
        if mode == "explicit":
            deg = r.vec3("rotation_euler_deg", (0.0, 0.0, 0.0))
            return cls(
                location=r.vec3("location"),
                rotation_euler=(math.radians(deg[0]), math.radians(deg[1]), math.radians(deg[2])),
            )
        return cls.from_orbit(
            target=r.vec3("target", (0.0, 0.0, 0.0)),
            azimuth_deg=r.num("azimuth_deg", 0.0),
            elevation_deg=r.num("elevation_deg", 0.0),
            distance=r.positive("distance"),
        )

    @classmethod
    def from_orbit(
        cls, *, target: Vec3, azimuth_deg: float, elevation_deg: float, distance: float
    ) -> Placement:
        az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
        location = (
            target[0] + math.sin(az) * math.cos(el) * distance,
            target[1] - math.cos(az) * math.cos(el) * distance,
            target[2] + math.sin(el) * distance,
        )
        # Камера и свет смотрят вдоль своего -Z: наклон от вертикали плюс разворот по азимуту.
        return cls(location=location, rotation_euler=(math.pi / 2 - el, 0.0, az))


# ----------------------------------------------------------------------------- узлы


@dataclass(frozen=True)
class AssetRef:
    """Ссылка на внешний ассет. `path` — относительно корня `engine/`."""

    id: str
    path: str
    location: Vec3 = (0.0, 0.0, 0.0)
    rotation_euler_deg: Vec3 = (0.0, 0.0, 0.0)
    scale: float = 1.0
    is_hero: bool = False

    @classmethod
    def from_dict(cls, r: Reader) -> AssetRef:
        return cls(
            id=r.str_("id"),
            path=r.str_("path"),
            location=r.vec3("location", (0.0, 0.0, 0.0)),
            rotation_euler_deg=r.vec3("rotation_euler_deg", (0.0, 0.0, 0.0)),
            scale=r.positive("scale", 1.0),
            is_hero=r.flag("is_hero", False),
        )


@dataclass(frozen=True)
class Camera:
    id: str
    placement: Placement
    fov_deg: float = 35.0
    clip_start: float = 0.1
    clip_end: float = 100.0

    @classmethod
    def from_dict(cls, r: Reader) -> Camera:
        placement = r.child("placement")
        assert placement is not None
        fov = r.num("fov_deg", 35.0)
        if not 1.0 < fov < 179.0:
            raise ConfigValidationError(
                f"{r.path}.fov_deg: ожидался угол в (1, 179), получено {fov}"
            )
        return cls(
            id=r.str_("id"),
            placement=Placement.from_dict(placement),
            fov_deg=fov,
            clip_start=r.positive("clip_start", 0.1),
            clip_end=r.positive("clip_end", 100.0),
        )


LIGHT_TYPES = ("SUN", "AREA", "POINT", "SPOT")


@dataclass(frozen=True)
class Light:
    id: str
    type: str
    energy: float
    placement: Placement
    color: Vec3 = (1.0, 1.0, 1.0)
    size: float = 1.0

    @classmethod
    def from_dict(cls, r: Reader) -> Light:
        placement = r.child("placement")
        assert placement is not None
        return cls(
            id=r.str_("id"),
            type=r.choice("type", LIGHT_TYPES, default="AREA"),
            energy=r.positive("energy"),
            placement=Placement.from_dict(placement),
            color=r.vec3("color", (1.0, 1.0, 1.0)),
            size=r.positive("size", 1.0),
        )


@dataclass(frozen=True)
class Environment:
    """Земля и задник. Ровно то, что нужно, чтобы герой не висел в пустоте."""

    ground_enabled: bool = True
    ground_size: float = 12.0
    ground_color: Vec3 = (0.55, 0.55, 0.58)
    backdrop_enabled: bool = True
    backdrop_size: float = 12.0
    backdrop_distance: float = 3.0
    backdrop_color: Vec3 = (0.62, 0.66, 0.74)
    world_color: Vec3 = (0.05, 0.06, 0.08)
    world_strength: float = 1.0

    @classmethod
    def from_dict(cls, r: Reader | None) -> Environment:
        d = cls()
        if r is None:
            return d
        # Отсутствующая секция читается как пустая: у каждого поля есть значение по
        # умолчанию, поэтому ошибок из пустого Reader взяться неоткуда.
        ground = r.child("ground", optional=True) or Reader({})
        backdrop = r.child("backdrop", optional=True) or Reader({})
        world = r.child("world", optional=True) or Reader({})
        return cls(
            ground_enabled=ground.flag("enabled", d.ground_enabled),
            ground_size=ground.positive("size", d.ground_size),
            ground_color=ground.vec3("color", d.ground_color),
            backdrop_enabled=backdrop.flag("enabled", d.backdrop_enabled),
            backdrop_size=backdrop.positive("size", d.backdrop_size),
            backdrop_distance=backdrop.positive("distance", d.backdrop_distance),
            backdrop_color=backdrop.vec3("color", d.backdrop_color),
            world_color=world.vec3("color", d.world_color),
            world_strength=world.num("strength", d.world_strength),
        )


@dataclass(frozen=True)
class RenderSettings:
    width: int = 960
    height: int = 1280
    samples: int = 64
    film_transparent: bool = False
    # Standard, а не AgX: cel-заливка не должна съезжать в тональном маппинге.
    view_transform: str = "Standard"

    @classmethod
    def from_dict(cls, r: Reader | None) -> RenderSettings:
        if r is None:
            return cls()
        d = cls()
        return cls(
            width=int(r.positive("width", float(d.width))),
            height=int(r.positive("height", float(d.height))),
            samples=int(r.positive("samples", float(d.samples))),
            film_transparent=r.flag("film_transparent", d.film_transparent),
            view_transform=r.str_("view_transform", d.view_transform),
        )


@dataclass(frozen=True)
class Scene:
    name: str
    assets: list[AssetRef]
    cameras: list[Camera]
    lights: list[Light]
    environment: Environment = field(default_factory=Environment)
    render: RenderSettings = field(default_factory=RenderSettings)
    style_profile: str | None = None
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: Any) -> Scene:
        r = Reader(data)
        version = int(r.num("schema_version", float(SCHEMA_VERSION)))
        if version != SCHEMA_VERSION:
            raise ConfigValidationError(
                f"$.schema_version: поддерживается {SCHEMA_VERSION}, получено {version}"
            )
        style_profile = r.data.get("style_profile")
        if style_profile is not None and not isinstance(style_profile, str):
            raise ConfigValidationError("$.style_profile: ожидался путь строкой")
        scene = cls(
            name=r.str_("name"),
            assets=[AssetRef.from_dict(a) for a in r.children("assets", min_items=1)],
            cameras=[Camera.from_dict(c) for c in r.children("cameras", min_items=1)],
            lights=[Light.from_dict(item) for item in r.children("lights", min_items=1)],
            environment=Environment.from_dict(r.child("environment", optional=True)),
            render=RenderSettings.from_dict(r.child("render", optional=True)),
            style_profile=style_profile,
            schema_version=version,
        )
        scene.validate()
        return scene

    def validate(self) -> None:
        """Проверки, которые нельзя сделать на уровне отдельного узла."""
        for label, ids in (
            ("assets", [a.id for a in self.assets]),
            ("cameras", [c.id for c in self.cameras]),
            ("lights", [item.id for item in self.lights]),
        ):
            duplicates = sorted({i for i in ids if ids.count(i) > 1})
            if duplicates:
                raise ConfigValidationError(f"$.{label}: неуникальные id: {duplicates}")
        # Ровно один герой: маска героя — центральный механизм неоднородного поводка
        # (Roadmap 7.13), и она обязана быть однозначной.
        heroes = [a.id for a in self.assets if a.is_hero]
        if len(heroes) != 1:
            raise ConfigValidationError(
                f"$.assets: ровно один ассет должен нести is_hero=true, найдено {len(heroes)}"
            )

    @property
    def hero(self) -> AssetRef:
        return next(a for a in self.assets if a.is_hero)

    def camera(self, camera_id: str) -> Camera:
        for cam in self.cameras:
            if cam.id == camera_id:
                return cam
        known = ", ".join(c.id for c in self.cameras)
        raise ConfigValidationError(f"камера {camera_id!r} не найдена; есть: {known}")


__all__ = [
    "SCHEMA_VERSION",
    "AssetRef",
    "Camera",
    "Environment",
    "Light",
    "Placement",
    "RenderSettings",
    "Scene",
    "Vec3",
]
