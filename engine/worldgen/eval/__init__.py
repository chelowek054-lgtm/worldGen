"""Оценочный слой: золотой набор, перцептивные хеши, проверка пересечений с train.

Реализует инфраструктуру задачи 0.1 (сбор золотого набора) и её гейт-критерий:
набор не должен пересекаться с обучающими источниками (0 коллизий по перцептивному хешу).
"""

from worldgen.eval.manifest import GoldenSetManifest
from worldgen.eval.overlap import find_collisions
from worldgen.eval.phash import dhash, hamming

__all__ = ["GoldenSetManifest", "find_collisions", "dhash", "hamming"]
