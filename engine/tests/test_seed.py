"""Детерминизм: один seed → одна и та же случайность."""

from __future__ import annotations

import random

import numpy as np

from worldgen.seed import set_seed


def test_python_random_deterministic() -> None:
    set_seed(123)
    a = [random.random() for _ in range(5)]
    set_seed(123)
    b = [random.random() for _ in range(5)]
    assert a == b


def test_numpy_deterministic() -> None:
    set_seed(123)
    a = np.random.rand(10)
    set_seed(123)
    b = np.random.rand(10)
    assert np.array_equal(a, b)


def test_different_seed_differs() -> None:
    set_seed(1)
    a = np.random.rand(10)
    set_seed(2)
    b = np.random.rand(10)
    assert not np.array_equal(a, b)


def test_torch_deterministic_if_available() -> None:
    torch = __import__("importlib").import_module("torch") if _has_torch() else None
    if torch is None:
        return  # torch не установлен — пропускаем
    set_seed(123)
    a = torch.rand(10)
    set_seed(123)
    b = torch.rand(10)
    assert torch.equal(a, b)


def _has_torch() -> bool:
    import importlib.util

    return importlib.util.find_spec("torch") is not None
