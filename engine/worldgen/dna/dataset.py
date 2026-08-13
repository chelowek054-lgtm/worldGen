"""Мультивид-датасет для контрастивного обучения ДНК (задачи 1.1 + 1.2).

Манифест — YAML со списком объектов и путей до их видов (рендеры/кадры одного
инстанса: Objaverse-рендеры, CO3D/MVImgNet, SAM-вырезки из видео — задача 1.1).
Каждый `__getitem__` отдаёт пару (anchor, positive) — два разных вида одного
объекта; один индекс датасета = один объект, поэтому в батче объект не
повторяется и in-batch негативы в `worldgen.dna.losses.info_nce_loss` корректны.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import yaml
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

DEFAULT_IMAGE_SIZE = 224

default_transform = transforms.Compose(
    [
        transforms.Resize((DEFAULT_IMAGE_SIZE, DEFAULT_IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ]
)


@dataclass(frozen=True)
class ObjectViews:
    object_id: str
    views: list[Path]


def load_manifest(path: str | Path) -> list[ObjectViews]:
    """Загрузить манифест мультивид-объектов.

    Формат (пути — относительно файла манифеста):
        objects:
          - id: mug_01
            views: [renders/mug_01/view_00.png, renders/mug_01/view_01.png]
    """
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = path.parent
    objects = []
    for entry in data.get("objects", []) or []:
        views = [root / v for v in entry["views"]]
        objects.append(ObjectViews(object_id=str(entry["id"]), views=views))
    return objects


class MultiViewPairDataset(Dataset):
    """Каждый элемент — пара (вид A, вид B) одного объекта. Объекты с < 2 видами пропускаются."""

    def __init__(
        self,
        objects: list[ObjectViews],
        transform: Any = default_transform,
        seed: int = 0,
    ) -> None:
        self.objects = [o for o in objects if len(o.views) >= 2]
        if not self.objects:
            raise ValueError("нужен хотя бы один объект с >= 2 видами")
        self.transform = transform
        self._rng = random.Random(seed)

    def __len__(self) -> int:
        return len(self.objects)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor | str]:
        obj = self.objects[idx]
        view_a, view_b = self._rng.sample(obj.views, 2)
        return {
            "object_id": obj.object_id,
            "anchor": self.transform(Image.open(view_a).convert("RGB")),
            "positive": self.transform(Image.open(view_b).convert("RGB")),
        }


class SyntheticMultiViewDataset(Dataset):
    """Синтетический датасет без файлов — для тестов и разработки трейнера/лоссов.

    Каждый «объект» — фиксированный случайный шаблон (seed = id объекта) + шум на
    вид, чтобы anchor/positive одного объекта были похожи, а разных объектов —
    нет. Не заменяет реальные мультивид-данные (задача 1.1) — только проверяет,
    что пайплайн форм/лоссов/трейнера исправен до их появления.
    """

    def __init__(
        self,
        n_objects: int = 16,
        image_size: int = DEFAULT_IMAGE_SIZE,
        noise_std: float = 0.05,
        seed: int = 0,
    ) -> None:
        self.n_objects = n_objects
        self.image_size = image_size
        self.noise_std = noise_std
        self._base_seed = seed

    def __len__(self) -> int:
        return self.n_objects

    def _template(self, object_id: int) -> torch.Tensor:
        generator = torch.Generator().manual_seed(self._base_seed + object_id)
        return torch.rand(3, self.image_size, self.image_size, generator=generator)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor | str]:
        template = self._template(idx)
        anchor = (template + torch.randn_like(template) * self.noise_std).clamp(0, 1)
        positive = (template + torch.randn_like(template) * self.noise_std).clamp(0, 1)
        return {"object_id": str(idx), "anchor": anchor, "positive": positive}


__all__ = [
    "ObjectViews",
    "load_manifest",
    "MultiViewPairDataset",
    "SyntheticMultiViewDataset",
    "default_transform",
    "DEFAULT_IMAGE_SIZE",
]
