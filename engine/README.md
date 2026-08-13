# engine — ML-пайплайн World-Gen

Нейросетевой движок генерации миров. Отдельный от веб-стека (`backend/`, `frontend/`)
компонент на PyTorch. Реализуется по фазам из
[docs/base-plans/](../docs/base-plans/README.md); текущий статус —
[STATUS.md](../docs/base-plans/STATUS.md).

## Что уже есть

**Задача 0.0 — Definition of Ready:**

- **Детерминизм** — [`worldgen/seed.py`](worldgen/seed.py): единая `set_seed()` для
  `random` / `numpy` / `torch` (+CUDA/cuDNN).
- **Конфиги** — Hydra + YAML в [`configs/`](configs/): один конфиг → один прогон.
- **Трекинг экспериментов** — абстрактный [`Tracker`](worldgen/tracking/base.py);
  бэкенд по умолчанию — **MLflow** (локальный file store), сменяется одной строкой
  конфига (`tracking=noop`).
- **Воспроизводимость** — [`scripts/reproduce.py`](scripts/reproduce.py):
  один конфиг → один прогон → залогированные метрики.

**Задача 0.1a — инструментарий золотого набора:**

- **Золотой набор** — holder-каталог [`data/golden_set/`](data/golden_set/README.md);
  перцептивный хеш и проверка пересечения с train — [`worldgen/eval/`](worldgen/eval/)
  (наполнение данными — задача 0.1b, ждёт источника).

**Задача 1.2 (каркас) — ДНК-компрессор:**

- [`worldgen/dna/`](worldgen/dna/) — Perceiver-ресемплер поверх замороженного
  визуального бэкбона, контрастив на view-инвариантность, трейнер/предиктор/чекпоинты.
  Заведено опережающе относительно гейта фазы 0 и мультивид-данных (задача 1.1) —
  см. [decision-log](../docs/base-plans/decision-log.md). Бэкбон по умолчанию —
  `random` (детерминированная проекция без сети/весов, только для проверки формы
  пайплайна); `dinov3` — реальный бэкбон, требует `.[eval]` и веса.

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

- `.[eval]` — метрики и бэкбоны (DINO/CLIP, FID, retrieval) — фазы 0.1–0.2 и реальный
  бэкбон `dinov3` в `worldgen/dna/`.
- `.[data]` — DVC (версионирование данных/весов).
- `.[gen]` — генеративный стек (`diffusers`, `peft`) — фаза 1.3+ (инъекция ДНК в генератор).
- `.[gpu]` — `xformers` (ставить на GPU-хосте).

> **CUDA:** по умолчанию ставится CPU-сборка `torch`. Для GPU переустановите torch
> под вашу CUDA согласно инструкции на pytorch.org, затем `pip install -e .[gpu]`.

## Команды

```bash
# Тесты
.venv/Scripts/pytest

# Прогон-заглушка DoR (MLflow-трекинг по умолчанию → runs/mlruns)
.venv/Scripts/python scripts/reproduce.py
.venv/Scripts/python scripts/reproduce.py tracking=noop run_name=exp1 seed=7

# Обучение ДНК-компрессора (без --manifest — синтетические данные, проверка пайплайна)
.venv/Scripts/python scripts/train_dna.py
.venv/Scripts/python scripts/train_dna.py data.manifest=data/dna_train/manifest.yaml backbone=dinov3

# UI MLflow (локальный SQLite-бэкенд)
.venv/Scripts/mlflow ui --backend-store-uri sqlite:///runs/mlflow.db
```

## Структура

```
engine/
  configs/
    config.yaml         # заглушка DoR (задача 0.0)
    dna_config.yaml      # обучение ДНК-компрессора (задача 1.2)
    tracking/            # mlflow / noop
    backbone/             # random (без сети) / dinov3
    eval/                 # golden_set.yaml
  worldgen/               # пакет
    seed.py               # детерминизм
    paths.py               # абсолютные пути (независимо от cwd)
    tracking/               # Tracker (ABC) + mlflow/noop + factory
    eval/                    # phash / overlap / manifest золотого набора
    dna/                      # ДНК-компрессор (фаза 1.2): backbone, model,
                              # losses, dataset, trainer, predictor, checkpoints
  scripts/
    reproduce.py           # заглушка DoR: один конфиг → один прогон → метрики
    check_overlap.py        # гейт 0.1: eval-набор не пересекается с train
    train_dna.py             # обучение ДНК-компрессора
  tests/                  # pytest: seed / tracking / reproduce / eval / dna
  data/
    golden_set/           # holder набора для регресс-проверок (DVC, задача 0.1)
    dna_train/              # holder мультивид-данных для контрастива (DVC, задача 1.1)
  runs/                   # выходы прогонов (gitignored)
```

Артефакты (`runs/`, `mlruns/`, `data/**`) не коммитятся — см. [`.gitignore`](.gitignore).
