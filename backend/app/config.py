from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    google_fact_check_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GOOGLE_FACT_CHECK_API_KEY"),
    )
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY"),
    )
    database_url: str = "sqlite:///./fact_check.db"

    # Configurações do Banco Vetorial
    vector_db_path: str = str(BACKEND_DIR / "data" / "chroma")
    vector_db_collection: str = "fact_checks"
    vector_db_embedding_provider: str = "auto"
    vector_db_model_dir: str = str(BACKEND_DIR / "data" / "models" / "all-MiniLM-L6-v2")
    vector_db_similarity_threshold: float = 0.50
    vector_db_top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
