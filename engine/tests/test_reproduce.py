"""Воспроизводимость: один конфиг → те же метрики (в пределах допуска фазы 0)."""

from __future__ import annotations

from omegaconf import OmegaConf

from scripts.reproduce import run_experiment


def _cfg(seed: int = 1234, n: int = 100_000):
    return OmegaConf.create({"seed": seed, "experiment": {"n": n}})


def test_same_config_same_metrics() -> None:
    m1 = run_experiment(_cfg())
    m2 = run_experiment(_cfg())
    assert m1 == m2  # бит-в-бит при одинаковом seed


def test_within_phase0_tolerance() -> None:
    # Гейт фазы 0: повтор того же конфига — в пределах ±2%.
    m1 = run_experiment(_cfg())
    m2 = run_experiment(_cfg())
    assert abs(m1["mean"] - m2["mean"]) <= 0.02 * abs(m1["mean"])


def test_different_seed_changes_metrics() -> None:
    m1 = run_experiment(_cfg(seed=1))
    m2 = run_experiment(_cfg(seed=2))
    assert m1 != m2
