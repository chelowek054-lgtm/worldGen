"""Трекер без внешнего бэкенда: пишет параметры/метрики в локальные JSON.

Полезен для тестов, CI и офлайн-прогонов, где не нужен MLflow.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from worldgen.paths import RUNS_DIR
from worldgen.tracking.base import Tracker


class NoopTracker(Tracker):
    def __init__(self, runs_dir: str | Path | None = None) -> None:
        self._runs_dir = Path(runs_dir) if runs_dir is not None else RUNS_DIR
        self._run_dir: Path | None = None
        self._params: dict[str, Any] = {}
        self._metrics: list[dict[str, Any]] = []

    def start_run(self, run_name: str, params: Mapping[str, Any] | None = None) -> None:
        self._run_dir = self._runs_dir / run_name
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._params = {}
        self._metrics = []
        if params:
            self.log_params(params)

    def _require_run(self) -> Path:
        if self._run_dir is None:
            raise RuntimeError("start_run() должен быть вызван до логирования")
        return self._run_dir

    def log_params(self, params: Mapping[str, Any]) -> None:
        run_dir = self._require_run()
        self._params.update(dict(params))
        (run_dir / "params.json").write_text(
            json.dumps(self._params, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def log_metrics(self, metrics: Mapping[str, float], step: int | None = None) -> None:
        run_dir = self._require_run()
        self._metrics.append({"step": step, **{k: float(v) for k, v in metrics.items()}})
        (run_dir / "metrics.json").write_text(
            json.dumps(self._metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def log_artifact(self, path: str | Path) -> None:
        # Артефакты остаются на месте; для no-op достаточно ссылки в params.
        self._require_run()  # бросит, если прогон не открыт
        artifacts = self._params.setdefault("_artifacts", [])
        artifacts.append(str(path))
        self.log_params({})  # сброс params.json с обновлённым списком

    def end_run(self) -> None:
        self._run_dir = None


__all__ = ["NoopTracker"]
