"""Pydantic models for ``POST /api/v1/dbs/{name}/query`` (camelCase JSON)."""

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class QueryRequest(CamelModel):
    sql: str


class QueryResult(CamelModel):
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool
    max_rows: int
