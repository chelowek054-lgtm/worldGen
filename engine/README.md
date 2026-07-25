# engine — ML-пайплайн World-Gen

Нейросетевой движок генерации миров. Отдельный от веб-стека (`backend/`, `frontend/`)
компонент на PyTorch. Реализуется по фазам из
[docs/base-plans/](../docs/base-plans/README.md); текущий статус —
[STATUS.md](../docs/base-plans/STATUS.md).

## Что уже есть (задача 0.0 — Definition of Ready)

- **Детерминизм** — [`worldgen/seed.py`](worldgen/seed.py): единая `set_seed()` для
  `random` / `numpy` / `torch` (+CUDA/cuDNN).
- **Конфиги** — Hydra + YAML в [`configs/`](configs/): один конфиг → один прогон.
- **Трекинг экспериментов** — абстрактный [`Tracker`](worldgen/tracking/base.py);
  бэкенд по умолчанию — **MLflow** (локальный file store), сменяется одной строкой
  конфига (`tracking=noop`).
- **Воспроизводимость** — [`scripts/reproduce.py`](scripts/reproduce.py):
  один конфиг → один прогон → залогированные метрики.
- **Золотой набор** — holder-каталог [`data/golden_set/`](data/golden_set/README.md)
  (наполнение — задача 0.1).

## Установка

```bash
cd engine
python -m venv .venv
# Windows:
.venv/Scripts/pip install -e .[dev]
# Linux/macOS:
# .venv/bin/pip install -e .[dev]
```

Дополнительные группы зависимостей:

- `.[eval]` — метрики и бэкбоны (DINO/CLIP, FID, retrieval) — фазы 0.1–0.2.
- `.[data]` — DVC (версионирование данных/весов).
- `.[gen]` — генеративный стек (`diffusers`, `peft`) — фаза 1+.
- `.[gpu]` — `xformers` (ставить на GPU-хосте).

> **CUDA:** по умолчанию ставится CPU-сборка `torch`. Для GPU переустановите torch
> под вашу CUDA согласно инструкции на pytorch.org, затем `pip install -e .[gpu]`.

## Команды

```bash
# Тесты
.venv/Scripts/pytest

# Прогон (MLflow-трекинг по умолчанию → runs/mlruns)
.venv/Scripts/python scripts/reproduce.py

# Прогон без внешнего трекинга (метрики в runs/<run_name>/*.json)
.venv/Scripts/python scripts/reproduce.py tracking=noop run_name=exp1 seed=7

# UI MLflow (локальный SQLite-бэкенд)
.venv/Scripts/mlflow ui --backend-store-uri sqlite:///runs/mlflow.db
```

## Структура

```
engine/
  configs/            # Hydra: config.yaml + tracking/{mlflow,noop}.yaml
  worldgen/           # пакет
    seed.py           # детерминизм
    paths.py          # абсолютные пути (независимо от cwd)
    tracking/         # Tracker (ABC) + mlflow/noop + factory
  scripts/
    reproduce.py      # один конфиг → один прогон → метрики
  tests/              # pytest: seed / tracking / reproduce
  data/golden_set/    # holder набора (DVC, задача 0.1)
  runs/               # выходы прогонов (gitignored)
```

Артефакты (`runs/`, `mlruns/`, `data/**`) не коммитятся — см. [`.gitignore`](.gitignore).
