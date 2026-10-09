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
    return int(normalize_usage(usage, app_type=app_type)['total_tokens'])


def normalize_usage(payload: dict[str, Any], *, request_model: str = "", app_type: str = "codex") -> dict[str, int | str | bool]:
    usage = payload.get('usage', payload) if isinstance(payload, dict) else payload
    invalid = usage is not None and not isinstance(usage, dict)
    usage = usage if isinstance(usage, dict) else {}

    def count(value):
        nonlocal invalid
        # Match JavaScript's exact integer range; booleans are not token counts.
        if type(value) not in (int, float) or not 0 <= value <= 9007199254740991 or int(value) != value:
            invalid = True
            return 0
        return int(value)

    def pick(source, names, fallback=0):
        present = [name for name in names if name in source]
        for name in present:
            count(source[name])
        return count(source[present[0]]) if present else fallback

    def details(names):
        nonlocal invalid
        for name in names:
            if usage.get(name) is not None and not isinstance(usage[name], dict):
                invalid = True
        return next((usage[name] for name in names if isinstance(usage.get(name), dict)), {})

    input_details = details(['prompt_tokens_details', 'input_tokens_details', 'input_token_details'])
    output_details = details(['output_tokens_details', 'completion_tokens_details'])
    input_tokens = pick(usage, ['input_tokens', 'prompt_tokens'])
    output_tokens = pick(usage, ['output_tokens', 'completion_tokens'])
    cache_read = pick(usage, ['cached_input_tokens', 'cache_read_input_tokens', 'cache_read_tokens'], pick(input_details, ['cached_tokens']))
    cache_creation = pick(usage, ['cache_write_tokens', 'cache_creation_input_tokens', 'cache_creation_tokens'])
    reasoning = pick(usage, ['reasoning_tokens'], pick(output_details, ['reasoning_tokens']))
    native_anthropic = 'cache_read_input_tokens' in usage or 'cache_creation_input_tokens' in usage
    semantics = pick(usage, ['input_token_semantics', 'token_semantics_version'], 2 if native_anthropic or app_type == 'claude' else 0)
    if semantics not in (0, 1, 2):
        invalid = True
    if ((semantics != 2 and cache_read > input_tokens) or
            (semantics == 1 and cache_read + cache_creation > input_tokens) or reasoning > output_tokens):
        invalid = True
    total = count(input_tokens + output_tokens + (cache_read + cache_creation if semantics == 2 else cache_creation if semantics == 0 else 0))
    if 'total_tokens' in usage and count(usage['total_tokens']) != total:
        invalid = True
    missing = invalid or not any(name in usage for name in ('input_tokens', 'prompt_tokens')) or not any(name in usage for name in ('output_tokens', 'completion_tokens'))
    return {
        "request_model": request_model,
        "input_tokens": 0 if invalid else input_tokens,
        "output_tokens": 0 if invalid else output_tokens,
        "cache_read_tokens": 0 if invalid else cache_read,
        "cache_creation_tokens": 0 if invalid else cache_creation,
        "input_token_semantics": 0 if invalid else semantics,
        "reasoning_tokens": 0 if invalid else reasoning,
        "total_tokens": 0 if invalid else total,
        "usage_missing": missing,
        "usage_invalid": invalid,
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
