# Разработка

Онбординг и конвенции. Что делать прямо сейчас — в
[HANDOFF](../base-plans/HANDOFF.md).

## Две части репозитория

Репозиторий содержит два независимых Python-окружения; смешивать их нельзя.

| Часть | Что это | Окружение |
| ----- | ------- | --------- |
| `engine/` | ML-движок и воркер: сборка сцены, рендер, перерисовка | свой `pyproject.toml`, venv в `engine/.venv` |
| `backend/` + `frontend/` | Сервис сцены (граф, реестр, очередь) и редактор | свой `pyproject.toml`, Docker Compose |

Роль веб-стека в архитектуре описана в
[architecture, раздел 4](../architects/system/architecture.md#4-стек): `backend/`
хранит граф сцены и реестр и держит очередь заданий, `frontend/` — редактор
сцены, `engine/` эти задания исполняет.

## Команды

Движок (venv в `engine/`):

```bash
cd engine
.venv/Scripts/python -m pytest tests/ -q
.venv/Scripts/ruff check .
.venv/Scripts/mypy .
```

Веб-стек (через `make`):

```bash
make up          # поднять стек (dev, hot-reload)
make migrate     # миграции
make test-back   # pytest в контейнере
make test-front  # vitest в контейнере
make lint        # ruff + eslint
```

## Конвенции

- **Python (обе части):** `ruff`, line-length 100, py312, правила `E, F, I, UP, B`;
  типы — `mypy`; тесты — `pytest`.
- **Frontend:** ESLint (`@nuxt/eslint`), строгий TypeScript, состояние — Pinia.
- **Коммиты:** Conventional Commits (`feat:`, `fix:`, `docs:`…), trunk-based.
- **Воспроизводимость в движке:** один конфиг → один прогон → залогированные
  метрики; seed фиксируется через `set_seed()`, конфиги — Hydra, трекинг — MLflow,
  данные и веса — DVC.
- **Сцена описывается данными, рендерер их потребляет.** Логики сцены внутри
  рендер-скриптов быть не должно — иначе смена рендерера перестаёт быть правкой
  одного модуля.

## Материалы

| Документ | О чём |
| -------- | ----- |
| [Уроки pet-проекта OCR](ocr-pipeline-lessons.md) | Практические паттерны ML-пайплайна: очистка данных, метрики, MLflow, мера уверенности, структура модулей. |

## Что в `engine/` не является ядром

`engine/worldgen/dna/` — каркас ДНК-компрессора, написанный до смены парадигмы.
Понижен до кода retrieval-ключа и в текущем срезе не используется. Не развивать,
пока не потребуется реестр ассетов — см. [HANDOFF](../base-plans/HANDOFF.md).
