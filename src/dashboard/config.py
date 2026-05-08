from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/dashboard.db"
    jwt_secret: str = "change-me"
    pipeline_api_key: str = "change-me"
    dev_token: str = "local-dev-only"
    daily_goal_threshold: int = 20
    timezone: str = "Europe/Berlin"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
