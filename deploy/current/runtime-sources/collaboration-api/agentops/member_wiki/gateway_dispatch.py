"""Durable revision retries; source, publication and attempt commits are explicit.

Reservations survive process death. Publication remains protected by the owner
lock and exact reserved head; finishing a superseded attempt rolls it back.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
try:
    from agentops.member_wiki import gateway_materializer as publisher
    from agentops.ai_usage.delta_revisions import refresh_pending_scopes
except ModuleNotFoundError:
    from agentops_local.member_wiki import gateway_materializer as publisher
    from agentops_local.ai_usage.delta_revisions import refresh_pending_scopes

LEASE_SECONDS=300
RETRY_SECONDS=60


class SupersededAttempt(RuntimeError):
    pass


def _enabled():
    return os.getenv('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED','false').lower()=='true'


def _now(cutoff):
    return max(cutoff,datetime.now(timezone.utc))


def candidates(orm, *, cutoff, limit):
    return orm.execute(text('''WITH requests AS MATERIALIZED (
        SELECT a.user_id::text AS owner_user_id,h.request_id::text,h.revision_id::text,
          (c.revision_id IS NULL) AS missing,s.last_attempt_at,min(j.enqueued_at) AS enqueued_at
        FROM public.ai_gateway_delta_consumer_jobs j
        JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        JOIN public.ai_gateway_delta_heads h ON h.request_id=r.request_id
        JOIN public.ai_gateway_admissions a ON a.id=h.request_id
        LEFT JOIN public.member_wiki_gateway_contributions c ON c.revision_id=h.revision_id
        LEFT JOIN public.member_wiki_gateway_retry_state s ON s.revision_id=h.revision_id
        WHERE j.consumer='member_wiki' AND j.consumed_at IS NULL AND j.enqueued_at<:cutoff
          AND a.admitted_at<:cutoff AND (s.next_attempt_at IS NULL OR s.next_attempt_at<=:cutoff)
        GROUP BY a.user_id,h.request_id,h.revision_id,c.revision_id,s.last_attempt_at), ranked AS (
        SELECT *,row_number() OVER(PARTITION BY owner_user_id
          ORDER BY missing DESC,last_attempt_at NULLS FIRST,enqueued_at,request_id) AS position FROM requests)
        SELECT owner_user_id,request_id,revision_id FROM ranked WHERE position=1
        ORDER BY last_attempt_at NULLS FIRST,enqueued_at,owner_user_id LIMIT :limit'''),
        {'cutoff':cutoff,'limit':limit}).all()


def reserve_attempt(orm, candidate, *, now):
    attempt=str(uuid.uuid4())
    values=dict(owner=candidate.owner_user_id,request=candidate.request_id,revision=candidate.revision_id,
        attempt=attempt,now=now,until=now+timedelta(seconds=LEASE_SECONDS))
    row=orm.execute(text('''INSERT INTO public.member_wiki_gateway_retry_state
        (revision_id,owner_user_id,attempt_id,attempt_count,last_attempt_at,next_attempt_at,status,last_error_code)
        SELECT h.revision_id,a.user_id,CAST(:attempt AS uuid),1,:now,:until,'reserved',NULL
        FROM public.ai_gateway_delta_heads h JOIN public.ai_gateway_admissions a ON a.id=h.request_id
        WHERE h.request_id=CAST(:request AS uuid) AND h.revision_id=CAST(:revision AS uuid)
          AND a.user_id=CAST(:owner AS uuid) AND EXISTS(
            SELECT 1 FROM public.ai_gateway_delta_consumer_jobs j JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
            WHERE r.request_id=h.request_id AND j.consumer='member_wiki' AND j.consumed_at IS NULL)
        ON CONFLICT(revision_id) DO UPDATE SET attempt_id=EXCLUDED.attempt_id,
          attempt_count=member_wiki_gateway_retry_state.attempt_count+1,
          last_attempt_at=EXCLUDED.last_attempt_at,next_attempt_at=EXCLUDED.next_attempt_at,status='reserved',last_error_code=NULL
        WHERE member_wiki_gateway_retry_state.owner_user_id=EXCLUDED.owner_user_id
          AND member_wiki_gateway_retry_state.next_attempt_at<=:now
        RETURNING attempt_count'''),values).scalar_one_or_none()
    if row is None:return None
    orm.execute(text('''UPDATE public.member_wiki_gateway_attempts SET status='superseded',finished_at=:now
        WHERE revision_id=CAST(:revision AS uuid) AND finished_at IS NULL'''),values)
    orm.execute(text('''INSERT INTO public.member_wiki_gateway_attempts
        (attempt_id,revision_id,owner_user_id,started_at,lease_until,status)
        VALUES(CAST(:attempt AS uuid),CAST(:revision AS uuid),CAST(:owner AS uuid),:now,:until,'reserved')'''),values)
    return {**values,'attempt_count':row}


def finish_attempt(orm, ticket, *, status, now, error=None):
    if status not in {'published','staged','busy','failed','noop'}:
        raise ValueError('invalid Wiki attempt result')
    delay=min(900,RETRY_SECONDS*2**min(ticket['attempt_count']-1,4)) if status=='failed' else (5 if status=='busy' else 0)
    values={**ticket,'status':status,'error':error,'finished':now,'next':now+timedelta(seconds=delay)}
    updated=orm.execute(text('''UPDATE public.member_wiki_gateway_retry_state SET status=:status,
        last_error_code=:error,next_attempt_at=:next WHERE revision_id=CAST(:revision AS uuid)
          AND attempt_id=CAST(:attempt AS uuid) AND status='reserved' RETURNING revision_id'''),values).first()
    if updated is None:raise SupersededAttempt('Wiki attempt reservation changed; transaction must roll back')
    updated=orm.execute(text('''UPDATE public.member_wiki_gateway_attempts SET status=:status,error_code=:error,finished_at=:finished
        WHERE attempt_id=CAST(:attempt AS uuid) AND finished_at IS NULL RETURNING attempt_id'''),values).first()
    if updated is None:raise SupersededAttempt('Wiki attempt already finished; transaction must roll back')


def run_pending(orm, *, cutoff, limit=32, generate_text=None, embed_text=None):
    if cutoff.tzinfo is None or type(limit) is not int or not 1<=limit<=256:
        raise ValueError('Wiki dispatcher requires a zoned time and bounded limit')
    counts=dict(status='processed',published_count=0,staged_count=0,busy_count=0,failed_count=0,noop_count=0,fenced_count=0)
    if not _enabled():return {**counts,'status':'disabled'}
    counts['delta_dispatch']=refresh_pending_scopes(orm,limit=limit)
    selected=candidates(orm,cutoff=cutoff,limit=limit)
    orm.commit()
    for candidate in selected:
        if not _enabled():
            counts['status']='disabled';break
        ticket=reserve_attempt(orm,candidate,now=_now(cutoff))
        if ticket is None:
            orm.rollback();counts['busy_count']+=1;continue
        orm.commit()  # A crash cannot erase this attempt and its retry order.
        try:
            result=publisher.publish_owner(orm,owner_user_id=candidate.owner_user_id,cutoff=cutoff,
                selected_heads={candidate.request_id:candidate.revision_id},generate_text=generate_text,embed_text=embed_text)
            status=result['status']
            finish_attempt(orm,ticket,status=status,now=_now(cutoff),error='owner_busy' if status=='busy' else None)
            orm.commit();counts[status+'_count']+=1
        except SupersededAttempt:
            orm.rollback();counts['fenced_count']+=1
        except Exception as error:
            orm.rollback()
            # Never persist model exception text or private inputs.
            code='source_validation_failed' if isinstance(error,ValueError) else 'publication_failed'
            try:
                finish_attempt(orm,ticket,status='failed',now=_now(cutoff),error=code)
                orm.commit();counts['failed_count']+=1
            except SupersededAttempt:
                orm.rollback();counts['fenced_count']+=1
    return counts
