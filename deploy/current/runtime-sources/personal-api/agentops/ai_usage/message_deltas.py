"""Pure candidate projections over immutable, server-bound admission snapshots.

No database/consumer integration yet. Indices reference the original message list;
neither content nor token events are rewritten. Tool results remain reports, not
independent verification that an action ran.
"""
import hashlib
import json
from datetime import datetime

MAX_REQUESTS = 256
MAX_MESSAGES = 32_000
MAX_SERIALIZED_BYTES = 16 * 1024 * 1024


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def _known(snapshot):
    payload = snapshot['payload']
    boundary = payload.get('request_message_count')
    return (type(boundary) is int and 0 <= boundary < len(payload['messages'])
            and payload.get('context_source') in ('client_conversation', 'independent_request'))


def _complete(snapshot):
    return snapshot['payload'].get('content_complete') is True and 200 <= snapshot['status_code'] < 400


def _scope(snapshot):
    payload = snapshot['payload']
    if not _known(snapshot) or not _complete(snapshot):
        return None
    if payload.get('context_source') != 'client_conversation' or not payload.get('conversation_id'):
        return None
    return (snapshot['member_id'], snapshot['gateway_instance_id'], snapshot['project_id'], payload['conversation_id'])


def _tool_kind(message):
    metadata = message.get('metadata') or {}
    kind = metadata.get('type')
    if kind in ('function_call', 'custom_tool_call', 'tool_use'):
        return 'call'
    if message.get('role') == 'tool':
        if kind in ('function_call_output', 'custom_tool_call_output', 'tool_result') or metadata.get('tool_call_id'):
            return 'reported_result'
        return 'unknown'
    return None


def _validate(snapshots):
    if not isinstance(snapshots, list) or len(snapshots) > MAX_REQUESTS:
        raise ValueError('request budget exceeded or invalid batch')
    identities, times, message_keys, source_hashes = set(), {}, {}, {}
    byte_count = message_count = 0
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    for source in snapshots:
        try:
            for field in ('request_id', 'member_id', 'gateway_instance_id'):
                if not isinstance(source[field], str) or not source[field].strip():
                    raise ValueError('invalid server identity')
            identity = source['request_id']
            if identity in identities:
                raise ValueError('duplicate request identity')
            identities.add(identity)
            if source['project_id'] is not None and (not isinstance(source['project_id'], str) or not source['project_id'].strip()):
                raise ValueError('invalid server project')
            stamp = datetime.fromisoformat(source['admitted_at'])
            if stamp.utcoffset() is None:
                raise ValueError('server admission time must include timezone')
            if type(source['status_code']) is not int or not 100 <= source['status_code'] <= 599:
                raise ValueError('invalid status code')
            messages = source['payload']['messages']
            if not isinstance(messages, list) or any(not isinstance(m, dict) for m in messages):
                raise ValueError('invalid messages')
            if any(not isinstance(m.get('metadata', {}), dict) for m in messages):
                raise ValueError('invalid message metadata')
            payload = source['payload']
            boundary, origin = payload.get('request_message_count'), payload.get('context_source')
            if boundary is not None or origin is not None:
                if (type(boundary) is not int or not 0 <= boundary <= len(messages)
                        or origin not in ('client_conversation', 'independent_request')
                        or (payload.get('content_complete') is True and boundary == len(messages))):
                    raise ValueError('invalid message provenance')
            message_count += len(messages)
            if message_count > MAX_MESSAGES:
                raise ValueError('message budget exceeded')
            digest = hashlib.sha256()
            for chunk in encoder.iterencode(source):
                encoded = chunk.encode('utf-8')
                byte_count += len(encoded)
                if byte_count > MAX_SERIALIZED_BYTES:
                    raise ValueError('serialized byte budget exceeded')
                digest.update(encoded)
            times[identity] = stamp
            source_hashes[identity] = digest.hexdigest()
            # JSON types remain distinct (Python considers True == 1).
            message_keys[identity] = [_canonical(message) for message in messages]
        except (KeyError, TypeError, AttributeError, OverflowError, RecursionError) as error:
            raise ValueError('invalid admission snapshot') from error
    return times, message_keys, source_hashes


def derive_deltas(snapshots):
    """Caller supplies member/instance/project/time from trusted database columns."""
    times, message_keys, source_hashes = _validate(snapshots)
    result = {}
    for current in snapshots:
        payload = current['payload']
        messages = payload['messages']
        known = _known(current)
        complete = _complete(current)
        boundary = payload['request_message_count'] if known and complete else len(messages)
        scope = _scope(current)
        parents = [p for p in snapshots if scope is not None and _scope(p) == scope
                   and times[p['request_id']] < times[current['request_id']]
                   and len(p['payload']['messages']) <= boundary
                   and message_keys[p['request_id']] == message_keys[current['request_id']][:len(p['payload']['messages'])]]
        longest = max((len(p['payload']['messages']) for p in parents), default=0)
        parents = sorted((p for p in parents if len(p['payload']['messages']) == longest),
                         key=lambda p: p['request_id'])
        parent = parents[0] if len(parents) == 1 else None
        offset = len(parent['payload']['messages']) if parent else 0
        retained = list(range(offset, boundary))
        response = list(range(boundary, len(messages)))
        visible = retained + response
        status = ('incomplete' if not complete else 'legacy_unknown' if not known else
                  'independent_request' if payload['context_source'] == 'independent_request' else
                  'exact_prefix' if parent else 'ambiguous_prefix' if parents else 'unattributed_context')
        row = dict(request_id=current['request_id'], status=status,
                   parent_request_id=parent['request_id'] if parent else None,
                   candidate_parent_ids=[p['request_id'] for p in parents],
                   suppressed_input_indices=list(range(offset)), retained_input_indices=retained,
                   response_indices=response,
                   reported_tool_result_indices=[i for i in visible if _tool_kind(messages[i]) == 'reported_result'],
                   tool_call_indices=[i for i in visible if _tool_kind(messages[i]) == 'call'],
                   unknown_tool_indices=[i for i in visible if _tool_kind(messages[i]) == 'unknown'],
                   tool_execution_verified=False)
        row['source_sha256'] = source_hashes[current['request_id']]
        row['revision_sha256'] = _hash(dict(version=1, source=row['source_sha256'],
            parents=[source_hashes[p['request_id']] for p in parents], projection=row))
        result[current['request_id']] = row
    return result
