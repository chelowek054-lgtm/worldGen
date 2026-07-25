"""Перцептивный хеш изображений (dHash) для поиска near-duplicate.

dHash устойчив к масштабу/сжатию/лёгкой цветокоррекции: сравниваем соседние яркости,
кодируем знаки разностей. Расстояние Хэмминга между хешами ≈ перцептивная близость.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def dhash(image: Image.Image, hash_size: int = 8) -> int:
    """64-битный (при hash_size=8) dHash изображения."""
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(resized, dtype=np.int16)
    diff = pixels[:, 1:] > pixels[:, :-1]
    bits = 0
    for bit in diff.flatten():
        bits = (bits << 1) | int(bit)
    return bits


def dhash_path(path: str | Path, hash_size: int = 8) -> int:
    """dHash изображения по пути."""
    with Image.open(path) as img:
        return dhash(img, hash_size=hash_size)


def hamming(a: int, b: int) -> int:
    """Расстояние Хэмминга между двумя хешами."""
    return int(bin(a ^ b).count("1"))


__all__ = ["dhash", "dhash_path", "hamming"]
