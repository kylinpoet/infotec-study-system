from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DEFAULT_DB_URL = f"sqlite:///{(DATA_DIR / 'infotec.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = "Infotec Study System API"
    api_prefix: str = "/api/v1"
    database_url: str = DEFAULT_DB_URL
    allowed_origins: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_prefix="INFOTEC_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
