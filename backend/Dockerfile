# syntax=docker/dockerfile:1
# --- base ---
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN pip install --upgrade pip
COPY pyproject.toml ./

# --- dev: с dev-зависимостями и hot-reload (команда из override) ---
FROM base AS dev
RUN pip install ".[dev]" || pip install -e ".[dev]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- prod ---
FROM base AS prod
RUN pip install .
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
