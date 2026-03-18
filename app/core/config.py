from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_name: str = "Sector Relay"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    secret_key: str = Field(default="change-me-super-secret-32-bytes-minimum", min_length=32)
    access_token_expire_minutes: int = 20
    refresh_token_expire_days: int = 14
    database_url: str = "sqlite:///./sector_relay.db"
    sqlite_fallback_path: str = "./sector_relay.db"
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    world_tick_seconds: int = 1
    offline_progress_cap_hours: int = 8
    dev_seed_enabled: bool = True
    enable_dev_endpoints: bool = True
    redis_url: str | None = None
    bootstrap_admin_email: str | None = None
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None
    media_root: str = "./media"
    chat_upload_dir: str = "./media/chat"
    chat_upload_max_bytes: int = 4 * 1024 * 1024

    @property
    def normalized_database_url(self) -> str:
        if self.database_url.startswith(("postgresql", "sqlite")):
            return self.database_url
        fallback = Path(self.sqlite_fallback_path).resolve()
        return f"sqlite:///{fallback.as_posix()}"

    @property
    def is_dev(self) -> bool:
        return self.app_env != "production"

    @property
    def media_root_path(self) -> Path:
        return Path(self.media_root).resolve()

    @property
    def chat_upload_path(self) -> Path:
        return Path(self.chat_upload_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
