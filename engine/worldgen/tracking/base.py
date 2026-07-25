"""Абстракция трекинга экспериментов.

Весь код пишет метрики через интерфейс `Tracker`, а не напрямую в MLflow/W&B.
Смена бэкенда — это выбор реализации в `factory.build_tracker`, код экспериментов
не меняется.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class Tracker(ABC):
    """Минимальный контракт трекера. Поддерживает протокол контекст-менеджера."""

    @abstractmethod
    def start_run(self, run_name: str, params: Mapping[str, Any] | None = None) -> None:
        """Открыть прогон; при наличии — залогировать стартовые параметры."""

    @abstractmethod
    def log_params(self, params: Mapping[str, Any]) -> None:
        """Залогировать гиперпараметры/конфиг прогона."""

    @abstractmethod
    def log_metrics(self, metrics: Mapping[str, float], step: int | None = None) -> None:
        """Залогировать метрики (опционально с номером шага)."""

    @abstractmethod
    def log_artifact(self, path: str | Path) -> None:
        """Приложить артефакт (файл) к прогону."""

    @abstractmethod
    def end_run(self) -> None:
        """Закрыть прогон."""

    def __enter__(self) -> Tracker:
        return self

    def __exit__(self, *exc: object) -> None:
        self.end_run()


__all__ = ["Tracker"]
