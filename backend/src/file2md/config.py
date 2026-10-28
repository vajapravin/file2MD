"""Application configuration managed via pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for file2MD backend service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    APP_NAME: str = "file2md"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_LOG_LEVEL: str = "INFO"

    # --- Server ---
    HOST: str = "0.0.0.0"  # noqa: S104 - default server listen host
    PORT: int = 8086

    # --- Upload & Processing Limits ---
    MAX_UPLOAD_SIZE_MB: int = 60
    CONVERSION_TIMEOUT_SECONDS: int = 120

    # --- Redis & Background Jobs ---
    REDIS_URL: str = "redis://redis:6379/0"
    JOB_TTL_SECONDS: int = 3600  # 1 hour expiration for completed results

    # --- Chunking & Parallelization ---
    CHUNK_SPLIT_THRESHOLD_BYTES: int = 5 * 1024 * 1024  # 5 MB threshold
    CHUNK_PARALLEL_WORKERS: int = 4
    PDF_CHUNK_PAGE_SIZE: int = 15  # pages per chunk
    CSV_CHUNK_ROW_SIZE: int = 1000  # rows per chunk
    TXT_CHUNK_LINE_SIZE: int = 2000  # lines per chunk

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "https://file2md.vajapravin.me",
        "http://file2md.vajapravin.me",
    ]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
