import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archive_policy import filter_archived


def record(cid, name, running):
    return {
        'Id': cid, 'Name': name,
        'Config': {'Labels': {'com.docker.compose.service': 'wiki-mcp', 'com.docker.compose.project': 'smartbrain'}},
        'HostConfig': {'RestartPolicy': {'Name': 'no'}},
        'Image': 'sha256:' + 'a' * 64,
        'State': {'Running': running, 'Status': 'running' if running else 'exited'},
    }


def policy(old):
    digest = hashlib.sha256(json.dumps({k: old[k] for k in ('Config', 'HostConfig', 'Image')}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema_version': 1, 'archived': [{'container_id': old['Id'], 'configuration_sha256': digest, 'replacement_name': '/smartbrain-wiki-mcp-1', 'service': 'wiki-mcp', 'project': 'smartbrain'}]}


def test_exact_stopped_archive_retained_on_disk_but_not_active_snapshot():
    old = record('1' * 64, '/wiki-rollback', False)
    new = record('2' * 64, '/smartbrain-wiki-mcp-1', True)
    data = [old, new]
    assert filter_archived(data, policy(old)) == [new]
    assert data == [old, new]


@pytest.mark.parametrize('change', ['running', 'restart', 'configuration', 'missing_replacement'])
def test_refuses_unsafe_archive_policy(change):
    old = record('1' * 64, '/wiki-rollback', False)
    new = record('2' * 64, '/smartbrain-wiki-mcp-1', True)
    spec = policy(old)
    if change == 'running':
        old['State'].update(Running=True, Status='running')
    elif change == 'restart':
        old['HostConfig']['RestartPolicy']['Name'] = 'always'
    elif change == 'configuration':
        old['Config']['extra'] = 'changed'
    else:
        new['Name'] = '/other'
    with pytest.raises(ValueError):
        filter_archived([old, new], spec)


def test_absent_archive_does_not_drop_recovered_container():
    old = record('1' * 64, '/wiki-rollback', False)
    new = record('2' * 64, '/smartbrain-wiki-mcp-1', True)
    assert filter_archived([new], policy(old)) == [new]


def test_rejects_unknown_fields_or_duplicate_archive_id():
    old = record('1' * 64, '/wiki-rollback', False)
    spec = policy(old)
    spec['archived'].append(copy.deepcopy(spec['archived'][0]))
    with pytest.raises(ValueError):
        filter_archived([old], spec)
    spec = policy(old)
    spec['ignore_all'] = True
    with pytest.raises(ValueError):
        filter_archived([old], spec)
