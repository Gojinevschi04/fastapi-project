import logging
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: str | int = Field(default=logging.INFO)
    STORAGE_PATH: str = "storage"

    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASS: str = ""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        extra="ignore",
        populate_by_name=True,
    )

    @computed_field
    def DB_URL(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    def STORAGE_DIR(self) -> Path:  # noqa: N802
        return Path(__file__).parent.parent.parent / self.STORAGE_PATH


settings = Settings()
