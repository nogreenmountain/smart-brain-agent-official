"""Shared SmartBrain Gateway usage primitives.

The implementation mirrors the CPA-Manager-Plus event semantics: one immutable
event per upstream request, hashed API keys, and cache-aware token totals.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any


def generate_api_key(prefix: str = "sbk") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_api_key(value: str) -> str:
    if len(value) <= 10:
        return value[:3] + "…"
    return value[:8] + "…" + value[-4:]


def effective_input_tokens(
    input_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    semantics: int = 0,
    *,
    app_type: str = "codex",
) -> int:
    """Return billable/fresh input without double counting cached tokens."""
    value = max(int(input_tokens or 0), 0)
    if semantics == 2 or app_type.lower() not in {"codex", "gemini"}:
        return value
    if semantics == 1:
        return max(value - int(cache_read_tokens or 0) - int(cache_creation_tokens or 0), 0)
    return max(value - int(cache_read_tokens or 0), 0)


def total_tokens_from_usage(usage: dict[str, Any], *, app_type: str = "codex") -> int:
    inp = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
    out = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    read = int(usage.get("cache_read_tokens", usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)) or 0)
    create = int(usage.get("cache_creation_tokens", 0) or 0)
    semantics = int(usage.get("input_token_semantics", 0) or 0)
    return effective_input_tokens(inp, read, create, semantics, app_type=app_type) + out + read + create


def normalize_usage(payload: dict[str, Any], *, request_model: str = "", app_type: str = "codex") -> dict[str, int | str]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
    usage = usage or {}
    input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    details = usage.get("prompt_tokens_details") or usage.get("input_token_details") or {}
    cache_read = int(usage.get("cache_read_tokens", details.get("cached_tokens", 0)) or 0)
    cache_creation = int(usage.get("cache_creation_tokens", 0) or 0)
    semantics = int(usage.get("input_token_semantics", 0) or 0)
    return {
        "request_model": request_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_creation_tokens": cache_creation,
        "input_token_semantics": semantics,
        "total_tokens": total_tokens_from_usage(
            {"input_tokens": input_tokens, "output_tokens": output_tokens,
             "cache_read_tokens": cache_read, "cache_creation_tokens": cache_creation,
             "input_token_semantics": semantics},
            app_type=app_type,
        ),
    }


def extract_usage_from_sse(text: str) -> dict[str, Any] | None:
    """Find the final usage object in an OpenAI/Codex SSE response."""
    import json
    found: dict[str, Any] | None = None
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if raw in {"", "[DONE]"}:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("usage"), dict):
            found = obj
        if isinstance(obj, dict) and isinstance(obj.get("response"), dict) and isinstance(obj["response"].get("usage"), dict):
            found = obj["response"]
    return found
