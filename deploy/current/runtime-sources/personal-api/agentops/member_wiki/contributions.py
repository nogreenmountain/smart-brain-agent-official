"""Pure rebuild from current source contributions; no published Wiki mutation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import copy
import uuid

try:
    from agentops.member_wiki.domain import experience_from_dict,experience_to_dict,merge_experience
except ModuleNotFoundError:
    spec=importlib.util.spec_from_file_location('wiki_contribution_domain',Path(__file__).with_name('domain.py'))
    domain=importlib.util.module_from_spec(spec);sys.modules[spec.name]=domain;spec.loader.exec_module(domain)
    experience_from_dict=domain.experience_from_dict
    experience_to_dict=domain.experience_to_dict
    merge_experience=domain.merge_experience


def _hash(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def rebuild_experiences(*, owner_user_id, employee_id, contributions, current_revisions, baselines, known_experience_keys=()):
    by_revision={}
    known_keys=set(baselines) | set(known_experience_keys)
    for row in contributions:
        if row['owner_user_id']!=owner_user_id or row['employee_id']!=employee_id:
            raise ValueError('contribution owner mismatch')
        identity=(row['request_id'],row['revision_id'])
        if identity in by_revision:
            raise ValueError('duplicate contribution revision')
        by_revision[identity]=row
        known_keys.update(experience_from_dict(item).experience_key for item in row['experiences'])
    selected=[]
    for request,revision in current_revisions.items():
        if (request,revision) not in by_revision:
            raise ValueError('current contribution compilation is pending')
        selected.append(by_revision[request,revision])
    selected.sort(key=lambda row:(row['observed_at'],row['request_id']))
    grouped={}
    for row in selected:
        for item in row['experiences']:
            value=experience_from_dict(item)
            value.source_session_ids=(row['request_id'],)
            grouped.setdefault(value.experience_key,[]).append((row,value))
    output={}
    for key in sorted(known_keys):
        items=grouped.get(key,[])
        baseline=baselines.get(key)
        value=None
        baseline_sources=set()
        base_count=0
        if baseline:
            if baseline['owner_user_id']!=owner_user_id or baseline['employee_id']!=employee_id:
                raise ValueError('baseline owner mismatch')
            baseline_sources=set(baseline['source_session_ids'])
            if baseline_sources.intersection(current_revisions) or baseline['status']!='active':
                raise ValueError('opaque or retired baseline requires audit')
            value=experience_from_dict(baseline['experience'])
            if value.experience_key!=key:
                raise ValueError('baseline experience key mismatch')
            base_count=baseline['observation_count']
        for _,incoming in items:
            value=merge_experience(value,incoming) if value else incoming
        personal_sources={row['request_id'] for row,_ in items}
        sources=sorted(baseline_sources|personal_sources)
        result=dict(status='active' if value else 'stale',experience=experience_to_dict(value) if value else None,
                    source_session_ids=sources,observation_count=base_count+len(personal_sources),
                    owner_user_id=owner_user_id,employee_id=employee_id,preserved_baseline=copy.deepcopy(baseline))
        # Full source coordinates are separate from the bounded experience summary.
        # Empty current contributions must also change the revision identity.
        dependencies=[row for row in selected if any(experience_from_dict(item).experience_key==key
            for historical in contributions if historical['request_id']==row['request_id']
            for item in historical['experiences'])]
        result['revision_sha256']=_hash(dict(version=1,projection=result,contributions=dependencies))
        output[key]=result
    return output


def rebuild_owned_experiences(*, owner_user_id, contributions, current_revisions, baselines, known_experience_keys=()):
    """Rebuild already owner-verified inputs across historical display aliases.

    This pure helper is not authorization: the publisher must verify immutable
    request ownership and baseline bindings in its database transaction first.
    Legacy callers keep their stricter alias contract in rebuild_experiences.
    """
    owner = str(uuid.UUID(str(owner_user_id)))
    storage_key = 'gateway-owner:' + owner
    records = []
    normalized_baselines = {}
    for row in contributions:
        if str(row['owner_user_id']) != owner:
            raise ValueError('contribution owner mismatch')
        records.append({**row, 'employee_id':storage_key})
    for key, baseline in baselines.items():
        if str(baseline['owner_user_id']) != owner:
            raise ValueError('baseline owner mismatch')
        normalized_baselines[key] = {**baseline,'employee_id':storage_key}
    result = rebuild_experiences(owner_user_id=owner,employee_id=storage_key,
        contributions=records,current_revisions=current_revisions,baselines=normalized_baselines,
        known_experience_keys=known_experience_keys)
    for key,value in result.items():
        value['preserved_baseline'] = copy.deepcopy(baselines.get(key))
        value['revision_sha256'] = _hash(dict(version='owner-v1',projection=value,heads=current_revisions))
    return result
