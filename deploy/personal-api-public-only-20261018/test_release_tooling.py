from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
import signal
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import relay_release_core as core
import relay_remote_runner as runner
import relay_remote_dispatch as dispatch


RELEASE = "personal-api-public-only-20261018-r1"
NOW = datetime(2026, 10, 17, 12, 30, tzinfo=timezone.utc)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class GateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.backup = self.root / "20261017T120000Z"
        self.backup.mkdir()
        (self.backup / "backup-state.json").write_bytes(
            b'{"status":"complete","consistency":"online",'
            b'"clickhouse":{"database":"default","backup_name":"fixture"}}'
        )
        (self.backup / "SHA256SUMS").write_bytes(b"fixture manifest\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def backup_state(self) -> dict[str, str]:
        return {
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "static",
            "Result": "success",
            "MainPID": "0",
            "ControlPID": "0",
            "Job": "",
            "InvocationID": "1" * 32,
            "ExecMainCode": "1",
            "ExecMainStatus": "0",
            "ExecMainStartTimestampMonotonic": "1000000",
            "ExecMainExitTimestampMonotonic": "2000000",
        }

    def backup_receipt(self) -> dict[str, object]:
        return {
            "schema": core.FRESH_BACKUP_SCHEMA,
            "release": RELEASE,
            "issued_at": "2026-10-17T12:05:00+00:00",
            "completed_at": "2026-10-17T12:04:00+00:00",
            "invocation_id": "1" * 32,
            "exec_main_start_timestamp_monotonic": "1000000",
            "exec_main_exit_timestamp_monotonic": "2000000",
            "backup_dir": str(self.backup),
            "backup_state_sha256": digest((self.backup / "backup-state.json").read_bytes()),
            "sha256sums_sha256": digest((self.backup / "SHA256SUMS").read_bytes()),
            "registered_services": 20,
            "dynamic_capacity": {
                "checker_sha256": core.EXPECTED_CAPACITY_CHECKER_SHA256,
                "checked_at": "2026-10-17T11:59:00+00:00",
                "exit_code": 0,
                "free_bytes": 400 * 1024**3,
                "required_bytes": 350 * 1024**3,
            },
        }

    def windows_receipt(self) -> dict[str, object]:
        return {
            "schema": core.WINDOWS_READY_SCHEMA,
            "release": RELEASE,
            "issued_at": "2026-10-17T12:10:00+00:00",
            "restart_completed_at": "2026-10-17T12:08:00+00:00",
            "active_connections_before_restart": 1,
            "idle_connection_gate": {
                "classification": "idle_retained_http_connection",
                "sample_count": 2,
                "sample_interval_seconds": 18,
                "send_queue_zero": True,
                "receive_queue_zero": True,
                "byte_counters_stable": True,
                "backend_connection_count": 0,
                "watchdog_stopped_before_restart": True,
            },
            "relay": {
                "pid": 4100,
                "started_at": "2026-10-17T12:07:00+00:00",
                "listener_count": 1,
                "listener_pid": 4100,
            },
            "backend": {"pid": 4200, "listener_count": 1, "listener_pid": 4200},
            "watchdog": {
                "state": "Enabled/Running",
                "stable_polls": 2,
                "pid_stable": True,
            },
            "hashes": {
                "start_services": core.EXPECTED_WINDOWS_START_SERVICES_SHA256,
                "proxy_server": core.EXPECTED_WINDOWS_PROXY_SERVER_SHA256,
            },
            "internal_key": {
                "length": core.EXPECTED_WINDOWS_INTERNAL_KEY_LENGTH,
                "sha256": core.EXPECTED_WINDOWS_INTERNAL_KEY_SHA256,
            },
            "anonymous_models_status": 401,
            "unmarked_models_status": 403,
            "remote_panel_status": 403,
            "firewall_restricted": True,
            "backend_loopback_only": True,
            "authorized_models_status": "deferred_to_post_cutover",
            "post_cutover_authenticated_smoke_required": True,
        }

    def test_r4_release_identity_and_restored_old_runtime_are_pinned(self) -> None:
        self.assertEqual(core.RELEASE, RELEASE)
        self.assertEqual(
            runner.NAME,
            "smartbrain-personal-key-api-20260923-filter-internal-r1",
        )
        self.assertEqual(runner.UNIT, "smartbrain-personal-gateway-current.service")
        self.assertEqual(
            runner.OLD_NAME,
            runner.NAME + "-rollback-public-only-20261018-r1",
        )
        self.assertEqual(
            runner.FAILED_NAME_PREFIX,
            runner.NAME + "-failed-public-only-20261018-r1-",
        )
        self.assertEqual(
            runner.CANDIDATE_NAME,
            "smartbrain-public-only-ready-20261018-r1",
        )
        self.assertEqual(
            runner.RELEASE_DIR,
            pathlib.Path(
                "/srv/smartbrain/releases/personal-api-public-only-20261018-r1"
            ),
        )
        self.assertEqual(
            dispatch.REMOTE_RELEASE,
            "/srv/smartbrain/releases/personal-api-public-only-20261018-r1",
        )
        self.assertEqual(
            runner.CANDIDATE_RESULT_PATH,
            pathlib.Path(
                "/srv/smartbrain/acceptance/personal-api-relay-auth-20261017/"
                "candidate-result.json"
            ),
        )
        self.assertEqual(
            runner.CANDIDATE_SOURCE_PATH,
            pathlib.Path(
                "/srv/smartbrain/acceptance/personal-api-relay-auth-20261017/"
                "candidate-input/personal_gateway_proxy.py"
            ),
        )
        self.assertEqual(
            runner.EXPECTED_OLD_ID,
            "7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20",
        )
        self.assertEqual(
            runner.EXPECTED_OLD_IMAGE,
            "sha256:532a68da4610413d60bfc861addfb341a7a862bc6819964aa3bfe218cecbf6cc",
        )
        self.assertEqual(
            runner.EXPECTED_OLD_STARTED_AT,
            "2026-10-17T13:44:51.228032986Z",
        )

    def test_dispatch_default_smoke_timeout_and_cap_remain_unchanged(self) -> None:
        self.assertEqual(
            inspect.signature(dispatch.build_dispatch_program)
            .parameters["smoke_timeout_seconds"]
            .default,
            300,
        )
        backup_receipt = {"schema": core.FRESH_BACKUP_SCHEMA, "release": RELEASE}
        windows_receipt = {"schema": core.WINDOWS_READY_SCHEMA, "release": RELEASE}
        _, manifest = dispatch.build_dispatch_program(
            "promote",
            attempt_id="20261017T123000Z",
            backup_receipt=backup_receipt,
            windows_receipt=windows_receipt,
        )
        self.assertEqual(manifest["unit"], "smartbrain-personal-public-only-promote-20261018-r1-20261017T123000Z")
        dispatch.build_dispatch_program(
            "promote",
            smoke_timeout_seconds=900,
            attempt_id="20261017T123001Z",
            backup_receipt=backup_receipt,
            windows_receipt=windows_receipt,
        )
        with self.assertRaisesRegex(ValueError, "between 60 and 900"):
            dispatch.build_dispatch_program(
                "promote",
                smoke_timeout_seconds=901,
                attempt_id="20261017T123002Z",
                backup_receipt=backup_receipt,
                windows_receipt=windows_receipt,
            )

    def test_complete_systemd_fields_are_required(self) -> None:
        state = self.backup_state()
        core.validate_backup_systemd_state(state)
        state.pop("ExecMainStatus")
        with self.assertRaisesRegex(core.GateError, "ExecMainStatus"):
            core.validate_backup_systemd_state(state)

    def test_timestamp_parser_accepts_powershell_seven_digit_fraction(self) -> None:
        parsed = core.parse_timestamp(
            "2026-10-17T18:49:24.4855363+08:00",
            "PowerShell timestamp",
        )
        self.assertEqual(parsed.isoformat(), "2026-10-17T10:49:24.485536+00:00")

    def test_fresh_backup_binds_invocation_timestamps_and_artifacts(self) -> None:
        receipt = self.backup_receipt()
        result = core.validate_fresh_backup_receipt(
            receipt,
            self.backup_state(),
            now=NOW,
            backup_root=self.root,
        )
        self.assertEqual(result["invocation_id"], "1" * 32)

        stale = dict(receipt)
        stale["invocation_id"] = "2" * 32
        with self.assertRaisesRegex(core.GateError, "Invocation"):
            core.validate_fresh_backup_receipt(
                stale, self.backup_state(), now=NOW, backup_root=self.root
            )

        (self.backup / "SHA256SUMS").write_bytes(b"tampered")
        with self.assertRaisesRegex(core.GateError, "SHA256SUMS"):
            core.validate_fresh_backup_receipt(
                receipt, self.backup_state(), now=NOW, backup_root=self.root
            )

    def test_preflight_age_is_anchored_to_backup_start_not_release_time(self) -> None:
        receipt = self.backup_receipt()
        receipt["dynamic_capacity"]["checked_at"] = "2026-10-17T11:59:30+00:00"
        receipt["completed_at"] = "2026-10-17T13:58:00+00:00"
        receipt["issued_at"] = "2026-10-17T13:59:00+00:00"

        result = core.validate_fresh_backup_receipt(
            receipt,
            self.backup_state(),
            now=datetime(2026, 10, 17, 14, 0, tzinfo=timezone.utc),
            backup_root=self.root,
        )

        self.assertEqual(
            result["dynamic_capacity"]["checked_at"],
            "2026-10-17T11:59:30+00:00",
        )

    def test_preflight_must_be_tightly_bound_before_backup_start(self) -> None:
        now = datetime(2026, 10, 17, 14, 0, tzinfo=timezone.utc)
        for checked_at in (
            "2026-10-17T11:49:59+00:00",
            "2026-10-17T12:00:01+00:00",
        ):
            with self.subTest(checked_at=checked_at):
                receipt = self.backup_receipt()
                receipt["dynamic_capacity"]["checked_at"] = checked_at
                receipt["completed_at"] = "2026-10-17T13:58:00+00:00"
                receipt["issued_at"] = "2026-10-17T13:59:00+00:00"
                with self.assertRaisesRegex(core.GateError, "preflight.*backup start"):
                    core.validate_fresh_backup_receipt(
                        receipt,
                        self.backup_state(),
                        now=now,
                        backup_root=self.root,
                    )

    def test_fresh_receipt_age_and_preflight_not_before_remain_enforced(self) -> None:
        stale = self.backup_receipt()
        with self.assertRaisesRegex(core.GateError, "fresh backup receipt is stale"):
            core.validate_fresh_backup_receipt(
                stale,
                self.backup_state(),
                now=datetime(2026, 10, 17, 14, 6, tzinfo=timezone.utc),
                backup_root=self.root,
            )

        predating = self.backup_receipt()
        predating["dynamic_capacity"]["checked_at"] = (
            "2026-10-17T08:19:36+00:00"
        )
        with self.assertRaisesRegex(core.GateError, "predates the release gate"):
            core.validate_fresh_backup_receipt(
                predating,
                self.backup_state(),
                now=NOW,
                backup_root=self.root,
            )

    def test_fresh_backup_requires_real_complete_online_state(self) -> None:
        receipt = self.backup_receipt()
        backup_state_path = self.backup / "backup-state.json"

        backup_state_path.write_bytes(
            b'{"status":"complete","consistency":"offline",'
            b'"clickhouse":{"database":"default","backup_name":"fixture"}}'
        )
        receipt["backup_state_sha256"] = digest(backup_state_path.read_bytes())
        with self.assertRaisesRegex(core.GateError, "online consistency"):
            core.validate_fresh_backup_receipt(
                receipt, self.backup_state(), now=NOW, backup_root=self.root
            )

        backup_state_path.write_bytes(
            b'{"status":"success","consistency":"online",'
            b'"clickhouse":{"database":"default","backup_name":"fixture"}}'
        )
        receipt["backup_state_sha256"] = digest(backup_state_path.read_bytes())
        with self.assertRaisesRegex(core.GateError, "complete status"):
            core.validate_fresh_backup_receipt(
                receipt, self.backup_state(), now=NOW, backup_root=self.root
            )

    def test_windows_ready_requires_new_runtime_and_explicit_post_cutover_probe(self) -> None:
        receipt = self.windows_receipt()
        result = core.validate_windows_ready_receipt(receipt, now=NOW)
        self.assertEqual(result["relay_pid"], 4100)

        no_post_cutover_gate = json.loads(json.dumps(receipt))
        no_post_cutover_gate["authorized_models_status"] = 401
        with self.assertRaisesRegex(core.GateError, "post-cutover"):
            core.validate_windows_ready_receipt(no_post_cutover_gate, now=NOW)

        active_stream = json.loads(json.dumps(receipt))
        active_stream["idle_connection_gate"]["byte_counters_stable"] = False
        with self.assertRaisesRegex(core.GateError, "idle connection"):
            core.validate_windows_ready_receipt(active_stream, now=NOW)

        duplicate = json.loads(json.dumps(receipt))
        duplicate["relay"]["listener_count"] = 2
        with self.assertRaisesRegex(core.GateError, "listener"):
            core.validate_windows_ready_receipt(duplicate, now=NOW)

    def test_receipts_reject_raw_secret_fields(self) -> None:
        receipt = self.windows_receipt()
        receipt["authorization"] = "Bearer should-never-be-stored"
        with self.assertRaisesRegex(core.GateError, "secret"):
            core.validate_windows_ready_receipt(receipt, now=NOW)


class FakeRecoveryOps:
    def __init__(self, *, phase: str, expected_network: dict[str, dict[str, object]]):
        detached = phase in {
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
        renamed = phase in {
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
        has_new = phase in {
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
        self.expected_network = expected_network
        self.containers = {
            "old-id": {
                "Id": "old-id",
                "Name": "/" + (runner.OLD_NAME if renamed else runner.NAME),
                "Image": runner.EXPECTED_OLD_IMAGE,
                "Created": "2026-10-17T12:00:00+00:00",
                "Config": {"Labels": {}},
                "running": False,
                "fingerprint": "f" * 64,
                "network": {} if detached else json.loads(json.dumps(expected_network)),
            }
        }
        if has_new:
            self.containers["new-id"] = {
                "Id": "new-id",
                "Name": "/" + runner.NAME,
                "Image": "sha256:" + "d" * 64,
                "Created": "2026-10-17T12:21:00+00:00",
                "Config": {"Labels": {"smartbrain.scope": core.RELEASE}},
                "running": phase in {
                    "new_started",
                    "inventory_updated",
                    "awaiting_smoke",
                    "recovery_started",
                    "recovery_failed",
                },
                "fingerprint": "n" * 64,
                "network": json.loads(json.dumps(expected_network)),
            }
        self.unit_bytes = b"new unit"
        self.inventory_bytes = b'{"container_id":"new-id"}'
        self.calls: list[str] = []

    def stop_unit(self) -> None:
        self.calls.append("stop_unit")

    def container_exists(self, container_id: str) -> bool:
        return container_id in self.containers

    def inspect(self, container_id: str) -> dict[str, object]:
        return self.containers[container_id]

    def stop_container(self, container_id: str) -> None:
        self.calls.append("stop:" + container_id)
        self.containers[container_id]["running"] = False

    def detach_container(self, container_id: str) -> None:
        self.calls.append("detach:" + container_id)
        self.containers[container_id]["network"] = {}

    def container_name(self, container_id: str) -> str:
        return str(self.containers[container_id]["Name"])

    def name_owner(self, name: str) -> str | None:
        wanted = "/" + name
        for container_id, value in self.containers.items():
            if value["Name"] == wanted:
                return container_id
        return None

    def rename_container(self, container_id: str, name: str) -> None:
        owner = self.name_owner(name)
        if owner is not None and owner != container_id:
            raise RuntimeError("name collision")
        self.calls.append(f"rename:{container_id}:{name}")
        self.containers[container_id]["Name"] = "/" + name

    def connect_network(self, container_id: str, name: str, endpoint: dict[str, object]) -> None:
        self.calls.append(f"connect:{container_id}:{name}")
        self.containers[container_id]["network"][name] = json.loads(json.dumps(endpoint))

    def network_shape(self, container_id: str) -> dict[str, dict[str, object]]:
        return json.loads(json.dumps(self.containers[container_id]["network"]))

    def write_unit(self, value: bytes) -> None:
        self.calls.append("write_unit")
        self.unit_bytes = value

    def write_inventory(self, value: bytes) -> None:
        self.calls.append("write_inventory")
        self.inventory_bytes = value

    def daemon_reload(self) -> None:
        self.calls.append("daemon_reload")

    def reset_failed_unit(self) -> None:
        self.calls.append("reset_failed")

    def start_unit(self) -> None:
        self.calls.append("start_unit")
        self.containers["old-id"]["running"] = True

    def wait_running(self, container_id: str) -> None:
        if not self.containers[container_id]["running"]:
            raise RuntimeError("not running")

    def fingerprint(self, container_id: str) -> str:
        return str(self.containers[container_id]["fingerprint"])

    def container_running(self, container_id: str) -> bool:
        return bool(self.containers[container_id]["running"])

    def read_unit_bytes(self) -> bytes:
        return self.unit_bytes

    def read_inventory_bytes(self) -> bytes:
        return self.inventory_bytes

    def validate_restored_unit(self, old_id: str) -> None:
        if old_id != "old-id" or not self.containers[old_id]["running"]:
            raise RuntimeError("unit not restored")

    def validate_restored_public(self) -> dict[str, int]:
        return {"health": 200, "anonymous_models": 401}


class RecoveryTests(unittest.TestCase):
    def test_each_destructive_stage_recovers_exact_old_identity(self) -> None:
        recoverable_stages = (
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
        )
        self.assertEqual(
            set(recoverable_stages) | {"recovery_failed"},
            runner.DESTRUCTIVE_STAGES,
        )
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]},
            "smartbrain_data": {"IPAddress": "172.19.0.10", "Aliases": [runner.NAME]},
            "smartbrain_host-ingress": {"IPAddress": "172.20.0.10", "Aliases": [runner.NAME]},
        }
        for phase in recoverable_stages:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                unit = root / "old-unit.service"
                inventory = root / "old-inventory.json"
                unit.write_bytes(b"old unit")
                inventory.write_bytes(b'{"container_id":"old-id"}')
                store = core.StageStore(root / "stage.json")
                fields = {
                    "old_id": "old-id",
                    "new_id": (
                        None
                        if phase
                        in {
                            "cutover_starting",
                            "old_stopped",
                            "old_detached",
                            "old_renamed",
                            "new_create_planned",
                        }
                        else "new-id"
                    ),
                    "old_fingerprint": "f" * 64,
                    "old_network": expected_network,
                    "unit_backup_path": str(unit),
                    "unit_backup_sha256": digest(unit.read_bytes()),
                    "inventory_backup_path": str(inventory),
                    "inventory_backup_sha256": digest(inventory.read_bytes()),
                }
                if phase == "new_create_planned":
                    fields["planned_new_name"] = runner.NAME
                    fields["planned_new_image"] = "sha256:" + "d" * 64
                    fields["new_create_intent_at"] = "2026-10-17T12:20:00+00:00"
                store.write(phase, **fields)
                ops = FakeRecoveryOps(phase=phase, expected_network=expected_network)
                result = runner.recover_release(ops, store, reason="failure-injection")
                self.assertEqual(result["stage"], "restored")
                self.assertEqual(ops.container_name("old-id"), "/" + runner.NAME)
                self.assertTrue(ops.containers["old-id"]["running"])
                self.assertEqual(ops.network_shape("old-id"), expected_network)
                self.assertEqual(ops.unit_bytes, b"old unit")
                self.assertEqual(ops.inventory_bytes, b'{"container_id":"old-id"}')

                # Recovery is idempotent after the terminal restored stage.
                again = runner.recover_release(ops, store, reason="repeat")
                self.assertEqual(again["stage"], "restored")

    def test_failed_container_name_collision_cannot_block_restore(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "old-unit.service"
            inventory = root / "old-inventory.json"
            unit.write_bytes(b"old unit")
            inventory.write_bytes(b"old inventory")
            store = core.StageStore(root / "stage.json")
            store.write(
                "new_started",
                old_id="old-id",
                new_id="new-id",
                old_fingerprint="f" * 64,
                old_network=expected_network,
                unit_backup_path=str(unit),
                unit_backup_sha256=digest(unit.read_bytes()),
                inventory_backup_path=str(inventory),
                inventory_backup_sha256=digest(inventory.read_bytes()),
            )
            ops = FakeRecoveryOps(phase="new_started", expected_network=expected_network)
            ops.containers["collision"] = {
                "Id": "collision",
                "Name": "/" + runner.FAILED_NAME_PREFIX + "new-id",
                "running": False,
                "fingerprint": "c" * 64,
                "network": {},
            }
            runner.recover_release(ops, store, reason="collision")
            self.assertEqual(ops.container_name("old-id"), "/" + runner.NAME)

    def test_create_intent_recovers_exact_name_owner_when_new_id_was_not_returned(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "old-unit.service"
            inventory = root / "old-inventory.json"
            unit.write_bytes(b"old unit")
            inventory.write_bytes(b"old inventory")
            store = core.StageStore(root / "stage.json")
            store.write(
                "new_create_planned",
                old_id="old-id",
                old_fingerprint="f" * 64,
                old_network=expected_network,
                unit_backup_path=str(unit),
                unit_backup_sha256=digest(unit.read_bytes()),
                inventory_backup_path=str(inventory),
                inventory_backup_sha256=digest(inventory.read_bytes()),
                planned_new_name=runner.NAME,
                planned_new_image="sha256:" + "d" * 64,
                new_create_intent_at="2026-10-17T12:20:00+00:00",
            )
            ops = FakeRecoveryOps(
                phase="new_create_planned", expected_network=expected_network
            )
            result = runner.recover_release(ops, store, reason="create-return-interrupted")
            self.assertEqual(result["stage"], "restored")
            self.assertEqual(ops.container_name("old-id"), "/" + runner.NAME)
            self.assertTrue(
                ops.container_name("new-id").startswith("/" + runner.FAILED_NAME_PREFIX)
            )

    def test_recovery_failed_after_delayed_owner_refuses_a_second_mutating_recovery(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }

        class DelayedOwnerOps(FakeRecoveryOps):
            first_lookup = True

            def name_owner(self, name: str) -> str | None:
                if name == runner.NAME and self.first_lookup:
                    self.first_lookup = False
                    return None
                return super().name_owner(name)

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "old-unit.service"
            inventory = root / "old-inventory.json"
            unit.write_bytes(b"old unit")
            inventory.write_bytes(b"old inventory")
            store = core.StageStore(root / "stage.json")
            store.write(
                "new_create_planned",
                old_id="old-id",
                old_fingerprint="f" * 64,
                old_network=expected_network,
                unit_backup_path=str(unit),
                unit_backup_sha256=digest(unit.read_bytes()),
                inventory_backup_path=str(inventory),
                inventory_backup_sha256=digest(inventory.read_bytes()),
                planned_new_name=runner.NAME,
                planned_new_image="sha256:" + "d" * 64,
                new_create_intent_at="2026-10-17T12:20:00+00:00",
            )
            ops = DelayedOwnerOps(
                phase="new_create_planned", expected_network=expected_network
            )
            with self.assertRaisesRegex(core.GateError, "unexpected container"):
                runner.recover_release(ops, store, reason="owner-not-visible-yet")
            self.assertEqual(store.read()["stage"], "recovery_failed")
            calls_after_first_attempt = list(ops.calls)
            containers_after_first_attempt = json.loads(json.dumps(ops.containers))
            with self.assertRaises(core.GateError):
                runner.recover_release(ops, store, reason="owner-now-visible")
            self.assertEqual(store.read()["stage"], "recovery_failed")
            self.assertEqual(ops.calls, calls_after_first_attempt)
            self.assertEqual(ops.containers, containers_after_first_attempt)

    def test_planned_owner_with_wrong_identity_is_rejected(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        for field, value in (
            ("Image", "sha256:" + "e" * 64),
            ("Created", "2026-10-17T12:19:59+00:00"),
            ("Config", {"Labels": {"smartbrain.scope": "other-release"}}),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                unit = root / "old-unit.service"
                inventory = root / "old-inventory.json"
                unit.write_bytes(b"old unit")
                inventory.write_bytes(b"old inventory")
                store = core.StageStore(root / "stage.json")
                store.write(
                    "new_create_planned",
                    old_id="old-id",
                    old_fingerprint="f" * 64,
                    old_network=expected_network,
                    unit_backup_path=str(unit),
                    unit_backup_sha256=digest(unit.read_bytes()),
                    inventory_backup_path=str(inventory),
                    inventory_backup_sha256=digest(inventory.read_bytes()),
                    planned_new_name=runner.NAME,
                    planned_new_image="sha256:" + "d" * 64,
                    new_create_intent_at="2026-10-17T12:20:00+00:00",
                )
                ops = FakeRecoveryOps(
                    phase="new_create_planned", expected_network=expected_network
                )
                ops.containers["new-id"][field] = value
                with self.assertRaisesRegex(core.GateError, "planned new container identity"):
                    runner.recover_release(ops, store, reason="wrong-planned-owner")
                self.assertEqual(ops.container_name("old-id"), "/" + runner.OLD_NAME)

    def test_unplanned_name_owner_is_never_adopted_for_recovery(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "old-unit.service"
            inventory = root / "old-inventory.json"
            unit.write_bytes(b"old unit")
            inventory.write_bytes(b"old inventory")
            store = core.StageStore(root / "stage.json")
            store.write(
                "old_renamed",
                old_id="old-id",
                old_fingerprint="f" * 64,
                old_network=expected_network,
                unit_backup_path=str(unit),
                unit_backup_sha256=digest(unit.read_bytes()),
                inventory_backup_path=str(inventory),
                inventory_backup_sha256=digest(inventory.read_bytes()),
            )
            ops = FakeRecoveryOps(phase="new_created", expected_network=expected_network)
            with self.assertRaisesRegex(core.GateError, "unexpected container"):
                runner.recover_release(ops, store, reason="unplanned-owner")

    def test_promoted_stage_is_terminal_and_recovery_only_rechecks_evidence(self) -> None:
        runtime = {"unit": "active/enabled", "public_anonymous": 401}
        report = {
            "schema": "smartbrain.personal-relay-promoted/v1",
            "release": RELEASE,
            "status": "passed",
            "finalized_at": "2026-10-17T12:30:00+00:00",
            "new_id": "new-id",
            "old_id": "old-id",
            "candidate_image": "sha256:" + "d" * 64,
            "candidate_source_sha256": "e" * 64,
            "authenticated_smoke": {"request_id_sha256": "b" * 64},
            "runtime": runtime,
        }

        class Ops:
            def __init__(self):
                self.reports = []

            def validate_promoted_runtime(self, new_id):
                self.validated = new_id
                return runtime

            def write_promoted(self, value):
                self.reports.append(dict(value))

        with tempfile.TemporaryDirectory() as directory:
            store = core.StageStore(pathlib.Path(directory) / "stage.json")
            store.write(
                "promoted",
                old_id="old-id",
                new_id="new-id",
                promoted_report=report,
                promoted_report_sha256=digest(runner._promoted_report_bytes(report)),
            )
            ops = Ops()
            result = runner.recover_release(ops, store, reason="must-not-rollback")
            self.assertEqual(result["stage"], "promoted")
            self.assertEqual(ops.validated, "new-id")
            self.assertEqual(ops.reports, [report])


class PromotionBoundaryTests(unittest.TestCase):
    def test_stale_pre_r3_restore_started_at_is_rejected_before_mutation(self) -> None:
        candidate_image = "sha256:" + "d" * 64
        source_bytes = b"candidate source"
        source_digest = digest(source_bytes)

        class Ops:
            mutations = 0

            def container_exists(self, reference):
                return reference == candidate_image

            def inspect(self, reference):
                self.inspected = reference
                return {
                    "Id": runner.EXPECTED_OLD_ID,
                    "Image": runner.EXPECTED_OLD_IMAGE,
                    "State": {
                        "StartedAt": "2026-10-17T13:08:12.815573307Z",
                        "Running": True,
                    },
                }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "current.service"
            inventory = root / "inventory.json"
            source = root / "candidate.py"
            candidate_result = root / "candidate-result.json"
            fresh = root / "fresh.json"
            windows = root / "windows.json"
            unit.write_bytes(b"old unit")
            inventory.write_text(
                json.dumps({"container_id": runner.EXPECTED_OLD_ID}), encoding="utf-8"
            )
            source.write_bytes(source_bytes)
            candidate_result.write_text(
                json.dumps(
                    {
                        "status": "candidate-tested-no-promote",
                        "tests_exit": 0,
                        "candidate_image": candidate_image,
                        "base_image": runner.EXPECTED_OLD_IMAGE,
                        "source_sha256": source_digest,
                    }
                ),
                encoding="utf-8",
            )
            fresh.write_text("{}", encoding="utf-8")
            windows.write_text("{}", encoding="utf-8")
            store = core.StageStore(root / "stage.json")
            ops = Ops()
            with mock.patch.multiple(
                runner,
                AUTH_SMOKE_RECEIPT_PATH=root / "smoke.json",
                PENDING_MARKER=root / "pending",
                UNIT_PATH=unit,
                INVENTORY_PATH=inventory,
                FRESH_BACKUP_RECEIPT_PATH=fresh,
                WINDOWS_READY_RECEIPT_PATH=windows,
                CANDIDATE_RESULT_PATH=candidate_result,
                CANDIDATE_SOURCE_PATH=source,
                BACKUP_ROOT=root / "backups",
            ), mock.patch.object(
                runner,
                "validate_release_gates",
                return_value={
                    "backup": {"invocation_id": "f" * 32},
                    "windows": {"relay_pid": 476},
                },
            ):
                with self.assertRaisesRegex(
                    core.GateError, "current personal gateway identity changed"
                ):
                    runner.promote_release(ops, store, smoke_timeout_seconds=300)
            self.assertEqual(ops.mutations, 0)
            self.assertEqual(ops.inspected, runner.NAME)
            self.assertIsNone(store.read())

    def test_current_container_create_is_bracketed_by_intent_and_id_receipts(self) -> None:
        source = inspect.getsource(runner.promote_release)
        intent = source.index('"new_create_planned",\n')
        create = source.index("new_id = ops.create_container(NAME, config)")
        receipt = source.index('store.write("new_created", new_id=new_id)')
        self.assertLess(intent, create)
        self.assertLess(create, receipt)

    def test_sigterm_during_first_recovery_material_write_is_settled(self) -> None:
        class Ops:
            def container_exists(self, reference):
                return reference == candidate_image

            def inspect(self, reference):
                self.assert_reference = reference
                return old

            def validate_unit(self, container_id):
                return {}

            def network_shape_data(self, container):
                return expected_network

            def fingerprint_data(self, container):
                return "f" * 64

            def secret_safe_env_summary(self, config):
                return []

        candidate_image = "sha256:" + "d" * 64
        source_bytes = b"candidate source"
        source_digest = digest(source_bytes)
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        old = {
            "Id": runner.EXPECTED_OLD_ID,
            "Image": runner.EXPECTED_OLD_IMAGE,
            "State": {
                "StartedAt": runner.EXPECTED_OLD_STARTED_AT,
                "Running": True,
            },
            "Config": {"Env": [], "Labels": {}},
            "HostConfig": {},
            "NetworkSettings": {"Networks": expected_network},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "current.service"
            inventory = root / "inventory.json"
            source = root / "candidate.py"
            candidate_result = root / "candidate-result.json"
            fresh = root / "fresh.json"
            windows = root / "windows.json"
            unit.write_bytes(b"old unit")
            inventory.write_text(
                json.dumps({"container_id": runner.EXPECTED_OLD_ID}), encoding="utf-8"
            )
            source.write_bytes(source_bytes)
            candidate_result.write_text(
                json.dumps(
                    {
                        "status": "candidate-tested-no-promote",
                        "tests_exit": 0,
                        "candidate_image": candidate_image,
                        "base_image": runner.EXPECTED_OLD_IMAGE,
                        "source_sha256": source_digest,
                    }
                ),
                encoding="utf-8",
            )
            fresh.write_text("{}", encoding="utf-8")
            windows.write_text("{}", encoding="utf-8")
            store = core.StageStore(root / "stage.json")
            original_atomic = core.atomic_write_bytes
            calls = 0

            def interrupt_first_write(path, data, mode=0o600):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise runner.TerminationRequested("during rollback material write")
                return original_atomic(path, data, mode)

            with mock.patch.multiple(
                runner,
                AUTH_SMOKE_RECEIPT_PATH=root / "smoke.json",
                PENDING_MARKER=root / "pending",
                UNIT_PATH=unit,
                INVENTORY_PATH=inventory,
                FRESH_BACKUP_RECEIPT_PATH=fresh,
                WINDOWS_READY_RECEIPT_PATH=windows,
                CANDIDATE_RESULT_PATH=candidate_result,
                CANDIDATE_SOURCE_PATH=source,
                ROLLBACK_DIR=root / "rollback",
                EVIDENCE_DIR=root / "evidence",
                BACKUP_ROOT=root / "backups",
            ), mock.patch.object(
                runner,
                "validate_release_gates",
                return_value={
                    "backup": {"invocation_id": "f" * 32},
                    "windows": {"relay_pid": 476},
                },
            ), mock.patch.object(
                core, "atomic_write_bytes", side_effect=interrupt_first_write
            ):
                with self.assertRaises(runner.TerminationRequested):
                    runner.promote_release(Ops(), store, smoke_timeout_seconds=300)
            self.assertEqual(store.read()["stage"], "precutover_failed")
            failure = json.loads((root / "evidence" / "promotion-failed.json").read_text())
            self.assertEqual(failure["error_type"], "TerminationRequested")

    def test_container_existence_probe_has_a_finite_timeout(self) -> None:
        completed = subprocess.CompletedProcess(["docker", "inspect", "missing"], 1)
        with mock.patch.object(runner.subprocess, "run", return_value=completed) as called:
            self.assertFalse(runner.RealOps().container_exists("missing"))
        self.assertEqual(called.call_args.kwargs["timeout"], 60)

    def test_failure_evidence_write_cannot_prevent_destructive_stage_recovery(self) -> None:
        expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]}
        }
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unit = root / "old-unit.service"
            inventory = root / "old-inventory.json"
            unit.write_bytes(b"old unit")
            inventory.write_bytes(b"old inventory")
            store = core.StageStore(root / "stage.json")
            store.write(
                "old_renamed",
                old_id="old-id",
                old_fingerprint="f" * 64,
                old_network=expected_network,
                unit_backup_path=str(unit),
                unit_backup_sha256=digest(unit.read_bytes()),
                inventory_backup_path=str(inventory),
                inventory_backup_sha256=digest(inventory.read_bytes()),
            )
            ops = FakeRecoveryOps(phase="old_renamed", expected_network=expected_network)
            original_write_json = core.atomic_write_json

            def fail_only_diagnostic(path, value, mode=0o600):
                if pathlib.Path(path).name == "promotion-failed.json":
                    raise OSError("diagnostic filesystem unavailable")
                return original_write_json(path, value, mode)

            with mock.patch.object(runner, "EVIDENCE_DIR", root / "evidence"), mock.patch.object(
                core, "atomic_write_json", side_effect=fail_only_diagnostic
            ):
                result = runner._settle_promotion_failure(
                    ops,
                    store,
                    error=RuntimeError("injected cutover failure"),
                    old_id="old-id",
                    candidate_id=None,
                    new_id=None,
                )
            self.assertEqual(result["stage"], "restored")
            self.assertEqual(ops.container_name("old-id"), "/" + runner.NAME)


class PreflightTests(GateContractTests):
    def test_successful_fresh_backup_does_not_require_a_second_dynamic_budget(self) -> None:
        class Ops:
            def backup_state(self):
                return self_state

            def read_static_capacity(self):
                return {
                    "checked_at": "2026-10-17T12:29:00+00:00",
                    "disk_free_bytes": {
                        path: threshold for path, threshold in core.STATIC_DISK_THRESHOLDS.items()
                    },
                    "memory_available_bytes": core.MIN_MEMORY_AVAILABLE_BYTES,
                }

            def run_dynamic_capacity(self):
                raise AssertionError("post-backup dynamic checker must not run")

            def verify_backup_registration(self):
                return 20

        self_state = self.backup_state()
        result = runner.validate_release_gates(
            Ops(),
            self.backup_receipt(),
            self.windows_receipt(),
            now=NOW,
            backup_root=self.root,
        )
        self.assertEqual(
            result["static_capacity"]["disk_free_bytes"],
            core.STATIC_DISK_THRESHOLDS,
        )

    def test_post_backup_static_capacity_failure_is_before_any_mutation(self) -> None:
        class Ops:
            mutations = 0

            def backup_state(self):
                return self_state

            def read_static_capacity(self):
                return {
                    "checked_at": "2026-10-17T12:29:00+00:00",
                    "disk_free_bytes": {
                        "/var/lib/docker": 40 * 1024**3,
                        "/srv/smartbrain": 20 * 1024**3,
                        "/srv/smartbrain-backups": 250 * 1024**3 - 1,
                        "/srv/smartbrain-cold": 250 * 1024**3,
                    },
                    "memory_available_bytes": 2 * 1024**3,
                }

            def run_dynamic_capacity(self):
                raise AssertionError("pre-backup dynamic capacity must not be rerun after backup")

            def verify_backup_registration(self):
                return 20

        self_state = self.backup_state()
        with self.assertRaisesRegex(core.GateError, "/srv/smartbrain-backups"):
            runner.validate_release_gates(
                Ops(),
                self.backup_receipt(),
                self.windows_receipt(),
                now=NOW,
                backup_root=self.root,
            )
        self.assertEqual(Ops.mutations, 0)


class FinalizeTests(unittest.TestCase):
    def test_only_authenticated_200_smoke_can_mark_promoted(self) -> None:
        class Ops:
            def validate_promoted_runtime(self, new_id):
                self.validated = new_id
                return {"unit": "active/enabled", "public_anonymous": 401}

            def write_promoted(self, report):
                self.report = report

        with tempfile.TemporaryDirectory() as directory:
            store = core.StageStore(pathlib.Path(directory) / "stage.json")
            store.write(
                "awaiting_smoke",
                old_id="old-id",
                new_id="new-id",
                awaiting_smoke_at="2026-10-17T12:20:00+00:00",
            )
            receipt = {
                "schema": core.AUTH_SMOKE_SCHEMA,
                "release": RELEASE,
                "observed_at": "2026-10-17T12:21:00+00:00",
                "new_container_id": "new-id",
                "public_models_status": 200,
                "direct_windows_models_status": 403,
                "public_gateway_authenticated": True,
                "public_response_object": "list",
                "credential_fingerprint_unchanged": True,
                "public_model_count": 4,
                "verification_kind": "public_models",
                "request_id_sha256": "b" * 64,
                "smoke_summary_sha256": "c" * 64,
            }
            ops = Ops()
            result = runner.finalize_release(ops, store, receipt, now=NOW)
            self.assertEqual(result["stage"], "promoted")
            self.assertEqual(ops.validated, "new-id")
            self.assertEqual(ops.report["status"], "passed")

    def test_stage_commit_interruption_materializes_terminal_evidence_idempotently(self) -> None:
        class InterruptAfterPromotedStore(core.StageStore):
            interrupted = False

            def write(self, stage, **fields):
                value = super().write(stage, **fields)
                if stage == "promoted" and not self.interrupted:
                    self.interrupted = True
                    raise runner.TerminationRequested("after promoted stage commit")
                return value

        class Ops:
            def __init__(self):
                self.reports = []

            def validate_promoted_runtime(self, new_id):
                return {"unit": "active/enabled", "public_anonymous": 401}

            def write_promoted(self, report):
                self.reports.append(dict(report))

        with tempfile.TemporaryDirectory() as directory:
            store = InterruptAfterPromotedStore(pathlib.Path(directory) / "stage.json")
            store.write(
                "awaiting_smoke",
                old_id="old-id",
                new_id="new-id",
                candidate_image="sha256:" + "d" * 64,
                candidate_source_sha256="e" * 64,
                awaiting_smoke_at="2026-10-17T12:20:00+00:00",
            )
            ops = Ops()
            result = runner.finalize_release(ops, store, self.valid_receipt(), now=NOW)
            self.assertEqual(result["stage"], "promoted")
            self.assertEqual(len(ops.reports), 1)
            self.assertEqual(
                result["promoted_report_sha256"], digest(runner._promoted_report_bytes(ops.reports[0]))
            )

    def test_terminal_evidence_interruption_retries_from_authoritative_stage(self) -> None:
        class Ops:
            def __init__(self):
                self.reports = []

            def validate_promoted_runtime(self, new_id):
                return {"unit": "active/enabled", "public_anonymous": 401}

            def write_promoted(self, report):
                self.reports.append(dict(report))
                if len(self.reports) == 1:
                    raise runner.TerminationRequested("after promoted evidence write")

        with tempfile.TemporaryDirectory() as directory:
            store = core.StageStore(pathlib.Path(directory) / "stage.json")
            store.write(
                "awaiting_smoke",
                old_id="old-id",
                new_id="new-id",
                candidate_image="sha256:" + "d" * 64,
                candidate_source_sha256="e" * 64,
                awaiting_smoke_at="2026-10-17T12:20:00+00:00",
            )
            ops = Ops()
            result = runner.finalize_release(ops, store, self.valid_receipt(), now=NOW)
            self.assertEqual(result["stage"], "promoted")
            self.assertEqual(len(ops.reports), 2)
            self.assertEqual(ops.reports[0], ops.reports[1])

    @staticmethod
    def valid_receipt() -> dict[str, object]:
        return {
            "schema": core.AUTH_SMOKE_SCHEMA,
            "release": RELEASE,
            "observed_at": "2026-10-17T12:21:00+00:00",
            "new_container_id": "new-id",
            "public_models_status": 200,
            "direct_windows_models_status": 403,
            "public_gateway_authenticated": True,
            "public_response_object": "list",
            "credential_fingerprint_unchanged": True,
            "public_model_count": 4,
            "verification_kind": "public_models",
            "request_id_sha256": "b" * 64,
            "smoke_summary_sha256": "c" * 64,
        }

    def test_tampered_authenticated_smoke_predicates_never_mark_promoted(self) -> None:
        class Ops:
            def validate_promoted_runtime(self, new_id):
                raise AssertionError("runtime validation must not run")

            def write_promoted(self, report):
                raise AssertionError("promoted evidence must not be written")

        valid = {
            "schema": core.AUTH_SMOKE_SCHEMA,
            "release": RELEASE,
            "observed_at": "2026-10-17T12:21:00+00:00",
            "new_container_id": "new-id",
            "public_models_status": 200,
            "direct_windows_models_status": 403,
            "public_gateway_authenticated": True,
            "public_response_object": "list",
            "credential_fingerprint_unchanged": True,
            "public_model_count": 4,
            "verification_kind": "public_models",
            "request_id_sha256": "b" * 64,
            "smoke_summary_sha256": "c" * 64,
        }
        for field, tampered in (
            ("public_gateway_authenticated", False),
            ("public_response_object", "error"),
            ("credential_fingerprint_unchanged", False),
            ("public_model_count", 0),
            ("direct_windows_models_status", 200),
            ("smoke_summary_sha256", "invalid"),
        ):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    store = core.StageStore(pathlib.Path(directory) / "stage.json")
                    store.write(
                        "awaiting_smoke",
                        old_id="old-id",
                        new_id="new-id",
                        awaiting_smoke_at="2026-10-17T12:20:00+00:00",
                    )
                    receipt = dict(valid)
                    receipt[field] = tampered
                    with self.assertRaises(core.GateError):
                        runner.finalize_release(Ops(), store, receipt, now=NOW)
                    self.assertEqual(store.read()["stage"], "awaiting_smoke")

    def test_anonymous_only_or_failed_smoke_never_marks_promoted(self) -> None:
        class Ops:
            def validate_promoted_runtime(self, new_id):
                raise AssertionError("runtime validation must not run")

            def write_promoted(self, report):
                raise AssertionError("promoted evidence must not be written")

        with tempfile.TemporaryDirectory() as directory:
            store = core.StageStore(pathlib.Path(directory) / "stage.json")
            store.write(
                "awaiting_smoke",
                old_id="old-id",
                new_id="new-id",
                awaiting_smoke_at="2026-10-17T12:20:00+00:00",
            )
            receipt = {
                "schema": core.AUTH_SMOKE_SCHEMA,
                "release": RELEASE,
                "observed_at": "2026-10-17T12:21:00+00:00",
                "new_container_id": "new-id",
                "public_models_status": 401,
                "direct_windows_models_status": 403,
                "request_id_sha256": "b" * 64,
            }
            with self.assertRaisesRegex(core.GateError, "authentication marker"):
                runner.finalize_release(Ops(), store, receipt, now=NOW)
            self.assertEqual(store.read()["stage"], "awaiting_smoke")


class DispatchTests(unittest.TestCase):
    def test_bootstrap_uses_hash_pinned_systemd_oneshot(self) -> None:
        backup_receipt = {"schema": core.FRESH_BACKUP_SCHEMA, "release": RELEASE}
        windows_receipt = {"schema": core.WINDOWS_READY_SCHEMA, "release": RELEASE}
        program, manifest = dispatch.build_dispatch_program(
            "promote",
            smoke_timeout_seconds=300,
            attempt_id="20261017T123000Z",
            backup_receipt=backup_receipt,
            windows_receipt=windows_receipt,
        )
        self.assertIn("systemd-run", program)
        self.assertIn("Type=oneshot", program)
        self.assertIn("--no-block", program)
        self.assertIn("TimeoutStartSec=3600", program)
        self.assertIn("TimeoutStopSec=infinity", program)
        self.assertIn("KillMode=mixed", program)
        self.assertNotIn("TimeoutStartSec=1200", program)
        self.assertIn(manifest["core_sha256"], program)
        self.assertIn(manifest["runner_sha256"], program)
        self.assertIn(dispatch.REMOTE_FRESH_BACKUP, program)
        self.assertIn(dispatch.REMOTE_WINDOWS_READY, program)
        self.assertIn(digest(json.dumps(backup_receipt, sort_keys=True, indent=2).encode() + b"\n"), program)
        self.assertIn(digest(json.dumps(windows_receipt, sort_keys=True, indent=2).encode() + b"\n"), program)
        self.assertNotIn("Bearer ", program)

    def test_promote_bootstrap_requires_both_gate_receipts(self) -> None:
        with self.assertRaisesRegex(ValueError, "gate receipts"):
            dispatch.build_dispatch_program(
                "promote", attempt_id="20261017T123000Z"
            )

    def test_review_only_main_never_calls_remote(self) -> None:
        calls = []

        def forbidden(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("remote must not be called")

        self.assertEqual(dispatch.promote_main([], remote_fn=forbidden), 2)
        self.assertEqual(calls, [])

    def test_all_command_wrappers_default_to_zero_remote_review_mode(self) -> None:
        here = pathlib.Path(__file__).resolve().parent
        for filename in ("promote_remote.py", "recovery_remote.py", "finalize_remote.py"):
            result = subprocess.run(
                [sys.executable, str(here / filename)],
                cwd=here,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 2, filename)
            self.assertIn("review-only", result.stdout, filename)
            self.assertEqual(result.stderr, "", filename)

    def test_finalize_upload_rejects_raw_secret(self) -> None:
        receipt = {
            "schema": core.AUTH_SMOKE_SCHEMA,
            "release": RELEASE,
            "observed_at": "2026-10-17T12:21:00+00:00",
            "new_container_id": "new-id",
            "public_models_status": 200,
            "direct_windows_models_status": 403,
            "request_id_sha256": "c" * 64,
            "authorization": "Bearer forbidden",
        }
        with self.assertRaisesRegex(core.GateError, "secret"):
            dispatch.build_smoke_receipt_program(receipt)


class RecoveryFailedSettlementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.expected_network = {
            "smartbrain_app": {"IPAddress": "172.18.0.10", "Aliases": [runner.NAME]},
            "smartbrain_data": {"IPAddress": "172.19.0.10", "Aliases": [runner.NAME]},
            "smartbrain_host-ingress": {"IPAddress": "172.20.0.10", "Aliases": [runner.NAME]},
        }
        self.unit = root / "old-unit.service"
        self.inventory = root / "old-inventory.json"
        self.unit.write_bytes(b"old unit")
        self.inventory.write_bytes(b'{"container_id":"old-id"}')
        self.store = core.StageStore(root / "stage.json")
        self.store.write(
            "recovery_failed",
            old_id="old-id",
            new_id="new-id",
            candidate_id="candidate-id",
            old_fingerprint="f" * 64,
            old_network=self.expected_network,
            unit_backup_path=str(self.unit),
            unit_backup_sha256=digest(self.unit.read_bytes()),
            inventory_backup_path=str(self.inventory),
            inventory_backup_sha256=digest(self.inventory.read_bytes()),
            recovery_error_type="GateError",
        )
        self.ops = FakeRecoveryOps(
            phase="recovery_failed", expected_network=self.expected_network
        )
        self.ops.containers["old-id"].update(
            {
                "Name": "/" + runner.NAME,
                "running": True,
                "network": json.loads(json.dumps(self.expected_network)),
            }
        )
        self.ops.containers["new-id"].update(
            {
                "Name": "/" + runner.FAILED_NAME_PREFIX + "new",
                "running": False,
                "network": {},
            }
        )
        self.ops.containers["candidate-id"] = {
            "Id": "candidate-id",
            "Name": "/" + runner.CANDIDATE_NAME,
            "Image": "sha256:" + "d" * 64,
            "Created": "2026-10-17T12:00:00+00:00",
            "Config": {"Labels": {"smartbrain.scope": core.RELEASE}},
            "running": False,
            "fingerprint": "c" * 64,
            "network": self.expected_network,
        }
        self.ops.unit_bytes = self.unit.read_bytes()
        self.ops.inventory_bytes = self.inventory.read_bytes()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_recovery_failed_exactly_restored_only_commits_terminal_stage(self) -> None:
        before = json.loads(json.dumps(self.ops.containers))
        before_sequence = self.store.read()["sequence"]

        result = runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(result["stage"], "restored")
        self.assertEqual(result["resumed_from"], "recovery_failed")
        self.assertTrue(result["settled_existing_restoration"])
        self.assertEqual(result["sequence"], before_sequence + 1)
        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.ops.containers, before)

    def test_missing_persisted_new_container_fails_closed_without_restart(self) -> None:
        self.ops.containers.pop("new-id")

        with self.assertRaisesRegex(core.GateError, "new container"):
            runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.store.read()["stage"], "recovery_failed")

    def test_settlement_read_error_fails_closed_without_restart(self) -> None:
        with mock.patch.object(
            self.ops, "read_unit_bytes", side_effect=OSError("injected read failure")
        ), self.assertRaisesRegex(OSError, "injected read failure"):
            runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.store.read()["stage"], "recovery_failed")

    def test_unit_mismatch_fails_closed_without_restart(self) -> None:
        self.ops.unit_bytes = b"unexpected unit"
        before = json.loads(json.dumps(self.ops.containers))

        with self.assertRaisesRegex(core.GateError, "unit"):
            runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.ops.containers, before)
        self.assertEqual(self.store.read()["stage"], "recovery_failed")

    def test_running_candidate_fails_closed_without_restart(self) -> None:
        self.ops.containers["candidate-id"]["running"] = True
        before = json.loads(json.dumps(self.ops.containers))

        with self.assertRaisesRegex(core.GateError, "candidate"):
            runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.ops.containers, before)
        self.assertEqual(self.store.read()["stage"], "recovery_failed")

    def test_missing_persisted_new_identity_fails_closed_without_restart(self) -> None:
        state = self.store.read()
        state.pop("new_id")
        self.store.path.write_text(json.dumps(state), encoding="utf-8")
        before = json.loads(json.dumps(self.ops.containers))

        with self.assertRaisesRegex(core.GateError, "new container identity"):
            runner.recover_release(self.ops, self.store, reason="operator-settle")

        self.assertEqual(self.ops.calls, [])
        self.assertEqual(self.ops.containers, before)
        self.assertEqual(self.store.read()["stage"], "recovery_failed")


class WaitRunningRaceTests(unittest.TestCase):
    def test_wait_running_tolerates_initial_exited_snapshots_until_healthy(self) -> None:
        class Clock:
            now = 0.0

            def monotonic(self) -> float:
                return self.now

            def sleep(self, seconds: float) -> None:
                self.now += seconds

        exited = {
            "State": {"Running": False, "Status": "exited"},
            "NetworkSettings": {"Networks": {}},
        }
        running = {
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {
                "Networks": {"smartbrain_app": {"IPAddress": "172.18.0.17"}}
            },
        }
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        clock = Clock()
        ops = runner.RealOps()
        with mock.patch.object(
            ops, "inspect", side_effect=[exited, exited, running]
        ) as inspected, mock.patch.object(
            runner.time, "monotonic", side_effect=clock.monotonic
        ), mock.patch.object(
            runner.time, "sleep", side_effect=clock.sleep
        ) as slept, mock.patch.object(
            runner.urllib.request, "urlopen", return_value=response
        ) as opened:
            ops.wait_running("old-id", timeout_seconds=10)

        self.assertEqual(inspected.call_count, 3)
        self.assertEqual(slept.call_count, 2)
        opened.assert_called_once_with("http://172.18.0.17:8000/health", timeout=4)

    def test_wait_running_permanently_exited_fails_at_deadline(self) -> None:
        class Clock:
            now = 0.0

            def monotonic(self) -> float:
                return self.now

            def sleep(self, seconds: float) -> None:
                self.now += seconds

        exited = {
            "State": {"Running": False, "Status": "exited"},
            "NetworkSettings": {"Networks": {}},
        }
        clock = Clock()
        ops = runner.RealOps()
        with mock.patch.object(
            ops, "inspect", return_value=exited
        ) as inspected, mock.patch.object(
            runner.time, "monotonic", side_effect=clock.monotonic
        ), mock.patch.object(
            runner.time, "sleep", side_effect=clock.sleep
        ) as slept, self.assertRaisesRegex(
            core.GateError, "container startup timeout"
        ):
            ops.wait_running("old-id", timeout_seconds=3)

        self.assertEqual(inspected.call_count, 3)
        self.assertEqual(slept.call_count, 3)

    def test_wait_running_respects_the_hard_deadline_during_health_probe(self) -> None:
        class Clock:
            def __init__(self) -> None:
                self.now = 0.0
                self.probe_timeouts: list[float] = []

            def monotonic(self) -> float:
                return self.now

            def sleep(self, seconds: float) -> None:
                self.now += seconds

            def urlopen(self, url: str, timeout: float):
                self.probe_timeouts.append(timeout)
                self.now += timeout
                raise OSError("still starting")

        running = {
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {
                "Networks": {"smartbrain_app": {"IPAddress": "172.18.0.17"}}
            },
        }
        clock = Clock()
        ops = runner.RealOps()
        with mock.patch.object(
            ops, "inspect", return_value=running
        ), mock.patch.object(
            runner.time, "monotonic", side_effect=clock.monotonic
        ), mock.patch.object(
            runner.time, "sleep", side_effect=clock.sleep
        ), mock.patch.object(
            runner.urllib.request, "urlopen", side_effect=clock.urlopen
        ), self.assertRaisesRegex(core.GateError, "container startup timeout"):
            ops.wait_running("old-id", timeout_seconds=3)

        self.assertLessEqual(clock.now, 3.0)
        self.assertTrue(clock.probe_timeouts)
        self.assertTrue(all(0 < value <= 3 for value in clock.probe_timeouts))
        self.assertEqual(
            inspect.signature(runner.RealOps.wait_running)
            .parameters["timeout_seconds"]
            .default,
            60,
        )

    def test_wait_running_fails_if_container_exits_after_becoming_running(self) -> None:
        class Clock:
            now = 0.0

            def monotonic(self) -> float:
                return self.now

            def sleep(self, seconds: float) -> None:
                self.now += seconds

        running = {
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {
                "Networks": {"smartbrain_app": {"IPAddress": "172.18.0.17"}}
            },
        }
        exited = {
            "State": {"Running": False, "Status": "exited"},
            "NetworkSettings": {"Networks": {}},
        }
        clock = Clock()
        ops = runner.RealOps()
        with mock.patch.object(
            ops, "inspect", side_effect=[running, exited]
        ), mock.patch.object(
            runner.time, "monotonic", side_effect=clock.monotonic
        ), mock.patch.object(
            runner.time, "sleep", side_effect=clock.sleep
        ) as slept, mock.patch.object(
            runner.urllib.request, "urlopen", side_effect=OSError("not ready")
        ), self.assertRaisesRegex(core.GateError, "container exited during startup"):
            ops.wait_running("old-id", timeout_seconds=10)

        self.assertEqual(slept.call_count, 1)

    def test_wait_running_propagates_unexpected_health_probe_errors(self) -> None:
        running = {
            "State": {"Running": True, "Status": "running"},
            "NetworkSettings": {
                "Networks": {"smartbrain_app": {"IPAddress": "172.18.0.17"}}
            },
        }
        ops = runner.RealOps()
        with mock.patch.object(
            ops, "inspect", return_value=running
        ), mock.patch.object(
            runner.urllib.request, "urlopen", side_effect=ValueError("unexpected probe bug")
        ), self.assertRaisesRegex(ValueError, "unexpected probe bug"):
            ops.wait_running("old-id", timeout_seconds=10)


class TerminationRecoveryTests(unittest.TestCase):
    def test_sigterm_is_raised_as_a_catchable_release_exception_and_restored(self) -> None:
        class FakeSignal:
            SIGTERM = signal.SIGTERM

            def __init__(self) -> None:
                self.current = object()
                self.calls = []

            def getsignal(self, number):
                self.calls.append(("get", number))
                return self.current

            def signal(self, number, handler):
                previous = self.current
                self.current = handler
                self.calls.append(("set", number, handler))
                return previous

        fake = FakeSignal()
        original = fake.current
        with self.assertRaises(runner.TerminationRequested):
            with runner.termination_as_exception(signal_module=fake):
                fake.current(fake.SIGTERM, None)
        self.assertIs(fake.current, original)


if __name__ == "__main__":
    unittest.main()
