"""Абсолютные пути каркаса, независимые от текущей рабочей директории."""

from __future__ import annotations

from pathlib import Path

# engine/worldgen/paths.py → parents[1] == engine/
ENGINE_ROOT: Path = Path(__file__).resolve().parents[1]
RUNS_DIR: Path = ENGINE_ROOT / "runs"
DATA_DIR: Path = ENGINE_ROOT / "data"
CONFIGS_DIR: Path = ENGINE_ROOT / "configs"

__all__ = ["ENGINE_ROOT", "RUNS_DIR", "DATA_DIR", "CONFIGS_DIR"]
