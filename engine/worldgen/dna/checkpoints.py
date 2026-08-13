"""Сохранение/загрузка чекпоинтов ДНК-компрессора."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch


@dataclass
class Checkpoint:
    model_state_dict: dict[str, Any]
    config: dict[str, Any] = field(default_factory=dict)
    epoch: int = 0
    metric: float | None = None


def save_checkpoint(path: str | Path, checkpoint: Checkpoint) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": checkpoint.model_state_dict,
            "config": checkpoint.config,
            "epoch": checkpoint.epoch,
            "metric": checkpoint.metric,
        },
        path,
    )


def load_checkpoint(path: str | Path, map_location: str | torch.device = "cpu") -> Checkpoint:
    data = torch.load(Path(path), map_location=map_location, weights_only=False)
    return Checkpoint(
        model_state_dict=data["model_state_dict"],
        config=data.get("config", {}),
        epoch=int(data.get("epoch", 0)),
        metric=data.get("metric"),
    )


__all__ = ["Checkpoint", "save_checkpoint", "load_checkpoint"]
