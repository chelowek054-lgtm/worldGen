"""Скрипт воспроизводимости: один конфиг → один прогон → залогированные метрики.

Опорная точка Definition of Ready (задача 0.0). Пока эксперимент — детерминированная
заглушка; в фазах 0.1+ `run_experiment` заменяется реальной оценкой на золотом наборе.

Запуск (из каталога engine/):
    python scripts/reproduce.py
    python scripts/reproduce.py run_name=exp1 seed=7 tracking=noop
"""

from __future__ import annotations

import hydra
from omegaconf import DictConfig, OmegaConf

from worldgen.seed import set_seed
from worldgen.tracking import build_tracker


def run_experiment(cfg: DictConfig) -> dict[str, float]:
    """Детерминированная заглушка эксперимента.

    Фиксирует seed и считает простые статистики по псевдослучайной выборке —
    доказывает, что «один конфиг → те же метрики». Заменяется реальной оценкой в 0.1+.
    """
    import numpy as np

    set_seed(int(cfg.seed))
    sample = np.random.rand(int(cfg.experiment.n))
    return {"mean": float(sample.mean()), "std": float(sample.std())}


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    metrics = run_experiment(cfg)

    tracking_cfg = OmegaConf.to_container(cfg.tracking, resolve=True)
    assert isinstance(tracking_cfg, dict)

    with build_tracker(tracking_cfg) as tracker:
        tracker.start_run(str(cfg.run_name), params={"seed": cfg.seed, "n": cfg.experiment.n})
        tracker.log_metrics(metrics)

    print(f"[reproduce] run={cfg.run_name} seed={cfg.seed} metrics={metrics}")


if __name__ == "__main__":
    main()
