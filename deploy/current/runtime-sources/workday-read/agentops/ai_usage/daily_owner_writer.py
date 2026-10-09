"""Candidate UUID report transaction, selected by the migrated periodic worker.

Requires the owner-identity migration. Unowned legacy rows are never selected,
archived, replaced or assigned. Sources are immutable personal requests and
project requests with verified UUID/instance mirrors. Legacy collectors still
require their independent ownership/completeness audit before consumption.
"""
import hashlib
import json
import uuid
import logging
from dataclasses import asdict
from sqlalchemy import text
try:
    from agentops.ai_usage import daily_owner_scope as scope,daily_log_service as daily
    from agentops.workday.identity import derive_employee_identity
except ModuleNotFoundError:
    from agentops_local.ai_usage import daily_owner_scope as scope,daily_log_service as daily
    from agentops_local.workday.identity import derive_employee_identity


def lock_owner_day(orm, *, owner_user_id, work_date):
    owner=str(uuid.UUID(str(owner_user_id)))
    return bool(orm.execute(text('SELECT pg_try_advisory_xact_lock(hashtextextended(:identity,0))'),
        {'identity':json.dumps(['daily-worklog-owner-v1',owner,work_date.isoformat()])}).scalar_one())


def generate_owner_reports(orm, *, work_date, generate_text=None):
    owners=scope.owner_ids_for_day(orm,work_date=work_date)
    counts=dict(ready_count=0,empty_count=0,skipped_count=0,failure_count=0)
    for owner in owners:
        try:
            result=generate_owner_day(orm,owner_user_id=owner,work_date=work_date,generate_text=generate_text)
            counts[{'ready':'ready_count','empty':'empty_count','skipped':'skipped_count','busy':'failure_count'}[result]]+=1
        except Exception:
            counts['failure_count']+=1
            # SQL/model exceptions can contain private report bodies. Metadata
            # is sufficient for scheduling retry; do not log exception payloads.
            logging.getLogger(__name__).error('UUID daily report failed; owner=%s date=%s; pending retained',owner,work_date)
    return daily.DailyWorklogRunResult(employee_count=len(owners),**counts)


def _acknowledge(orm,capture,input_sha256):
    scope.queue.mark_consumed(orm,list(capture.pending_requests))
    scope.revisions.acknowledge_jobs(orm,consumer='daily_worklog',revisions=list(capture.pending_revisions))
    from . import cc_daily_inputs as cc_daily
    cc_daily.acknowledge(orm,owner=capture.owner_user_id,day=capture.work_date,
      captured=capture.cc_inputs,input_sha256=input_sha256)


def generate_owner_day(orm, *, owner_user_id, work_date, generate_text=None):
    """Commit one owner/day, or rollback and propagate failure for durable retry."""
    owner=str(uuid.UUID(str(owner_user_id)))
    params={'owner':owner,'day':work_date}
    try:
        if not lock_owner_day(orm,owner_user_id=owner,work_date=work_date):
            orm.rollback()
            return 'busy'
        account=orm.execute(text('''SELECT a.email,u.full_name FROM public.users u
            JOIN auth.users a ON a.id=u.id WHERE u.id=CAST(:owner AS uuid) AND u.is_active IS TRUE'''),params).first()
        if account is None:
            raise ValueError('daily report owner must be an active account')
        employee_id,employee_name=derive_employee_identity(user_id=uuid.UUID(owner),
            email=account.email or '',full_name=account.full_name)
        capture=scope.capture_owner_day(orm,owner_user_id=owner,work_date=work_date)
        conversations=[daily.WorklogConversation(**{k:v for k,v in row.items() if k!='messages'},
            messages=tuple(daily.WorklogMessage(**message) for message in row['messages'])) for row in capture.sources]
        fingerprint=hashlib.sha256(json.dumps(['daily-owner-input-v1',owner,work_date.isoformat(),
            daily._input_fingerprint(conversations)],separators=(',',':')).encode()).hexdigest()
        if capture.cc_inputs:
            from . import cc_daily_inputs as cc_daily
            fingerprint=hashlib.sha256(json.dumps(['daily-owner-cc-v1',fingerprint,
              cc_daily.fingerprint(capture.cc_inputs)],separators=(',',':')).encode()).hexdigest()
        from . import daily_generation_manifests as manifests
        manifested=manifests.installed(orm)
        candidates=[conversation for conversation in conversations if daily.has_execution_signal(conversation)]
        batches=list(daily._conversation_batches(candidates))
        prompts=[daily.build_daily_worklog_prompt(employee_name=employee_name,work_date=work_date,conversations=batch)
                 for batch in batches]
        model=daily._model_name()
        source_manifest=None
        current_manifest=None
        if manifested:
            source_manifest,fingerprint=manifests.prepare(capture,model=model,prompts=prompts)
            current_manifest=manifests.current(orm,owner=owner,day=work_date)
        previous=orm.execute(text('''SELECT input_sha256 FROM public.ai_daily_worklog_inputs
            WHERE owner_user_id=CAST(:owner AS uuid) AND work_date=:day'''),params).scalar_one_or_none()
        if previous==fingerprint and (not manifested or current_manifest==fingerprint):
            _acknowledge(orm,capture,fingerprint)
            orm.commit()
            return 'skipped'
        generator=generate_text or daily._call_model
        generations=[]
        for batch,prompt in zip(batches,prompts):
            generations.append(daily.parse_daily_worklog_response(generator(prompt),
                allowed_session_ids={item.session_id for item in batch}))
        generation=(daily.merge_daily_worklog_generations(generations) if generations else
                    daily.DailyWorklogGeneration(work_items=(),report_markdown='',source_session_ids=()))
        # Whole old report and matching fingerprint, scoped by owner on both sides.
        orm.execute(text('''INSERT INTO public.ai_daily_worklog_revisions
            (owner_user_id,employee_id,work_date,input_sha256,report)
            SELECT r.owner_user_id,r.employee_id,r.work_date,i.input_sha256,to_jsonb(r)
            FROM public.ai_daily_work_logs r LEFT JOIN public.ai_daily_worklog_inputs i
              ON i.owner_user_id=r.owner_user_id AND i.work_date=r.work_date
            WHERE r.owner_user_id=CAST(:owner AS uuid) AND r.work_date=:day'''),params)
        status='ready' if generation.work_items else 'empty'
        items=[{k:list(v) if isinstance(v,tuple) else v for k,v in asdict(item).items()
                if k!='source_session_ids'} for item in generation.work_items]
        orm.execute(text('''INSERT INTO public.ai_daily_work_logs
            (owner_user_id,employee_id,employee_name,work_date,timezone,status,report_markdown,
             work_items,source_session_ids,source_count,model,generated_at,updated_at)
            VALUES (CAST(:owner AS uuid),:employee,:name,:day,'Asia/Shanghai',:status,:markdown,
              CAST(:items AS jsonb),CAST(:sources AS jsonb),:count,:model,now(),now())
            ON CONFLICT (owner_user_id,work_date) WHERE owner_user_id IS NOT NULL DO UPDATE SET
              employee_id=EXCLUDED.employee_id,employee_name=EXCLUDED.employee_name,status=EXCLUDED.status,
              report_markdown=EXCLUDED.report_markdown,work_items=EXCLUDED.work_items,
              source_session_ids=EXCLUDED.source_session_ids,source_count=EXCLUDED.source_count,
              model=EXCLUDED.model,generated_at=EXCLUDED.generated_at,updated_at=now()'''),
            {**params,'employee':employee_id,'name':employee_name,'status':status,
             'markdown':generation.report_markdown or None,'items':json.dumps(items,ensure_ascii=False),
             'sources':json.dumps(list(generation.source_session_ids)),
             'count':len(generation.source_session_ids),'model':model})
        orm.execute(text('''INSERT INTO public.ai_daily_worklog_inputs(owner_user_id,employee_id,work_date,input_sha256)
            VALUES (CAST(:owner AS uuid),:employee,:day,:sha)
            ON CONFLICT (owner_user_id,work_date) WHERE owner_user_id IS NOT NULL DO UPDATE SET
              employee_id=EXCLUDED.employee_id,input_sha256=EXCLUDED.input_sha256,updated_at=now()'''),
            {**params,'employee':employee_id,'sha':fingerprint})
        if manifested:
            manifests.record(orm,owner=owner,day=work_date,source_manifest=source_manifest,input_sha256=fingerprint)
        _acknowledge(orm,capture,fingerprint)
        orm.commit()
        return status
    except Exception:
        orm.rollback()
        raise
