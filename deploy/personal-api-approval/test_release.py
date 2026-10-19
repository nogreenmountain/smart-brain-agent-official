import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('registration_release', Path(__file__).with_name('release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class FakeOps:
    def __init__(self, fail=None, recovery_fails=False):
        self.fail = fail
        self.recovery_fails = recovery_fails
        self.calls = []
        self.stages = []

    def mark(self, stage, **fields):
        self.stages.append(stage)

    def __getattr__(self, name):
        def action(*args):
            self.calls.append(name)
            if self.fail == name or name == 'restore' and self.recovery_fails:
                raise RuntimeError('synthetic fault')
            if name == 'prepare_candidate':
                return 'candidate'
            if name == 'create_current':
                return 'successor'
        return action


def test_success_finishes_only_after_runtime_and_inventory():
    ops = FakeOps()
    assert release.promote(ops) == 'successor'
    assert ops.stages[-1] == 'promoted'
    assert ops.calls.index('validate_current') < ops.calls.index('update_inventory')
    assert ops.calls.index('wait_drained') < ops.calls.index('stop_current')
    assert 'restore' not in ops.calls and ops.calls[-1] == 'stop_candidate'


@pytest.mark.parametrize('where', ['preflight', 'prepare_candidate', 'check_candidate', 'preflight_again', 'wait_drained'])
def test_before_cutover_failure_never_restarts_existing_service(where):
    ops = FakeOps(fail=where)
    with pytest.raises(RuntimeError):
        release.promote(ops)
    assert 'stop_current' not in ops.calls and 'restore' not in ops.calls
    assert 'promoted' not in ops.stages


@pytest.mark.parametrize('where', ['stop_current', 'detach_old', 'rename_old', 'create_current',
                                  'bind_start_current', 'validate_current', 'update_inventory'])
def test_after_cutover_failure_runs_one_restore(where):
    ops = FakeOps(fail=where)
    with pytest.raises(RuntimeError):
        release.promote(ops)
    assert ops.calls.count('restore') == 1
    assert ops.stages[-2:] == ['recovery_started', 'restored']
    assert 'promoted' not in ops.stages


def test_failed_recovery_is_recorded_without_retry_loop():
    ops = FakeOps(fail='validate_current', recovery_fails=True)
    with pytest.raises(RuntimeError):
        release.promote(ops)
    assert ops.calls.count('restore') == 1
    assert ops.stages[-1] == 'recovery_requires_attention'


@pytest.mark.parametrize('field,value', [('membership_policy', 'release_allowlist'), ('member_count', 26), ('status', 'failed')])
def test_old_or_unhealthy_runtime_never_passes(field, value):
    health = {'status': 'ok', 'membership_policy': 'registered_active', 'member_count': None,
              'concurrency': {'max_active': 8, 'max_waiting': 24, 'database_limit': 3,
                              'queue_timeout_seconds': 60., 'request_body_limit_bytes': 16777216}}
    release.validate_health(health)
    health[field] = value
    with pytest.raises(AssertionError):
        release.validate_health(health)


def test_restore_does_not_restart_untouched_old_service():
    ops = release.Ops.__new__(release.Ops)
    ops.state = {'old_fingerprint': 'old', 'old_network': {'app': {}}}
    ops.unit_before = b'unit'
    ops.inventory_before = b'inventory'
    checks = []
    ops.helper = SimpleNamespace(name_owner=lambda name: release.OLD,
        container_running=lambda cid: True, fingerprint=lambda cid: 'old',
        network_shape=lambda cid: {'app': {}}, read_unit_bytes=lambda: b'unit',
        read_inventory_bytes=lambda: b'inventory', validate_unit=lambda cid: checks.append(cid))
    ops.restore(None)
    assert checks == [release.OLD]


def test_rollback_does_not_stop_an_active_successor():
    ops = release.Ops.__new__(release.Ops)
    ops.state = {}
    stopped = []
    ops.helper = SimpleNamespace(name_owner=lambda name: 'new', container_running=lambda cid: True,
                                 stop_unit=lambda: stopped.append(True))
    def busy(cid):
        raise RuntimeError('active requests')
    ops.wait_drained = busy
    with pytest.raises(RuntimeError, match='active requests'):
        ops.restore('new')
    assert stopped == []


def test_overlay_sources_are_readable_by_the_runtime_user():
    dockerfile = Path(__file__).with_name('Dockerfile').read_text()
    for source in ('ai_gateway.py',):
        assert 'COPY --chown=10001:10001 --chmod=0644 ' + source in dockerfile
    assert dockerfile.rstrip().endswith('USER 10001:10001')


def test_restore_releases_docker_slash_prefixed_successor_name():
    ops = release.Ops.__new__(release.Ops)
    ops.state = {'old_fingerprint': 'old', 'old_network': {}}
    ops.unit_before, ops.inventory_before = b'unit', b'inventory'
    names = {'new': '/' + release.NAME, release.OLD: '/' + release.ROLLBACK_NAME}
    def rename(cid, name):
        assert '/' + name not in names.values(), 'Docker name is still occupied'
        names[cid] = '/' + name
    ops.helper = SimpleNamespace(
        name_owner=lambda name: 'new', container_running=lambda cid: False,
        stop_unit=lambda: None, stop_container=lambda cid: None, detach_container=lambda cid: None,
        container_name=lambda cid: names[cid], rename_container=rename,
        inspect=lambda cid: {'NetworkSettings': {'Networks': {}}},
        write_unit=lambda value: None, write_inventory=lambda value: None,
        daemon_reload=lambda: None, reset_failed_unit=lambda: None, start_unit=lambda: None,
        wait_running=lambda cid: None, validate_unit=lambda cid: None,
        fingerprint=lambda cid: 'old', network_shape=lambda cid: {},
        source_sha=lambda cid: release.PROXY_SHA)
    ops.restore('new')
    assert names[release.OLD] == '/' + release.NAME
    assert names['new'] != '/' + release.NAME


def test_new_attempt_has_its_own_candidate_identity():
    assert release.CANDIDATE_NAME == 'smartbrain-approval-ready-' + release.RELEASE.removeprefix('personal-api-approval-')
    assert release.ROLLBACK_NAME == release.NAME + '-rollback-' + release.RELEASE.removeprefix('personal-api-')
