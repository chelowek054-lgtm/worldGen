"""Трекер поверх MLflow (локальный file store по умолчанию)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from worldgen.paths import RUNS_DIR
from worldgen.tracking.base import Tracker


class MlflowTracker(Tracker):
    def __init__(
        self,
        tracking_uri: str | None = None,
        experiment_name: str = "worldgen",
    ) -> None:
        import mlflow

        self._mlflow = mlflow
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        # MLflow 3.x перевёл file store в maintenance mode — используем локальный
        # SQLite-бэкенд (рекомендованный локальный вариант), артефакты — рядом со store.
        uri = tracking_uri or ("sqlite:///" + (RUNS_DIR / "mlflow.db").as_posix())
        prefix = "sqlite:///"
        base = Path(uri[len(prefix) :]).parent if uri.startswith(prefix) else RUNS_DIR
        base.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(uri)
        artifact_location = (base / "mlartifacts").as_uri()
        if mlflow.get_experiment_by_name(experiment_name) is None:
            mlflow.create_experiment(experiment_name, artifact_location=artifact_location)
        mlflow.set_experiment(experiment_name)
        self._active = False

    def start_run(self, run_name: str, params: Mapping[str, Any] | None = None) -> None:
        self._mlflow.start_run(run_name=run_name)
        self._active = True
        if params:
            self.log_params(params)

    def log_params(self, params: Mapping[str, Any]) -> None:
        self._mlflow.log_params(dict(params))

    def log_metrics(self, metrics: Mapping[str, float], step: int | None = None) -> None:
        self._mlflow.log_metrics({k: float(v) for k, v in metrics.items()}, step=step)

    def log_artifact(self, path: str | Path) -> None:
        self._mlflow.log_artifact(str(path))

    def end_run(self) -> None:
        if self._active:
            self._mlflow.end_run()
            self._active = False


__all__ = ["MlflowTracker"]
