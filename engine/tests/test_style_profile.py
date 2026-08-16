"""Профиль стиля: шкала поводка и инварианты, которые нельзя размыть опечаткой."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from worldgen.jsonread import ConfigValidationError
from worldgen.style import StyleProfile

MINIMAL: dict[str, Any] = {
    "schema_version": 1,
    "name": "cel",
    "leash": {
        "short": {"hero": 0.2, "background": 0.2},
        "long": {"hero": 0.6, "background": 0.8},
    },
}


def profile_dict(**overrides: Any) -> dict[str, Any]:
    data = deepcopy(MINIMAL)
    data.update(overrides)
    return data


def test_levels_are_ordered_by_freedom() -> None:
    profile = StyleProfile.from_dict(profile_dict())
    assert profile.levels == ["short", "long"]


def test_hero_never_freer_than_background() -> None:
    """Структурный замок из ADR 0002: герой перерисовывается не свободнее фона."""
    data = profile_dict(leash={"broken": {"hero": 0.8, "background": 0.3}})
    with pytest.raises(ConfigValidationError, match="не свободнее фона"):
        StyleProfile.from_dict(data)


def test_denoise_strength_is_normalised() -> None:
    data = profile_dict(leash={"x": {"hero": 1.5, "background": 1.5}})
    with pytest.raises(ConfigValidationError, match=r"\[0, 1\]"):
        StyleProfile.from_dict(data)


def test_leash_scale_cannot_be_empty() -> None:
    with pytest.raises(ConfigValidationError, match="leash"):
        StyleProfile.from_dict(profile_dict(leash={}))


def test_unknown_level_reports_known_ones() -> None:
    profile = StyleProfile.from_dict(profile_dict())
    with pytest.raises(ConfigValidationError, match="short"):
        profile.level("medium")


def test_palette_requires_hex_colors() -> None:
    with pytest.raises(ConfigValidationError, match="palette"):
        StyleProfile.from_dict(profile_dict(palette=["зелёненький"]))


def test_tone_steps_below_two_rejected() -> None:
    """Одна ступень — это не cel, а плоская заливка: стиль перестаёт читаться."""
    with pytest.raises(ConfigValidationError, match="tone_steps"):
        StyleProfile.from_dict(profile_dict(presentation={"tone_steps": 1}))


def test_presentation_defaults_applied() -> None:
    profile = StyleProfile.from_dict(profile_dict())
    assert profile.presentation.tone_steps == 3
    assert profile.presentation.style_reference is None
