"""Проверка пересечения золотого набора с обучающими источниками.

Гейт-критерий задачи 0.1: набор read-only и не пересекается с train — проверка по
перцептивному хешу возвращает 0 коллизий. Здесь — сама проверка (детект near-duplicate).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from worldgen.eval.phash import dhash_path, hamming

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Порог Хэмминга: ≤ threshold считается near-duplicate. Для 64-битного dHash
# значение ~5 — общепринятая консервативная граница.
DEFAULT_THRESHOLD = 5


@dataclass(frozen=True)
class Collision:
    eval_path: Path
    train_path: Path
    distance: int


def _iter_images(root: str | Path) -> list[Path]:
    return [p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS]


def hash_dir(root: str | Path) -> dict[Path, int]:
    """dHash всех изображений под каталогом (рекурсивно)."""
    return {p: dhash_path(p) for p in _iter_images(root)}


def find_collisions(
    eval_root: str | Path,
    train_roots: Iterable[str | Path],
    threshold: int = DEFAULT_THRESHOLD,
) -> list[Collision]:
    """Вернуть пары (eval, train) с перцептивным расстоянием ≤ threshold.

    Пустой список = набор чист (гейт 0.1 пройден). Сложность O(|eval|·|train|) —
    достаточно для небольшого золотого набора; при росте train заменить на BK-tree.
    """
    eval_hashes = hash_dir(eval_root)
    train_hashes: dict[Path, int] = {}
    for root in train_roots:
        train_hashes.update(hash_dir(root))

    collisions: list[Collision] = []
    for eval_path, eval_hash in eval_hashes.items():
        for train_path, train_hash in train_hashes.items():
            distance = hamming(eval_hash, train_hash)
            if distance <= threshold:
                collisions.append(Collision(eval_path, train_path, distance))
    return collisions


__all__ = ["Collision", "hash_dir", "find_collisions", "IMAGE_EXTENSIONS", "DEFAULT_THRESHOLD"]
