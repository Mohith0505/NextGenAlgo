from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "db" / "dev.db"


def _default_database_url() -> str:
    sqlite_path = DEFAULT_SQLITE_PATH
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+pysqlite:///{sqlite_path.as_posix()}"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    api_v1_prefix: str = "/api"
    app_name: str = "Next-Gen Algo Terminal API"
    environment: str = "local"
    secret_key: str = "change-me"
    access_token_expires_minutes: int = 30
    refresh_token_expires_minutes: int = 60 * 24 * 7
    database_url: str = Field(default_factory=_default_database_url)
    sqlalchemy_echo: bool = False
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
