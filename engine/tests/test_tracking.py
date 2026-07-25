"""Трекинг: no-op пишет JSON, фабрика собирает нужную реализацию."""

from __future__ import annotations

import json

from worldgen.tracking import Tracker, build_tracker
from worldgen.tracking.noop_tracker import NoopTracker


def test_factory_builds_noop() -> None:
    tracker = build_tracker({"name": "noop"})
    assert isinstance(tracker, NoopTracker)
    assert isinstance(tracker, Tracker)


def test_factory_rejects_unknown() -> None:
    try:
        build_tracker({"name": "does-not-exist"})
    except ValueError:
        return
    raise AssertionError("ожидалась ValueError для неизвестного трекера")


def test_noop_writes_metrics(tmp_path) -> None:
    tracker = NoopTracker(runs_dir=tmp_path)
    with tracker:
        tracker.start_run("unit", params={"seed": 1})
        tracker.log_metrics({"mean": 0.5, "std": 0.1})

    run_dir = tmp_path / "unit"
    params = json.loads((run_dir / "params.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert params["seed"] == 1
    assert metrics[0]["mean"] == 0.5
    assert metrics[0]["std"] == 0.1


def test_mlflow_tracker_sqlite_roundtrip(tmp_path) -> None:
    # Регресс-гард: MLflow 3.x снял поддержку file store; работаем на SQLite-бэкенде.
    import mlflow

    from worldgen.tracking.mlflow_tracker import MlflowTracker

    uri = "sqlite:///" + (tmp_path / "mlflow.db").as_posix()
    with MlflowTracker(tracking_uri=uri, experiment_name="unit") as tracker:
        tracker.start_run("r", params={"seed": 1})
        tracker.log_metrics({"mean": 0.5})

    mlflow.set_tracking_uri(uri)
    df = mlflow.search_runs(experiment_names=["unit"])
    assert len(df) == 1
    assert float(df["metrics.mean"].iloc[0]) == 0.5
