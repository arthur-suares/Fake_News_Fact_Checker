from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    google_fact_check_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GOOGLE_FACT_CHECK_API_KEY"),
    )
    database_url: str = "sqlite:///./fact_check.db"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
