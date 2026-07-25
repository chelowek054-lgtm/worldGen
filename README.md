# worldGen

Монорепозиторий проекта: **Nuxt 4 (TS)** фронтенд + **FastAPI** бэкенд, оркестрация через **Docker Compose**.

## Структура

```
worldGen/
├── docker-compose.yml          # базовый (prod-like) стек
├── docker-compose.override.yml # оверрайд для локальной разработки (hot-reload)
├── .env.example                # шаблон переменных окружения
├── Makefile                    # короткие команды (make up / down / migrate ...)
├── frontend/                   # SPA/SSR приложение на Nuxt 4 + TypeScript
├── backend/                    # REST API на FastAPI (async, SQLAlchemy, Alembic)
├── docs/                       # документация по ролям (аналитики, разработчики, девопсы, архитекторы, QA, продукт)
├── scripts/                    # вспомогательные скрипты (bootstrap, seed, backup)
└── infra/                      # инфраструктурные конфиги (nginx, postgres init)
```

## Быстрый старт

```bash
cp .env.example .env      # заполнить секреты
make up                   # поднять весь стек в dev-режиме
make migrate              # применить миграции БД
```

После запуска:

| Сервис         | URL                        |
| -------------- | -------------------------- |
| Frontend (Nuxt)| http://localhost:3000      |
| Backend (API)  | http://localhost:8000/docs |
| Через nginx    | http://localhost           |

## Документация

Начните с [docs/README.md](docs/README.md) — навигация по разделам для каждой роли.
