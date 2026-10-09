"""Read token components from the ledger, retaining absent optional counts."""
import json


def _first_details_sql(names):
    # Match normalize_usage's first-object selection, including an empty object.
    return '(CASE ' + ' '.join(
        f"WHEN jsonb_typeof(a.event_payload->'usage'->'{name}')='object' THEN a.event_payload->'usage'->'{name}'"
        for name in names) + " ELSE '{}'::jsonb END)"


INPUT_DETAILS_SQL = _first_details_sql(['prompt_tokens_details','input_tokens_details','input_token_details'])
OUTPUT_DETAILS_SQL = _first_details_sql(['output_tokens_details','completion_tokens_details'])

# Transfer booleans only: usage may contain arbitrary unbounded provider data.
REPORTED_SQL = f"""jsonb_build_object(
    'cache_read',COALESCE((a.event_payload->'usage') ?| ARRAY['cached_input_tokens','cache_read_input_tokens','cache_read_tokens']
        OR {INPUT_DETAILS_SQL} ? 'cached_tokens',false),
    'cache_creation',COALESCE((a.event_payload->'usage') ?| ARRAY['cache_write_tokens','cache_creation_input_tokens','cache_creation_tokens'],false),
    'reasoning',COALESCE((a.event_payload->'usage') ? 'reasoning_tokens'
        OR {OUTPUT_DETAILS_SQL} ? 'reasoning_tokens',false)
)"""


def from_ledger(row):
    values = dict(fresh_input_tokens=None,total_input_tokens=None,cache_read_tokens=None,
        cache_creation_tokens=None,reasoning_tokens=None,input_token_semantics=None)
    if row.usage_missing:
        return values
    semantics = getattr(row,'input_token_semantics',None)
    if semantics not in (0,1,2):
        return values
    reported = getattr(row,'reported_tokens',None) or {}
    if isinstance(reported,str):
        reported = json.loads(reported)
    values['input_token_semantics'] = semantics
    raw_input = int(row.input_tokens or 0)
    total_input = int(row.total_tokens or 0) - int(row.output_tokens or 0)
    if total_input >= 0:
        values['total_input_tokens'] = total_input
    for short,field in [('cache_read','cache_read_tokens'),('cache_creation','cache_creation_tokens'),('reasoning','reasoning_tokens')]:
        if reported.get(short) is True:
            value = getattr(row,field,None)
            if type(value) is int and value >= 0:
                values[field] = value
    read,created = values['cache_read_tokens'],values['cache_creation_tokens']
    fresh = (raw_input if semantics == 2 else raw_input-read-created
        if semantics == 1 and read is not None and created is not None else raw_input-read
        if semantics == 0 and read is not None else None)
    if fresh is not None and fresh >= 0:
        values['fresh_input_tokens'] = fresh
    return values
