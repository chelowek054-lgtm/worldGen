# worldGen

Движок генерации изображений сцен, в которых персонажи и объекты **остаются
собой** между кадрами, ракурсами и сюжетными репликами.

Пользователь приносит своих героев и свой стиль; система отвечает за
содержание — геометрию, композицию, идентичность. Ценность появляется там, где
мир переиспользуется: те же персонажи в сотне кадров и в разных сюжетных ветках.
Одиночную красивую иллюстрацию дешевле получить обычной диффузией.

## Устройство

```
worldGen/
├── engine/      # движок: сборка сцены, рендер, перерисовка (воркер)
├── backend/     # сервис сцены: граф, реестр ассетов, очередь заданий (FastAPI)
├── frontend/    # редактор сцены (Nuxt 4 + TS)
├── docs/        # документация
├── infra/       # nginx, инициализация Postgres
└── scripts/     # служебные скрипты
```

`engine/` и веб-стек — **раздельные Python-окружения**; зависимости не
объединяются, код друг друга не импортирует. Связь — через API и очередь
заданий.

## С чего начать

| Вопрос | Куда |
| ------ | ---- |
| **Что делается сейчас, как включиться** | [docs/base-plans/HANDOFF.md](docs/base-plans/HANDOFF.md) |
| Как система устроена | [docs/architects/system/architecture.md](docs/architects/system/architecture.md) |
| Что решено, а что открыто | [docs/base-plans/Roadmap.md](docs/base-plans/Roadmap.md) |
| Вся документация | [docs/README.md](docs/README.md) |

## Запуск

Движок (venv в `engine/`, см. [engine/README.md](engine/README.md)):

```bash
cd engine
python -m venv .venv
.venv/Scripts/pip install -e .[dev]     # Windows; Linux/macOS — .venv/bin/pip
.venv/Scripts/python -m pytest tests/ -q
```

Веб-стек (Docker Compose, см. [Makefile](Makefile)):

```bash
cp .env.example .env
make up          # поднять стек (dev, hot-reload)
make migrate     # применить миграции
```

| Сервис | URL |
| ------ | --- |
| Frontend | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| Через nginx | http://localhost |

## Состояние

Проект на стадии первого сквозного среза: проверяется, переживает ли
идентичность персонажа перерисовку генератором. План среза —
[Roadmap-MVP](docs/base-plans/Roadmap-MVP.md), шаги `S0`–`S7`.

Веб-стек существует как каркас; его роль в архитектуре определена, но сервис
сцены и редактор ещё не реализованы.
