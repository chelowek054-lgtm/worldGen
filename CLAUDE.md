# worldGen

Монорепо из двух независимых частей:
- **Веб-стек**: `frontend/` (Nuxt 4 + TS) + `backend/` (FastAPI, async) — CRUD-приложение,
  оркестрируется через Docker Compose.
- **ML-движок**: `engine/` (PyTorch) — отдельный пакет `worldgen`, генерация миров.
  Не смешивать зависимости и код с веб-стеком.

## Текущий фокус

Реализуется MVP из [docs/base-plans/Roadmap-MVP.md](docs/base-plans/Roadmap-MVP.md).
**Перед началом работы прочитать [docs/base-plans/HANDOFF.md](docs/base-plans/HANDOFF.md)** —
там состояние окружения, порядок чтения и список документов, которые устарели после
смены парадигмы и при буквальном чтении уводят в сторону (в том числе
`detailed-implementation-plan.md` и каркас `engine/worldgen/dna/`, который больше
не является ядром).

## Нестандартный стек

- **engine/** — Hydra-конфиги (один YAML-конфиг = один прогон), MLflow-трекинг
  (бэкенд переключается `tracking=noop` → JSON-метрики вместо MLflow), DVC для
  версионирования данных/весов. Детерминизм обязателен: любой прогон обязан проходить
  через `set_seed()` ([engine/worldgen/seed.py](engine/worldgen/seed.py)).
- Имена пакетов внутри `backend/pyproject.toml` и `frontend/package.json`
  (`online-atelier-*`) — унаследованы от шаблона, не переименовывать без причины,
  это не смежный проект.
- `engine/data/golden_set/` — read-only эталонный набор, версионируется через DVC,
  а не git. Не коммитить сырые файлы напрямую в git.

## Ключевые команды

Веб-стек (через `make`, см. [Makefile](Makefile)):
```bash
make up             # поднять весь стек (dev, hot-reload)
make migrate        # применить alembic-миграции
make test-back       # pytest внутри backend-контейнера
make test-front      # vitest внутри frontend-контейнера
make lint            # ruff (backend) + eslint (frontend)
```

ML-движок (venv в `engine/`, см. [engine/README.md](engine/README.md)):
```bash
cd engine
.venv/Scripts/pytest                              # тесты
.venv/Scripts/python scripts/reproduce.py         # прогон с MLflow-трекингом
.venv/Scripts/python scripts/reproduce.py tracking=noop run_name=exp1 seed=7
.venv/Scripts/ruff check .
.venv/Scripts/mypy .
```

## Архитектурные ограничения

- `engine/` и веб-стек — раздельные Python-окружения и раздельные pyproject.toml;
  не объединять зависимости, не импортировать код `backend/` из `engine/` и наоборот.
- Единый стиль линтинга для обоих Python-пакетов: `ruff`, line-length 100, py312,
  правила `E, F, I, UP, B` (см. `[tool.ruff]` в обоих `pyproject.toml`).
- Прогресс `engine/` фиксируется по фазам с гейтами go/no-go — статус в
  [docs/base-plans/STATUS.md](docs/base-plans/STATUS.md), решения и метрики гейтов —
  в [docs/base-plans/decision-log.md](docs/base-plans/decision-log.md). Перед началом
  новой фазы сверяться с этими файлами, а не только с кодом.
- Артефакты прогонов ML-движка (`engine/runs/`, `mlruns/`) и вся `engine/data/**`
  не коммитятся в git — см. [engine/.gitignore](engine/.gitignore).
- Docker Compose: `docker-compose.yml` — базовый (prod-like), `docker-compose.override.yml`
  подхватывается автоматически поверх для dev (hot-reload); не сливать их в один файл.
