from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[1]


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH / ".env")

    DB_URL: str
    JWT_SECRET: str = Field(min_length=32)
    JWT_EXPIRE_MINUTES: int = 30
    IA_LINK_CACHE_TTL_DAYS: int = 30


@lru_cache
def get_config() -> Config:
    return Config()  # type: ignore
