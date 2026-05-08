"""Unified JSON error body (camelCase fields)."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ErrorDetail(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    error: ErrorDetail
