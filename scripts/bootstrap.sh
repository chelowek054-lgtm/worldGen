#!/usr/bin/env bash
# Первичная настройка окружения: .env + сборка + запуск + миграции.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env из .env.example — проверьте секреты перед продакшеном."
fi

docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head

echo "Готово. Frontend: http://localhost:3000 | API: http://localhost:8000/docs"
