"""Immutable compiled contributions. No report publication or consumer ACK here."""
import importlib.util
import json
from pathlib import Path
from sqlalchemy import text
try:
    from agentops.member_wiki import contributions as domain
except ModuleNotFoundError:
    spec=importlib.util.spec_from_file_location('wiki_contribution_store_domain',Path(__file__).with_name('contributions.py'))
    domain=importlib.util.module_from_spec(spec);spec.loader.exec_module(domain)


def save_contribution(orm, *, revision_id, request_id, owner_user_id, employee_id, model, experiences):
    normalized=[]
    for item in experiences:
        value=domain.experience_from_dict(item)
        value.source_session_ids=(str(request_id),)
        normalized.append(domain.experience_to_dict(value))
    values=dict(revision_id=str(revision_id),request_id=str(request_id),owner_user_id=str(owner_user_id),
        employee_id=employee_id,model=model,compiler_version='personal-wiki-contribution-v1',experiences=normalized)
    digest=domain._hash(values)
    params={**values,'experiences':json.dumps(normalized,ensure_ascii=False,sort_keys=True,separators=(',',':')),
            'content_sha256':digest}
    row=orm.execute(text('''INSERT INTO public.member_wiki_gateway_contributions
        (revision_id,request_id,owner_user_id,employee_id,model,compiler_version,content_sha256,experiences)
        VALUES (:revision_id,:request_id,:owner_user_id,:employee_id,:model,:compiler_version,:content_sha256,CAST(:experiences AS jsonb))
        ON CONFLICT(revision_id) DO NOTHING RETURNING content_sha256'''),params).first()
    if row is None:
        row=orm.execute(text('''SELECT content_sha256 FROM public.member_wiki_gateway_contributions
            WHERE revision_id=:revision_id'''),params).first()
    if row is None or row.content_sha256!=digest:
        raise ValueError('immutable Wiki contribution differs; explicit compiler revision required')
    return digest
