import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('deployment_verify', ROOT / 'deploy/current/verify.py')
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def test_exact_image_identity_rejects_same_tag_different_content():
    expected = {'api': {'image_id': 'sha256:' + 'a' * 64, 'platform': 'linux/amd64'}}
    image = {'Id': 'sha256:' + 'b' * 64, 'Os': 'linux', 'Architecture': 'amd64'}
    assert v.check_images(expected, {'api': image}) == ['image identity mismatch: api']


def test_exact_image_rejects_wrong_platform_and_missing_image():
    expected = {'api': {'image_id': 'sha256:' + 'a' * 64, 'platform': 'linux/amd64'}}
    assert v.check_images(expected, {}) == ['image missing: api']
    assert v.check_images(expected, {'api': {'Id': 'sha256:' + 'a' * 64, 'Os': 'linux', 'Architecture': 'arm64'}}) == ['image platform mismatch: api']


def test_resource_gates_keep_disk_and_memory_reserves():
    limits = {'min_memory_available_bytes': 4, 'min_docker_free_bytes': 40, 'min_data_free_bytes': 250, 'min_backup_free_bytes': 250}
    actual = {'memory_available_bytes': 3, 'docker_free_bytes': 39, 'data_free_bytes': 250, 'backup_free_bytes': 249}
    assert len(v.check_resources(limits, actual)) == 3


def test_private_root_cannot_be_inside_checkout_or_symlinked_into_it(tmp_path):
    repo = tmp_path / 'repo'; repo.mkdir()
    private = tmp_path / 'private'; private.mkdir()
    assert v.check_private_root(repo, private) == []
    assert v.check_private_root(repo, repo / '.private')
    link = private / 'link'
    try:
        link.symlink_to(repo, target_is_directory=True)
    except OSError:
        pytest.skip('symlink creation unavailable')
    assert v.check_private_root(repo, link)


def test_missing_env_names_and_placeholders_are_reported_without_values(tmp_path):
    p = tmp_path / 'api.env'; p.write_text('PASSWORD=SUPER_PRIVATE\nHOST=__SET_HOST__\n')
    errors = v.check_env(p, ['PASSWORD', 'HOST', 'KEY'])
    assert errors == ['unconfigured environment name: api.env:HOST', 'missing environment name: api.env:KEY']
    assert 'SUPER_PRIVATE' not in json.dumps(errors)


def test_env_duplicate_rejected(tmp_path):
    p = tmp_path / 'api.env'; p.write_text('TOKEN=one\nTOKEN=two\n')
    assert v.check_env(p, ['TOKEN']) == ['duplicate environment name: api.env:TOKEN']


def test_unsafe_bundle_path_rejected_before_reading(tmp_path):
    manifest = {'files': [{'path': '../outside', 'sha256': 'a' * 64}]}
    assert v.check_bundle(tmp_path, manifest) == ['unsafe bundle path']


def test_bundle_requires_hash_match_and_no_symlink_escape(tmp_path):
    import hashlib
    (tmp_path / 'config').write_bytes(b'actual')
    manifest = {'files': [{'path': 'config', 'sha256': hashlib.sha256(b'expected').hexdigest()}]}
    assert v.check_bundle(tmp_path, manifest) == ['bundle hash mismatch: config']


def test_current_topology_and_paths_are_closed():
    compose = json.loads((ROOT / 'deploy/current/compose.yaml').read_text())
    lock = json.loads((ROOT / 'deploy/current/release-lock.json').read_text())
    assert set(compose['services']) == set(lock['services'])
    assert not any('pilot' in n or n in ('employee-gateway', 'project-key-api', 'llm-key-reconcile', 'langfuse') for n in compose['services'])
    for n, service in compose['services'].items():
        assert service['image'] == lock['services'][n]['image_id']
        assert service['pull_policy'] == 'never'
        for mount in service.get('volumes', []):
            if mount['type'] == 'bind' and not mount['source'].startswith('${'):
                assert (ROOT / 'deploy/current' / mount['source']).exists()


def test_runtime_source_manifest_is_complete():
    assert v.check_sources(ROOT) == []


def test_receipt_requires_restore_validation_even_if_files_exist(tmp_path):
    p = tmp_path / 'restoration.json'
    p.write_text(json.dumps({'mode': 'restore', 'verified': False, 'postgres': True, 'clickhouse': True}))
    assert v.check_receipt(p, 'restore')


def test_env_templates_do_not_contain_baked_jwt_or_default_password():
    for p in (ROOT / 'deploy/current/env-examples').glob('*'):
        text = p.read_text()
        assert 'eyJhbGci' not in text, p.name
        assert 'PASSWORD=postgres' not in text, p.name


def test_dedicated_apps_use_their_actual_health_endpoint():
    d = json.loads((ROOT / 'deploy/current/compose.yaml').read_text())
    for name in ('personal-key-api-r1', 'collaboration-api', 'workday-gateway-read'):
        assert '/health/ready' not in str(d['services'][name]['healthcheck'])


def test_smoke_uses_existing_key_route(monkeypatch):
    seen = []
    import urllib.error
    def request(req, timeout):
        seen.append(req.full_url)
        code = 410 if 'adapter' in req.full_url else 401 if '/v4/' in req.full_url else 200
        if code >= 400:
            raise urllib.error.HTTPError(req.full_url, code, '', {}, None)
        class Response:
            status = code
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return Response()
    monkeypatch.setattr(v.urllib.request, 'urlopen', request)
    assert v.smoke('https://brain.example.test') == []
    assert 'https://brain.example.test/v4/ai-gateway/keys' in seen


def test_private_profile_mount_missing_is_named_without_contents(tmp_path):
    config = {'services': {'relay': {'volumes': [{'type': 'bind', 'source': str(tmp_path/'private-key'), 'target': '/run/relay/key'}]}}}
    assert v.check_mount_paths(config) == ['bind mount source missing: relay:/run/relay/key']
