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
    backend_kind: str | None = Field(
        default=None,
        description=(
            "Logical backend id: postgres | mysql | … Omit to infer from URL scheme "
            "(e.g. postgres://, mysql://)."
        ),
    )


class RegisteredDatabaseListItem(CamelModel):
    """One row from ``GET /api/v1/dbs``."""

    name: str
    backend_kind: str | None = Field(
        default=None,
        description="Registered SQL backend driver id (postgres, mysql, …).",
    )
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


class NaturalQueryRequest(CamelModel):
    prompt: str
    llm_settings_id: int | None = Field(
        default=None,
        description="Use this LLM profile; omit to use the default profile",
    )


class NaturalQueryResponse(CamelModel):
    sql: str
    warnings: list[str] = Field(default_factory=list)


# Re-export query contract models (canonical definitions in ``schemas/query.py``).
from db_query.schemas.query import QueryRequest, QueryResult  # noqa: E402

__all__ = [
    "CamelModel",
    "PutDatabaseBody",
    "RegisteredDatabaseListItem",
    "PutDatabaseResponse",
    "DatabaseMetadataResponse",
    "NaturalQueryRequest",
    "NaturalQueryResponse",
    "QueryRequest",
    "QueryResult",
]
