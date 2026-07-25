"""Детерминизм: единая точка фиксации всех источников случайности.

Опора всей воспроизводимости фазы 0 — один и тот же seed обязан давать один и тот же
прогон. Покрываем `random`, `numpy` и (если установлен) `torch`, включая CUDA и cuDNN.
"""

from __future__ import annotations

import os
import random


def set_seed(seed: int, *, deterministic: bool = True) -> None:
    """Зафиксировать seed во всех источниках случайности.

    Args:
        seed: значение seed.
        deterministic: включить детерминированные алгоритмы cuDNN (медленнее, но
            воспроизводимо). Отключается для скорости, когда точный детерминизм не нужен.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:  # numpy — обязательная зависимость, но не роняем каркас
        pass

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


__all__ = ["set_seed"]
