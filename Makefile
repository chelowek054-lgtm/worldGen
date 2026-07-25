# Makefile — короткие команды для повседневной работы.
.PHONY: help up down build logs ps migrate makemigration test-back test-front lint fmt shell-back

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Поднять весь стек (dev)
	docker compose up -d

down: ## Остановить и удалить контейнеры
	docker compose down

build: ## Пересобрать образы
	docker compose build

logs: ## Логи всех сервисов
	docker compose logs -f

ps: ## Статус сервисов
	docker compose ps

migrate: ## Применить миграции БД
	docker compose exec backend alembic upgrade head

makemigration: ## Создать миграцию: make makemigration m="описание"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

test-back: ## Тесты backend
	docker compose exec backend pytest

test-front: ## Тесты frontend
	docker compose exec frontend npm run test

lint: ## Линт backend + frontend
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint

shell-back: ## Shell внутри backend-контейнера
	docker compose exec backend bash
