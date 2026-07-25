"""Сборка трекера по конфигу. Единственное место, знающее о конкретных бэкендах."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from worldgen.tracking.base import Tracker


def build_tracker(cfg: Mapping[str, Any]) -> Tracker:
    """Построить трекер по секции конфига `tracking`.

    Ожидает ключ `name` (`mlflow` | `noop`). Смена бэкенда — только здесь и в конфиге.
    """
    name = str(cfg.get("name", "noop")).lower()

    if name == "mlflow":
        from worldgen.tracking.mlflow_tracker import MlflowTracker

        return MlflowTracker(
            tracking_uri=cfg.get("tracking_uri"),
            experiment_name=cfg.get("experiment_name", "worldgen"),
        )
    if name == "noop":
        from worldgen.tracking.noop_tracker import NoopTracker

        return NoopTracker()

    raise ValueError(f"Неизвестный трекер: {name!r} (ожидалось 'mlflow' или 'noop')")


__all__ = ["build_tracker"]
