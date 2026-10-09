"""Exact CC owner/day inputs, affected dates and atomic daily acknowledgements."""
import hashlib
import json
from sqlalchemy import text
try:
    from agentops.ai_usage import cc_input_revisions as cc
except ModuleNotFoundError:
    from agentops_local.ai_usage import cc_input_revisions as cc


def installed(orm):
    return orm.execute(text("SELECT to_regclass('public.cc_daily_revision_days') IS NOT NULL")).scalar_one()


def record_days(orm, *, revision_id, previous_id):
    orm.execute(text('''INSERT INTO public.cc_daily_revision_days(revision_id,owner_user_id,work_date)
      SELECT r.id,r.owner_user_id,days.work_date FROM public.cc_input_revisions r
      CROSS JOIN LATERAL (
        SELECT ((r.snapshot->'session'->>'started_at')::timestamptz AT TIME ZONE 'Asia/Shanghai')::date AS work_date
        UNION SELECT d.work_date FROM public.cc_daily_revision_days d
          WHERE d.revision_id=CAST(:previous AS uuid) AND d.owner_user_id=r.owner_user_id) days
      WHERE r.id=CAST(:revision AS uuid)'''),dict(revision=str(revision_id),previous=str(previous_id) if previous_id else None))


HEAD_DAYS='''public.cc_daily_revision_days d JOIN public.cc_input_heads h ON h.revision_id=d.revision_id
    JOIN public.cc_input_revisions r ON r.id=h.revision_id AND r.owner_user_id=d.owner_user_id'''


def owner_ids(orm,work_date):
    return [str(v) for v in orm.execute(text(f'SELECT DISTINCT d.owner_user_id FROM {HEAD_DAYS} WHERE d.work_date=:day'),{'day':work_date}).scalars()]


def pending_dates(orm,through):
    if not cc.enabled():return []
    return list(orm.execute(text(f'''SELECT DISTINCT d.work_date FROM {HEAD_DAYS}
      WHERE d.work_date<=:day AND (
        NOT EXISTS(SELECT 1 FROM public.cc_daily_input_receipts a
          WHERE a.revision_id=d.revision_id AND a.owner_user_id=d.owner_user_id AND a.work_date=d.work_date)
        OR NOT EXISTS(SELECT 1 FROM public.cc_daily_report_sources applied
          WHERE applied.revision_id=d.revision_id AND applied.owner_user_id=d.owner_user_id AND applied.work_date=d.work_date
            AND applied.included=(r.content_complete AND NOT r.previously_seen_payload
              AND ((r.snapshot->'session'->>'started_at')::timestamptz AT TIME ZONE 'Asia/Shanghai')::date=d.work_date
              AND EXISTS(SELECT 1 FROM public.project_members pm
                WHERE pm.project_id=r.project_id AND pm.user_id=r.owner_user_id))))
      ORDER BY d.work_date LIMIT 366'''),{'day':through}).scalars())


def capture_day(orm, *, owner, day):
    if not cc.enabled():
        if installed(orm) and orm.execute(text('''SELECT EXISTS(SELECT 1 FROM public.cc_daily_report_sources
          WHERE owner_user_id=CAST(:owner AS uuid) AND work_date=:day)'''),dict(owner=str(owner),day=day)).scalar_one():
            raise ValueError('CC report consumption disabled; existing report preserved')
        return (),()
    rows=orm.execute(text(f'''WITH selected AS MATERIALIZED (
      SELECT r.id,r.session_id,r.project_id,r.snapshot,r.snapshot_sha256,r.content_complete,r.previously_seen_payload,
        ((r.snapshot->'session'->>'started_at')::timestamptz AT TIME ZONE 'Asia/Shanghai')::date AS source_day,
        EXISTS(SELECT 1 FROM public.project_members pm WHERE pm.project_id=r.project_id AND pm.user_id=r.owner_user_id) AS authorized
      FROM {HEAD_DAYS} WHERE d.owner_user_id=CAST(:owner AS uuid) AND d.work_date=:day
      ORDER BY r.session_id LIMIT 257)
      SELECT id,session_id,project_id,snapshot_sha256,content_complete,previously_seen_payload,source_day,authorized,
        CASE WHEN sum(octet_length(snapshot::text)) OVER ()<=8388608 THEN snapshot END AS snapshot FROM selected'''),
      dict(owner=str(owner),day=day)).mappings().all()
    if len(rows)>256 or any(r['snapshot'] is None for r in rows):
        raise ValueError('CC daily input budget exceeded')
    records=[];captured=[]
    for row in rows:
        included=(row['source_day']==day and row['content_complete'] and not row['previously_seen_payload'] and row['authorized'])
        captured.append(dict(revision=str(row['id']),session=str(row['session_id']),project=str(row['project_id']),
          digest=row['snapshot_sha256'],authorized=row['authorized'],included=included))
        if included:
            s=row['snapshot']['session']
            records.append(dict(session_id=str(row['session_id']),revision_id=str(row['id']),source='cc_switch',
              title=s['title'] or s['task_title'] or 'CC input',messages=[dict(role=m['role'],content=m['content']) for m in row['snapshot']['messages']]))
    return tuple(records),tuple(captured)


def fingerprint(captured):
    return hashlib.sha256(json.dumps(captured,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def fence(orm, *, owner, captured):
    if captured and not cc.enabled():raise ValueError('CC daily input changed: consumer disabled')
    for item in captured:
        params=dict(owner=str(owner),id=item['session'],revision=item['revision'],project=item['project'])
        orm.execute(text('SELECT id FROM public.ai_chat_sessions WHERE id=CAST(:id AS uuid) FOR SHARE'),params).one()
        head=orm.execute(text('SELECT revision_id::text FROM public.cc_input_heads WHERE session_id=CAST(:id AS uuid) FOR SHARE'),params).scalar_one()
        _,digest=cc._raw_snapshot(orm,item['session'])
        membership=orm.execute(text('''SELECT pm.user_id FROM public.project_members pm JOIN public.users u ON u.id=pm.user_id
          WHERE pm.user_id=CAST(:owner AS uuid) AND pm.project_id=CAST(:project AS uuid) AND u.is_active IS TRUE FOR SHARE OF pm,u'''),params).first()
        if head!=item['revision'] or digest!=item['digest'] or (membership is not None)!=item['authorized']:
            raise ValueError('CC daily input changed or permission changed during generation')


def acknowledge(orm, *, owner, day, captured, input_sha256):
    fence(orm,owner=owner,captured=captured)
    if not captured:return
    params=dict(owner=str(owner),day=day)
    orm.execute(text('DELETE FROM public.cc_daily_report_sources WHERE owner_user_id=CAST(:owner AS uuid) AND work_date=:day'),params)
    for item in captured:
        values={**params,**item,'sha':input_sha256}
        orm.execute(text('''INSERT INTO public.cc_daily_report_sources(owner_user_id,work_date,session_id,revision_id,included)
          VALUES(CAST(:owner AS uuid),:day,CAST(:session AS uuid),CAST(:revision AS uuid),:included)'''),values)
        orm.execute(text('''INSERT INTO public.cc_daily_input_receipts(revision_id,owner_user_id,work_date,input_sha256,included)
          VALUES(CAST(:revision AS uuid),CAST(:owner AS uuid),:day,:sha,:included) ON CONFLICT DO NOTHING'''),values)
        orm.execute(text('''UPDATE public.cc_input_consumer_jobs j SET status='consumed',updated_at=now()
          WHERE revision_id=CAST(:revision AS uuid) AND consumer='daily' AND status='pending'
          AND NOT EXISTS(SELECT 1 FROM public.cc_daily_revision_days d WHERE d.revision_id=j.revision_id AND NOT EXISTS(
            SELECT 1 FROM public.cc_daily_input_receipts a WHERE a.revision_id=d.revision_id AND a.owner_user_id=d.owner_user_id AND a.work_date=d.work_date))'''),values)
