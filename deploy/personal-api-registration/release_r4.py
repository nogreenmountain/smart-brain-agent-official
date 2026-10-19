"""Guarded one-shot registration release. Importing this file has no side effects."""
import copy
import hashlib
import json
import pathlib
import sys
import time
import urllib.request
from datetime import datetime, timezone

RELEASE = 'personal-api-registration-20261019-r4'
ROOT = pathlib.Path('/srv/smartbrain/releases') / RELEASE
OLD = '052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e'
IMAGE = 'sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1'
STARTED = '2026-10-18T14:43:13.86527095Z'
PROXY_SHA = '075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe'
NAME = 'smartbrain-personal-key-api-20260923-filter-internal-r1'
ROLLBACK_NAME = NAME + '-rollback-registration-20261019-r4'
CANDIDATE_NAME = 'smartbrain-registration-ready-20261019-r4'


def validate_health(health):
    assert health['status'] == 'ok'
    assert health['membership_policy'] == 'registered_active'
    assert health['member_count'] is None
    for key, value in {'max_active': 8, 'max_waiting': 24, 'database_limit': 3,
                       'queue_timeout_seconds': 60.0, 'request_body_limit_bytes': 16777216}.items():
        assert health['concurrency'][key] == value, key


def promote(ops):
    """All recovery decisions are journaled; an existing attempt is never replayed."""
    candidate = new = None
    cutover = False
    try:
        ops.preflight()
        candidate = ops.prepare_candidate()
        ops.check_candidate(candidate)
        ops.stop_candidate(candidate)
        ops.preflight_again()
        ops.wait_drained(OLD)
        ops.mark('cutover_starting')
        cutover = True
        ops.stop_current()
        ops.detach_old()
        ops.rename_old()
        new = ops.create_current()
        ops.bind_start_current(new)
        ops.validate_current(new)
        ops.update_inventory(new)
        ops.mark('promoted', new_id=new, user_creation_acceptance='pending')
        return new
    except BaseException as error:
        ops.mark('failed', error_type=type(error).__name__, new_id=new)
        if cutover:
            try:
                ops.mark('recovery_started', new_id=new)
                ops.restore(new)
                ops.mark('restored', new_id=new)
            except BaseException as recovery_error:
                ops.mark('recovery_requires_attention', error_type=type(recovery_error).__name__, new_id=new)
                raise
        raise
    finally:
        if candidate:
            ops.stop_candidate(candidate)


class Ops:
    def __init__(self):
        # Reuse reviewed Docker/systemd primitives, never the previous release entry points.
        sys.path.insert(0, str(ROOT / 'tooling'))
        import relay_remote_runner as base
        self.base = base
        self.helper = base.RealOps()
        self.evidence = ROOT / 'evidence'
        self.state_path = self.evidence / 'release-stage.json'
        assert not self.state_path.exists(), 'existing release attempt; inspect before recovery, never replay'
        self.state = {}
        self.helper.store = self

    def read(self):
        return self.state

    def mark(self, stage, **fields):
        self.state.update(fields)
        self.state.update(stage=stage, at=datetime.now(timezone.utc).isoformat())
        self.base.core.atomic_write_json(self.state_path, self.state)
        self.base.core.atomic_write_json(self.evidence / ('stage-%02d.json' % self.state.get('sequence', 0)), self.state)
        self.state['sequence'] = self.state.get('sequence', 0) + 1

    def gates(self):
        for marker in ('/etc/smartbrain-maintenance.pending', '/run/smartbrain-maintenance.pending',
                       '/srv/smartbrain-backups/backups/.maintenance.pending'):
            assert not pathlib.Path(marker).exists(), 'maintenance pending'
        assert not list(pathlib.Path('/run').glob('smartbrain*intent*'))
        capacity = self.helper.read_static_capacity()
        self.base.core.validate_static_capacity(capacity, now=self.base.core.utc_now())
        backup = self.helper.backup_state()
        self.base.core.validate_backup_systemd_state(backup)
        receipt = json.loads((self.evidence / 'backup-verified.json').read_text())
        assert receipt['invocation_id'] == backup['InvocationID'] and receipt['verified'] is True
        assert (self.base.core.utc_now() - datetime.fromisoformat(receipt['verified_at'])).total_seconds() < 7200
        assert self.helper.verify_backup_registration() == 20
        return {'capacity': capacity, 'backup_invocation': backup['InvocationID']}

    def preflight(self):
        assert not self.state_path.exists(), 'existing attempt: inspect or recover, do not replay'
        assert not self.helper.container_exists(ROLLBACK_NAME)
        assert not self.helper.container_exists(CANDIDATE_NAME)
        self.built = json.loads((self.evidence / 'build-verified.json').read_text())
        tested = json.loads((self.evidence / 'tests-image.json').read_text())
        assert tested['exit_code'] == 0 and tested['image'] == self.built['image']
        assert self.built['base_image'] == IMAGE
        for name, sha in self.built['sources'].items():
            assert hashlib.sha256((ROOT / 'input' / name).read_bytes()).hexdigest() == sha
        self.old = self.helper.inspect(NAME)
        assert self.old['Id'] == OLD and self.old['Image'] == IMAGE
        assert self.old['State']['StartedAt'] == STARTED and self.old['State']['Running']
        self.helper.validate_unit(OLD)
        assert self.helper.source_sha(OLD) == PROXY_SHA
        self.unit_before = self.helper.read_unit_bytes()
        assert self.unit_before == self.base._unit_bytes(OLD), 'current unit differs from reviewed template'
        self.inventory_before = self.helper.read_inventory_bytes()
        assert json.loads(self.inventory_before)['container_id'] == OLD
        self.base.core.atomic_write_bytes(self.evidence / 'old-current.private.json', json.dumps(self.old).encode())
        self.base.core.atomic_write_bytes(self.evidence / 'old-current-unit.service', self.unit_before)
        self.base.core.atomic_write_bytes(self.evidence / 'old-inventory.private.json', self.inventory_before)
        self.mark('prepared', old_id=OLD, old_image=IMAGE, old_network=self.helper.network_shape_data(self.old),
                  old_fingerprint=self.helper.fingerprint_data(self.old), gates=self.gates())

    def config(self, candidate=False):
        config = self.base.clone_config(self.old, self.built['image'], candidate=candidate)
        config['Env'] = copy.deepcopy(self.old['Config']['Env'])
        if not candidate:
            config['Labels'] = dict(config.get('Labels') or {})
            config['Labels']['smartbrain.scope'] = RELEASE
        return config

    def prepare_candidate(self):
        cid = self.helper.create_container(CANDIDATE_NAME, self.config(candidate=True))
        self.mark('candidate_created', candidate_id=cid)
        try:
            self.helper.start_container(cid)
            self.helper.wait_running(cid)
        except BaseException:
            if self.helper.container_running(cid):
                self.helper.stop_container(cid)
            raise
        return cid

    def health(self, cid):
        container = self.helper.inspect(cid)
        ip = container['NetworkSettings']['Networks']['smartbrain_app']['IPAddress']
        with urllib.request.urlopen('http://' + ip + ':8000/health', timeout=5) as response:
            return json.load(response)

    def check_candidate(self, cid):
        validate_health(self.health(cid))
        for name, sha in self.built['sources'].items():
            actual = hashlib.sha256(self.base.run(['docker', 'exec', cid, 'cat', '/app/agentops/api/' + name])).hexdigest()
            assert actual == sha, 'candidate source drift'
        assert self.helper.source_sha(cid) == PROXY_SHA, 'proxy must stay unchanged'
        self.base.assert_relay_env(self.helper.inspect(cid)['Config'])
        ip = self.helper.inspect(cid)['NetworkSettings']['Networks']['smartbrain_app']['IPAddress']
        assert self.helper.request_status('http://' + ip + ':8000/v1/models') == 401
        assert self.helper.request_status('http://' + ip + ':8000/v4/ai-gateway/keys') == 401
        self.mark('source_health_verified', checked_id=cid)

    def stop_candidate(self, cid):
        if self.helper.container_running(cid):
            self.wait_drained(cid)
            self.helper.stop_container(cid)

    def preflight_again(self):
        self.gates()
        now = self.helper.inspect(NAME)
        assert now['Id'] == OLD and now['State']['StartedAt'] == STARTED and now['State']['Running']
        assert self.helper.fingerprint_data(now) == self.state['old_fingerprint']
        assert self.helper.read_unit_bytes() == self.unit_before
        assert self.helper.read_inventory_bytes() == self.inventory_before

    def wait_drained(self, cid):
        for _ in range(300):
            if self.base.runtime_drained(self.health(cid)):
                time.sleep(1)
                if self.base.runtime_drained(self.health(cid)):
                    return
            time.sleep(1)
        raise RuntimeError('active requests remain; refusing stop')

    def stop_current(self):
        self.helper.stop_unit()
        assert not self.helper.container_running(OLD)
        self.mark('old_stopped')

    def detach_old(self):
        self.helper.detach_container(OLD)
        self.mark('old_detached')

    def rename_old(self):
        self.helper.rename_container(OLD, ROLLBACK_NAME)
        self.mark('old_renamed')

    def create_current(self):
        self.mark('new_create_planned', planned_new_name=NAME, planned_new_image=self.built['image'])
        cid = self.helper.create_container(NAME, self.config())
        self.mark('new_created', new_id=cid)
        return cid

    def bind_start_current(self, cid):
        self.helper.write_unit(self.base._unit_bytes(cid))
        self.helper.daemon_reload()
        self.mark('unit_bound', new_id=cid)
        self.helper.start_unit()
        self.helper.wait_running(cid)
        self.mark('new_running', new_id=cid)

    def validate_current(self, cid):
        self.check_candidate(cid)
        current = self.helper.inspect(cid)
        assert current['Image'] == self.built['image']
        assert current['HostConfig'] == self.old['HostConfig']
        assert self.helper.network_shape_data(current) == self.state['old_network']
        expected = copy.deepcopy(self.old['Config'])
        actual = copy.deepcopy(current['Config'])
        for value in (expected, actual):
            value.pop('Image', None)
            value.pop('Hostname', None)
            value.get('Labels', {}).pop('smartbrain.scope', None)
        assert actual == expected, 'unexpected runtime Config change'
        unit = self.helper.validate_unit(cid)
        statuses = {}
        for path, status in {'/login': 200, '/health/ready': 200, '/v4/ai-gateway/keys': 401,
                             '/v4/personal-api/v1/models': 401, '/v4/personal-api/v1/responses': 401}.items():
            statuses[path] = self.helper.request_status('https://39.105.79.0' + path)
            assert statuses[path] == status, path
        assert self.helper.request_status('http://192.168.10.146:9000/v1/models') == 403
        assert self.helper.request_status('http://192.168.10.146:9000/v1/models', headers={'X-SmartBrain-Gateway-Proxy': 'personal-api'}) == 401
        self.gates()
        self.mark('runtime_verified', new_id=cid, public_statuses=statuses,
                  unit={k:unit[k] for k in ('ActiveState', 'SubState', 'MainPID', 'InvocationID', 'UnitFileState')})

    def update_inventory(self, cid):
        value = json.loads(self.inventory_before)
        value.update(observed_at=datetime.now(timezone.utc).isoformat(), container_id=cid,
                     image_id=self.built['image'], configuration_sha256=self.helper.fingerprint(cid),
                     previous_container_id=OLD, previous_image_id=IMAGE, release=RELEASE,
                     scope='supplemental exact runtime preservation; not full frozen coordinator')
        self.helper.write_inventory(json.dumps(value, indent=2).encode() + b'\n')
        assert json.loads(self.helper.read_inventory_bytes())['container_id'] == cid

    def restore(self, new):
        # Discover a created successor even if the Docker response was lost.
        owner = self.helper.name_owner(NAME)
        if owner == OLD and self.helper.container_running(OLD):
            if (self.helper.fingerprint(OLD) == self.state['old_fingerprint']
                    and self.helper.network_shape(OLD) == self.state['old_network']
                    and self.helper.read_unit_bytes() == self.unit_before
                    and self.helper.read_inventory_bytes() == self.inventory_before):
                self.helper.validate_unit(OLD)
                return
        if new is None and owner not in (None, OLD):
            candidate = self.helper.inspect(owner)
            assert candidate['Image'] == self.built['image'] and candidate['Config']['Labels']['smartbrain.scope'] == RELEASE
            new = owner
            self.state['new_id'] = new
        if new and self.helper.container_running(new):
            self.wait_drained(new)
        self.helper.stop_unit()
        if new:
            self.helper.stop_container(new)
            self.helper.detach_container(new)
            if self.helper.container_name(new).lstrip('/') == NAME:
                self.helper.rename_container(new, NAME + '-failed-registration-20261019-r4')
        if self.helper.container_name(OLD).lstrip('/') != NAME:
            self.helper.rename_container(OLD, NAME)
        networks = self.helper.inspect(OLD)['NetworkSettings']['Networks']
        for network, endpoint in self.state['old_network'].items():
            if network not in networks:
                self.helper.connect_network(OLD, network, endpoint)
        self.helper.write_unit(self.unit_before)
        self.helper.write_inventory(self.inventory_before)
        self.helper.daemon_reload()
        self.helper.reset_failed_unit()
        self.helper.start_unit()
        self.helper.wait_running(OLD)
        self.helper.validate_unit(OLD)
        assert self.helper.fingerprint(OLD) == self.state['old_fingerprint']
        assert self.helper.network_shape(OLD) == self.state['old_network']
        assert self.helper.source_sha(OLD) == PROXY_SHA


if __name__ == '__main__':
    ops = Ops()
    with ops.helper.acquire_locks(), ops.base.termination_as_exception():
        promote(ops)
    print(json.dumps(ops.state))
