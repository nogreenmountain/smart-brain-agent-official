"""Bounded summary fold over ordered current contributions for one owned key.

The caller supplies verified current sources in ordered, byte-bounded pages.
No raw conversation is needed; full source coordinates remain separate from
the domain's deliberately bounded summary fields.
"""
import hashlib
import json
import uuid
try:
    from agentops.member_wiki.domain import experience_from_dict,experience_to_dict,merge_experience
except ModuleNotFoundError:
    from agentops_local.member_wiki.domain import experience_from_dict,experience_to_dict,merge_experience


def _encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


class KeyFold:
    def __init__(self, *, owner_user_id, experience_key, metadata_budget=8*1024*1024):
        self.owner=str(uuid.UUID(str(owner_user_id)))
        self.key=experience_key
        self.metadata_budget=metadata_budget
        self.metadata_bytes=0
        self.heads={}
        self.experience=None
        self.position=None
        self.digest=hashlib.sha256()

    def add(self,row):
        if str(row['owner_user_id'])!=self.owner:
            raise ValueError('Wiki contribution owner mismatch')
        request=str(row['request_id']);revision=str(row['revision_id'])
        if request in self.heads:
            raise ValueError('duplicate current Wiki request contribution')
        position=(row['observed_at'],request)
        if self.position is not None and position<=self.position:
            raise ValueError('Wiki contribution order must be strictly increasing')
        metadata=dict(owner_user_id=self.owner,request_id=request,revision_id=revision,
            observed_at=row['observed_at'],project_id=row.get('project_id'),content_sha256=row['content_sha256'])
        size=len(_encoded(metadata))
        if self.metadata_bytes+size>self.metadata_budget:
            raise ValueError('Wiki complete source metadata budget exceeded')
        value=self.experience
        normalized=[]
        for raw in row['experiences']:
            incoming=experience_from_dict(raw)
            if incoming.experience_key!=self.key:
                raise ValueError('Wiki fold received an unrelated experience key')
            incoming.source_session_ids=(request,)
            normalized.append(experience_to_dict(incoming))
            value=merge_experience(value,incoming) if value else incoming
        if not normalized:
            raise ValueError('Wiki fold source has no contribution for the selected key')
        encoded=_encoded(dict(metadata=metadata,experiences=normalized))
        self.digest.update(len(encoded).to_bytes(8,'big'));self.digest.update(encoded)
        self.experience=value
        self.heads[request]=revision
        self.metadata_bytes+=size
        self.position=position

    def finish(self):
        result=dict(status='active' if self.experience else 'stale',
            experience=experience_to_dict(self.experience) if self.experience else None,
            source_session_ids=sorted(self.heads),observation_count=len(self.heads),owner_user_id=self.owner,
            employee_id='gateway-owner:'+self.owner,preserved_baseline=None)
        result['revision_sha256']=hashlib.sha256(_encoded(dict(version='key-stream-v1',
            projection=result,contributions_sha256=self.digest.hexdigest()))).hexdigest()
        return result
