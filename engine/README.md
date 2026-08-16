# engine — ML-пайплайн World-Gen

Движок генерации сцен. Отдельный от веб-стека (`backend/`, `frontend/`) компонент
на PyTorch; в целевой архитектуре — воркер, исполняющий задания сервиса сцены.

Что делается сейчас — [docs/base-plans/HANDOFF.md](../docs/base-plans/HANDOFF.md).
Как устроена система — [architecture.md](../docs/architects/system/architecture.md).

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

**Срез MVP — сцена и рендер (шаги S0–S1):**

- **Описание сцены** — [`worldgen/scene/`](worldgen/scene/): схема JSON, валидация,
  соглашение об осях. Сцена — данные; рендерер их потребляет и ничего не решает сам.
- **Профиль стиля** — [`worldgen/style/`](worldgen/style/): подача, палитра и шкала
  длины поводка (раздельно герой / фон).
- **Рендер** — [`worldgen/render/`](worldgen/render/): поиск Blender и запуск
  подпроцессом. Скрипты для исполнения внутри Blender — в
  [`worldgen/render/blender/`](worldgen/render/blender/), пакетом они не импортируются
  (`bpy` вне Blender не существует).
- **Конфиги среза** — [`configs/mvp/`](configs/mvp/): сцена, болванка, профиль стиля.

Проверено на **Blender 5.1.1** (headless): EEVEE отдаёт Combined, Depth, Normal и
CryptoObject в один multilayer EXR. Путь ищется автоматически (в том числе
Steam-установка), переопределяется переменной `WORLDGEN_BLENDER`.

**`worldgen/dna/` — не ядро, не развивать.**

Каркас ДНК-компрессора (Perceiver-ресемплер поверх замороженного бэкбона,
контрастив, трейнер/предиктор/чекпоинты) написан до смены парадигмы. Понижен до
кода retrieval-ключа и в текущем срезе не используется — подробнее в
[HANDOFF](../docs/base-plans/HANDOFF.md) и [decision-log](../docs/base-plans/decision-log.md).
Не принимать за основу, пока не понадобится реестр ассетов.

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

# Сцена → кадр (S0). Без --camera берётся первый ракурс из описания.
.venv/Scripts/python scripts/render_scene.py --scene configs/mvp/scene.json --all-cameras
.venv/Scripts/python scripts/render_scene.py --scene configs/mvp/scene.proxy.json --camera front

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
    mvp/                   # срез MVP: сцена, болванка, профиль стиля
  worldgen/               # пакет
    seed.py               # детерминизм
    paths.py               # абсолютные пути (независимо от cwd)
    tracking/               # Tracker (ABC) + mlflow/noop + factory
    eval/                    # phash / overlap / manifest золотого набора
    dna/                      # ДНК-компрессор (фаза 1.2): backbone, model,
                              # losses, dataset, trainer, predictor, checkpoints
    jsonread.py                # чтение JSON-конфигов с путём до поля в ошибке
    scene/                      # схема и загрузка описания сцены
    style/                       # профиль стиля: подача, палитра, поводок
    render/                       # запуск Blender подпроцессом
      blender/                     # скрипты, исполняемые внутри Blender (bpy)
  scripts/
    reproduce.py           # заглушка DoR: один конфиг → один прогон → метрики
    check_overlap.py        # гейт 0.1: eval-набор не пересекается с train
    train_dna.py             # обучение ДНК-компрессора
    render_scene.py           # сцена → кадр (S0)
  tests/                  # pytest: seed / tracking / reproduce / eval / dna
  data/
    golden_set/           # holder набора для регресс-проверок (DVC, задача 0.1)
    dna_train/              # holder мультивид-данных для контрастива (DVC, задача 1.1)
    assets/                  # ассеты сцены: герой и болванка (DVC, шаг S0)
  runs/                   # выходы прогонов (gitignored)
```

Артефакты (`runs/`, `mlruns/`, `data/**`) не коммитятся — см. [`.gitignore`](.gitignore).
