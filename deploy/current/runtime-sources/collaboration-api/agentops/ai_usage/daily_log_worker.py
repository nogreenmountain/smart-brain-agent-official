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
) -> int:
    if failure_count > 0:
        return max(retry_seconds, 60)
    scheduled=max(int((next_run_at(now) - now.astimezone(TIMEZONE)).total_seconds()), 1)
    if os.getenv('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED','false').lower()=='true':
        return min(scheduled,max(retry_seconds,60))
    return scheduled


def _pending_dates(orm, *, through):
    from agentops.ai_usage.worklog_queue import pending_dates
    return pending_dates(orm,through=through)


def _refresh_deltas(orm):
    from agentops.ai_usage.delta_revisions import refresh_pending_scopes
    return refresh_pending_scopes(orm)


def _pending_delta_dates(orm, *, through):
    from agentops.ai_usage.delta_revisions import pending_work_dates
    return pending_work_dates(orm,through=through)


def _scheduled_generator(orm):
    from sqlalchemy import text
    from agentops.ai_usage.daily_log_service import generate_daily_worklogs
    owned=orm.execute(text("""SELECT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='ai_daily_work_logs' AND column_name='owner_user_id')""")).scalar_one()
    if not owned:
        return generate_daily_worklogs
    # A migrated database must never call the incompatible alias writer, even
    # when an operator disables consumption during rollback or maintenance.
    flags=('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED','AI_WORKLOG_INCREMENTAL_ENABLED','AI_WORKLOG_PERSONAL_DELTAS_ENABLED')
    if not all(os.getenv(flag,'false').lower()=='true' for flag in flags):
        raise RuntimeError('UUID worklog storage requires all consumer flags; writing suspended')
    ready=orm.execute(text("""SELECT EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='ai_gateway_personal_delta_sources' AND column_name='project_id')""")).scalar_one()
    if not ready:
        raise RuntimeError('UUID periodic writer requires the project source migration; writing suspended')
    from agentops.ai_usage.daily_owner_writer import generate_owner_reports
    return generate_owner_reports


def generate_scheduled_day(orm, *, work_date):
    return _scheduled_generator(orm)(orm,work_date=work_date)


def run_due_worklogs(orm, *, now: datetime, generate=None):
    if generate is None:
        generate=_scheduled_generator(orm)
    due=latest_due_date(now)
    dates={due}
    if os.getenv('SB_CC_INPUT_REVISIONS_ENABLED','false').lower()=='true':
        from agentops.ai_usage.cc_daily_inputs import pending_dates
        dates.update(pending_dates(orm,due))
    if os.getenv('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED','false').lower()=='true':
        if os.getenv('AI_WORKLOG_PERSONAL_DELTAS_ENABLED','false').lower()=='true':
            result=_refresh_deltas(orm)
            if result['failed_scopes']:
                raise RuntimeError('Personal delta scopes failed; receipts preserved for retry')
            dates.update(_pending_delta_dates(orm,through=due))
        dates.update(_pending_dates(orm,through=due))
    return [(work_date,generate(orm,work_date=work_date)) for work_date in sorted(dates)]


def main() -> None:
    from agentops.common.orm import get_orm_session

    logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"))
    retry_seconds = int(os.getenv("AI_WORKLOG_RETRY_SECONDS", "900"))
    due_date = latest_due_date(datetime.now(TIMEZONE))
    while True:
        session_generator = get_orm_session()
        orm = next(session_generator)
        failure_count=1
        try:
            personal=os.getenv('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED','false').lower()=='true'
            results=(run_due_worklogs(orm,now=datetime.now(TIMEZONE)) if personal
                     else [(due_date,generate_scheduled_day(orm,work_date=due_date))])
            failure_count=sum(result.failure_count for _,result in results)
            for work_date,result in results:
                logger.info(
                    "AI daily worklog run: date=%s employees=%s ready=%s empty=%s skipped=%s failed=%s",
                    work_date,result.employee_count,result.ready_count,result.empty_count,result.skipped_count,result.failure_count)
        except Exception:
            orm.rollback()
            logger.exception('AI daily worklog cycle failed; pending requests remain retryable')
        finally:
            session_generator.close()

        now = datetime.now(TIMEZONE)
        delay = sleep_seconds_after_run(
            now,
            failure_count=failure_count,
            retry_seconds=retry_seconds,
        )
        time.sleep(delay)
        if failure_count == 0:
            due_date = next_run_at(now).date()


if __name__ == "__main__":
    main()
