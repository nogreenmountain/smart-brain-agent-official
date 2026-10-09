from __future__ import annotations

import logging
import os
import time
from datetime import datetime, time as clock_time, timedelta, timezone


TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
logger = logging.getLogger(__name__)


def _schedule_time() -> clock_time:
    hour = min(max(int(os.getenv("MEMBER_WIKI_RUN_HOUR", "21")), 0), 23)
    minute = min(max(int(os.getenv("MEMBER_WIKI_RUN_MINUTE", "0")), 0), 59)
    return clock_time(hour=hour, minute=minute)


def next_run_at(now: datetime) -> datetime:
    local_now = now.astimezone(TIMEZONE)
    scheduled = datetime.combine(local_now.date(), _schedule_time(), tzinfo=TIMEZONE)
    if local_now >= scheduled:
        scheduled += timedelta(days=1)
    return scheduled


def sleep_seconds_after_run(
    now: datetime,
    *,
    failure_count: int,
    retry_seconds: int,
) -> int:
    if failure_count > 0:
        return max(int(retry_seconds), 60)
    return max(int((next_run_at(now) - now.astimezone(TIMEZONE)).total_seconds()), 1)


def main() -> None:
    from agentops.common.orm import get_orm_session
    from agentops.member_wiki.service import update_member_wikis

    logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"))
    retry_seconds = int(os.getenv("MEMBER_WIKI_RETRY_SECONDS", "900"))
    now = datetime.now(TIMEZONE)
    delay = max(int((next_run_at(now) - now).total_seconds()), 1)
    while True:
        time.sleep(delay)

        session_generator = get_orm_session()
        orm = next(session_generator)
        failure_count = 1
        try:
            result = update_member_wikis(orm, cutoff=datetime.now(timezone.utc))
            failure_count = result.failure_count
            logger.info(
                "member Wiki run: members=%s updated=%s empty=%s sessions=%s experiences=%s failed=%s",
                result.candidate_member_count,
                result.updated_member_count,
                result.empty_member_count,
                result.session_count,
                result.experience_count,
                result.failure_count,
            )
        except Exception:
            orm.rollback()
            logger.error("member Wiki scheduled run failed; pending retained")
        finally:
            session_generator.close()

        delay = sleep_seconds_after_run(datetime.now(TIMEZONE),
            failure_count=failure_count,retry_seconds=retry_seconds)


if __name__ == "__main__":
    main()
