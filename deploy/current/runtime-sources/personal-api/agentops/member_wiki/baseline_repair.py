"""Exact source-header correction for an explicitly reviewed legacy baseline.

The projection preserves body bytes. The explicit transaction entry point only
accepts an operator-reviewed snapshot, appends a version and immutable ledger,
and never adopts content, binds access, calls a model or commits the caller.
"""
import json
import uuid
import re


def _coordinates(value):
    if not isinstance(value,(list,tuple)) or not value:
        raise ValueError('Wiki repair requires explicit source coordinates')
    try:
        valid=all(isinstance(item,str) and str(uuid.UUID(item))==item for item in value)
    except (ValueError,TypeError,AttributeError):
        valid=False
    if not valid or len(set(value))!=len(value):
        raise ValueError('Wiki repair source coordinates require audit')
    return list(value)


def repair_source_header(markdown, *, declared_ids, complete_ids):
    declared=_coordinates(declared_ids);complete=_coordinates(complete_ids)
    if not set(declared)<set(complete):
        raise ValueError('Wiki source repair must append audited missing coordinates')
    if not isinstance(markdown,str) or len(markdown.encode('utf-8'))>8*1024*1024:
        raise ValueError('Wiki repair document budget exceeded')
    newline='\r\n' if markdown.startswith('---\r\n') else '\n'
    opening='---'+newline;closing=newline+'---'+newline
    if not markdown.startswith(opening) or closing not in markdown[len(opening):]:
        raise ValueError('Wiki repair requires canonical source frontmatter')
    header,body=markdown[len(opening):].split(closing,1)
    lines=header.split(newline)
    matches=[i for i,line in enumerate(lines) if line.startswith('source_session_ids:')]
    if len(matches)!=1:
        raise ValueError('Wiki repair requires one audited source header')
    index=matches[0]
    try:observed=json.loads(lines[index].partition(':')[2].strip())
    except (ValueError,TypeError):
        raise ValueError('Wiki repair source header is not canonical JSON') from None
    if observed!=declared:
        raise ValueError('Wiki repair source header differs from reviewed coordinates')
    lines[index]='source_session_ids: '+json.dumps(complete,ensure_ascii=False)
    result=opening+newline.join(lines)+closing+body
    if len(result.encode('utf-8'))>8*1024*1024:
        raise ValueError('Wiki repair document budget exceeded')
    return result


def _snapshot(orm, experience_id):
    from sqlalchemy import text
    # One SQL statement and one bounded transfer; JSON stays in PostgreSQL if
    # it exceeds the budget. Table locks below also exclude legacy phantoms.
    row=orm.execute(text('''WITH snapshot AS MATERIALIZED (
      SELECT jsonb_build_object('current',to_jsonb(w),
        'versions',(SELECT jsonb_agg(to_jsonb(v) ORDER BY v.version)
          FROM public.member_wiki_experience_versions v WHERE v.experience_id=w.id),
        'sources',(SELECT jsonb_agg(to_jsonb(s) ORDER BY s.session_id)
          FROM public.member_wiki_experience_sources s WHERE s.experience_id=w.id),
        'scopes',(SELECT jsonb_agg(to_jsonb(f) ORDER BY f.session_id)
          FROM public.member_wiki_legacy_source_scopes f WHERE f.session_id IN
            (SELECT session_id FROM public.member_wiki_experience_sources WHERE experience_id=w.id))) AS value
      FROM public.member_wiki_experiences w WHERE w.id=CAST(:id AS uuid))
      SELECT CASE WHEN octet_length(value::text)<=8388608 THEN value END AS payload,
        encode(sha256(convert_to(value::text,'UTF8')),'hex') AS digest FROM snapshot'''),{'id':str(experience_id)}).first()
    if row is None or row.payload is None:
        raise ValueError('Wiki repair snapshot is missing or exceeds budget')
    return row.payload,row.digest


def apply_source_repair(orm, *, experience_id, owner_user_id, reviewed_sha256, repair_id):
    """Append an explicitly reviewed source-only version in a dedicated Session.

    The caller commits/rolls back. All repair effects use a savepoint, including
    SQL failures after individual writes. NOWAIT table locks are intentional for
    an operator maintenance batch; this is not a periodic worker API. Review
    covers exact current/version/source/frozen-origin rows, not their content
    completeness. Do not call with pending unrelated ORM objects.
    """
    from sqlalchemy import text
    experience_id=str(uuid.UUID(str(experience_id)));owner_user_id=str(uuid.UUID(str(owner_user_id)))
    repair_id=str(uuid.UUID(str(repair_id)))
    if not re.fullmatch('[0-9a-f]{64}',str(reviewed_sha256)):
        raise ValueError('Wiki source repair requires a reviewed SHA256')
    if orm.new or orm.dirty or orm.deleted:
        raise ValueError('Wiki source repair requires a dedicated Session')
    with orm.begin_nested():
        # Cover writers that do not acquire a parent row lock, including source
        # and version inserts. Reads continue; competing writes fail immediately.
        orm.execute(text('''LOCK TABLE public.member_wiki_experiences,
          public.member_wiki_experience_versions,public.member_wiki_experience_sources,
          public.member_wiki_legacy_source_scopes,public.member_wiki_access_bindings,
          public.member_wiki_source_repairs IN SHARE ROW EXCLUSIVE MODE NOWAIT'''))
        payload,digest=_snapshot(orm,experience_id)
        existing=orm.execute(text('''SELECT * FROM public.member_wiki_source_repairs
          WHERE repair_id=CAST(:id AS uuid)'''),{'id':repair_id}).mappings().first()
        if existing is not None:
            if (str(existing['experience_id'])!=experience_id or str(existing['owner_user_id'])!=owner_user_id
                or existing['reviewed_sha256']!=reviewed_sha256 or existing['resulting_sha256']!=digest):
                raise ValueError('Wiki repair replay differs from recorded review or result')
            return dict(version=existing['after_version'],replayed=True,completeness_attested=False)
        if digest!=reviewed_sha256:
            raise ValueError('Wiki repair snapshot drifted after review')
        current=payload['current'];versions=payload['versions'] or [];sources=payload['sources'] or [];scopes=payload['scopes'] or []
        declared=_coordinates(current['source_session_ids'])
        complete=_coordinates([s['session_id'] for s in sources])
        if not set(declared)<set(complete):
            raise ValueError('Wiki declared sources must be a strict subset of audited source rows')
        scoped={f['session_id']:f for f in scopes}
        if set(scoped)!=set(complete) or any(s['source']!='cc_switch' for s in sources) or any(
            f['owner_user_id']!=owner_user_id or f['source']!='cc_switch' or not f['project_id'] for f in scopes):
            raise ValueError('Wiki source repair owner or frozen origin requires audit')
        previous=current['current_version']
        if (len(versions)!=previous or [v['version'] for v in versions]!=list(range(1,previous+1))
            or versions[-1]['markdown_content']!=current['markdown_content']
            or versions[-1]['structured_content']!=current['structured_content']):
            raise ValueError('Wiki source repair current and version history disagree')
        historic=set()
        for version in versions:historic.update(_coordinates(version['source_session_ids']))
        if historic!=set(complete):
            raise ValueError('Wiki source repair version and source coverage disagree')
        complete=declared+[s for s in complete if s not in set(declared)]
        markdown=repair_source_header(current['markdown_content'],declared_ids=declared,complete_ids=complete)
        params=dict(id=experience_id,version=previous+1,markdown=markdown,sources=json.dumps(complete))
        orm.execute(text('''UPDATE public.member_wiki_experiences SET markdown_content=:markdown,
          source_session_ids=CAST(:sources AS jsonb),current_version=:version,updated_at=now()
          WHERE id=CAST(:id AS uuid)'''),params)
        orm.execute(text('''INSERT INTO public.member_wiki_experience_versions
          (experience_id,version,run_id,structured_content,markdown_content,source_session_ids)
          SELECT id,:version,NULL,structured_content,:markdown,CAST(:sources AS jsonb)
          FROM public.member_wiki_experiences WHERE id=CAST(:id AS uuid)'''),params)
        _,resulting=_snapshot(orm,experience_id)
        orm.execute(text('''INSERT INTO public.member_wiki_source_repairs
          (repair_id,experience_id,owner_user_id,reviewed_sha256,resulting_sha256,
            before_version,after_version,complete_source_ids,completeness_attested)
          VALUES(CAST(:repair AS uuid),CAST(:id AS uuid),CAST(:owner AS uuid),:review,:result,
            :previous,:version,CAST(:sources AS jsonb),false)'''),
          params|dict(repair=repair_id,owner=owner_user_id,review=reviewed_sha256,result=resulting,previous=previous))
        return dict(version=previous+1,replayed=False,completeness_attested=False)
