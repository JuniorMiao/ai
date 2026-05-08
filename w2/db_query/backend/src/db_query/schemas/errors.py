"""Unified JSON error body for API responses (camelCase keys per constitution).

Contract shape::

    { "error": { "code": string, "message": string } }
"""

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
