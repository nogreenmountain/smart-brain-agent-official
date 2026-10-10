"""Select active services while retaining explicitly archived containers.

The policy is a trusted, checksum-bound deployment file, not client input.
Only exact stopped containers with an unchanged configuration can be excluded.
"""
import hashlib
import json
import re


def filter_archived(records, policy):
    if not isinstance(policy, dict) or set(policy) != {'schema_version', 'archived'} or policy['schema_version'] != 1:
        raise ValueError('invalid archive policy')
    rows = policy['archived']
    if not isinstance(rows, list) or len(rows) > 64:
        raise ValueError('invalid archive policy entries')
    ids = set()
    omitted = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'container_id', 'configuration_sha256', 'replacement_name', 'service', 'project'}:
            raise ValueError('invalid archive entry')
        if any(not isinstance(row[k], str) or not re.fullmatch(r'[a-f0-9]{64}', row[k]) for k in ('container_id', 'configuration_sha256')):
            raise ValueError('invalid archive identity')
        if not isinstance(row['replacement_name'], str) or not re.fullmatch(r'/[A-Za-z0-9][A-Za-z0-9_.-]*', row['replacement_name']):
            raise ValueError('invalid replacement name')
        if any(not isinstance(row[k], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', row[k]) for k in ('service', 'project')):
            raise ValueError('invalid archive service identity')
        if row['container_id'] in ids:
            raise ValueError('duplicate archive identity')
        ids.add(row['container_id'])
        archived = [c for c in records if c['Id'] == row['container_id']]
        if not archived:
            continue
        c = archived[0]
        labels = c['Config'].get('Labels') or {}
        digest = hashlib.sha256(json.dumps({k: c[k] for k in ('Config', 'HostConfig', 'Image')}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if (len(archived) != 1 or c['State']['Running'] or c['State']['Status'] not in ('created', 'exited')
                or c['HostConfig']['RestartPolicy']['Name'] != 'no' or digest != row['configuration_sha256']
                or labels.get('com.docker.compose.service') != row['service']
                or labels.get('com.docker.compose.project') != row['project']):
            raise ValueError('archived container changed or is active')
        replacements = [r for r in records if r['Id'] != c['Id'] and r['Name'] == row['replacement_name']
                        and r['State']['Running']
                        and (r['Config'].get('Labels') or {}).get('com.docker.compose.service') == row['service']
                        and (r['Config'].get('Labels') or {}).get('com.docker.compose.project') == row['project']]
        if len(replacements) != 1:
            raise ValueError('active replacement missing or ambiguous')
        omitted.add(c['Id'])
    return [c for c in records if c['Id'] not in omitted]
