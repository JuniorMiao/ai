"""LLM upstream error mapping."""

import httpx
from openai import APIStatusError

from db_query.services.llm_errors import map_llm_upstream_error


def test_insufficient_quota_maps_to_429_chinese() -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    body = {
        "error": {
            "message": "You exceeded your current quota",
            "type": "insufficient_quota",
            "param": None,
            "code": "insufficient_quota",
        }
    }
    exc = APIStatusError("insufficient_quota", response=resp, body=body)
    status, detail = map_llm_upstream_error(exc)
    assert status == 429
    assert "insufficient_quota" in detail
    assert "billing" in detail
