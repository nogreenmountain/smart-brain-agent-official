from __future__ import annotations

import os
import logging
import time
from datetime import date, datetime, time as clock_time, timedelta, timezone


TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
logger = logging.getLogger(__name__)


def _schedule_time() -> clock_time:
    hour = min(max(int(os.getenv("AI_WORKLOG_RUN_HOUR", "20")), 0), 23)
    minute = min(max(int(os.getenv("AI_WORKLOG_RUN_MINUTE", "0")), 0), 59)
    return clock_time(hour=hour, minute=minute)


def latest_due_date(now: datetime) -> date:
    local_now = now.astimezone(TIMEZONE)
    if local_now.time() >= _schedule_time():
        return local_now.date()
    return local_now.date() - timedelta(days=1)


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
    catching_up: bool = False,
) -> int:
    if failure_count > 0:
        return max(retry_seconds, 60)
    if catching_up:
        return 1
    return max(int((next_run_at(now) - now.astimezone(TIMEZONE)).total_seconds()), 1)


def _oldest_pending_date(orm, *, through: date) -> date | None:
    """Find the oldest session day that has not produced a terminal worklog."""
    from sqlalchemy import text

    row = orm.execute(
        text("""
            SELECT min((s.started_at AT TIME ZONE 'Asia/Shanghai')::date) AS work_date
            FROM public.ai_chat_sessions s
            WHERE s.started_at < (:through + INTERVAL '1 day')
              AND EXISTS (
                  SELECT 1 FROM public.ai_chat_messages m WHERE m.session_id = s.id
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM public.ai_daily_work_logs l
                  WHERE l.employee_id = s.employee_id
                    AND l.work_date = (s.started_at AT TIME ZONE 'Asia/Shanghai')::date
                    AND l.status IN ('ready', 'empty')
              )
        """),
        {"through": through},
    ).first()
    return getattr(row, "work_date", None) if row else None


def main() -> None:
    from agentops.ai_usage.daily_log_service import generate_daily_worklogs
    from agentops.common.orm import get_orm_session

    logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"))
    retry_seconds = int(os.getenv("AI_WORKLOG_RETRY_SECONDS", "900"))
    due_date: date | None = None
    while True:
        session_generator = get_orm_session()
        orm = next(session_generator)
        try:
            latest = latest_due_date(datetime.now(TIMEZONE))
            if due_date is None:
                pending = _oldest_pending_date(orm, through=latest) or latest
                floor_raw = os.getenv("AI_WORKLOG_BACKFILL_START_DATE", "").strip()
                floor = date.fromisoformat(floor_raw) if floor_raw else None
                due_date = max(pending, floor) if floor else pending
            result = generate_daily_worklogs(orm, work_date=due_date)
            logger.info(
                "AI daily worklog run: date=%s employees=%s ready=%s empty=%s skipped=%s failed=%s",
                due_date,
                result.employee_count,
                result.ready_count,
                result.empty_count,
                result.skipped_count,
                result.failure_count,
            )
        finally:
            session_generator.close()

        now = datetime.now(TIMEZONE)
        target = latest_due_date(now)
        catching_up = result.failure_count == 0 and due_date < target
        delay = sleep_seconds_after_run(
            now,
            failure_count=result.failure_count,
            retry_seconds=retry_seconds,
            catching_up=catching_up,
        )
        time.sleep(delay)
        if result.failure_count == 0:
            if catching_up:
                due_date = due_date + timedelta(days=1)
            else:
                due_date = None


if __name__ == "__main__":
    main()