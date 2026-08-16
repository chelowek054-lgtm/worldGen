# Backend — FastAPI

Асинхронный REST API. Python 3.12, SQLAlchemy 2.0 (async), Alembic, Redis.

**Роль в архитектуре** — сервис сцены: хранит граф сцены и реестр ассетов
(Postgres), держит очередь заданий на рендер (Redis), отдаёт превью и принимает
правки. Задания исполняет `engine/`. Подробнее —
[architecture, раздел 4](../docs/architects/system/architecture.md#4-стек).

> Пока это каркас из шаблона: роль определена, сервис сцены не реализован.
> Окружение отдельное от `engine/` — зависимости не объединять, код друг друга
> не импортировать.

## Структура

```
backend/
├── pyproject.toml           # зависимости и конфиг инструментов (ruff, pytest)
├── alembic.ini              # конфиг миграций
├── alembic/                 # окружение и версии миграций
├── app/
│   ├── main.py              # точка входа, сборка FastAPI
│   ├── core/                # config, безопасность, общие настройки
│   ├── api/v1/              # версионированные роутеры и эндпоинты
│   ├── models/              # ORM-модели (SQLAlchemy)
│   ├── schemas/             # Pydantic-схемы (DTO)
│   ├── services/            # бизнес-логика
│   ├── db/                  # engine, сессии
│   └── utils/               # вспомогательные функции
└── tests/                   # pytest
```

## Разработка

Внутри Docker — автоматически (`make up`), доступно на http://localhost:8000/docs.

Миграции:

```bash
make makemigration m="create users"   # сгенерировать
make migrate                           # применить
```

Локально без Docker:

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
