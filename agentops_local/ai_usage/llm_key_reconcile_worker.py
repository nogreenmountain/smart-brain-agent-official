"""Single-shot recovery worker for durable personal gateway operations.

The worker is deliberately a one-shot process. A systemd timer (or an
equivalent supervisor) invokes it periodically, while the PostgreSQL
advisory lock prevents two instances from reconciling the same gateway at
the same time. It never creates a new operation and never retries a native
gateway call outside the state machine's reconciliation methods.
"""

from __future__ import annotations

import argparse
import logging
import os
import uuid
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import text

from agentops.common.orm import session_scope

from .llm_key_runtime import build_service


LOGGER = logging.getLogger(__name__)
DEFAULT_LIMIT = 25
MAX_LIMIT = 100


def _instance_id() -> str:
    try:
        return str(uuid.UUID(os.environ["SB_LLM_GATEWAY_INSTANCE_ID"]))
    except (KeyError, ValueError, TypeError):
        raise RuntimeError("gateway_configuration_unavailable") from None


@contextmanager
def instance_advisory_lock(orm, instance_id: str) -> Iterator[bool]:
    """Hold a PostgreSQL session-level lock for the whole reconciliation.

    The lock is best-effort: a competing timer invocation simply returns no
    work. Unlocking happens on every path, including native gateway failures.
    """

    locked = bool(
        orm.execute(
            text("SELECT pg_try_advisory_lock(hashtext(:instance_id))"),
            {"instance_id": instance_id},
        ).scalar()
    )
    try:
        yield locked
    finally:
        if locked:
            orm.execute(
                text("SELECT pg_advisory_unlock(hashtext(:instance_id))"),
                {"instance_id": instance_id},
            )
        orm.rollback()


def _validate_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def run_once(*, limit: int = DEFAULT_LIMIT):
    """Reconcile one bounded batch and return the state-machine results."""

    limit = _validate_limit(limit)
    instance_id = _instance_id()
    with session_scope() as orm:
        service = build_service(orm)
        try:
            with instance_advisory_lock(orm, instance_id) as acquired:
                if not acquired:
                    LOGGER.info("gateway reconciliation skipped: lock is held")
                    return []
                return service.reconcile_pending(limit=limit)
        finally:
            service.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile pending personal LLM gateway operations")
    parser.add_argument("--once", action="store_true", help="run one bounded reconciliation batch")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args(argv)
    if not args.once:
        parser.error("only --once mode is supported")
    if os.getenv("SB_LLM_GATEWAY_RECONCILER_ENABLED") != "1":
        LOGGER.info("gateway reconciliation disabled")
        return 0
    run_once(limit=args.limit)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    raise SystemExit(main())
