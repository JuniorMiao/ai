"""Map OpenAI-compatible SDK errors to HTTP status and short user-facing messages."""

from __future__ import annotations


def _openai_error_payload(exc: BaseException) -> str:
    """Best-effort extract of OpenAI `error.message` and type for heuristics."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            parts: list[str] = []
            for k in ("type", "code", "message"):
                v = err.get(k)
                if v is not None:
                    parts.append(str(v))
            if parts:
                return " ".join(parts)
    return str(exc).lower()


def map_llm_upstream_error(exc: BaseException) -> tuple[int, str]:
    """
    Return ``(http_status, detail)`` for JSON ``error.message``.

    - 401: bad API key
    - 429: rate limit or **insufficient quota** (OpenAI often uses 429 for both)
    - 502: other upstream / unknown
    """
    try:
        from openai import APIStatusError, AuthenticationError, RateLimitError
    except ImportError:  # pragma: no cover
        return 502, f"自然语言生成失败: {exc}"

    if isinstance(exc, AuthenticationError):
        return (
            401,
            "LLM API 密钥无效或已失效，请在「LLM 设置」中更新 API Key 或环境变量。",
        )

    if isinstance(exc, RateLimitError):
        return _message_for_429(exc)

    if isinstance(exc, APIStatusError):
        sc = int(getattr(exc, "status_code", 0) or 0)
        if sc == 429:
            return _message_for_429(exc)
        if sc == 401:
            return (
                401,
                "LLM API 密钥未授权，请检查「LLM 设置」中的密钥或 Base URL。",
            )
        if sc == 400:
            snippet = _snippet(exc)
            return 502, f"LLM 请求被拒绝（400）: {snippet}"
        snippet = _snippet(exc)
        return 502, f"LLM 服务返回错误（HTTP {sc}）: {snippet}"

    return 502, f"自然语言生成失败: {exc}"


def _snippet(exc: BaseException, limit: int = 320) -> str:
    s = str(exc)
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _message_for_429(exc: BaseException) -> tuple[int, str]:
    payload = _openai_error_payload(exc)
    if "insufficient_quota" in payload:
        return (
            429,
            "OpenAI 账户额度已用尽（insufficient_quota）。请在计费页面充值或更换可用的 API Key："
            " https://platform.openai.com/account/billing",
        )
    return (
        429,
        "LLM 接口返回 429（请求过于频繁或触发限制）。请稍后重试；若持续出现请检查套餐与用量。",
    )
