"""Immutable provenance for fresh UUID daily generations; never backfill history."""
import hashlib
import json
from pathlib import Path
import uuid
from sqlalchemy import text

MAX_INPUT_BYTES = 16 * 1024 * 1024
COMPILER_FILES = (
    'daily_owner_writer.py', 'daily_owner_scope.py', 'daily_log_service.py',
    'daily_log.py', 'daily_delta_sources.py', 'cc_daily_inputs.py',
    'daily_generation_manifests.py',
)


def installed(orm):
    return orm.execute(text("SELECT to_regclass('public.ai_daily_generation_manifests') IS NOT NULL")).scalar_one()


def prepare(capture, *, model, prompts):
    """Freeze all normalized sources and actual prompts before any model call."""
    payload = dict(schema='daily-generation-v1', owner_user_id=str(capture.owner_user_id),
        work_date=capture.work_date.isoformat(), sources=capture.sources,
        cc_states=capture.cc_inputs, model=model, prompts=prompts,
        compiler_files={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                        for name in COMPILER_FILES})
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(encoded.encode('utf-8')) > MAX_INPUT_BYTES:
        raise ValueError('daily generation input budget exceeded')
    return encoded, hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def current(orm, *, owner, day):
    """Fail on any existing head/report/input drift, including before recompilation."""
    orm.execute(text("SET LOCAL TIME ZONE 'UTC'"))
    row = orm.execute(text('''SELECT m.input_sha256,
        (m.report=to_jsonb(r) AND m.input_sha256=i.input_sha256) AS intact
        FROM public.ai_daily_generation_heads h
        JOIN public.ai_daily_generation_manifests m ON m.id=h.generation_id
        LEFT JOIN public.ai_daily_work_logs r ON r.owner_user_id=h.owner_user_id AND r.work_date=h.work_date
        LEFT JOIN public.ai_daily_worklog_inputs i ON i.owner_user_id=h.owner_user_id AND i.work_date=h.work_date
        WHERE h.owner_user_id=CAST(:owner AS uuid) AND h.work_date=:day'''), dict(owner=owner, day=day)).first()
    if row is not None and row.intact is not True:
        raise ValueError('daily generation report or input drift')
    return row.input_sha256 if row else None


def record(orm, *, owner, day, source_manifest, input_sha256):
    # Serialize the stored output in PostgreSQL, avoiding Python float/timezone round trips.
    orm.execute(text("SET LOCAL TIME ZONE 'UTC'"))
    params = dict(owner=owner, day=day, manifest=source_manifest, sha=input_sha256, id=str(uuid.uuid4()))
    orm.execute(text('''INSERT INTO public.ai_daily_generation_manifests
        (id,owner_user_id,work_date,input_sha256,source_manifest,report)
        SELECT CAST(:id AS uuid),r.owner_user_id,r.work_date,:sha,CAST(:manifest AS jsonb),to_jsonb(r)
        FROM public.ai_daily_work_logs r WHERE r.owner_user_id=CAST(:owner AS uuid) AND r.work_date=:day'''), params)
    orm.execute(text('''INSERT INTO public.ai_daily_generation_heads(owner_user_id,work_date,generation_id)
        VALUES(CAST(:owner AS uuid),:day,CAST(:id AS uuid))
        ON CONFLICT(owner_user_id,work_date) DO UPDATE SET generation_id=EXCLUDED.generation_id'''), params)
