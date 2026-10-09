"""UUID-only source capture for the next daily report writer.

No report writes, commits or acknowledgements. The existing alias-keyed writer
is not made safe merely by adding this entry point; it must migrate as a unit.
"""
from dataclasses import dataclass
from datetime import date
import uuid
from sqlalchemy import text
try:
    from agentops.ai_usage import daily_delta_sources as sources,delta_revisions as revisions,worklog_queue as queue
except ModuleNotFoundError:
    from agentops_local.ai_usage import daily_delta_sources as sources,delta_revisions as revisions,worklog_queue as queue


@dataclass(frozen=True)
class OwnerDayCapture:
    owner_user_id: str
    work_date: date
    sources: tuple[dict, ...]
    pending_requests: tuple[str, ...]
    pending_revisions: tuple[str, ...]
    cc_inputs: tuple[dict, ...] = ()


def owner_ids_for_day(orm, *, work_date):
    rows=orm.execute(text('''SELECT DISTINCT user_id FROM public.ai_gateway_personal_delta_sources
        WHERE work_date=:work_date ORDER BY user_id'''),{'work_date':work_date}).all()
    from . import cc_daily_inputs as cc_daily
    owners={str(uuid.UUID(str(row.user_id))) for row in rows}
    if cc_daily.cc.enabled():owners.update(cc_daily.owner_ids(orm,work_date))
    return sorted(owners)


def capture_owner_day(orm, *, owner_user_id, work_date):
    owner=str(uuid.UUID(str(owner_user_id)))
    # Capture receipts first. A later arrival may be read but remains pending;
    # an unread request is never acknowledged by a future caller of this result.
    requests=queue.pending_requests(orm,owner_user_id=owner,work_date=work_date)
    jobs=revisions.pending_jobs(orm,consumer='daily_worklog',owner_user_id=owner,work_date=work_date)
    records=sources.read_sources(orm,owner_user_id=owner,work_date=work_date)
    read_ids={row['session_id'] for row in records}
    from . import cc_daily_inputs as cc_daily
    cc_records,cc_inputs=cc_daily.capture_day(orm,owner=owner,day=work_date)
    return OwnerDayCapture(owner,work_date,tuple(records)+cc_records,
        tuple(identity for identity in requests if identity in read_ids),
        tuple(str(job.revision_id) for job in jobs if str(job.request_id) in read_ids),cc_inputs)
