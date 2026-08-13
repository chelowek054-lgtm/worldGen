"""Замороженный визуальный бэкбон для извлечения плотных признаков объекта.

Фаза 1.2: ДНК-компрессор (`worldgen.dna.model.DNACompressor`) сжимает признаки этого
бэкбона в N инвариантных токенов. Бэкбон всегда заморожен — обучается только
компрессор.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

import torch
from torch import nn


class FeatureBackbone(ABC):
    """Контракт извлечения плотных патч-признаков. Реализация всегда заморожена."""

    @property
    @abstractmethod
    def feature_dim(self) -> int:
        """Размерность признака одного патча."""

    @abstractmethod
    def __call__(self, images: torch.Tensor) -> torch.Tensor:
        """images: [B, 3, H, W] в [0, 1] → патч-признаки [B, P, feature_dim]."""


class RandomBackbone(FeatureBackbone):
    """Детерминированная случайная проекция вместо DINOv3.

    Не требует весов/интернета — для тестов, CI и разработки компрессора/трейнера
    до появления мультивид-данных (задача 1.1) и/или без доступа к сети. Не несёт
    семантики: контрастив на этом бэкбоне не докажет инвариантность объекта, только
    то, что пайплайн (форма тензоров, лоссы, чекпоинты) исправен.
    """

    def __init__(self, feature_dim: int = 384, seed: int = 0) -> None:
        self._feature_dim = feature_dim
        generator = torch.Generator().manual_seed(seed)
        self._proj = nn.Conv2d(3, feature_dim, kernel_size=16, stride=16)
        with torch.no_grad():
            for p in self._proj.parameters():
                p.copy_(torch.randn(p.shape, generator=generator))
        self._proj.requires_grad_(False)
        self._proj.eval()

    @property
    def feature_dim(self) -> int:
        return self._feature_dim

    @torch.no_grad()
    def __call__(self, images: torch.Tensor) -> torch.Tensor:
        feats = self._proj(images)  # [B, D, h, w]
        b, d, h, w = feats.shape
        return feats.permute(0, 2, 3, 1).reshape(b, h * w, d)


class Dinov3Backbone(FeatureBackbone):
    """DINOv3 (через `transformers`) — реальный бэкбон для 1.2+.

    Требует пакет `transformers` (группа `engine[eval]`) и доступ к весам (сеть
    или локальный кэш HuggingFace). Импорт — лениво, чтобы `RandomBackbone`
    работал без этой зависимости.
    """

    def __init__(self, model_name: str = "facebook/dinov3-vits16-pretrain-lvd1689m") -> None:
        try:
            from transformers import AutoModel
        except ImportError as exc:  # pragma: no cover - covered by RandomBackbone в тестах
            raise ImportError(
                "Dinov3Backbone требует `pip install -e .[eval]` (пакет transformers)."
            ) from exc

        self._model = AutoModel.from_pretrained(model_name)
        self._model.requires_grad_(False)
        self._model.eval()
        self._feature_dim = int(self._model.config.hidden_size)

    @property
    def feature_dim(self) -> int:
        return self._feature_dim

    @torch.no_grad()
    def __call__(self, images: torch.Tensor) -> torch.Tensor:
        out = self._model(pixel_values=images)
        return out.last_hidden_state[:, 1:, :]  # без CLS-токена


def build_backbone(cfg: Mapping[str, Any]) -> FeatureBackbone:
    """Собрать бэкбон по конфигу (`name`: `random` | `dinov3`)."""
    name = str(cfg.get("name", "random")).lower()
    if name == "random":
        return RandomBackbone(
            feature_dim=int(cfg.get("feature_dim", 384)),
            seed=int(cfg.get("seed", 0)),
        )
    if name == "dinov3":
        return Dinov3Backbone(
            model_name=str(cfg.get("model_name", "facebook/dinov3-vits16-pretrain-lvd1689m"))
        )
    raise ValueError(f"Неизвестный бэкбон: {name!r} (ожидалось 'random' или 'dinov3')")


__all__ = ["FeatureBackbone", "RandomBackbone", "Dinov3Backbone", "build_backbone"]
