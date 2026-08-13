# Документация для разработчиков

Онбординг, соглашения и практические гайды.

## Быстрый старт

```bash
cp .env.example .env
make up          # поднять стек (dev, hot-reload)
make migrate     # применить миграции
```

- Frontend: http://localhost:3000
- API (Swagger): http://localhost:8000/docs
- Через nginx: http://localhost

Список команд — `make help`.

## Соглашения

- **Backend:** линт/формат — `ruff`; типы — `mypy`; тесты — `pytest`. Слои: `api → services → models`.
- **Frontend:** ESLint (`@nuxt/eslint`), строгий TypeScript, состояние — Pinia (`app/stores`).
- **Ветки/коммиты:** trunk-based, Conventional Commits (`feat:`, `fix:`, `docs:`…).
- **API:** версионируется через префикс `/api/v1`.

## Разделы

- Онбординг нового разработчика.
- Гайды по типовым задачам (добавить эндпоинт, страницу, миграцию).
- Описание доменной модели и структуры кода.
- [Уроки pet-проекта OCR (CRNN)](ocr-pipeline-lessons.md) — практические паттерны
  ML-пайплайна (очистка данных, метрики, MLflow, confidence score), применимые к
  развитию `engine/` в фазах 0.1–0.2.
