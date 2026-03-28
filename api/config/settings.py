from pathlib import Path
from pydantic_settings import BaseSettings


def _read_secret(name: str) -> str:
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    raise RuntimeError(f"Secret '{name}' not found at {path}")


def _read_secret_optional(name: str, default: str = "") -> str:
    path = Path(f"/run/secrets/{name}")
    return path.read_text().strip() if path.exists() else default


class Settings(BaseSettings):
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "ispider"
    postgres_user: str = "ispider"

    redis_host: str = "redis"
    redis_port: int = 6379

    anthropic_model_batch: str = "claude-haiku-4-5-20251001"
    anthropic_model_query: str = "claude-sonnet-4-6"

    push_score_threshold: int = 70
    push_rate_limit_per_hour: int = 5
    vapid_subject: str = "mailto:admin@localhost"

    fetch_interval_minutes: int = 15

    @property
    def postgres_password(self) -> str:
        return _read_secret("postgres_password")

    @property
    def anthropic_api_key(self) -> str:
        return _read_secret("anthropic_api_key")

    @property
    def vapid_private_key(self) -> str:
        return _read_secret_optional("vapid_private_key")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_prefix = "ISPIDER_"


settings = Settings()
