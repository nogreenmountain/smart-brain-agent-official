"""Durable per-request worklog acknowledgement, in the report transaction."""
import uuid
try:
    from sqlalchemy import text
except ModuleNotFoundError:
    def text(value): return value


def pending_dates(orm, *, through, limit=31):
    if not isinstance(limit,int) or isinstance(limit,bool) or limit<=0:
        raise ValueError('Pending date limit must be a positive integer')
    rows=orm.execute(text('''SELECT DISTINCT work_date
        FROM public.ai_daily_worklog_pending_requests
        WHERE consumed_at IS NULL AND work_date<=:through
        ORDER BY work_date LIMIT :limit'''),{'through':through,'limit':limit}).all()
    return [row.work_date for row in rows]


def pending_requests(orm, *, employee_id=None, work_date, owner_user_id=None):
    conditions=['work_date=:work_date','consumed_at IS NULL'];params={'work_date':work_date}
    if employee_id is not None:
        conditions.append('employee_id=:employee_id');params['employee_id']=employee_id
    if owner_user_id is not None:
        conditions.append('''EXISTS (SELECT 1 FROM public.ai_gateway_admissions a
            WHERE a.id=p.request_id AND a.user_id=CAST(:owner_user_id AS uuid))''')
        params['owner_user_id']=str(uuid.UUID(str(owner_user_id)))
    elif employee_id is None:
        raise ValueError('worklog pending requests require owner UUID or explicit legacy scope')
    rows=orm.execute(text(f'''SELECT request_id FROM public.ai_daily_worklog_pending_requests p
        WHERE {' AND '.join(conditions)} ORDER BY request_id'''),params).all()
    return [str(row.request_id) for row in rows]


def mark_consumed(orm, requests):
    if not requests:return
    orm.execute(text('''UPDATE public.ai_daily_worklog_pending_requests SET consumed_at=now()
        WHERE consumed_at IS NULL AND request_id=ANY(CAST(:requests AS uuid[]))'''),{'requests':requests})
