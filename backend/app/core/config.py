"""Application settings, loaded from environment variables / .env.

Nothing here is hard-coded at a call site: every tunable (model names, top_k,
the score floor, CORS origins) is a setting so the demo can be retuned without
touching code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "RAG Document Assistant API"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    # Vector store
    vector_store_dir: str = str(BACKEND_ROOT / "data" / "vector_store")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Retrieval
    top_k: int = 4
    min_score: float = 0.25

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 120
    temperature: float = 0.1  # low: we want faithful extraction, not creativity

    # CORS - comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
