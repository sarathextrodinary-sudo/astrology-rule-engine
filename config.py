from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    debug: bool = False
    database_url: str
    secret_key: str

    # Tell Pydantic to read from the local .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    # lru_cache ensures the .env file is read only once instead of on every request
    return Settings()