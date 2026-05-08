"""Application settings.

Environment variables use prefix ``DB_QUERY_``:

- ``DB_QUERY_SQLITE_PATH`` — SQLite file path (optional; default ``w2/db_query/db_query.db``).
- ``DB_QUERY_QUERY_MAX_ROWS`` — default row cap for queries without LIMIT (default ``1000``).
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_sqlite_path() -> Path:
    # backend/src/db_query/config.py -> parents -> w2/db_query/db_query.db
    return Path(__file__).resolve().parent.parent.parent.parent / "db_query.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_QUERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sqlite_path: Path = Field(default_factory=_default_sqlite_path)
    query_max_rows: int = Field(
        default=1000,
        ge=1,
        le=1_000_000,
        description="Default LIMIT when omitted from user SQL",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
