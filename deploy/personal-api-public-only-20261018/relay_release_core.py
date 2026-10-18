"""Shared, secret-safe contracts for the personal relay production release.

This module is imported by the local offline tests and copied byte-for-byte to
the production release directory by the guarded dispatchers.  It deliberately
contains no SSH, Docker, or systemd side effects.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


RELEASE = "personal-api-public-only-20261018-r1"
FRESH_BACKUP_SCHEMA = "smartbrain.fresh-backup-receipt/v1"
WINDOWS_READY_SCHEMA = "smartbrain.windows-relay-ready/v1"
AUTH_SMOKE_SCHEMA = "smartbrain.personal-relay-auth-smoke/v1"
STAGE_SCHEMA = "smartbrain.personal-relay-release-stage/v1"

EXPECTED_CAPACITY_CHECKER_SHA256 = (
    "4eceabcedeed3776b6e5463e445593e1e286d12e92afcc9c6dcc5f5a91c3fc7c"
)
EXPECTED_WINDOWS_START_SERVICES_SHA256 = (
    "ae95ac240d24ba695f24fee0105f1e1ec6b5177ecb52d0d74c39e73737e6a2e6"
)
EXPECTED_WINDOWS_PROXY_SERVER_SHA256 = (
    "8ee401eb7169347f4308a29c3c942121e0f9ce10479eb240e9c0a286607a208c"
)
EXPECTED_WINDOWS_INTERNAL_KEY_SHA256 = (
    "f6801d8c2ec3f069a2b269f051cddf34251f2fb0eaa47ba5b721377a3fb236a6"
)
EXPECTED_WINDOWS_INTERNAL_KEY_LENGTH = 77

FRESH_BACKUP_NOT_BEFORE = datetime(2026, 10, 17, 8, 19, 37, tzinfo=timezone.utc)
WINDOWS_RESTART_NOT_BEFORE = datetime(2026, 10, 17, 9, 2, tzinfo=timezone.utc)
MAX_RECEIPT_AGE = timedelta(hours=2)
MAX_PREFLIGHT_TO_BACKUP_START = timedelta(minutes=10)
STATIC_DISK_THRESHOLDS = {
    "/var/lib/docker": 40 * 1024**3,
    "/srv/smartbrain": 20 * 1024**3,
    "/srv/smartbrain-backups": 250 * 1024**3,
    "/srv/smartbrain-cold": 250 * 1024**3,
}
MIN_MEMORY_AVAILABLE_BYTES = 2 * 1024**3


class GateError(RuntimeError):
    """A fail-closed release gate rejection safe to show to an operator."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{field} is missing")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    # PowerShell/.NET round-trip timestamps commonly carry seven fractional
    # digits, while Python 3.10's fromisoformat accepts at most microseconds.
    normalized = re.sub(r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)", r"\1", normalized)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise GateError(f"{field} is not an ISO timestamp") from error
    if parsed.tzinfo is None:
        raise GateError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise GateError(f"{field} is not a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise GateError(f"{field} is not a SHA-256 digest") from error
    return value.lower()


def _require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise GateError(f"{field} is invalid")
    return value


def reject_raw_secrets(value: Any, path: str = "receipt") -> None:
    """Reject receipt fields or string values that could contain credentials."""

    forbidden_key_parts = (
        "authorization",
        "bearer",
        "secret",
        "raw_key",
        "key_value",
        "token_value",
        "password",
    )
    forbidden_value_prefixes = ("bearer ", "cpa_", "sbk_", "sk-")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in forbidden_key_parts):
                raise GateError(f"raw secret field is forbidden at {path}.{key}")
            reject_raw_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_raw_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.strip().lower()
        if lowered.startswith(forbidden_value_prefixes):
            raise GateError(f"raw secret value is forbidden at {path}")


BACKUP_SYSTEMD_FIELDS = (
    "ActiveState",
    "SubState",
    "UnitFileState",
    "Result",
    "MainPID",
    "ControlPID",
    "Job",
    "InvocationID",
    "ExecMainCode",
    "ExecMainStatus",
    "ExecMainStartTimestampMonotonic",
    "ExecMainExitTimestampMonotonic",
)


def validate_backup_systemd_state(state: Mapping[str, Any]) -> None:
    for field in BACKUP_SYSTEMD_FIELDS:
        if field not in state:
            raise GateError(f"backup systemd field {field} is missing")
    wanted = {
        "ActiveState": "inactive",
        "SubState": "dead",
        "UnitFileState": "static",
        "Result": "success",
        "MainPID": "0",
        "ControlPID": "0",
        "Job": "",
        # systemctl show exposes the waitid CLD_EXITED code numerically.
        "ExecMainCode": "1",
        "ExecMainStatus": "0",
    }
    for field, expected in wanted.items():
        if str(state.get(field, "")) != expected:
            raise GateError(f"backup systemd field {field} is not {expected}")
    invocation = str(state.get("InvocationID", ""))
    if len(invocation) != 32 or any(char not in "0123456789abcdefABCDEF" for char in invocation):
        raise GateError("backup InvocationID is invalid")
    for field in ("ExecMainStartTimestampMonotonic", "ExecMainExitTimestampMonotonic"):
        raw = str(state.get(field, ""))
        if not raw.isdigit() or int(raw) <= 0:
            raise GateError(f"backup systemd field {field} is invalid")


def _validate_receipt_time(
    issued_at: datetime,
    *,
    now: datetime,
    not_before: datetime,
    label: str,
) -> None:
    current = now.astimezone(timezone.utc)
    if issued_at < not_before:
        raise GateError(f"{label} predates the release gate")
    if issued_at > current + timedelta(minutes=2):
        raise GateError(f"{label} is in the future")
    if current - issued_at > MAX_RECEIPT_AGE:
        raise GateError(f"{label} is stale")


def validate_dynamic_capacity_receipt(value: Any, *, now: datetime) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise GateError("dynamic capacity receipt is missing")
    if _require_sha256(value.get("checker_sha256"), "capacity checker SHA") != EXPECTED_CAPACITY_CHECKER_SHA256:
        raise GateError("capacity checker SHA does not match the reviewed checker")
    if value.get("exit_code") != 0:
        raise GateError("dynamic capacity check did not pass")
    checked_at = parse_timestamp(value.get("checked_at"), "capacity checked_at")
    _validate_receipt_time(
        checked_at,
        now=now,
        not_before=FRESH_BACKUP_NOT_BEFORE,
        label="dynamic capacity receipt",
    )
    free_bytes = _require_int(value.get("free_bytes"), "capacity free_bytes", minimum=1)
    required_bytes = _require_int(value.get("required_bytes"), "capacity required_bytes", minimum=1)
    if free_bytes < required_bytes:
        raise GateError("dynamic capacity free bytes are below required bytes")
    return {
        "checker_sha256": EXPECTED_CAPACITY_CHECKER_SHA256,
        "checked_at": checked_at.isoformat(),
        "free_bytes": free_bytes,
        "required_bytes": required_bytes,
    }


def validate_static_capacity(value: Any, *, now: datetime) -> dict[str, Any]:
    """Validate the normal post-backup operating reserves.

    The dynamic checker belongs before a full backup because its transient
    budget is intentionally consumed by that backup.  After completion, the
    release gate uses the long-standing four-disk and memory reserves instead
    of requiring capacity for an immediate second full backup.
    """

    if not isinstance(value, Mapping):
        raise GateError("static capacity receipt is missing")
    checked_at = parse_timestamp(value.get("checked_at"), "static capacity checked_at")
    _validate_receipt_time(
        checked_at,
        now=now,
        not_before=FRESH_BACKUP_NOT_BEFORE,
        label="static capacity receipt",
    )
    disk_free = value.get("disk_free_bytes")
    if not isinstance(disk_free, Mapping):
        raise GateError("static disk capacity values are missing")
    validated_disks: dict[str, int] = {}
    for path, threshold in STATIC_DISK_THRESHOLDS.items():
        free = _require_int(disk_free.get(path), f"static capacity {path}", minimum=1)
        if free < threshold:
            raise GateError(f"static capacity {path} is below its reserve")
        validated_disks[path] = free
    memory = _require_int(
        value.get("memory_available_bytes"), "static memory available", minimum=1
    )
    if memory < MIN_MEMORY_AVAILABLE_BYTES:
        raise GateError("static memory available is below its reserve")
    return {
        "checked_at": checked_at.isoformat(),
        "disk_free_bytes": validated_disks,
        "memory_available_bytes": memory,
    }


def validate_fresh_backup_receipt(
    receipt: Any,
    state: Mapping[str, Any],
    *,
    now: datetime,
    backup_root: pathlib.Path,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise GateError("fresh backup receipt is missing")
    reject_raw_secrets(receipt)
    if receipt.get("schema") != FRESH_BACKUP_SCHEMA or receipt.get("release") != RELEASE:
        raise GateError("fresh backup receipt identity is invalid")
    validate_backup_systemd_state(state)

    issued_at = parse_timestamp(receipt.get("issued_at"), "backup issued_at")
    completed_at = parse_timestamp(receipt.get("completed_at"), "backup completed_at")
    _validate_receipt_time(
        issued_at,
        now=now,
        not_before=FRESH_BACKUP_NOT_BEFORE,
        label="fresh backup receipt",
    )
    if completed_at < FRESH_BACKUP_NOT_BEFORE or completed_at > issued_at:
        raise GateError("fresh backup completion time is invalid")

    invocation = str(receipt.get("invocation_id", ""))
    if invocation != str(state.get("InvocationID")):
        raise GateError("fresh backup Invocation does not match systemd")
    timestamp_pairs = (
        ("exec_main_start_timestamp_monotonic", "ExecMainStartTimestampMonotonic"),
        ("exec_main_exit_timestamp_monotonic", "ExecMainExitTimestampMonotonic"),
    )
    for receipt_field, state_field in timestamp_pairs:
        if str(receipt.get(receipt_field, "")) != str(state.get(state_field, "")):
            raise GateError(f"fresh backup {receipt_field} does not match systemd")

    root = backup_root.resolve(strict=True)
    raw_dir = receipt.get("backup_dir")
    if not isinstance(raw_dir, str):
        raise GateError("fresh backup directory is missing")
    backup_dir = pathlib.Path(raw_dir).resolve(strict=True)
    if backup_dir.parent != root or not backup_dir.is_dir():
        raise GateError("fresh backup directory is outside the approved root")
    if (
        not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", backup_dir.name)
        or any(
            word in backup_dir.name.lower()
            for word in ("partial", "failed", "tmp", "temp", "stage")
        )
    ):
        raise GateError("fresh backup directory is not final")
    backup_started = datetime.strptime(backup_dir.name, "%Y%m%dT%H%M%SZ").replace(
        tzinfo=timezone.utc
    )

    backup_state = backup_dir / "backup-state.json"
    sums = backup_dir / "SHA256SUMS"
    if not backup_state.is_file() or not sums.is_file():
        raise GateError("fresh backup final artifacts are missing")
    expected_state = _require_sha256(receipt.get("backup_state_sha256"), "backup-state SHA")
    expected_sums = _require_sha256(receipt.get("sha256sums_sha256"), "SHA256SUMS SHA")
    if sha256_file(backup_state) != expected_state:
        raise GateError("backup-state.json hash does not match receipt")
    if sha256_file(sums) != expected_sums:
        raise GateError("SHA256SUMS hash does not match receipt")
    try:
        backup_state_data = json.loads(backup_state.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError("backup-state.json is not readable JSON") from error
    if not isinstance(backup_state_data, Mapping):
        raise GateError("backup-state.json is not an object")
    if str(backup_state_data.get("status", "")).lower() != "complete":
        raise GateError("backup-state.json does not record complete status")
    if str(backup_state_data.get("consistency", "")).lower() != "online":
        raise GateError("backup-state.json does not record online consistency")
    clickhouse = backup_state_data.get("clickhouse")
    if (
        not isinstance(clickhouse, Mapping)
        or not isinstance(clickhouse.get("database"), str)
        or not clickhouse.get("database")
        or not isinstance(clickhouse.get("backup_name"), str)
        or not clickhouse.get("backup_name")
    ):
        raise GateError("backup-state.json ClickHouse identity is incomplete")
    if receipt.get("registered_services") != 20:
        raise GateError("fresh backup registration count is not 20")

    capacity = validate_dynamic_capacity_receipt(
        receipt.get("dynamic_capacity"), now=backup_started
    )
    dynamic_checked = parse_timestamp(
        capacity.get("checked_at"), "capacity checked_at"
    )
    if (
        dynamic_checked > backup_started
        or backup_started - dynamic_checked > MAX_PREFLIGHT_TO_BACKUP_START
        or backup_started > completed_at
    ):
        raise GateError("capacity preflight is not tightly bound to backup start")
    return {
        "invocation_id": invocation,
        "completed_at": completed_at.isoformat(),
        "backup_dir": str(backup_dir),
        "backup_state_sha256": expected_state,
        "sha256sums_sha256": expected_sums,
        "dynamic_capacity": capacity,
    }


def validate_windows_ready_receipt(receipt: Any, *, now: datetime) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise GateError("Windows ready receipt is missing")
    reject_raw_secrets(receipt)
    if receipt.get("schema") != WINDOWS_READY_SCHEMA or receipt.get("release") != RELEASE:
        raise GateError("Windows ready receipt identity is invalid")
    issued_at = parse_timestamp(receipt.get("issued_at"), "Windows issued_at")
    restarted_at = parse_timestamp(receipt.get("restart_completed_at"), "Windows restart_completed_at")
    _validate_receipt_time(
        issued_at,
        now=now,
        not_before=WINDOWS_RESTART_NOT_BEFORE,
        label="Windows ready receipt",
    )
    if restarted_at < WINDOWS_RESTART_NOT_BEFORE or restarted_at > issued_at:
        raise GateError("Windows restart time is invalid")
    active_connections = _require_int(
        receipt.get("active_connections_before_restart"),
        "Windows active_connections_before_restart",
    )
    if active_connections:
        idle_gate = receipt.get("idle_connection_gate")
        if not isinstance(idle_gate, Mapping):
            raise GateError("Windows idle connection gate is missing")
        if (
            active_connections != 1
            or idle_gate.get("classification") != "idle_retained_http_connection"
            or _require_int(idle_gate.get("sample_count"), "idle sample_count") < 2
            or _require_int(
                idle_gate.get("sample_interval_seconds"), "idle sample_interval_seconds"
            )
            < 10
            or idle_gate.get("send_queue_zero") is not True
            or idle_gate.get("receive_queue_zero") is not True
            or idle_gate.get("byte_counters_stable") is not True
            or idle_gate.get("backend_connection_count") != 0
            or idle_gate.get("watchdog_stopped_before_restart") is not True
        ):
            raise GateError("Windows idle connection gate did not prove a safe restart")

    relay = receipt.get("relay")
    backend = receipt.get("backend")
    watchdog = receipt.get("watchdog")
    hashes = receipt.get("hashes")
    if not all(isinstance(item, Mapping) for item in (relay, backend, watchdog, hashes)):
        raise GateError("Windows ready receipt sections are incomplete")
    relay_pid = _require_int(relay.get("pid"), "relay pid", minimum=1)
    backend_pid = _require_int(backend.get("pid"), "backend pid", minimum=1)
    relay_started_at = parse_timestamp(relay.get("started_at"), "relay started_at")
    if relay_started_at < WINDOWS_RESTART_NOT_BEFORE or relay_started_at > restarted_at:
        raise GateError("relay PID did not start during the reviewed restart")
    if relay.get("listener_count") != 1 or relay.get("listener_pid") != relay_pid:
        raise GateError("relay listener identity is not unique")
    if backend.get("listener_count") != 1 or backend.get("listener_pid") != backend_pid:
        raise GateError("backend listener identity is not unique")
    if watchdog.get("state") != "Enabled/Running":
        raise GateError("watchdog is not enabled and running")
    if _require_int(watchdog.get("stable_polls"), "watchdog stable_polls") < 2 or watchdog.get("pid_stable") is not True:
        raise GateError("watchdog did not preserve stable runtime identity")
    if hashes.get("start_services") != EXPECTED_WINDOWS_START_SERVICES_SHA256:
        raise GateError("Windows start-services SHA does not match")
    if hashes.get("proxy_server") != EXPECTED_WINDOWS_PROXY_SERVER_SHA256:
        raise GateError("Windows proxy-server SHA does not match")
    if (receipt.get("unmarked_models_status") != 403 or receipt.get("remote_panel_status") != 403
        or receipt.get("firewall_restricted") is not True or receipt.get("backend_loopback_only") is not True):
        raise GateError("Windows public-only boundary is incomplete")
    if receipt.get("anonymous_models_status") != 401:
        raise GateError("Windows anonymous models boundary did not return 401")
    if (
        receipt.get("authorized_models_status") != "deferred_to_post_cutover"
        or receipt.get("post_cutover_authenticated_smoke_required") is not True
    ):
        raise GateError("Windows post-cutover authenticated smoke is not required explicitly")
    return {
        "issued_at": issued_at.isoformat(),
        "restart_completed_at": restarted_at.isoformat(),
        "relay_pid": relay_pid,
        "backend_pid": backend_pid,
        "authenticated_probe": "deferred_to_post_cutover",
    }


def validate_auth_smoke_receipt(
    receipt: Any,
    *,
    now: datetime,
    awaiting_at: datetime,
    new_container_id: str,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise GateError("authenticated smoke receipt is missing")
    reject_raw_secrets(receipt)
    if receipt.get("schema") != AUTH_SMOKE_SCHEMA or receipt.get("release") != RELEASE:
        raise GateError("authenticated smoke receipt identity is invalid")
    observed_at = parse_timestamp(receipt.get("observed_at"), "authenticated smoke observed_at")
    current = now.astimezone(timezone.utc)
    if observed_at < awaiting_at.astimezone(timezone.utc) or observed_at > current + timedelta(minutes=2):
        raise GateError("authenticated smoke timestamp is outside the cutover window")
    if current - observed_at > timedelta(minutes=15):
        raise GateError("authenticated smoke receipt is stale")
    if receipt.get("new_container_id") != new_container_id:
        raise GateError("authenticated smoke container identity does not match")
    if receipt.get("direct_windows_models_status") != 403:
        raise GateError("direct Windows AI access is not forbidden")
    if receipt.get("public_gateway_authenticated") is not True:
        raise GateError("public gateway authentication marker is missing")
    if receipt.get("credential_fingerprint_unchanged") is not True:
        raise GateError("credential fingerprint changed or was not verified")
    kind = receipt.get("verification_kind")
    if kind == "natural_completed_request":
        count = _require_int(receipt.get("successful_completed_requests"), "completed request count", minimum=1)
    elif kind == "public_models":
        if receipt.get("public_models_status") != 200 or receipt.get("public_response_object") != "list":
            raise GateError("authenticated public models probe did not return a successful list")
        count = _require_int(receipt.get("public_model_count"), "public model count", minimum=1)
    else:
        raise GateError("unsupported public verification kind")
    request_digest = _require_sha256(receipt.get("request_id_sha256"), "smoke request id SHA")
    summary_digest = _require_sha256(receipt.get("smoke_summary_sha256"), "smoke summary SHA")
    return {"observed_at":observed_at.isoformat(), "public_gateway_authenticated":True,
            "verification_kind":kind, "verified_count":count,
            "request_id_sha256":request_digest, "smoke_summary_sha256":summary_digest}


def atomic_write_bytes(path: pathlib.Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        # POSIX permits fsync on a directory to make the rename durable.
        # Windows does not expose an equivalent directory descriptor; the
        # production runner is Linux, while Windows support is retained for
        # deterministic offline tests.
        if os.name != "nt":
            directory_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: pathlib.Path, value: Mapping[str, Any], mode: int = 0o600) -> None:
    reject_raw_secrets(value)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    atomic_write_bytes(path, payload, mode)


class StageStore:
    def __init__(self, path: pathlib.Path):
        self.path = path

    def read(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schema") != STAGE_SCHEMA or value.get("release") != RELEASE:
            raise GateError("release stage file has an invalid identity")
        reject_raw_secrets(value)
        return value

    def write(self, stage: str, **fields: Any) -> dict[str, Any]:
        previous = self.read()
        value: dict[str, Any] = dict(previous or {})
        value.update(fields)
        value.update(
            {
                "schema": STAGE_SCHEMA,
                "release": RELEASE,
                "stage": stage,
                "sequence": int((previous or {}).get("sequence", 0)) + 1,
                "updated_at": utc_now().isoformat(),
            }
        )
        atomic_write_json(self.path, value)
        return value
