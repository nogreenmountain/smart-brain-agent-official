import importlib
import uuid
from contextlib import contextmanager


def worker():
    return importlib.import_module("agentops_local.ai_usage.llm_key_reconcile_worker")


class FakeLock:
    def __init__(self, acquired=True):
        self.acquired = acquired
        self.closed = False

    def __enter__(self):
        return self.acquired

    def __exit__(self, *_):
        self.closed = True


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result if result is not None else []
        self.error = error
        self.closed = False
        self.calls = []

    def reconcile_pending(self, *, limit):
        self.calls.append(limit)
        if self.error:
            raise self.error
        return self.result

    def close(self):
        self.closed = True


class FakeOrm:
    pass


def fake_session_scope(orm):
    @contextmanager
    def scope():
        yield orm

    return scope()


def test_run_once_uses_advisory_lock_and_closes_service(monkeypatch):
    m = worker()
    monkeypatch.setenv("SB_LLM_GATEWAY_INSTANCE_ID", str(uuid.uuid4()))
    service = FakeService([{"status": "confirmed"}])
    lock = FakeLock(acquired=True)
    monkeypatch.setattr(m, "session_scope", lambda: fake_session_scope(FakeOrm()))
    monkeypatch.setattr(m, "build_service", lambda *_args, **_kwargs: service)
    monkeypatch.setattr(m, "instance_advisory_lock", lambda *_args, **_kwargs: lock)

    assert m.run_once(limit=7) == [{"status": "confirmed"}]
    assert service.calls == [7]
    assert service.closed is True
    assert lock.closed is True


def test_run_once_skips_when_another_worker_holds_lock(monkeypatch):
    m = worker()
    monkeypatch.setenv("SB_LLM_GATEWAY_INSTANCE_ID", str(uuid.uuid4()))
    service = FakeService()
    lock = FakeLock(acquired=False)
    monkeypatch.setattr(m, "session_scope", lambda: fake_session_scope(FakeOrm()))
    monkeypatch.setattr(m, "build_service", lambda *_args, **_kwargs: service)
    monkeypatch.setattr(m, "instance_advisory_lock", lambda *_args, **_kwargs: lock)

    assert m.run_once(limit=25) == []
    assert service.calls == []
    assert service.closed is True


def test_run_once_closes_lock_and_service_when_reconcile_fails(monkeypatch):
    m = worker()
    monkeypatch.setenv("SB_LLM_GATEWAY_INSTANCE_ID", str(uuid.uuid4()))
    service = FakeService(error=RuntimeError("temporary"))
    lock = FakeLock(acquired=True)
    monkeypatch.setattr(m, "session_scope", lambda: fake_session_scope(FakeOrm()))
    monkeypatch.setattr(m, "build_service", lambda *_args, **_kwargs: service)
    monkeypatch.setattr(m, "instance_advisory_lock", lambda *_args, **_kwargs: lock)

    try:
        m.run_once(limit=25)
    except RuntimeError:
        pass
    else:
        raise AssertionError("run_once must surface reconcile errors")
    assert service.closed is True
    assert lock.closed is True
