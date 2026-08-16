"""Профиль стиля — один объект конфигурации на проект (Roadmap 7.12).

Управляет обоими концами цепочки сразу (Roadmap-MVP 4.4):

| Задаёт  | Рендеру                          | Генератору                      |
| ------- | -------------------------------- | ------------------------------- |
| Подача  | ступени тона, толщина контура    | стилевой референс               |
| Цвет    | палитра                          | палитра как ограничение         |
| Свобода | —                                | длина поводка (герой / фон)     |

Поводок — не одно число, а именованная шкала: строки матрицы из
Roadmap-MVP 5 это ровно её уровни. Раздельность «герой / фон» заложена с самого
начала, хотя расходятся они только на S4: неоднородный поводок — центральный
механизм ADR 0002, и городить его задним числом дороже.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from worldgen.jsonread import ConfigValidationError, Reader

SCHEMA_VERSION = 1

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class Presentation:
    """Подача: чем управляем в рендере и чем — в генераторе."""

    tone_steps: int = 3
    outline_thickness: float = 0.004
    style_reference: str | None = None

    @classmethod
    def from_dict(cls, r: Reader | None) -> Presentation:
        if r is None:
            return cls()
        d = cls()
        steps = int(r.positive("tone_steps", float(d.tone_steps)))
        if steps < 2:
            raise ConfigValidationError(
                f"{r.path}.tone_steps: ступеней тона нужно минимум 2, получено {steps}"
            )
        reference = r.data.get("style_reference")
        if reference is not None and not isinstance(reference, str):
            raise ConfigValidationError(f"{r.path}.style_reference: ожидался путь строкой")
        return cls(
            tone_steps=steps,
            outline_thickness=r.positive("outline_thickness", d.outline_thickness),
            style_reference=reference,
        )


@dataclass(frozen=True)
class LeashLevel:
    """Длина поводка на одном уровне шкалы: сила перерисовки, 0 — рендер как есть.

    Герою свободы даётся не больше, чем фону: это и есть структурный замок из
    ADR 0002, и нарушение почти наверняка означает опечатку в конфиге.
    """

    name: str
    hero: float
    background: float

    @classmethod
    def from_dict(cls, name: str, r: Reader) -> LeashLevel:
        hero = r.unit("hero")
        background = r.unit("background")
        if hero > background:
            raise ConfigValidationError(
                f"{r.path}: поводок героя ({hero}) длиннее фонового ({background}); "
                "герой перерисовывается не свободнее фона"
            )
        return cls(name=name, hero=hero, background=background)


@dataclass(frozen=True)
class StyleProfile:
    name: str
    presentation: Presentation = field(default_factory=Presentation)
    palette: tuple[str, ...] = ()
    leash: dict[str, LeashLevel] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: Any) -> StyleProfile:
        r = Reader(data)
        version = int(r.num("schema_version", float(SCHEMA_VERSION)))
        if version != SCHEMA_VERSION:
            raise ConfigValidationError(
                f"$.schema_version: поддерживается {SCHEMA_VERSION}, получено {version}"
            )
        palette = r.data.get("palette", [])
        if not isinstance(palette, list) or any(
            not isinstance(c, str) or not _HEX_COLOR.match(c) for c in palette
        ):
            raise ConfigValidationError("$.palette: ожидался список цветов вида '#rrggbb'")
        levels = {
            name: LeashLevel.from_dict(name, child)
            for name, child in r.named_children("leash", min_items=1).items()
        }
        return cls(
            name=r.str_("name"),
            presentation=Presentation.from_dict(r.child("presentation", optional=True)),
            palette=tuple(palette),
            leash=levels,
            schema_version=version,
        )

    def level(self, name: str) -> LeashLevel:
        if name not in self.leash:
            known = ", ".join(sorted(self.leash))
            raise ConfigValidationError(f"уровень поводка {name!r} не найден; есть: {known}")
        return self.leash[name]

    @property
    def levels(self) -> list[str]:
        """Уровни по возрастанию свободы — порядок строк матрицы из Roadmap-MVP 5."""
        return sorted(self.leash, key=lambda n: (self.leash[n].hero, self.leash[n].background))


def load_style_profile(path: str | Path) -> StyleProfile:
    profile_path = Path(path)
    if not profile_path.is_file():
        raise ConfigValidationError(f"профиль стиля не найден: {profile_path}")
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigValidationError(f"{profile_path}: битый JSON — {exc}") from exc
    return StyleProfile.from_dict(data)


__all__ = [
    "SCHEMA_VERSION",
    "LeashLevel",
    "Presentation",
    "StyleProfile",
    "load_style_profile",
]
