from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # БД
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "prices"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"


    REDIS_URL: str = "redis://localhost:6379/0"


    DERIBIT_API_BASE: str = "https://www.deribit.com/api/v2"
    TICKERS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["btc_usd", "eth_usd"]
    )



    APP_NAME: str = "deribit-price-service"
    LOG_LEVEL: str = "INFO"

    @field_validator("TICKERS", mode="before")
    @classmethod
    def parse_tickers(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [str(item).strip().lower() for item in value]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
