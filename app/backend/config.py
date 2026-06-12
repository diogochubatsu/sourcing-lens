"""
ArbitLens Backend Configuration
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / "config" / ".env"


class Settings(BaseSettings):
    database_url: str = ""

    class Config:
        extra = "ignore"
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
