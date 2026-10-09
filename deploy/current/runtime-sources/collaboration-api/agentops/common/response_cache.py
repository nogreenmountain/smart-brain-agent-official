from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from agentops.common import cache


ModelT = TypeVar("ModelT", bound=BaseModel)
VERSION_TTL_SECONDS = 365 * 24 * 60 * 60


def _version_key(scope: str) -> str:
    return f"response-cache-version:{scope}"


def _version(scope: str) -> int:
    key = _version_key(scope)
    current = cache.get(key)
    if current is None:
        if cache.set_if_absent(key, VERSION_TTL_SECONDS, "1"):
            return 1
        # Another worker initialized or invalidated the scope after our miss.
        # Read its value instead of overwriting a newer version with 1.
        current = cache.get(key)
        if current is None:
            current = str(cache.incr(key))
            cache.expire(key, VERSION_TTL_SECONDS)
    return int(current)


def _response_key(
    scope: str,
    dimensions: dict[str, Any],
    *,
    version: int | None = None,
) -> str:
    normalized = json.dumps(dimensions, sort_keys=True, default=str, ensure_ascii=False)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    selected_version = _version(scope) if version is None else version
    return f"response-cache:{scope}:v{selected_version}:{digest}"


def _decode_model(payload: str | None, model_type: type[ModelT]) -> ModelT | None:
    if payload is None:
        return None
    try:
        return model_type.model_validate_json(payload)
    except Exception:
        return None


def _get_model_at_version(
    scope: str,
    model_type: type[ModelT],
    version: int,
    dimensions: dict[str, Any],
) -> ModelT | None:
    payload = cache.get(_response_key(scope, dimensions, version=version))
    return _decode_model(payload, model_type)


def get_model_with_version(
    scope: str,
    model_type: type[ModelT],
    **dimensions: Any,
) -> tuple[ModelT | None, int]:
    version = _version(scope)
    payload = cache.get(_response_key(scope, dimensions, version=version))
    return _decode_model(payload, model_type), version


def get_model(
    scope: str,
    model_type: type[ModelT],
    **dimensions: Any,
) -> ModelT | None:
    value, _ = get_model_with_version(scope, model_type, **dimensions)
    return value


def set_model(
    scope: str,
    value: BaseModel,
    ttl_seconds: int,
    *,
    version: int | None = None,
    **dimensions: Any,
) -> None:
    cache.setex(
        _response_key(scope, dimensions, version=version),
        ttl_seconds,
        value.model_dump_json(),
    )


def get_or_build_model(
    scope: str,
    model_type: type[ModelT],
    builder: Callable[[], ModelT],
    *,
    ttl_seconds: int,
    lock_ttl_seconds: int = 30,
    wait_seconds: float = 5.0,
    poll_seconds: float = 0.05,
    **dimensions: Any,
) -> ModelT:
    """Return a cached response and serialize expensive cross-worker fills."""
    deadline = time.monotonic() + max(wait_seconds, 0.0)
    while True:
        cached, version = get_model_with_version(scope, model_type, **dimensions)
        if cached is not None:
            return cached

        response_key = _response_key(scope, dimensions, version=version)
        lock_key = f"{response_key}:fill-lock"
        owner = uuid.uuid4().hex
        if cache.set_if_absent(lock_key, lock_ttl_seconds, owner):
            try:
                cached = _get_model_at_version(scope, model_type, version, dimensions)
                if cached is not None:
                    return cached
                result = builder()
                set_model(
                    scope,
                    result,
                    ttl_seconds,
                    version=version,
                    **dimensions,
                )
                return result
            finally:
                cache.delete_if_value(lock_key, owner)

        if time.monotonic() >= deadline:
            # Keep the request available even if the lock holder died or an
            # aggregation legitimately takes longer than the bounded wait.
            # Do not publish this fallback result into the shared cache.
            return builder()
        time.sleep(max(poll_seconds, 0.01))


def bump(scope: str) -> int:
    version = cache.incr(_version_key(scope))
    cache.expire(_version_key(scope), VERSION_TTL_SECONDS)
    return version
