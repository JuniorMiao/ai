"""Request/response models for database APIs (camelCase JSON)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PutDatabaseBody(CamelModel):
    url: str


class RegisteredDatabaseListItem(CamelModel):
    """One row from ``GET /api/v1/dbs``."""

    name: str
    created_at: str | None = None
    updated_at: str | None = None


class PutDatabaseResponse(CamelModel):
    name: str
    created_at: str


class DatabaseMetadataResponse(CamelModel):
    """Use ``schema_snapshot`` to avoid clashing with ``BaseModel.metadata``."""

    name: str
    schema_snapshot: dict[str, Any] = Field(serialization_alias="metadata")
    fetched_at: str


class QueryRequest(CamelModel):
    sql: str


class QueryResult(CamelModel):
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool
    max_rows: int


class NaturalQueryRequest(CamelModel):
    prompt: str


class NaturalQueryResponse(CamelModel):
    sql: str
    warnings: list[str] = Field(default_factory=list)
