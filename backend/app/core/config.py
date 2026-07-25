from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из переменных окружения / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    # Безопасность
    secret_key: str = "change_me"
    access_token_expire_minutes: int = 60

    # База данных / кэш
    database_url: str = "postgresql+asyncpg://atelier:atelier@db:5432/atelier"
    redis_url: str = "redis://redis:6379/0"

    # CORS: список origin через запятую в переменной BACKEND_CORS_ORIGINS
    backend_cors_origins: str = Field(default="http://localhost:3000")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
