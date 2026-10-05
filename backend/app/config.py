from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    google_fact_check_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GOOGLE_FACT_CHECK_API_KEY"),
    )
    database_url: str = "sqlite:///./fact_check.db"
    secret_key: str

    model_config = SettingsConfigDict(
        # .env na raiz do repositório ou em backend/ (o último tem prioridade)
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        # o .env da raiz pode ter variáveis do frontend (ex.: NEXT_PUBLIC_API_URL)
        extra="ignore",
    )


settings = Settings()
