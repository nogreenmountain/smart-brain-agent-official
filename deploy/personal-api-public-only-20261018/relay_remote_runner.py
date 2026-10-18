"""Remote production runner for the personal relay-auth release.

The module keeps orchestration functions importable for offline fault-injection
tests.  Linux-specific operations are provided by :class:`RealOps` below and
are instantiated only by ``main()``.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import http.client
import json
import os
import pathlib
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Iterator, Mapping

import relay_release_core as core


NAME = "smartbrain-personal-key-api-20260923-filter-internal-r1"
OLD_NAME = NAME + "-rollback-public-only-20261018-r1"
FAILED_NAME_PREFIX = NAME + "-failed-public-only-20261018-r1-"
CANDIDATE_NAME = "smartbrain-public-only-ready-20261018-r1"
UNIT = "smartbrain-personal-gateway-current.service"
UNIT_PATH = pathlib.Path("/etc/systemd/system") / UNIT
INVENTORY_PATH = pathlib.Path(
    "/etc/smartbrain/runtime-inventory/request-project-attribution-20261009.json"
)
RELEASE_DIR = pathlib.Path("/srv/smartbrain/releases/personal-api-public-only-20261018-r1")
EVIDENCE_DIR = RELEASE_DIR / "evidence"
ROLLBACK_DIR = RELEASE_DIR / "rollback"
STAGE_PATH = EVIDENCE_DIR / "release-stage.json"
FRESH_BACKUP_RECEIPT_PATH = EVIDENCE_DIR / "fresh-backup-receipt.json"
WINDOWS_READY_RECEIPT_PATH = EVIDENCE_DIR / "windows-ready-receipt.json"
AUTH_SMOKE_RECEIPT_PATH = EVIDENCE_DIR / "authenticated-smoke-receipt.json"
CANDIDATE_RESULT_PATH = pathlib.Path(
    "/srv/smartbrain/acceptance/personal-api-relay-auth-20261017/candidate-result.json"
)
CANDIDATE_SOURCE_PATH = pathlib.Path(
    "/srv/smartbrain/acceptance/personal-api-relay-auth-20261017/"
    "candidate-input/personal_gateway_proxy.py"
)
CAPACITY_CHECKER = pathlib.Path(
    "/srv/smartbrain/releases/ubuntu-2026.08.29-next-major-r2-backup-20260923/"
    "deploy/ubuntu/check-backup-capacity.py"
)
STACK_ENV = CAPACITY_CHECKER.parent / ".env"
BACKUP_ROOT = pathlib.Path("/srv/smartbrain-backups/backups")
SOURCE_PATH = "/app/agentops/api/personal_gateway_proxy.py"
RELAY_MODE = "smartbrain_relay"
RELAY_URL = "http://192.168.10.146:9000"
EXPECTED_OLD_ID = "7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20"
EXPECTED_OLD_IMAGE = "sha256:532a68da4610413d60bfc861addfb341a7a862bc6819964aa3bfe218cecbf6cc"
EXPECTED_OLD_STARTED_AT = "2026-10-17T13:44:51.228032986Z"
BACKUP_LOCK = pathlib.Path("/srv/smartbrain-backups/backups/.backup.lock")
MAINTENANCE_LOCK = pathlib.Path("/run/lock/smartbrain-maintenance.lock")
PENDING_MARKER = pathlib.Path("/etc/smartbrain-maintenance.pending")

UNIT_SYSTEMD_FIELDS = (
    "ActiveState",
    "SubState",
    "UnitFileState",
    "Result",
    "MainPID",
    "ControlPID",
    "Job",
    "InvocationID",
    "ExecStart",
)


def validate_release_gates(
    ops: Any,
    backup_receipt: Mapping[str, Any],
    windows_receipt: Mapping[str, Any],
    *,
    now: datetime,
    backup_root: pathlib.Path,
) -> dict[str, Any]:
    """Validate every mutable gate before any Docker mutation."""

    backup = core.validate_fresh_backup_receipt(
        backup_receipt,
        ops.backup_state(),
        now=now,
        backup_root=backup_root,
    )
    windows = core.validate_windows_ready_receipt(windows_receipt, now=now)
    static_capacity = core.validate_static_capacity(ops.read_static_capacity(), now=now)
    if ops.verify_backup_registration() != 20:
        raise core.GateError("backup registration count is not 20")
    return {"backup": backup, "windows": windows, "static_capacity": static_capacity}


def _verified_backup(path_value: Any, digest_value: Any, label: str) -> bytes:
    if not isinstance(path_value, str):
        raise core.GateError(f"{label} backup path is missing")
    path = pathlib.Path(path_value)
    if not path.is_file():
        raise core.GateError(f"{label} backup file is missing")
    payload = path.read_bytes()
    if core.sha256_bytes(payload) != digest_value:
        raise core.GateError(f"{label} backup hash does not match")
    return payload


def _unique_failed_name(ops: Any, new_id: str) -> str:
    base = FAILED_NAME_PREFIX + new_id[:12]
    if ops.name_owner(base) in (None, new_id):
        return base
    for suffix in range(1, 100):
        candidate = f"{base}-{suffix}"
        if ops.name_owner(candidate) in (None, new_id):
            return candidate
    raise core.GateError("no collision-free failed container name is available")


def _verify_restored(ops: Any, state: Mapping[str, Any]) -> dict[str, Any]:
    old_id = str(state["old_id"])
    if ops.container_name(old_id) != "/" + NAME:
        raise core.GateError("old container name was not restored")
    ops.wait_running(old_id)
    if ops.fingerprint(old_id) != state.get("old_fingerprint"):
        raise core.GateError("old container fingerprint changed during recovery")
    if ops.network_shape(old_id) != state.get("old_network"):
        raise core.GateError("old container network identity was not restored")
    ops.validate_restored_unit(old_id)
    public = ops.validate_restored_public()
    if public.get("health") != 200 or public.get("anonymous_models") != 401:
        raise core.GateError("restored public boundary verification failed")
    return dict(public)


def _discover_planned_new_container(
    ops: Any,
    state: Mapping[str, Any],
    old_id: str,
) -> str | None:
    """Recover a create result only from the persisted exact-name intent."""

    if state.get("planned_new_name") != NAME:
        return None
    owner = ops.name_owner(NAME)
    if owner in (None, old_id):
        return None
    if not isinstance(owner, str) or not owner:
        raise core.GateError("planned new container identity is invalid")
    candidate = ops.inspect(owner)
    config = candidate.get("Config")
    labels = config.get("Labels") if isinstance(config, Mapping) else None
    created = core.parse_timestamp(
        candidate.get("Created"), "planned new container created timestamp"
    )
    intent_at = core.parse_timestamp(
        state.get("new_create_intent_at"), "new container create intent timestamp"
    )
    if (
        candidate.get("Id") != owner
        or candidate.get("Name") != "/" + NAME
        or candidate.get("Image") != state.get("planned_new_image")
        or not isinstance(labels, Mapping)
        or labels.get("smartbrain.scope") != core.RELEASE
        or created < intent_at
    ):
        raise core.GateError("planned new container identity does not match create intent")
    return owner


def _promoted_report_bytes(report: Mapping[str, Any]) -> bytes:
    core.reject_raw_secrets(report)
    return json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _materialize_promoted_evidence(
    ops: Any,
    state: Mapping[str, Any],
    *,
    verify_runtime: bool = True,
) -> dict[str, Any]:
    """Verify the authoritative promoted stage and derive promoted.json."""

    if state.get("stage") != "promoted":
        raise core.GateError("release stage is not promoted")
    report = state.get("promoted_report")
    if not isinstance(report, Mapping):
        raise core.GateError("promoted stage is missing its complete report")
    normalized = dict(report)
    if (
        normalized.get("schema") != "smartbrain.personal-relay-promoted/v1"
        or normalized.get("release") != core.RELEASE
        or normalized.get("status") != "passed"
        or normalized.get("new_id") != state.get("new_id")
        or normalized.get("old_id") != state.get("old_id")
    ):
        raise core.GateError("promoted report identity does not match the terminal stage")
    expected_digest = state.get("promoted_report_sha256")
    actual_digest = core.sha256_bytes(_promoted_report_bytes(normalized))
    if expected_digest != actual_digest:
        raise core.GateError("promoted report digest does not match the terminal stage")
    if verify_runtime:
        new_id = state.get("new_id")
        if not isinstance(new_id, str) or not new_id:
            raise core.GateError("promoted stage is missing the new container identity")
        current_runtime = ops.validate_promoted_runtime(new_id)
        if current_runtime != normalized.get("runtime"):
            raise core.GateError("promoted runtime differs from the terminal report")
    ops.write_promoted(normalized)
    return normalized


def _settle_existing_restoration(
    ops: Any,
    store: core.StageStore,
    state: Mapping[str, Any],
    *,
    reason: str,
    unit_bytes: bytes,
    inventory_bytes: bytes,
) -> dict[str, Any]:
    """Commit a verified completed rollback without restarting healthy production."""

    if state.get("stage") != "recovery_failed":
        raise core.GateError("recovery settlement requires the recovery_failed stage")
    old_id = str(state.get("old_id") or "")
    if not old_id:
        raise core.GateError("persisted old container identity is missing")
    if ops.name_owner(NAME) != old_id:
        raise core.GateError("production container name is not owned by the restored old container")
    if ops.read_unit_bytes() != unit_bytes:
        raise core.GateError("restored unit bytes differ from the verified rollback")
    if ops.read_inventory_bytes() != inventory_bytes:
        raise core.GateError("restored inventory bytes differ from the verified rollback")

    new_id = state.get("new_id")
    if not isinstance(new_id, str) or not new_id:
        raise core.GateError("persisted new container identity is missing")
    if not ops.container_exists(new_id):
        raise core.GateError(
            "persisted new container is unavailable during recovery settlement"
        )
    if ops.container_running(new_id):
        raise core.GateError("persisted new container is still running")
    if ops.network_shape(new_id):
        raise core.GateError("persisted new container is still attached to a network")
    if not ops.container_name(new_id).startswith("/" + FAILED_NAME_PREFIX):
        raise core.GateError("persisted new container does not have the reviewed failed name")

    candidate_id = state.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise core.GateError("persisted candidate container identity is missing")
    if not ops.container_exists(candidate_id):
        raise core.GateError(
            "persisted candidate container is unavailable during recovery settlement"
        )
    if ops.container_running(candidate_id):
        raise core.GateError("persisted candidate container is still running")
    if ops.container_name(candidate_id) == "/" + NAME:
        raise core.GateError("persisted candidate container owns the production name")

    public = _verify_restored(ops, state)
    return store.write(
        "restored",
        recovery_reason=reason,
        resumed_from="recovery_failed",
        restored_public=public,
        settled_existing_restoration=True,
    )


def recover_release(
    ops: Any,
    store: core.StageStore,
    *,
    reason: str,
) -> dict[str, Any]:
    """Idempotently restore the exact old runtime from any destructive stage."""

    state = store.read()
    if state is None:
        raise core.GateError("release stage is missing; automatic recovery is unsafe")
    if state.get("stage") == "restored":
        _verify_restored(ops, state)
        return state
    if state.get("stage") == "promoted":
        _materialize_promoted_evidence(ops, state)
        return state

    old_id = str(state.get("old_id") or "")
    if not old_id or not ops.container_exists(old_id):
        raise core.GateError("old container is unavailable for recovery")
    unit_bytes = _verified_backup(
        state.get("unit_backup_path"), state.get("unit_backup_sha256"), "unit"
    )
    inventory_bytes = _verified_backup(
        state.get("inventory_backup_path"),
        state.get("inventory_backup_sha256"),
        "inventory",
    )
    if state.get("stage") == "recovery_failed":
        return _settle_existing_restoration(
            ops,
            store,
            state,
            reason=reason,
            unit_bytes=unit_bytes,
            inventory_bytes=inventory_bytes,
        )

    new_id = state.get("new_id")
    if not isinstance(new_id, str) or not new_id:
        planned_owner = _discover_planned_new_container(ops, state, old_id)
        if planned_owner is not None:
            new_id = planned_owner
            state = store.write(
                "new_discovered_for_recovery",
                new_id=new_id,
                discovered_new_name=NAME,
            )

    resume_from = str(state.get("stage", "unknown"))
    store.write("recovery_started", recovery_reason=reason, resume_from=resume_from)
    try:
        ops.stop_unit()
        if isinstance(new_id, str) and new_id and ops.container_exists(new_id):
            ops.stop_container(new_id)
            ops.detach_container(new_id)
            if ops.container_name(new_id) == "/" + NAME:
                ops.rename_container(new_id, _unique_failed_name(ops, new_id))

        owner = ops.name_owner(NAME)
        if owner not in (None, old_id):
            raise core.GateError("production container name is owned by an unexpected container")
        if ops.container_name(old_id) != "/" + NAME:
            ops.rename_container(old_id, NAME)

        expected_network = state.get("old_network")
        if not isinstance(expected_network, Mapping):
            raise core.GateError("old network receipt is missing")
        current_network = ops.network_shape(old_id)
        for network_name, endpoint in expected_network.items():
            if current_network.get(network_name) != endpoint:
                if network_name in current_network:
                    ops.disconnect_network(old_id, network_name)
                ops.connect_network(old_id, network_name, dict(endpoint))

        ops.write_unit(unit_bytes)
        ops.write_inventory(inventory_bytes)
        ops.daemon_reload()
        ops.reset_failed_unit()
        ops.start_unit()
        public = _verify_restored(ops, state)
        return store.write(
            "restored",
            recovery_reason=reason,
            resumed_from=resume_from,
            restored_public=public,
        )
    except BaseException as error:
        store.write(
            "recovery_failed",
            recovery_reason=reason,
            resume_from=resume_from,
            recovery_error_type=type(error).__name__,
        )
        raise


def finalize_release(
    ops: Any,
    store: core.StageStore,
    receipt: Mapping[str, Any],
    *,
    now: datetime,
) -> dict[str, Any]:
    """Finalize only after an authenticated direct and public 200 smoke."""

    state = store.read()
    if state is not None and state.get("stage") == "promoted":
        _materialize_promoted_evidence(ops, state)
        return state
    if state is None or state.get("stage") != "awaiting_smoke":
        raise core.GateError("release is not awaiting authenticated smoke")
    new_id = state.get("new_id")
    if not isinstance(new_id, str) or not new_id:
        raise core.GateError("awaiting-smoke stage is missing the new container identity")
    awaiting_at = core.parse_timestamp(
        state.get("awaiting_smoke_at"), "stage awaiting_smoke_at"
    )
    smoke = core.validate_auth_smoke_receipt(
        receipt,
        now=now,
        awaiting_at=awaiting_at,
        new_container_id=new_id,
    )
    runtime = ops.validate_promoted_runtime(new_id)
    report = {
        "schema": "smartbrain.personal-relay-promoted/v1",
        "release": core.RELEASE,
        "status": "passed",
        "finalized_at": now.astimezone(timezone.utc).isoformat(),
        "new_id": new_id,
        "old_id": state.get("old_id"),
        "candidate_image": state.get("candidate_image"),
        "candidate_source_sha256": state.get("candidate_source_sha256"),
        "authenticated_smoke": smoke,
        "runtime": runtime,
    }
    report_digest = core.sha256_bytes(_promoted_report_bytes(report))
    try:
        committed = store.write(
            "promoted",
            finalized_at=report["finalized_at"],
            authenticated_smoke=smoke,
            finalized_runtime=runtime,
            promoted_report=report,
            promoted_report_sha256=report_digest,
        )
        _materialize_promoted_evidence(ops, committed, verify_runtime=False)
        return committed
    except BaseException:
        committed = store.read()
        if committed is not None and committed.get("stage") == "promoted":
            _materialize_promoted_evidence(ops, committed)
            return committed
        raise


# Keeping the tested contracts above free of subprocess assumptions makes
# failure injection deterministic.  The code below is the actual Linux layer.


def run(
    args: list[str],
    *,
    input_bytes: bytes | None = None,
    timeout: int = 60,
) -> bytes:
    result = subprocess.run(
        args,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        # Command output can contain private Docker create parameters or paths.
        raise RuntimeError(f"command failed with exit {result.returncode}: {args[0]}")
    return result.stdout


class DockerHTTP(http.client.HTTPConnection):
    def __init__(self) -> None:
        super().__init__("localhost", timeout=90)

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect("/var/run/docker.sock")


class TerminationRequested(RuntimeError):
    """Raised when systemd asks the release runner to stop."""


@contextlib.contextmanager
def termination_as_exception(*, signal_module: Any = signal) -> Iterator[None]:
    """Route SIGTERM through the normal exception/recovery state machine."""

    previous = signal_module.getsignal(signal_module.SIGTERM)

    def handle(signum: int, frame: Any) -> None:
        raise TerminationRequested("release runner received SIGTERM")

    signal_module.signal(signal_module.SIGTERM, handle)
    try:
        yield
    finally:
        signal_module.signal(signal_module.SIGTERM, previous)


def docker_api(method: str, path: str, payload: Any = None) -> Any:
    connection = DockerHTTP()
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    connection.request(method, "/v1.52" + path, body=body, headers={"Content-Type": "application/json"})
    response = connection.getresponse()
    data = response.read()
    connection.close()
    if response.status >= 300:
        raise RuntimeError(f"Docker API {method} {path.split('?', 1)[0]} failed HTTP {response.status}")
    return json.loads(data) if data else None


def set_relay_env(config: dict[str, Any]) -> dict[str, Any]:
    env = [
        item
        for item in (config.get("Env") or [])
        if not item.startswith("SB_PERSONAL_UPSTREAM_AUTH_MODE=")
        and not item.startswith("SB_PERSONAL_UPSTREAM_URL=")
    ]
    env.extend(
        [
            "SB_PERSONAL_UPSTREAM_AUTH_MODE=" + RELAY_MODE,
            "SB_PERSONAL_UPSTREAM_URL=" + RELAY_URL,
        ]
    )
    config["Env"] = env
    return config


def env_value(config: Mapping[str, Any], name: str) -> str | None:
    prefix = name + "="
    for item in config.get("Env") or []:
        if isinstance(item, str) and item.startswith(prefix):
            return item[len(prefix) :]
    return None


def assert_relay_env(config: Mapping[str, Any]) -> None:
    if env_value(config, "SB_PERSONAL_UPSTREAM_AUTH_MODE") != RELAY_MODE:
        raise core.GateError("promoted Config.Env did not set relay auth mode")
    if env_value(config, "SB_PERSONAL_UPSTREAM_URL") != RELAY_URL:
        raise core.GateError("promoted Config.Env did not set trusted relay URL")


def clone_config(old: Mapping[str, Any], image: str, *, candidate: bool = False) -> dict[str, Any]:
    config = copy.deepcopy(old["Config"])
    config["Image"] = image
    config["Hostname"] = ""
    host = copy.deepcopy(old["HostConfig"])
    host.pop("Links", None)
    if candidate:
        host["RestartPolicy"] = {"Name": "no", "MaximumRetryCount": 0}
        host["PortBindings"] = {}
        host["PublishAllPorts"] = False
        config["Labels"] = {
            key: value
            for key, value in (config.get("Labels") or {}).items()
            if not key.startswith("com.docker.compose.")
        }
    networks: dict[str, Any] = {}
    for network_name, endpoint in old["NetworkSettings"]["Networks"].items():
        new_endpoint: dict[str, Any] = {}
        if not candidate:
            if endpoint.get("IPAddress"):
                new_endpoint["IPAMConfig"] = {"IPv4Address": endpoint["IPAddress"]}
            new_endpoint["Aliases"] = [
                alias
                for alias in (endpoint.get("Aliases") or [])
                if alias not in (old["Id"], old["Id"][:12])
            ]
        networks[network_name] = new_endpoint
    config["HostConfig"] = host
    config["NetworkingConfig"] = {"EndpointsConfig": networks}
    return set_relay_env(config)


def runtime_drained(health):
    if not isinstance(health, dict) or health.get('status') != 'ok':
        return False
    counters = health.get('concurrency', {})
    expected = {'active': 0, 'waiting': 0, 'database_in_use': 0,
                'max_active': 8, 'max_waiting': 24, 'database_limit': 3}
    return all(type(counters.get(k)) is int and counters[k] == v for k, v in expected.items())


class RealOps:
    def __init__(self) -> None:
        self.store = core.StageStore(STAGE_PATH)

    @contextlib.contextmanager
    def acquire_locks(self) -> Iterator[None]:
        import fcntl

        handles = []
        try:
            for path in (BACKUP_LOCK, MAINTENANCE_LOCK):
                handle = path.open("a")
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BaseException:
                    handle.close()
                    raise core.GateError(f"release lock is held: {path}")
                handles.append(handle)
            yield
        finally:
            for handle in reversed(handles):
                try:
                    fcntl.flock(handle, fcntl.LOCK_UN)
                finally:
                    handle.close()

    def systemd_state(self, unit: str, fields: tuple[str, ...]) -> dict[str, str]:
        args = ["systemctl", "show", unit]
        for field in fields:
            args.extend(["-p", field])
        output = run(args).decode("utf-8", errors="strict")
        return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)

    def backup_state(self) -> dict[str, str]:
        return self.systemd_state("smartbrain-backup.service", core.BACKUP_SYSTEMD_FIELDS)

    def run_dynamic_capacity(self) -> dict[str, Any]:
        checker_sha = core.sha256_file(CAPACITY_CHECKER)
        if checker_sha != core.EXPECTED_CAPACITY_CHECKER_SHA256:
            raise core.GateError("live dynamic capacity checker SHA does not match")
        if not STACK_ENV.is_file():
            raise core.GateError("stack environment file is missing")
        command = [
            "/usr/bin/bash",
            "-c",
            'set -a; . "$1"; exec /usr/bin/python3 "$2"',
            "capacity-check",
            str(STACK_ENV),
            str(CAPACITY_CHECKER),
        ]
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=600,
            check=False,
        )
        if result.returncode != 0:
            raise core.GateError("live dynamic capacity check is blocked")
        return {
            "checker_sha256": checker_sha,
            "checked_at": core.utc_now().isoformat(),
            "exit_code": 0,
            "backup_free_bytes": shutil.disk_usage(BACKUP_ROOT).free,
        }

    def read_static_capacity(self) -> dict[str, Any]:
        memory_line = next(
            (
                line
                for line in pathlib.Path("/proc/meminfo").read_text(encoding="utf-8").splitlines()
                if line.startswith("MemAvailable:")
            ),
            "",
        )
        fields = memory_line.split()
        if len(fields) < 2 or not fields[1].isdigit():
            raise core.GateError("cannot read available memory")
        return {
            "checked_at": core.utc_now().isoformat(),
            "disk_free_bytes": {
                path: shutil.disk_usage(path).free
                for path in core.STATIC_DISK_THRESHOLDS
            },
            "memory_available_bytes": int(fields[1]) * 1024,
        }

    def verify_backup_registration(self) -> int:
        import importlib.util

        deploy = pathlib.Path(
            "/srv/smartbrain/releases/ubuntu-2026.08.29-next-major-r2-backup-20260923/"
            "deploy/ubuntu"
        )
        spec = importlib.util.spec_from_file_location("release_service_state", deploy / "service-state.py")
        if spec is None or spec.loader is None:
            raise core.GateError("backup service-state module is unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config, identity, environment = module.load_context(deploy)
        records = module.project_records(config["name"], environment, module.run_docker)
        state = module.capture_state(config, records, identity)
        module.verify_config_hashes(state, environment, module.run_docker)
        module.verify_image_references(state, environment, module.run_docker)
        return len(module.selected_services(state))

    def inspect(self, reference: str) -> dict[str, Any]:
        return json.loads(run(["docker", "inspect", reference]))[0]

    def container_exists(self, reference: str) -> bool:
        result = subprocess.run(
            ["docker", "inspect", reference],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
        return result.returncode == 0

    def container_name(self, container_id: str) -> str:
        return str(self.inspect(container_id)["Name"])

    def name_owner(self, name: str) -> str | None:
        if not self.container_exists(name):
            return None
        return str(self.inspect(name)["Id"])

    def fingerprint_data(self, container: Mapping[str, Any]) -> str:
        selected = {key: container[key] for key in ("Config", "HostConfig", "Image")}
        serialized = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return core.sha256_bytes(serialized)

    def fingerprint(self, container_id: str) -> str:
        return self.fingerprint_data(self.inspect(container_id))

    def container_running(self, container_id: str) -> bool:
        return bool(self.inspect(container_id)["State"]["Running"])

    def read_unit_bytes(self) -> bytes:
        return UNIT_PATH.read_bytes()

    def read_inventory_bytes(self) -> bytes:
        return INVENTORY_PATH.read_bytes()

    def network_shape_data(self, container: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        result = {}
        for name, endpoint in container["NetworkSettings"]["Networks"].items():
            aliases = sorted(
                alias
                for alias in (endpoint.get("Aliases") or [])
                if alias not in (container["Id"], container["Id"][:12])
            )
            result[name] = {"IPAddress": endpoint.get("IPAddress", ""), "Aliases": aliases}
        return result

    def network_shape(self, container_id: str) -> dict[str, dict[str, Any]]:
        return self.network_shape_data(self.inspect(container_id))

    def source_sha(self, container_id: str) -> str:
        return core.sha256_bytes(run(["docker", "exec", container_id, "cat", SOURCE_PATH]))

    def create_container(self, name: str, config: Mapping[str, Any]) -> str:
        return str(docker_api("POST", "/containers/create?name=" + name, config)["Id"])

    def start_container(self, container_id: str) -> None:
        run(["docker", "start", container_id])

    def stop_container(self, container_id: str) -> None:
        if self.inspect(container_id)["State"]["Running"]:
            run(["docker", "stop", "-t", "210", container_id], timeout=240)

    def detach_container(self, container_id: str) -> None:
        for network in list(self.inspect(container_id)["NetworkSettings"]["Networks"]):
            docker_api(
                "POST",
                "/networks/" + network + "/disconnect",
                {"Container": container_id, "Force": True},
            )

    def disconnect_network(self, container_id: str, network: str) -> None:
        docker_api(
            "POST",
            "/networks/" + network + "/disconnect",
            {"Container": container_id, "Force": True},
        )

    def connect_network(self, container_id: str, name: str, endpoint: dict[str, object]) -> None:
        docker_api(
            "POST",
            "/networks/" + name + "/connect",
            {
                "Container": container_id,
                "EndpointConfig": {
                    "IPAMConfig": {"IPv4Address": endpoint.get("IPAddress", "")},
                    "Aliases": list(endpoint.get("Aliases") or []),
                },
            },
        )

    def rename_container(self, container_id: str, name: str) -> None:
        run(["docker", "rename", container_id, name])

    def wait_running(self, container_id: str, timeout_seconds: int = 60) -> None:
        deadline = time.monotonic() + timeout_seconds
        saw_running = False
        while True:
            if time.monotonic() >= deadline:
                break
            current = self.inspect(container_id)
            if current["State"]["Running"]:
                saw_running = True
                ip = current["NetworkSettings"]["Networks"]["smartbrain_app"]["IPAddress"]
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    with urllib.request.urlopen(
                        f"http://{ip}:8000/health", timeout=min(4, remaining)
                    ) as response:
                        if response.status == 200:
                            return
                except OSError:
                    pass
            elif saw_running and current["State"]["Status"] == "exited":
                raise core.GateError("container exited during startup")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(1, remaining))
        raise core.GateError("container startup timeout")

    def stop_unit(self) -> None:
        state = self.store.read() or {}
        for _ in range(2):
            owner = self.name_owner(NAME)
            if owner is None and state.get('stage') == 'recovery_started':
                break
            if owner not in (state.get('old_id'), state.get('new_id')) or owner is None:
                raise core.GateError('unexpected container identity before service stop')
            current = self.inspect(owner)
            if not current['State']['Running']:
                break
            ip = current['NetworkSettings']['Networks']['smartbrain_app']['IPAddress']
            with urllib.request.urlopen('http://' + ip + ':8000/health', timeout=5) as response:
                if not runtime_drained(json.load(response)):
                    raise core.GateError('personal gateway has active requests; refusing stop')
            time.sleep(1)
        result = subprocess.run(
            ["systemctl", "stop", UNIT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=260,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("failed to stop current personal gateway unit")

    def start_unit(self) -> None:
        run(["systemctl", "start", UNIT], timeout=260)

    def reset_failed_unit(self) -> None:
        run(["systemctl", "reset-failed", UNIT])

    def daemon_reload(self) -> None:
        run(["systemctl", "daemon-reload"])

    def write_unit(self, value: bytes) -> None:
        core.atomic_write_bytes(UNIT_PATH, value, 0o644)

    def write_inventory(self, value: bytes) -> None:
        core.atomic_write_bytes(INVENTORY_PATH, value, 0o600)

    def validate_unit(self, container_id: str) -> dict[str, str]:
        state = self.systemd_state(UNIT, UNIT_SYSTEMD_FIELDS)
        wanted = {
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "Result": "success",
            "ControlPID": "0",
            "Job": "",
        }
        for field, expected in wanted.items():
            if state.get(field) != expected:
                raise core.GateError(f"personal gateway systemd field {field} is not {expected}")
        if not str(state.get("MainPID", "")).isdigit() or int(state["MainPID"]) <= 0:
            raise core.GateError("personal gateway MainPID is invalid")
        if container_id not in state.get("ExecStart", ""):
            raise core.GateError("personal gateway unit is not bound to the expected CID")
        return state

    def validate_restored_unit(self, old_id: str) -> None:
        self.validate_unit(old_id)

    def request_status(self, url: str, *, timeout: int = 15, headers=None) -> int:
        request = urllib.request.Request(url, method="GET", headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    def validate_restored_public(self) -> dict[str, int]:
        values = {
            "health": self.request_status("https://39.105.79.0/health/ready"),
            "anonymous_models": self.request_status(
                "https://39.105.79.0/v4/personal-api/v1/models"
            ),
        }
        return values

    def validate_candidate(self, container_id: str, source_digest: str) -> dict[str, Any]:
        current = self.inspect(container_id)
        assert_relay_env(current["Config"])
        if self.source_sha(container_id) != source_digest:
            raise core.GateError("candidate source digest mismatch in image")
        ip = current["NetworkSettings"]["Networks"]["smartbrain_app"]["IPAddress"]
        health = self.request_status(f"http://{ip}:8000/health", timeout=8)
        anonymous = self.request_status(f"http://{ip}:8000/v1/models", timeout=8)
        if health != 200 or anonymous != 401:
            raise core.GateError("candidate health or anonymous boundary failed")
        return {"health": health, "anonymous_models": anonymous}

    def validate_promoted_runtime(self, new_id: str) -> dict[str, Any]:
        state = self.store.read() or {}
        current = self.inspect(new_id)
        if not current["State"]["Running"]:
            raise core.GateError("promoted container is not running")
        assert_relay_env(current["Config"])
        if self.source_sha(new_id) != state.get("candidate_source_sha256"):
            raise core.GateError("promoted source digest mismatch")
        if self.network_shape_data(current) != state.get("old_network"):
            raise core.GateError("promoted network identity differs from old runtime")
        if core.sha256_bytes(
            json.dumps(current["HostConfig"], sort_keys=True, separators=(",", ":")).encode()
        ) != state.get("old_host_config_sha256"):
            raise core.GateError("promoted HostConfig differs from old runtime")
        unit = self.validate_unit(new_id)
        statuses = {
            "direct_windows_anonymous": self.request_status(RELAY_URL + "/v1/models"),
            "marked_windows_anonymous": self.request_status(RELAY_URL + "/v1/models", headers={"X-SmartBrain-Gateway-Proxy":"personal-api"}),
            "remote_windows_panel": self.request_status(RELAY_URL + "/panel"),
            "public_models_anonymous": self.request_status(
                "https://39.105.79.0/v4/personal-api/v1/models"
            ),
            "public_responses_anonymous": self.request_status(
                "https://39.105.79.0/v4/personal-api/v1/responses"
            ),
            "public_login": self.request_status("https://39.105.79.0/login"),
        }
        expected = {
            "direct_windows_anonymous": 403,
            "marked_windows_anonymous": 401,
            "remote_windows_panel": 403,
            "public_models_anonymous": 401,
            "public_responses_anonymous": 401,
            "public_login": 200,
        }
        if statuses != expected:
            raise core.GateError("promoted anonymous/public statuses are unexpected")
        return {
            "unit": {
                key: unit.get(key, "")
                for key in ("ActiveState", "SubState", "UnitFileState", "Result", "MainPID", "InvocationID")
            },
            "public_statuses": statuses,
            "network_preserved": True,
            "host_config_preserved": True,
        }

    def write_promoted(self, report: Mapping[str, Any]) -> None:
        core.atomic_write_json(EVIDENCE_DIR / "promoted.json", report)

    def secret_safe_env_summary(self, config: Mapping[str, Any]) -> list[dict[str, Any]]:
        result = []
        for item in config.get("Env") or []:
            name, separator, value = str(item).partition("=")
            result.append(
                {
                    "name": name,
                    "has_value": bool(separator),
                    "value_length": len(value),
                    "value_sha256": core.sha256_bytes(value.encode("utf-8")),
                }
            )
        return sorted(result, key=lambda row: row["name"])


def load_json(path: pathlib.Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise core.GateError(f"{label} is unavailable or invalid") from error
    if not isinstance(value, dict):
        raise core.GateError(f"{label} must be a JSON object")
    core.reject_raw_secrets(value)
    return value


def _unit_bytes(container_id: str) -> bytes:
    value = (
        "[Unit]\n"
        "Description=SmartBrain current registered-member personal gateway\n"
        "After=docker.service\n"
        "Requires=docker.service\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart=/usr/bin/docker start -a {container_id}\n"
        f"ExecStop=/usr/bin/docker stop -t 210 {container_id}\n"
        "Restart=no\n"
        "TimeoutStopSec=240\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    return value.encode("utf-8")


def _host_config_sha(container: Mapping[str, Any]) -> str:
    return core.sha256_bytes(
        json.dumps(container["HostConfig"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


DESTRUCTIVE_STAGES = {
    "cutover_starting",
    "old_stopped",
    "old_detached",
    "old_renamed",
    "new_create_planned",
    "new_discovered_for_recovery",
    "new_created",
    "unit_swapped",
    "new_started",
    "inventory_updated",
    "awaiting_smoke",
    "recovery_started",
    "recovery_failed",
}


def _settle_promotion_failure(
    ops: Any,
    store: core.StageStore,
    *,
    error: BaseException,
    old_id: str,
    candidate_id: str | None,
    new_id: str | None,
) -> dict[str, Any]:
    """Settle a promote exception without letting diagnostics block recovery."""

    state = store.read() or {}
    if state.get("stage") == "promoted":
        _materialize_promoted_evidence(ops, state)
        return dict(state)

    diagnostic_error_type: str | None = None
    try:
        core.atomic_write_json(
            EVIDENCE_DIR / "promotion-failed.json",
            {
                "schema": "smartbrain.personal-relay-promotion-failure/v1",
                "release": core.RELEASE,
                "failed_at": core.utc_now().isoformat(),
                "error_type": type(error).__name__,
                "stage": state.get("stage", "unknown"),
                "old_id": old_id,
                "new_id": new_id,
                "candidate_id": candidate_id,
            },
        )
    except BaseException as diagnostic_error:
        diagnostic_error_type = type(diagnostic_error).__name__

    if state.get("stage") in DESTRUCTIVE_STAGES:
        return recover_release(ops, store, reason="promotion-failure")
    return store.write(
        "precutover_failed",
        failure_type=type(error).__name__,
        failed_from=state.get("stage", "unknown"),
        diagnostic_error_type=diagnostic_error_type,
    )


def promote_release(
    ops: RealOps,
    store: core.StageStore,
    *,
    smoke_timeout_seconds: int,
) -> dict[str, Any]:
    if store.read() is not None:
        raise core.GateError("release stage already exists; inspect or recover, never replay")
    if AUTH_SMOKE_RECEIPT_PATH.exists():
        raise core.GateError("stale authenticated smoke receipt exists")
    if PENDING_MARKER.exists():
        raise core.GateError("maintenance is pending")
    if not UNIT_PATH.is_file() or not INVENTORY_PATH.is_file():
        raise core.GateError("current unit or runtime inventory is missing")
    if ops.container_exists(CANDIDATE_NAME) or ops.container_exists(OLD_NAME):
        raise core.GateError("release-specific candidate or rollback name already exists")

    backup_receipt = load_json(FRESH_BACKUP_RECEIPT_PATH, "fresh backup receipt")
    windows_receipt = load_json(WINDOWS_READY_RECEIPT_PATH, "Windows ready receipt")
    gates = validate_release_gates(
        ops,
        backup_receipt,
        windows_receipt,
        now=core.utc_now(),
        backup_root=BACKUP_ROOT,
    )
    candidate_result = load_json(CANDIDATE_RESULT_PATH, "candidate result")
    if candidate_result.get("status") != "candidate-tested-no-promote" or candidate_result.get("tests_exit") != 0:
        raise core.GateError("candidate result is not a successful no-promote result")
    image = candidate_result.get("candidate_image")
    source_digest = candidate_result.get("source_sha256")
    if not isinstance(image, str) or not image.startswith("sha256:"):
        raise core.GateError("candidate image digest is missing")
    if not isinstance(source_digest, str) or len(source_digest) != 64:
        raise core.GateError("candidate source digest is missing")
    if core.sha256_file(CANDIDATE_SOURCE_PATH) != source_digest:
        raise core.GateError("candidate input source digest mismatch")
    if not ops.container_exists(image):
        raise core.GateError("candidate image is unavailable")

    old = ops.inspect(NAME)
    if (
        old["Id"] != EXPECTED_OLD_ID
        or old["Image"] != EXPECTED_OLD_IMAGE
        or old["State"]["StartedAt"] != EXPECTED_OLD_STARTED_AT
        or not old["State"]["Running"]
    ):
        raise core.GateError("current personal gateway identity changed")
    if old["Image"] != candidate_result.get("base_image"):
        raise core.GateError("candidate base image differs from current container")
    ops.validate_unit(old["Id"])
    inventory_bytes = INVENTORY_PATH.read_bytes()
    inventory = json.loads(inventory_bytes)
    if inventory.get("container_id") != old["Id"]:
        raise core.GateError("runtime inventory is not bound to current CID")
    unit_bytes = UNIT_PATH.read_bytes()

    candidate_id: str | None = None
    new_id: str | None = None
    try:
        ROLLBACK_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        unit_backup = ROLLBACK_DIR / "old-unit.service"
        inventory_backup = ROLLBACK_DIR / "old-inventory.json"
        core.atomic_write_bytes(unit_backup, unit_bytes)
        core.atomic_write_bytes(inventory_backup, inventory_bytes)
        old_network = ops.network_shape_data(old)
        baseline = store.write(
            "baseline_saved",
            old_id=old["Id"],
            old_image=old["Image"],
            old_started_at=old["State"]["StartedAt"],
            old_fingerprint=ops.fingerprint_data(old),
            old_host_config_sha256=_host_config_sha(old),
            old_network=old_network,
            old_environment=ops.secret_safe_env_summary(old["Config"]),
            unit_backup_path=str(unit_backup),
            unit_backup_sha256=core.sha256_bytes(unit_bytes),
            inventory_backup_path=str(inventory_backup),
            inventory_backup_sha256=core.sha256_bytes(inventory_bytes),
            candidate_image=image,
            candidate_source_sha256=source_digest,
            backup_invocation_id=gates["backup"]["invocation_id"],
            windows_relay_pid=gates["windows"]["relay_pid"],
        )
        candidate_config = clone_config(old, image, candidate=True)
        assert_relay_env(candidate_config)
        candidate_id = ops.create_container(CANDIDATE_NAME, candidate_config)
        store.write("candidate_created", candidate_id=candidate_id)
        ops.start_container(candidate_id)
        ops.wait_running(candidate_id)
        candidate_checks = ops.validate_candidate(candidate_id, source_digest)
        store.write("candidate_verified", candidate_checks=candidate_checks)
        ops.stop_container(candidate_id)

        # Every mutable gate is checked again immediately before stopping the
        # current service while both release locks remain held.
        validate_release_gates(
            ops,
            backup_receipt,
            windows_receipt,
            now=core.utc_now(),
            backup_root=BACKUP_ROOT,
        )
        old_again = ops.inspect(NAME)
        if (
            old_again["Id"] != old["Id"]
            or old_again["State"]["StartedAt"] != old["State"]["StartedAt"]
            or ops.fingerprint_data(old_again) != baseline["old_fingerprint"]
            or not old_again["State"]["Running"]
        ):
            raise core.GateError("current container changed before cutover")
        if ops.container_exists(OLD_NAME):
            raise core.GateError("rollback container name became occupied")

        store.write("cutover_starting")
        ops.stop_unit()
        if ops.inspect(old["Id"])["State"]["Running"]:
            raise core.GateError("old container did not stop")
        store.write("old_stopped")
        ops.detach_container(old["Id"])
        store.write("old_detached")
        ops.rename_container(old["Id"], OLD_NAME)
        store.write("old_renamed")

        config = clone_config(old, image)
        config["Labels"] = dict(config.get("Labels") or {})
        config["Labels"]["smartbrain.scope"] = core.RELEASE
        assert_relay_env(config)
        store.write(
            "new_create_planned",
            planned_new_name=NAME,
            planned_new_image=image,
            new_create_intent_at=core.utc_now().isoformat(),
        )
        new_id = ops.create_container(NAME, config)
        store.write("new_created", new_id=new_id)
        ops.write_unit(_unit_bytes(new_id))
        ops.daemon_reload()
        store.write("unit_swapped")
        ops.start_unit()
        ops.wait_running(new_id)
        store.write("new_started")

        runtime = ops.validate_promoted_runtime(new_id)
        updated_inventory = dict(inventory)
        updated_inventory.update(
            {
                "observed_at": core.utc_now().isoformat(),
                "container_id": new_id,
                "image_id": image,
                "configuration_sha256": ops.fingerprint(new_id),
                "previous_container_id": old["Id"],
                "previous_image_id": old["Image"],
                "release": core.RELEASE,
                "scope": "supplemental exact runtime preservation; not full frozen coordinator",
            }
        )
        inventory_payload = json.dumps(
            updated_inventory, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8") + b"\n"
        ops.write_inventory(inventory_payload)
        store.write("inventory_updated", promoted_runtime=runtime)
        validate_release_gates(
            ops,
            backup_receipt,
            windows_receipt,
            now=core.utc_now(),
            backup_root=BACKUP_ROOT,
        )

        awaiting_at = core.utc_now()
        awaiting = {
            "schema": "smartbrain.personal-relay-awaiting-smoke/v1",
            "release": core.RELEASE,
            "status": "awaiting_authenticated_smoke",
            "awaiting_smoke_at": awaiting_at.isoformat(),
            "new_id": new_id,
            "old_id": old["Id"],
            "smoke_deadline": (
                awaiting_at + __import__("datetime").timedelta(seconds=smoke_timeout_seconds)
            ).isoformat(),
        }
        core.atomic_write_json(EVIDENCE_DIR / "cutover-awaiting-auth-smoke.json", awaiting)
        store.write(
            "awaiting_smoke",
            awaiting_smoke_at=awaiting_at.isoformat(),
            smoke_deadline=awaiting["smoke_deadline"],
        )

        deadline = time.monotonic() + smoke_timeout_seconds
        while time.monotonic() < deadline:
            if AUTH_SMOKE_RECEIPT_PATH.is_file():
                receipt = load_json(AUTH_SMOKE_RECEIPT_PATH, "authenticated smoke receipt")
                return finalize_release(ops, store, receipt, now=core.utc_now())
            time.sleep(1)
        raise core.GateError("authenticated smoke receipt timed out")
    except BaseException as error:
        settled = _settle_promotion_failure(
            ops,
            store,
            error=error,
            old_id=old["Id"],
            candidate_id=candidate_id,
            new_id=new_id,
        )
        if settled.get("stage") == "promoted":
            return settled
        raise
    finally:
        if candidate_id and ops.container_exists(candidate_id):
            ops.stop_container(candidate_id)


def status_report(ops: RealOps, store: core.StageStore) -> dict[str, Any]:
    stage = store.read()
    unit = ops.systemd_state(UNIT, UNIT_SYSTEMD_FIELDS)
    backup = ops.backup_state()
    return {
        "observed_at": core.utc_now().isoformat(),
        "release": core.RELEASE,
        "stage": stage,
        "unit": {
            key: unit.get(key, "")
            for key in ("ActiveState", "SubState", "UnitFileState", "Result", "MainPID", "InvocationID")
        },
        "backup": {
            key: backup.get(key, "")
            for key in core.BACKUP_SYSTEMD_FIELDS
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--smoke-timeout", type=int, default=300)
    recovery_parser = subparsers.add_parser("recover")
    recovery_parser.add_argument("--reason", default="operator-requested")
    subparsers.add_parser("finalize")
    subparsers.add_parser("status")
    args = parser.parse_args(argv)
    ops = RealOps()
    store = ops.store
    if args.command == "status":
        print(json.dumps(status_report(ops, store), ensure_ascii=False, sort_keys=True))
        return 0
    with termination_as_exception():
        with ops.acquire_locks():
            if args.command == "promote":
                if args.smoke_timeout < 60 or args.smoke_timeout > 900:
                    raise core.GateError("smoke timeout must be between 60 and 900 seconds")
                result = promote_release(
                    ops, store, smoke_timeout_seconds=args.smoke_timeout
                )
            elif args.command == "recover":
                result = recover_release(ops, store, reason=args.reason)
            else:
                receipt = load_json(AUTH_SMOKE_RECEIPT_PATH, "authenticated smoke receipt")
                result = finalize_release(ops, store, receipt, now=core.utc_now())
    print(json.dumps({"release": core.RELEASE, "stage": result.get("stage")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

