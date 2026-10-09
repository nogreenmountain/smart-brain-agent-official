"""Small PostgreSQL-backed worker for multimodal parse jobs."""
from __future__ import annotations

import logging
import os
import time
import uuid

try:
    from agentops.common.orm import get_orm_session
    from agentops.project_memory.async_parser import (
        claim_next_parse_job,
        process_parse_job,
        reap_timed_out_parse_jobs,
    )
except ModuleNotFoundError:  # source-tree tests
    from agentops_local.common.orm import get_orm_session
    from agentops_local.project_memory.async_parser import (
        claim_next_parse_job,
        process_parse_job,
        reap_timed_out_parse_jobs,
    )

logger = logging.getLogger(__name__)


def run_once(orm, *, worker_id: str | None = None) -> str | None:
    worker = worker_id or f"parser-{uuid.uuid4()}"
    reap_timed_out_parse_jobs(orm)
    job_id = claim_next_parse_job(
        orm,
        worker_id=worker,
        lease_seconds=max(int(os.getenv("PROJECT_MATERIAL_PARSE_LEASE_SECONDS", "900")), 1),
        max_concurrency=max(int(os.getenv("PROJECT_MATERIAL_PARSE_MAX_CONCURRENCY", "2")), 1),
    )
    if job_id is None:
        return None
    return process_parse_job(orm, job_id, worker_id=worker)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"))
    while True:
        generator = get_orm_session()
        orm = next(generator)
        try:
            result = run_once(orm)
        except Exception:
            logger.exception("material parse worker iteration failed")
            result = None
        finally:
            try:
                next(generator)
            except StopIteration:
                pass
        if result is None:
            time.sleep(float(os.getenv("PROJECT_MATERIAL_PARSE_POLL_SECONDS", "1")))


if __name__ == "__main__":
    main()
