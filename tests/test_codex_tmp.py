from __future__ import annotations

import json
import datetime as dt
import fcntl
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import tempfile
import threading
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "codex-tmp"
LAUNCHD_WRAPPER = Path(__file__).resolve().parents[1] / "bin" / "codex-tmp-launchd"
LAUNCHD_PLIST = (
    Path(__file__).resolve().parents[1]
    / "launchd"
    / "com.edwardtoday.codex-tmp-lifecycle.plist"
)


def load_script_module() -> object:
    loader = importlib.machinery.SourceFileLoader("codex_tmp_test_module", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class CodexTmpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.root = base / "tmp"
        self.state = base / "state"
        self.quarantine = base / "quarantine"
        self.recovery = base / "recovery"
        self.config = base / "config.json"
        self.config_data = {
            "complete_grace_hours": 0,
            "session_stale_hours": 0,
            "compact_grace_hours": 0,
            "quarantine_days": 999,
            "purge_pending_hours": 0,
            "sweep_interval_hours": 0,
            "max_quarantine_per_run": 10,
            "max_compact_per_run": 10,
            "max_purge_per_run": 10,
            "auto_adopt_after": "2999-01-01T00:00:00+00:00",
            "auto_adopt_min_age_seconds": 0,
            "orphan_active_hours": 24,
        }
        self.write_config()
        self.env = {
            **os.environ,
            "CODEX_THREAD_ID": "test-thread",
            "CODEX_TMP_ROOT": str(self.root),
            "CODEX_TMP_STATE": str(self.state),
            "CODEX_TMP_QUARANTINE": str(self.quarantine),
            "CODEX_TMP_RECOVERY": str(self.recovery),
            "CODEX_TMP_CONFIG": str(self.config),
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_config(self, **overrides: object) -> None:
        self.config_data.update(overrides)
        self.config.write_text(json.dumps(self.config_data), encoding="utf-8")

    def run_cli(self, *args: str, input_data: dict | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), *args],
            input=json.dumps(input_data) if input_data is not None else None,
            capture_output=True,
            text=True,
            env=self.env,
            check=check,
        )

    def test_complete_quarantine_and_restore_round_trip(self) -> None:
        self.run_cli("create", "example", "--session-id", "old-session")
        task = self.root / "example"
        (task / "evidence.txt").write_text("recover me", encoding="utf-8")
        self.run_cli("complete", "example", "--note", "test fixture")

        sweep = json.loads(self.run_cli("sweep").stdout)
        self.assertEqual(len(sweep["quarantined"]), 1)
        self.assertFalse(task.exists())
        self.assertEqual(len(list(self.quarantine.iterdir())), 1)

        restored = json.loads(self.run_cli("restore", "example").stdout)
        self.assertEqual(restored["status"], "active")
        self.assertEqual((task / "evidence.txt").read_text(encoding="utf-8"), "recover me")

    def test_create_does_not_attach_ambient_session_outside_task_cwd(self) -> None:
        self.run_cli("create", "owned")
        manifest = json.loads(
            (self.root / "owned" / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["owner_session_ids"], [])

    def test_explicit_session_id_is_attached(self) -> None:
        self.run_cli("create", "owned", "--session-id", "explicit-thread")
        manifest = json.loads(
            (self.root / "owned" / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["owner_session_ids"], ["explicit-thread"])

    def test_create_initializes_budget_and_lifecycle_directories(self) -> None:
        result = json.loads(self.run_cli("create", "budgeted").stdout)
        task = self.root / "budgeted"
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))

        self.assertEqual(result["budget"]["class"], "default")
        self.assertEqual(manifest["budget"]["expected_peak_bytes"], 2 * 1024**3)
        self.assertTrue((task / "checkpoint").is_dir())
        self.assertTrue((task / "evidence").is_dir())
        self.assertTrue((task / "scratch").is_dir())

    def test_emergency_pressure_warns_but_creates_large_task(self) -> None:
        self.state.mkdir(parents=True)
        (self.state / "capacity.json").write_text(
            json.dumps(
                {
                    "measured_at": "2999-01-01T00:00:00+00:00",
                    "tmp_allocated_bytes": 81 * 1024**3,
                    "recovery_store_allocated_bytes": 0,
                }
            ),
            encoding="utf-8",
        )

        result = self.run_cli("create", "large-under-pressure", "--budget-class", "large")
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "large-under-pressure").is_dir())
        self.assertIn(
            "disk pressure is emergency; large tasks were previously paused",
            payload["admission_warnings"],
        )

    def test_reservation_floor_warns_but_never_refuses_task_creation(self) -> None:
        self.write_config(system_emergency_free_gib=1_000_000)

        result = self.run_cli("create", "always-admit")
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "always-admit").is_dir())
        self.assertIn(
            "planning reservations project free space below the emergency floor",
            payload["admission_warnings"],
        )

    def test_corrupt_capacity_cache_warns_but_never_refuses_task_creation(self) -> None:
        self.state.mkdir(parents=True)
        (self.state / "capacity.json").write_text("{invalid-json", encoding="utf-8")

        result = self.run_cli("create", "capacity-cache-corrupt")
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "capacity-cache-corrupt").is_dir())
        self.assertTrue(
            any("capacity signal unavailable" in item for item in payload["admission_warnings"])
        )

    def test_corrupt_unrelated_manifest_warns_but_never_refuses_task_creation(self) -> None:
        broken = self.root / "broken-active"
        broken.mkdir(parents=True)
        (broken / ".codex-tmp-task.json").write_text("{invalid-json", encoding="utf-8")

        result = self.run_cli("create", "manifest-corrupt")
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "manifest-corrupt").is_dir())
        self.assertTrue(
            any("reservation signal incomplete" in item for item in payload["admission_warnings"])
        )

    def test_emergency_pressure_warns_for_default_task(self) -> None:
        self.state.mkdir(parents=True)
        (self.state / "capacity.json").write_text(
            json.dumps(
                {
                    "measured_at": "2999-01-01T00:00:00+00:00",
                    "tmp_allocated_bytes": 81 * 1024**3,
                    "recovery_store_allocated_bytes": 0,
                }
            ),
            encoding="utf-8",
        )

        payload = json.loads(self.run_cli("create", "default-under-pressure").stdout)

        self.assertEqual(payload["pressure"], "emergency")
        self.assertIn("disk pressure is emergency", payload["admission_warnings"])

    def test_expected_peak_above_advisory_level_never_blocks_creation(self) -> None:
        below = self.run_cli(
            "create", "exceptional-below", "--budget-class", "exceptional",
            "--expected-peak-gib", "15.5",
        )
        self.run_cli("complete", "exceptional-below")
        equal = self.run_cli(
            "create", "exceptional-equal", "--budget-class", "exceptional",
            "--expected-peak-gib", "16",
        )
        above = self.run_cli(
            "create", "exceptional-above", "--budget-class", "exceptional",
            "--expected-peak-gib", "16.1", check=False,
        )

        self.assertEqual(below.returncode, 0)
        self.assertEqual(equal.returncode, 0)
        self.assertEqual(above.returncode, 0)
        payload = json.loads(above.stdout)
        self.assertIn(
            "expected peak exceeds the exceptional advisory planning level; creation continues",
            payload["admission_warnings"],
        )
        self.assertTrue((self.root / "exceptional-above").exists())

    def test_exceptional_planning_level_can_be_raised_without_hard_admission_gate(self) -> None:
        self.write_config(exceptional_budget_gib=32, system_emergency_free_gib=0)

        result = self.run_cli(
            "create", "exceptional-config-raised", "--budget-class", "exceptional",
            "--expected-peak-gib", "32", check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "exceptional-config-raised").exists())

    def test_inventory_reports_capacity_and_reservations(self) -> None:
        self.run_cli("create", "reserved")

        inventory = json.loads(self.run_cli("inventory").stdout)

        self.assertEqual(inventory["reservations"]["reserved_bytes"], 2 * 1024**3)
        self.assertIn(inventory["capacity"]["pressure"], {"healthy", "soft", "hard", "emergency"})

    def test_capacity_measurement_timeout_uses_stale_cache_without_blocking(self) -> None:
        self.state.mkdir(parents=True)
        cached = {
            "measured_at": "2000-01-01T00:00:00+00:00",
            "tmp_allocated_bytes": 7 * 1024**3,
            "recovery_store_allocated_bytes": 3 * 1024**2,
        }
        (self.state / "capacity.json").write_text(json.dumps(cached), encoding="utf-8")
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            paths.prepare()
            config = module.load_config(paths)
            with mock.patch.object(
                module,
                "bounded_allocated_bytes",
                return_value=(None, "simulated timeout"),
            ):
                capacity = module.capacity_snapshot(paths, config, refresh_allocated=True)

        self.assertEqual(capacity["tmp_allocated_bytes"], cached["tmp_allocated_bytes"])
        self.assertEqual(
            capacity["recovery_store_allocated_bytes"],
            cached["recovery_store_allocated_bytes"],
        )
        self.assertTrue(capacity["allocated_stale"])
        self.assertEqual(capacity["allocated_errors"], ["simulated timeout"] * 2)

    def test_fenced_scratch_requires_release_before_cleanup(self) -> None:
        self.run_cli("create", "fenced")
        acquired = json.loads(
            self.run_cli("scratch-acquire", "fenced", "--session-id", "writer").stdout
        )
        scratch_path = Path(acquired["path"])
        (scratch_path / "build.bin").write_bytes(b"build")

        valid = json.loads(
            self.run_cli("scratch-check", "fenced", "--token", acquired["token"]).stdout
        )
        blocked_complete = self.run_cli("complete", "fenced", check=False)
        blocked_clean = self.run_cli(
            "scratch-clean", "fenced", "--allow-active", check=False
        )
        self.run_cli("scratch-release", "fenced", "--token", acquired["token"])
        cleaned = json.loads(
            self.run_cli("scratch-clean", "fenced", "--allow-active").stdout
        )
        invalid = json.loads(
            self.run_cli("scratch-check", "fenced", "--token", acquired["token"]).stdout
        )

        self.assertTrue(valid["valid"])
        self.assertIn("release all scratch fencing tokens", blocked_complete.stderr)
        self.assertIn("active scratch fencing tokens", blocked_clean.stderr)
        self.assertGreater(cleaned["reclaimed_allocated_bytes"], 0)
        self.assertFalse(scratch_path.exists())
        self.assertFalse(invalid["valid"])

    def test_scratch_tokens_cannot_be_parsed_as_options(self) -> None:
        self.run_cli("create", "prefixed-token")
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            with mock.patch.object(module.secrets, "token_urlsafe", return_value="-leading"):
                acquired = module.command_scratch_acquire(
                    mock.Mock(task="prefixed-token", session_id="writer"), paths
                )

        self.assertEqual(acquired["token"], "w_-leading")
        released = self.run_cli(
            "scratch-release", "prefixed-token", "--token", acquired["token"]
        )
        self.assertEqual(released.returncode, 0)

    def test_scratch_manifest_rejects_absolute_traversal_and_wrong_generation(self) -> None:
        for task_name, current_path in (
            ("absolute", "/tmp/outside"),
            ("traversal", "../../outside"),
            ("wrong-generation", "scratch/g00000002"),
        ):
            self.run_cli("create", task_name)
            acquired = json.loads(self.run_cli("scratch-acquire", task_name).stdout)
            self.run_cli("scratch-release", task_name, "--token", acquired["token"])
            manifest_path = self.root / task_name / ".codex-tmp-task.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["scratch"]["current_path"] = current_path
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = self.run_cli(
                "scratch-clean", task_name, "--allow-active", check=False
            )

            self.assertNotEqual(result.returncode, 0, task_name)
            self.assertIn("scratch path", result.stderr, task_name)

    def test_scratch_manifest_rejects_symlink_ancestor(self) -> None:
        self.run_cli("create", "symlink-ancestor")
        acquired = json.loads(self.run_cli("scratch-acquire", "symlink-ancestor").stdout)
        self.run_cli(
            "scratch-release", "symlink-ancestor", "--token", acquired["token"]
        )
        task = self.root / "symlink-ancestor"
        outside = self.root.parent / "outside-scratch"
        outside.mkdir()
        shutil.rmtree(task / "scratch")
        (task / "scratch").symlink_to(outside, target_is_directory=True)

        result = self.run_cli(
            "scratch-clean", "symlink-ancestor", "--allow-active", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scratch root is missing or invalid", result.stderr)
        self.assertTrue(outside.exists())

    def test_maintenance_cleans_completed_reproducible_outputs(self) -> None:
        self.write_config(complete_grace_hours=999)
        self.run_cli("create", "outputs")
        task = self.root / "outputs"
        (task / "repo" / "target").mkdir(parents=True)
        (task / "repo" / "target" / "binary").write_bytes(b"x" * 4096)
        (task / "web" / "node_modules").mkdir(parents=True)
        (task / "web" / "node_modules" / "package.js").write_text("x", encoding="utf-8")
        runtime_package = self.root.parent / "runtime-package"
        runtime_package.mkdir()
        (task / "web" / "node_modules" / "linked-package").symlink_to(
            runtime_package, target_is_directory=True
        )
        self.run_cli("complete", "outputs")

        result = self.run_cli("maintenance", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        maintenance = json.loads(result.stdout)
        check = json.loads(self.run_cli("check", "outputs").stdout)

        self.assertFalse((task / "repo" / "target").exists())
        self.assertFalse((task / "web" / "node_modules").exists())
        self.assertEqual(len(maintenance["output_cleanup"]), 1)
        self.assertNotIn("task content changed after it was marked complete", check["blockers"])

    def test_v2_new_task_claims_owner_generation_and_lease(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)

        payload = json.loads(self.run_cli("create", "v2-owned").stdout)
        manifest = json.loads(
            (self.root / "v2-owned" / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )

        self.assertEqual(payload["lifecycle_owner"], "v2")
        self.assertEqual(manifest["lifecycle_owner"], "v2")
        self.assertEqual(manifest["lifecycle_generation"], 1)
        self.assertIsNotNone(manifest["lease_expires_at"])

    def test_v2_auto_adoption_claims_new_directory(self) -> None:
        self.write_config(
            lifecycle_mode="v2-new",
            auto_adopt_after="2000-01-01T00:00:00+00:00",
        )
        task = self.root / "v2-adopted"
        task.mkdir(parents=True)

        self.run_cli("adopt")
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["lifecycle_owner"], "v2")
        self.assertEqual(manifest["lifecycle_generation"], 1)

    def test_shadow_reconcile_reports_without_mutating_legacy_task(self) -> None:
        self.write_config(lifecycle_mode="shadow")
        self.run_cli("create", "legacy-shadow")
        manifest_path = self.root / "legacy-shadow" / ".codex-tmp-task.json"
        before = manifest_path.read_bytes()

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(manifest_path.read_bytes(), before)
        self.assertEqual(maintenance["v2_reconcile"]["mode"], "shadow")
        self.assertEqual(maintenance["v2_reconcile"]["mutated"], [])
        self.assertTrue((self.state / "v2-shadow.json").exists())

    def test_shadow_observes_every_direct_child_including_unmanaged_and_corrupt(self) -> None:
        self.write_config(lifecycle_mode="shadow")
        self.run_cli("create", "managed-shadow")
        unmanaged = self.root / "unmanaged-shadow"
        unmanaged.mkdir(parents=True)
        corrupt = self.root / "corrupt-shadow"
        corrupt.mkdir(parents=True)
        (corrupt / ".codex-tmp-task.json").write_text("{invalid", encoding="utf-8")

        result = self.run_cli("maintenance", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        maintenance = json.loads(result.stdout)
        reconcile = maintenance["v2_reconcile"]

        self.assertEqual(reconcile["coverage"]["total_directories"], 3)
        self.assertEqual(reconcile["coverage"]["observed"], 3)
        self.assertEqual(reconcile["coverage"]["missing"], 0)
        self.assertEqual(reconcile["coverage"]["compare_count"], 3)
        observations = list((self.state / "v2-observations").glob("*.json"))
        self.assertEqual(len(observations), 3)
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in observations]
        self.assertTrue(
            all(payload["effective_decision"] == payload["legacy_decision"] for payload in payloads)
        )
        self.assertTrue(
            all(
                not payload["v2_more_aggressive"] or payload["explanation"]
                for payload in payloads
            )
        )

    def test_decision_compare_covers_one_hundred_synthetic_cases(self) -> None:
        module = load_script_module()
        actions = ["preserve", "clean-reproducible", "compact", "quarantine", "purge"]
        cases = 0

        for legacy_action in actions:
            for v2_action in actions:
                for mode in ("shadow", "v2-new"):
                    for owner in ("legacy", "v2"):
                        legacy = {"engine": "legacy", "action": legacy_action}
                        v2 = {"engine": "v2", "action": v2_action}
                        compared = module.compare_lifecycle_decisions(
                            legacy, v2, mode, owner
                        )
                        expected = legacy if mode == "shadow" or owner == "legacy" else v2
                        self.assertIs(compared["effective_decision"], expected)
                        self.assertEqual(
                            compared["v2_more_aggressive"],
                            actions.index(v2_action) > actions.index(legacy_action),
                        )
                        if compared["v2_more_aggressive"]:
                            self.assertTrue(compared["explanation"])
                        cases += 1

        self.assertEqual(cases, 100)

    def test_shadow_backfill_upgrades_only_missing_legacy_ownership_metadata(self) -> None:
        self.write_config(lifecycle_mode="shadow")
        self.run_cli("create", "legacy-backfill")
        task = self.root / "legacy-backfill"
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        instance_id = manifest.pop("task_instance_id")
        manifest.pop("lifecycle_owner")
        manifest.pop("lifecycle_generation")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        old_record = self.state / "ownership" / f"{instance_id}.json"
        old_record.unlink()

        maintenance = json.loads(self.run_cli("maintenance").stdout)
        upgraded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(upgraded["status"], "active")
        self.assertEqual(upgraded["lifecycle_owner"], "legacy")
        self.assertEqual(upgraded["lifecycle_generation"], 1)
        self.assertNotEqual(upgraded["task_instance_id"], instance_id)
        record = self.state / "ownership" / f"{upgraded['task_instance_id']}.json"
        self.assertTrue(record.exists())
        self.assertEqual(maintenance["v2_reconcile"]["mode"], "shadow")

    def test_v2_reconcile_cleans_expired_task_outputs_without_completion(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-expired")
        task = self.root / "v2-expired"
        target = task / "repo" / "target"
        target.mkdir(parents=True)
        (target / "binary").write_bytes(b"x" * 4096)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertFalse(target.exists())
        self.assertEqual(len(maintenance["v2_reconcile"]["output_cleanup"]), 1)
        self.assertEqual(
            json.loads(self.run_cli("status", "v2-expired").stdout)["state"],
            "blocked",
        )

    def test_v2_reconcile_preserves_outputs_while_lease_is_fresh(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-fresh")
        target = self.root / "v2-fresh" / "repo" / "target"
        target.mkdir(parents=True)
        (target / "binary").write_bytes(b"x" * 4096)

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(target.exists())
        self.assertEqual(maintenance["v2_reconcile"]["output_cleanup"], [])
        self.assertEqual(
            json.loads(self.run_cli("status", "v2-fresh").stdout)["state"],
            "in-use",
        )

    def test_session_end_expires_v2_lease_and_dispatcher_reclaims_outputs(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=24)
        self.run_cli("create", "v2-session-end", "--session-id", "ending-session")
        task = self.root / "v2-session-end"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)

        self.run_cli(
            "hook",
            input_data={
                "session_id": "ending-session",
                "cwd": str(task),
                "hook_event_name": "SessionEnd",
            },
        )
        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertFalse(target.exists())
        self.assertIn("v2-session-end", maintenance["v2_reconcile"]["mutated"])

    def test_stop_refreshes_v2_lease_and_preserves_outputs(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-stop", "--session-id", "active-session")
        task = self.root / "v2-stop"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)

        self.run_cli(
            "hook",
            input_data={
                "session_id": "active-session",
                "cwd": str(task),
                "hook_event_name": "Stop",
            },
        )
        self.run_cli("maintenance")

        self.assertTrue(target.exists())
        self.assertEqual(
            json.loads(self.run_cli("status", "v2-stop").stdout)["state"], "in-use"
        )

    def test_session_end_expires_only_its_own_v2_lease(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-shared", "--session-id", "session-a")
        task = self.root / "v2-shared"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)

        for session_id, event_name in (
            ("session-a", "Stop"),
            ("session-b", "SessionEnd"),
        ):
            self.run_cli(
                "hook",
                input_data={
                    "session_id": session_id,
                    "cwd": str(task),
                    "hook_event_name": event_name,
                },
            )
        maintenance = json.loads(self.run_cli("maintenance").stdout)

        manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertGreater(
            dt.datetime.fromisoformat(manifest["session_leases"]["session-a"]),
            dt.datetime.now(dt.timezone.utc),
        )
        self.assertLessEqual(
            dt.datetime.fromisoformat(manifest["session_leases"]["session-b"]),
            dt.datetime.now(dt.timezone.utc),
        )
        self.assertTrue(target.exists())
        self.assertNotIn("v2-shared", maintenance["v2_reconcile"]["mutated"])

    def test_v2_reconcile_preserves_outputs_while_process_cwd_is_task_root(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-process-cwd")
        task = self.root / "v2-process-cwd"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        process = subprocess.Popen(["sleep", "30"], cwd=task)
        try:
            maintenance = json.loads(self.run_cli("maintenance").stdout)
        finally:
            process.terminate()
            process.wait(timeout=5)

        self.assertTrue(target.exists())
        blocked = maintenance["v2_reconcile"]["output_cleanup"][0]["blocked"]
        self.assertIn("open file or cwd", blocked[0]["reason"])

    def test_v2_reconcile_preserves_outputs_in_dirty_task_repository(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-dirty-workspace")
        task = self.root / "v2-dirty-workspace"
        subprocess.run(["git", "init", "-q", str(task)], check=True)
        tracked = task / "source.txt"
        tracked.write_text("clean\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(task), "add", "source.txt"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(task),
                "-c",
                "user.name=Codex Test",
                "-c",
                "user.email=codex@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        tracked.write_text("dirty\n", encoding="utf-8")
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(target.exists())
        blocked = maintenance["v2_reconcile"]["output_cleanup"][0]["blocked"]
        self.assertIn("dirty enclosing Git repository", blocked[0]["reason"])

    def test_v2_reconcile_preserves_outputs_in_clean_local_only_task_repository(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-local-only")
        task = self.root / "v2-local-only"
        subprocess.run(["git", "init", "-q", str(task)], check=True)
        (task / ".gitignore").write_text("target/\n", encoding="utf-8")
        (task / "source.txt").write_text("local only\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(task), "add", ".gitignore", "source.txt"], check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(task),
                "-c",
                "user.name=Codex Test",
                "-c",
                "user.email=codex@example.invalid",
                "commit",
                "-qm",
                "local-only fixture",
            ],
            check=True,
        )
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(target.exists())
        blocked = maintenance["v2_reconcile"]["output_cleanup"][0]["blocked"]
        self.assertIn("Git repository has no remote", blocked[0]["reason"])

    def test_enclosing_git_blockers_inspects_parent_repository_history(self) -> None:
        module = load_script_module()
        repository = self.root.parent / "parent-repository"
        task = repository / "nested-task"
        task.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        (repository / "source.txt").write_text("local only\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "add", "source.txt"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "-c",
                "user.name=Codex Test",
                "-c",
                "user.email=codex@example.invalid",
                "commit",
                "-qm",
                "local-only parent",
            ],
            check=True,
        )

        blockers = module.enclosing_git_blockers(task)

        self.assertTrue(any("Git repository has no remote" in item for item in blockers))

    def test_v2_reconcile_preserves_symlink_only_node_modules_after_lease(self) -> None:
        self.write_config(lifecycle_mode="v2-new", active_lease_hours=1)
        self.run_cli("create", "v2-links")
        task = self.root / "v2-links"
        package = self.root.parent / "runtime" / "package"
        package.mkdir(parents=True)
        (package / "package.json").write_text("{}", encoding="utf-8")
        link = task / "node_modules" / "package"
        link.parent.mkdir()
        link.symlink_to(package, target_is_directory=True)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        self.run_cli("maintenance")

        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), package.resolve())

    def test_v2_hold_is_bounded_and_does_not_change_legacy_status(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        self.run_cli("create", "held")

        valid_until = (
            dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)
        ).isoformat()
        payload = json.loads(
            self.run_cli(
                "hold", "held", "--until", valid_until, "--reason", "needs review"
            ).stdout
        )
        self.assertEqual(payload["hold"]["reason"], "needs review")
        rejected = self.run_cli(
            "hold",
            "held",
            "--until",
            "2099-01-01T00:00:00+00:00",
            "--reason",
            "invalid because too long",
            check=False,
        )
        self.assertNotEqual(rejected.returncode, 0)
        cleared = json.loads(self.run_cli("hold", "held", "--clear").stdout)
        self.assertIsNone(cleared["hold"])

    def test_v2_hold_does_not_protect_reproducible_output_bytes(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        self.run_cli("create", "held-output")
        task = self.root / "held-output"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        valid_until = (
            dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)
        ).isoformat()
        self.run_cli(
            "hold", "held-output", "--until", valid_until, "--reason", "keep checkpoint"
        )
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        self.run_cli("maintenance")

        self.assertFalse(target.exists())
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(current["hold"]["reason"], "keep checkpoint")

    def test_hold_blocks_completed_task_quarantine(self) -> None:
        self.write_config(lifecycle_mode="v2-new", complete_grace_hours=0)
        self.run_cli("create", "held-complete")
        self.run_cli("complete", "held-complete")
        valid_until = (
            dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)
        ).isoformat()
        self.run_cli(
            "hold", "held-complete", "--until", valid_until, "--reason", "audit window"
        )

        sweep = json.loads(self.run_cli("sweep").stdout)

        self.assertEqual(sweep["quarantined"], [])
        self.assertTrue((self.root / "held-complete").exists())
        task_check = next(
            item for item in sweep["checked"] if item["task"].endswith("held-complete")
        )
        self.assertTrue(any("hold active" in item for item in task_check["blockers"]))

    def test_v2_output_blocker_is_reported_with_path_and_reason(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        self.run_cli("create", "blocked-output")
        task = self.root / "blocked-output"
        repository = task / "target" / "nested"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        (repository / "untracked.txt").write_text("dirty", encoding="utf-8")
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        blocked = maintenance["v2_reconcile"]["output_cleanup"][0]["blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["path"], str(task / "target"))
        self.assertIn("dirty Git repository", blocked[0]["reason"])
        self.assertTrue((task / "target").exists())

    def test_v2_completed_compaction_runs_through_single_dispatcher(self) -> None:
        self.write_config(
            lifecycle_mode="v2-new", compact_grace_hours=0, complete_grace_hours=999
        )
        external = self.root.parent / "external-recovery"
        external.mkdir()
        (external / "anchor.txt").write_text("recover", encoding="utf-8")
        self.run_cli("create", "v2-compact")
        task = self.root / "v2-compact"
        (task / "payload.txt").write_text("large body", encoding="utf-8")
        self.run_cli("complete", "v2-compact")
        self.run_cli(
            "compact",
            "v2-compact",
            "--depends-on",
            str(external),
            "--note",
            "external recovery source",
        )

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(len(maintenance["compaction"]["compacted"]), 1)
        manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["compaction"]["status"], "compacted")

    def test_v2_reconcile_rejects_stale_ownership_generation(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        self.run_cli("create", "stale-owner")
        task = self.root / "stale-owner"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        record_path = self.state / "ownership" / f"{manifest['task_instance_id']}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["generation"] = 2
        record_path.write_text(json.dumps(record), encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(target.exists())
        self.assertTrue(
            any(
                item["task"] == "stale-owner" and "ownership" in item["reason"]
                for item in maintenance["v2_reconcile"]["errors"]
            )
        )

    def test_v2_reconcile_never_mutates_legacy_owned_task(self) -> None:
        self.write_config(lifecycle_mode="shadow")
        self.run_cli("create", "legacy-owned")
        task = self.root / "legacy-owned"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        before = (task / ".codex-tmp-task.json").read_bytes()
        self.write_config(lifecycle_mode="v2-new")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(target.exists())
        self.assertEqual((task / ".codex-tmp-task.json").read_bytes(), before)
        self.assertEqual(maintenance["v2_reconcile"]["output_cleanup"], [])

    def test_concurrent_same_name_create_has_exactly_one_owner(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        processes = [
            subprocess.Popen(
                [str(SCRIPT), "create", "single-claim", "--session-id", f"session-{index}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.env,
            )
            for index in range(8)
        ]
        results = [process.communicate(timeout=20) for process in processes]

        self.assertEqual(sum(process.returncode == 0 for process in processes), 1, results)
        task = self.root / "single-claim"
        manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        records = list((self.state / "ownership").glob("*.json"))
        self.assertEqual(len(records), 1)
        record = json.loads(records[0].read_text(encoding="utf-8"))
        self.assertEqual(record["task_instance_id"], manifest["task_instance_id"])
        self.assertEqual(record["lifecycle_owner"], "v2")

    def test_maintenance_repairs_manifest_written_before_ownership_record(self) -> None:
        self.write_config(lifecycle_mode="v2-new")
        module = load_script_module()
        task = self.root / "ownership-crash"

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            paths.prepare()
            config = module.load_config(paths)
            args = module.argparse.Namespace(
                name="ownership-crash",
                session_id="owner",
                budget_class="default",
                expected_peak_gib=None,
            )
            with mock.patch.object(
                module, "write_ownership_record", side_effect=OSError("simulated crash")
            ):
                with self.assertRaises(OSError):
                    module.command_create(args, paths, config)

        manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        record_path = self.state / "ownership" / f"{manifest['task_instance_id']}.json"
        self.assertFalse(record_path.exists())

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(record_path.exists())
        self.assertEqual(maintenance["ownership"]["created"][0]["task"], "ownership-crash")

    def test_shadow_rollback_freezes_existing_v2_task(self) -> None:
        self.write_config(
            lifecycle_mode="v2-new", complete_grace_hours=0, compact_grace_hours=0
        )
        self.run_cli("create", "rollback-v2")
        task = self.root / "rollback-v2"
        target = task / "target"
        target.mkdir()
        (target / "binary").write_bytes(b"x" * 4096)
        self.run_cli("complete", "rollback-v2")
        manifest_path = task / ".codex-tmp-task.json"
        before = manifest_path.read_bytes()
        self.write_config(lifecycle_mode="shadow")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(task.exists())
        self.assertTrue(target.exists())
        self.assertEqual(manifest_path.read_bytes(), before)
        self.assertEqual(maintenance["v2_reconcile"]["mutated"], [])
        self.assertEqual(maintenance["output_cleanup"], [])
        checked = next(
            item for item in maintenance["sweep"]["checked"] if item["task"] == str(task)
        )
        self.assertIn("v2 task frozen by shadow rollback", checked["blockers"])

    def test_maintenance_preserves_symlink_only_node_modules(self) -> None:
        self.write_config(complete_grace_hours=999)
        self.run_cli("create", "runtime-links")
        task = self.root / "runtime-links"
        runtime_package = self.root.parent / "runtime" / "@oai" / "artifact-tool"
        runtime_package.mkdir(parents=True)
        (runtime_package / "package.json").write_text("{}", encoding="utf-8")
        package_link = task / "scratch" / "artifact-workspace" / "node_modules" / "@oai" / "artifact-tool"
        package_link.parent.mkdir(parents=True)
        package_link.symlink_to(runtime_package, target_is_directory=True)
        self.run_cli("complete", "runtime-links")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertTrue(package_link.is_symlink())
        self.assertEqual(package_link.resolve(), runtime_package.resolve())
        self.assertEqual(maintenance["output_cleanup"], [])

    def test_symlink_only_node_modules_surfaces_walk_errors(self) -> None:
        module = load_script_module()
        node_modules = self.root / "node_modules"
        node_modules.mkdir(parents=True)
        (node_modules / "linked-package").symlink_to(self.root, target_is_directory=True)

        def walk_with_descendant_error(
            path: Path, *, topdown: bool, followlinks: bool, onerror: object
        ) -> object:
            self.assertTrue(topdown)
            self.assertFalse(followlinks)
            yield str(path), [], ["linked-package"]
            assert callable(onerror)
            onerror(PermissionError("simulated scandir failure"))

        with mock.patch.object(module.os, "walk", side_effect=walk_with_descendant_error):
            with self.assertRaisesRegex(PermissionError, "simulated scandir failure"):
                module.is_symlink_only_node_modules(node_modules)

    def test_reproducible_cleanup_records_and_retries_interrupted_tombstone(self) -> None:
        self.run_cli("create", "output-retry")
        task = self.root / "output-retry"
        target = task / "repo" / "target"
        target.mkdir(parents=True)
        (target / "binary").write_bytes(b"x" * 4096)
        self.run_cli("complete", "output-retry")
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            manifest = module.load_manifest(task)
            assert manifest is not None
            with mock.patch.object(
                module,
                "remove_tree_same_device",
                side_effect=module.LifecycleError("changed during deletion"),
            ):
                interrupted = module.clean_reproducible_outputs(paths, task, manifest)

            self.assertEqual(interrupted["cleaned"], [])
            self.assertEqual(len(interrupted["blocked"]), 1)
            self.assertFalse(target.exists())
            tombstones = module.reproducible_output_tombstones(task)
            self.assertEqual(len(tombstones), 1)

            retried = module.clean_reproducible_outputs(paths, task, manifest)

        self.assertEqual(len(retried["cleaned"]), 1)
        self.assertEqual(retried["blocked"], [])
        self.assertEqual(module.reproducible_output_tombstones(task), [])

    def test_dirty_git_repository_blocks_quarantine(self) -> None:
        self.run_cli("create", "dirty")
        task = self.root / "dirty"
        subprocess.run(["git", "init", "-q", str(task / "repo")], check=True)
        (task / "repo" / "untracked.txt").write_text("dirty", encoding="utf-8")
        self.run_cli("complete", "dirty")

        result = json.loads(self.run_cli("check", "dirty").stdout)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("dirty Git repository" in item for item in result["blockers"]))

    def test_deep_dirty_git_repository_blocks_quarantine(self) -> None:
        self.run_cli("create", "deep-dirty")
        task = self.root / "deep-dirty"
        repository = task / "a" / "b" / "c" / "d" / "repo"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        (repository / "untracked.txt").write_text("dirty", encoding="utf-8")
        self.run_cli("complete", "deep-dirty")

        result = json.loads(self.run_cli("check", "deep-dirty").stdout)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("dirty Git repository" in item for item in result["blockers"]))

    def test_root_git_repository_ignores_lifecycle_manifest_only(self) -> None:
        self.run_cli("create", "root-repo")
        task = self.root / "root-repo"
        subprocess.run(["git", "init", "-q", str(task)], check=True)
        subprocess.run(["git", "-C", str(task), "config", "user.name", "Codex Test"], check=True)
        subprocess.run(
            ["git", "-C", str(task), "config", "user.email", "codex-test@example.invalid"],
            check=True,
        )
        (task / "tracked.txt").write_text("tracked", encoding="utf-8")
        subprocess.run(["git", "-C", str(task), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(task), "commit", "-qm", "fixture"], check=True)
        remote = self.root.parent / "root-repo-remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        subprocess.run(["git", "-C", str(task), "remote", "add", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(task), "push", "-qu", "origin", "HEAD"], check=True)
        self.run_cli("complete", "root-repo")

        manifest_only = json.loads(self.run_cli("check", "root-repo").stdout)
        self.assertTrue(manifest_only["eligible"])
        status = subprocess.run(
            ["git", "-C", str(task), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout, "")

        (task / "real-untracked.txt").write_text("dirty", encoding="utf-8")
        dirty = json.loads(self.run_cli("check", "root-repo").stdout)
        self.assertFalse(dirty["eligible"])
        self.assertTrue(any("dirty Git repository" in item for item in dirty["blockers"]))

    def test_clean_git_repository_with_local_only_history_blocks_cleanup(self) -> None:
        self.run_cli("create", "local-only")
        repository = self.root / "local-only" / "repo"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Codex Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repository), "config", "user.email", "codex-test@example.invalid"],
            check=True,
        )
        (repository / "unique.txt").write_text("local history", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "add", "unique.txt"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-qm", "local only"], check=True)
        self.run_cli("complete", "local-only")

        result = json.loads(self.run_cli("check", "local-only").stdout)

        self.assertFalse(result["eligible"])
        self.assertTrue(any("no remote" in item for item in result["blockers"]))

    def test_custom_git_ref_with_unique_history_blocks_cleanup(self) -> None:
        self.run_cli("create", "custom-ref")
        repository = self.root / "custom-ref" / "repo"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Codex Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repository), "config", "user.email", "codex-test@example.invalid"],
            check=True,
        )
        (repository / "tracked.txt").write_text("baseline", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-qm", "baseline"], check=True)
        remote = self.root.parent / "custom-ref-remote.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repository), "remote", "add", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repository), "push", "-qu", "origin", "HEAD"], check=True)
        tree = subprocess.run(
            ["git", "-C", str(repository), "write-tree"], capture_output=True, text=True, check=True
        ).stdout.strip()
        unique = subprocess.run(
            ["git", "-C", str(repository), "commit-tree", tree, "-p", "HEAD"],
            input="unique custom ref\n",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "-C", str(repository), "update-ref", "refs/notes/codex-tmp-test", unique],
            check=True,
        )
        self.run_cli("complete", "custom-ref")

        result = json.loads(self.run_cli("check", "custom-ref").stdout)

        self.assertFalse(result["eligible"])
        self.assertTrue(any("local-only Git history" in item for item in result["blockers"]))

    def test_remote_tracking_ref_does_not_replace_live_remote_verification(self) -> None:
        self.run_cli("create", "stale-remote-ref")
        repository = self.root / "stale-remote-ref" / "repo"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Codex Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repository), "config", "user.email", "codex-test@example.invalid"],
            check=True,
        )
        (repository / "tracked.txt").write_text("baseline", encoding="utf-8")
        subprocess.run(["git", "-C", str(repository), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-qm", "baseline"], check=True)
        remote = self.root.parent / "stale-remote-ref.git"
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repository), "remote", "add", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repository), "push", "-qu", "origin", "HEAD"], check=True)
        tree = subprocess.run(
            ["git", "-C", str(repository), "write-tree"], capture_output=True, text=True, check=True
        ).stdout.strip()
        unique = subprocess.run(
            ["git", "-C", str(repository), "commit-tree", tree, "-p", "HEAD"],
            input="local only\n",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "-C", str(repository), "update-ref", "refs/remotes/origin/local-only", unique],
            check=True,
        )
        self.run_cli("complete", "stale-remote-ref")

        result = json.loads(self.run_cli("check", "stale-remote-ref").stdout)

        self.assertFalse(result["eligible"])
        self.assertTrue(any("local-only Git history" in item for item in result["blockers"]))

    def test_unmanaged_task_is_never_quarantined(self) -> None:
        (self.root / "legacy").mkdir(parents=True)
        result = json.loads(self.run_cli("sweep").stdout)
        self.assertEqual(result["quarantined"], [])
        inventory = json.loads(self.run_cli("inventory").stdout)
        self.assertEqual(inventory["counts"]["unmanaged"], 1)

    def test_task_symlink_alias_is_rejected_before_resolution(self) -> None:
        self.run_cli("create", "real-task")
        alias = self.root / "alias-task"
        alias.symlink_to(self.root / "real-task", target_is_directory=True)

        result = self.run_cli("complete", "alias-task", check=False)
        manifest = json.loads(
            (self.root / "real-task" / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not be a symlink", result.stderr)
        self.assertEqual(manifest["status"], "active")

    def test_content_change_after_completion_blocks_quarantine(self) -> None:
        self.run_cli("create", "changed")
        task = self.root / "changed"
        (task / "checkpoint.txt").write_text("first", encoding="utf-8")
        self.run_cli("complete", "changed")
        (task / "checkpoint.txt").write_text("second", encoding="utf-8")

        result = json.loads(self.run_cli("check", "changed").stdout)
        self.assertFalse(result["eligible"])
        self.assertIn("task content changed after it was marked complete", result["blockers"])

    def test_legacy_fingerprint_requires_explicit_matching_refresh(self) -> None:
        self.run_cli("create", "legacy-fingerprint")
        task = self.root / "legacy-fingerprint"
        (task / "progress.md").write_text("stable", encoding="utf-8")
        self.run_cli("complete", "legacy-fingerprint")
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["fingerprint"].pop("sha256")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        before = json.loads(self.run_cli("check", "legacy-fingerprint").stdout)
        refreshed = json.loads(
            self.run_cli("refresh-fingerprint", "legacy-fingerprint").stdout
        )
        after = json.loads(self.run_cli("check", "legacy-fingerprint").stdout)

        self.assertIn("task content changed after it was marked complete", before["blockers"])
        self.assertTrue(refreshed["refreshed"])
        self.assertEqual(len(refreshed["fingerprint"]["sha256"]), 64)
        self.assertNotIn("task content changed after it was marked complete", after["blockers"])

    def test_legacy_fingerprint_refresh_rejects_identity_mismatch(self) -> None:
        self.run_cli("create", "legacy-mismatch")
        task = self.root / "legacy-mismatch"
        (task / "progress.md").write_text("stable", encoding="utf-8")
        self.run_cli("complete", "legacy-mismatch")
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["fingerprint"].pop("sha256")
        manifest["fingerprint"]["bytes"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = self.run_cli("refresh-fingerprint", "legacy-mismatch", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("identity fields do not match", result.stderr)

    def test_compaction_replaces_completed_task_with_recovery_stub(self) -> None:
        self.write_config(complete_grace_hours=999)
        recovery = self.root.parent / "evidence.tar.gz"
        recovery.write_text("verified evidence", encoding="utf-8")
        self.run_cli("create", "large-task", "--session-id", "live-session")
        task = self.root / "large-task"
        (task / "large.bin").write_bytes(b"x" * 1024 * 1024)
        (task / "checkpoint" / "progress.md").write_text("resume here", encoding="utf-8")
        self.run_cli("complete", "large-task")

        request = json.loads(
            self.run_cli(
                "compact",
                "large-task",
                "--depends-on",
                str(recovery),
                "--note",
                "restore from verified evidence",
            ).stdout
        )
        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(request["status"], "compact_pending")
        self.assertEqual(len(maintenance["compaction"]["compacted"]), 1)
        self.assertFalse((task / "large.bin").exists())
        self.assertTrue((task / "RECOVERY.md").exists())
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(manifest["compaction"]["status"], "compacted")
        self.assertGreater(manifest["compaction"]["reclaimed_allocated_bytes"], 0)
        self.assertIn(str(recovery), (task / "RECOVERY.md").read_text(encoding="utf-8"))
        package = Path(manifest["compaction"]["recovery_package"]["path"])
        self.assertEqual(
            (package / "payload" / "checkpoint" / "progress.md").read_text(encoding="utf-8"),
            "resume here",
        )
        self.assertIn(str(package), (task / "RECOVERY.md").read_text(encoding="utf-8"))

    def test_changed_recovery_package_blocks_compaction(self) -> None:
        self.write_config(complete_grace_hours=999)
        external = self.root.parent / "external-recovery"
        external.mkdir()
        self.run_cli("create", "changed-package")
        task = self.root / "changed-package"
        (task / "checkpoint" / "progress.md").write_text("first", encoding="utf-8")
        self.run_cli("complete", "changed-package")
        self.run_cli(
            "compact",
            "changed-package",
            "--depends-on",
            str(external),
            "--note",
            "verified external source",
        )
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        package = Path(manifest["compaction"]["recovery_package"]["path"])
        (package / "payload" / "checkpoint" / "progress.md").write_text(
            "changed", encoding="utf-8"
        )

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(maintenance["compaction"]["compacted"], [])
        self.assertTrue((task / "checkpoint" / "progress.md").exists())
        self.assertTrue(
            any(
                "recovery package content changed" in blocker
                for blocker in maintenance["compaction"]["checked"][0]["blockers"]
            )
        )

    def test_released_checkpoint_is_garbage_collected_after_grace(self) -> None:
        self.write_config(complete_grace_hours=999, recovery_gc_days=0)
        external = self.root.parent / "gc-external"
        external.mkdir()
        self.run_cli("create", "checkpoint-gc")
        task = self.root / "checkpoint-gc"
        (task / "checkpoint" / "progress.md").write_text("done", encoding="utf-8")
        self.run_cli("complete", "checkpoint-gc")
        self.run_cli(
            "compact",
            "checkpoint-gc",
            "--depends-on",
            str(external),
            "--note",
            "external source verified",
        )
        self.run_cli("maintenance")
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        package = Path(manifest["compaction"]["recovery_package"]["path"])

        released = json.loads(self.run_cli("release-checkpoint", "checkpoint-gc").stdout)
        dry_run = json.loads(self.run_cli("recovery-gc", "--dry-run").stdout)
        collected = json.loads(self.run_cli("recovery-gc").stdout)

        self.assertEqual(len(released["released_objects"]), 1)
        self.assertEqual(len(dry_run["purged"]), 1)
        self.assertEqual(len(collected["purged"]), 1)
        self.assertFalse(package.exists())

    def test_recovery_reference_is_scoped_to_task_instance_after_name_reuse(self) -> None:
        self.write_config(complete_grace_hours=999, quarantine_days=999, recovery_gc_days=999)
        external = self.root.parent / "instance-external"
        external.mkdir()

        self.run_cli("create", "reused")
        first_task = self.root / "reused"
        (first_task / "checkpoint" / "progress.md").write_text("first", encoding="utf-8")
        self.run_cli("complete", "reused")
        self.run_cli(
            "compact", "reused", "--depends-on", str(external),
            "--note", "first generation",
        )
        self.run_cli("maintenance")
        first_manifest = json.loads(
            (first_task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        first_instance = first_manifest["task_instance_id"]
        first_object = first_manifest["compaction"]["recovery_package"]["object_id"]
        self.write_config(complete_grace_hours=0)
        self.run_cli("sweep")
        self.write_config(complete_grace_hours=999)

        self.run_cli("create", "reused")
        second_task = self.root / "reused"
        (second_task / "checkpoint" / "progress.md").write_text("second", encoding="utf-8")
        self.run_cli("complete", "reused")
        self.run_cli(
            "compact", "reused", "--depends-on", str(external),
            "--note", "second generation",
        )
        self.run_cli("maintenance")
        second_manifest = json.loads(
            (second_task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        second_instance = second_manifest["task_instance_id"]
        second_object = second_manifest["compaction"]["recovery_package"]["object_id"]

        self.assertNotEqual(first_instance, second_instance)
        self.run_cli("release-checkpoint", "reused")
        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        self.assertIsNone(ledger["objects"][first_object]["references"][first_instance]["released_at"])
        self.assertIsNotNone(
            ledger["objects"][second_object]["references"][second_instance]["released_at"]
        )

        self.write_config(complete_grace_hours=0, quarantine_days=0)
        self.run_cli("sweep")
        self.run_cli("sweep")
        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(
            ledger["objects"][first_object]["references"][first_instance]["released_at"]
        )

    def test_recovery_reconciliation_registers_published_orphan(self) -> None:
        package = self.recovery / ("a" * 64)
        package.mkdir(parents=True)
        (package / "contract.json").write_text("{}", encoding="utf-8")

        self.run_cli("maintenance")

        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        record = ledger["objects"]["a" * 64]
        self.assertEqual(record["references"], {})
        self.assertIsNotNone(record["orphaned_at"])

    def test_recovery_reconciliation_finishes_ledger_delete_after_object_loss(self) -> None:
        self.state.mkdir(parents=True)
        object_id = "b" * 64
        (self.state / "recovery-references.json").write_text(
            json.dumps(
                {
                    "objects": {
                        object_id: {
                            "created_at": "2026-01-01T00:00:00+00:00",
                            "fingerprint": {},
                            "references": {},
                            "gc_state": "deleting",
                            "gc_started_at": "2026-01-01T00:00:00+00:00",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        self.run_cli("maintenance")

        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        self.assertNotIn(object_id, ledger["objects"])

    def test_recovery_reconciliation_marks_missing_referenced_object(self) -> None:
        self.state.mkdir(parents=True)
        object_id = "c" * 64
        (self.state / "recovery-references.json").write_text(
            json.dumps(
                {
                    "objects": {
                        object_id: {
                            "created_at": "2026-01-01T00:00:00+00:00",
                            "fingerprint": {},
                            "references": {
                                "instance": {
                                    "released_at": None,
                                    "created_at": "2026-01-01T00:00:00+00:00",
                                }
                            },
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        self.run_cli("inventory")

        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(ledger["objects"][object_id]["missing_at"])

    def test_recovery_publish_crash_without_manifest_releases_reference(self) -> None:
        self.run_cli("create", "publish-crash")
        task = self.root / "publish-crash"
        (task / "checkpoint" / "progress.md").write_text("resume", encoding="utf-8")
        self.run_cli("complete", "publish-crash")
        external = self.root.parent / "publish-crash-external"
        external.mkdir()
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            manifest = module.load_manifest(task)
            assert manifest is not None
            with self.assertRaises(RuntimeError):
                module.create_recovery_package(
                    paths,
                    config,
                    task,
                    manifest,
                    [str(external)],
                    [],
                    lambda _package: (_ for _ in ()).throw(RuntimeError("crash")),
                )

        before = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        reference = next(iter(next(iter(before["objects"].values()))["references"].values()))
        self.assertEqual(reference["state"], "publishing")
        self.assertIsNone(reference["released_at"])
        self.run_cli("inventory")
        after = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        reference = next(iter(next(iter(after["objects"].values()))["references"].values()))
        self.assertEqual(reference["state"], "released")
        self.assertIsNotNone(reference["released_at"])

    def test_recovery_publish_crash_after_manifest_activates_reference(self) -> None:
        self.run_cli("create", "publish-manifest-crash")
        task = self.root / "publish-manifest-crash"
        (task / "checkpoint" / "progress.md").write_text("resume", encoding="utf-8")
        self.run_cli("complete", "publish-manifest-crash")
        external = self.root.parent / "publish-manifest-crash-external"
        external.mkdir()
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            manifest = module.load_manifest(task)
            assert manifest is not None

            def persist_then_crash(package: dict[str, object]) -> None:
                manifest["compaction"] = {
                    "status": "pending",
                    "recovery_package": package,
                    "required_paths": [str(external)],
                }
                module.write_manifest(task, manifest)
                raise RuntimeError("crash after manifest")

            with self.assertRaises(RuntimeError):
                module.create_recovery_package(
                    paths,
                    config,
                    task,
                    manifest,
                    [str(external)],
                    [],
                    persist_then_crash,
                )

        self.run_cli("inventory")
        ledger = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        reference = next(iter(next(iter(ledger["objects"].values()))["references"].values()))
        self.assertEqual(reference["state"], "active")
        self.assertIsNone(reference["released_at"])

    def test_recovery_release_crash_after_task_purge_is_reconciled(self) -> None:
        self.write_config(complete_grace_hours=999, quarantine_days=999, recovery_gc_days=999)
        external = self.root.parent / "purge-release-external"
        external.mkdir()
        self.run_cli("create", "purge-release-crash")
        task = self.root / "purge-release-crash"
        (task / "checkpoint" / "progress.md").write_text("resume", encoding="utf-8")
        self.run_cli("complete", "purge-release-crash")
        self.run_cli(
            "compact", "purge-release-crash", "--depends-on", str(external),
            "--note", "verified external",
        )
        self.run_cli("maintenance")
        self.write_config(complete_grace_hours=0)
        self.run_cli("sweep")
        self.write_config(quarantine_days=0, purge_pending_hours=0)
        self.run_cli("sweep")
        entry = next(self.quarantine.iterdir())
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(
                module,
                "release_recovery_reference",
                side_effect=RuntimeError("crash after physical purge"),
            ):
                with self.assertRaises(RuntimeError):
                    module.purge_quarantine(paths, config, dry_run=False)

        self.assertFalse(entry.exists())
        before = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        reference = next(iter(next(iter(before["objects"].values()))["references"].values()))
        self.assertIsNone(reference["released_at"])
        self.run_cli("inventory")
        after = json.loads((self.state / "recovery-references.json").read_text(encoding="utf-8"))
        reference = next(iter(next(iter(after["objects"].values()))["references"].values()))
        self.assertEqual(reference["state"], "released")
        self.assertIsNotNone(reference["released_at"])

    def test_compaction_grace_defers_background_deletion(self) -> None:
        self.write_config(compact_grace_hours=999, complete_grace_hours=999)
        recovery = self.root.parent / "canonical-recovery"
        recovery.mkdir()
        self.run_cli("create", "deferred")
        task = self.root / "deferred"
        (task / "payload.bin").write_bytes(b"payload")
        self.run_cli("complete", "deferred")
        self.run_cli(
            "compact",
            "deferred",
            "--depends-on",
            str(recovery),
            "--note",
            "restore from canonical repository",
        )

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(maintenance["compaction"]["compacted"], [])
        self.assertTrue((task / "payload.bin").exists())
        blockers = maintenance["compaction"]["checked"][0]["blockers"]
        self.assertIn("compaction grace period has not elapsed", blockers)

    def test_compaction_requires_external_recovery_source(self) -> None:
        self.run_cli("create", "no-recovery")
        task = self.root / "no-recovery"
        (task / "payload.txt").write_text("important", encoding="utf-8")
        self.run_cli("complete", "no-recovery")

        missing = self.run_cli(
            "compact",
            "no-recovery",
            "--depends-on",
            str(self.root.parent / "missing"),
            "--note",
            "not actually recoverable",
            check=False,
        )
        internal = self.run_cli(
            "compact",
            "no-recovery",
            "--depends-on",
            str(task / "payload.txt"),
            "--note",
            "invalid in-task evidence",
            check=False,
        )

        self.assertNotEqual(missing.returncode, 0)
        self.assertNotEqual(internal.returncode, 0)
        self.assertTrue((task / "payload.txt").exists())

    def test_compaction_rejects_special_file_recovery_source(self) -> None:
        self.run_cli("create", "special-recovery")
        task = self.root / "special-recovery"
        (task / "payload.txt").write_text("important", encoding="utf-8")
        self.run_cli("complete", "special-recovery")

        result = self.run_cli(
            "compact",
            "special-recovery",
            "--depends-on",
            "/dev/null",
            "--note",
            "invalid device anchor",
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((task / "payload.txt").exists())

    def test_checkpoint_copy_rejects_symlink_swap_after_validation(self) -> None:
        self.run_cli("create", "checkpoint-symlink-race")
        task = self.root / "checkpoint-symlink-race"
        checkpoint = task / "checkpoint" / "progress.md"
        checkpoint.write_text("safe", encoding="utf-8")
        outside = self.root.parent / "outside-secret"
        outside.write_text("must not copy", encoding="utf-8")
        self.run_cli("complete", "checkpoint-symlink-race")
        external = self.root.parent / "checkpoint-race-external"
        external.mkdir()
        module = load_script_module()
        original_copy = module.copy_checkpoint_source
        swapped = False

        def swap_before_copy(task_path: Path, source: Path, destination: Path) -> None:
            nonlocal swapped
            if source.name == "checkpoint" and not swapped:
                swapped = True
                checkpoint.unlink()
                checkpoint.symlink_to(outside)
            original_copy(task_path, source, destination)

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            args = type(
                "Args",
                (),
                {
                    "depends_on": [str(external)],
                    "checkpoint": [],
                    "note": "race fixture",
                },
            )()
            with mock.patch.object(
                module, "copy_checkpoint_source", side_effect=swap_before_copy
            ):
                with self.assertRaises(module.LifecycleError):
                    module.request_compaction(args, paths, config, task)

        self.assertTrue(checkpoint.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "must not copy")
        published = [entry for entry in self.recovery.iterdir() if not entry.name.startswith(".")]
        self.assertEqual(published, [])

    def test_checkpoint_copy_rejects_ancestor_symlink_swap_after_validation(self) -> None:
        self.run_cli("create", "checkpoint-ancestor-race")
        task = self.root / "checkpoint-ancestor-race"
        checkpoint = task / "checkpoint"
        (checkpoint / "progress.md").write_text("safe", encoding="utf-8")
        outside = self.root.parent / "outside-checkpoint"
        outside.mkdir()
        (outside / "progress.md").write_text("secret", encoding="utf-8")
        displaced = task / "checkpoint-original"
        self.run_cli("complete", "checkpoint-ancestor-race")
        external = self.root.parent / "checkpoint-ancestor-external"
        external.mkdir()
        module = load_script_module()
        original_copy = module.copy_checkpoint_source
        swapped = False

        def swap_ancestor(task_path: Path, source: Path, destination: Path) -> None:
            nonlocal swapped
            if source.name == "checkpoint" and not swapped:
                swapped = True
                checkpoint.rename(displaced)
                checkpoint.symlink_to(outside, target_is_directory=True)
            original_copy(task_path, source, destination)

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            args = type(
                "Args",
                (),
                {
                    "depends_on": [str(external)],
                    "checkpoint": [],
                    "note": "ancestor race fixture",
                },
            )()
            with mock.patch.object(
                module, "copy_checkpoint_source", side_effect=swap_ancestor
            ):
                with self.assertRaises((module.LifecycleError, OSError)):
                    module.request_compaction(args, paths, config, task)

        self.assertTrue(checkpoint.is_symlink())
        self.assertEqual((outside / "progress.md").read_text(encoding="utf-8"), "secret")
        published = [entry for entry in self.recovery.iterdir() if not entry.name.startswith(".")]
        self.assertEqual(published, [])

    def test_compaction_rejects_sibling_tmp_task_as_recovery_source(self) -> None:
        self.run_cli("create", "source-task")
        self.run_cli("create", "candidate")
        candidate = self.root / "candidate"
        (candidate / "payload.txt").write_text("important", encoding="utf-8")
        self.run_cli("complete", "candidate")

        result = self.run_cli(
            "compact",
            "candidate",
            "--depends-on",
            str(self.root / "source-task"),
            "--note",
            "invalid sibling dependency",
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((candidate / "payload.txt").exists())

    def test_compaction_rejects_ancestor_of_managed_tmp_as_recovery_source(self) -> None:
        self.run_cli("create", "candidate")
        candidate = self.root / "candidate"
        (candidate / "payload.txt").write_text("important", encoding="utf-8")
        self.run_cli("complete", "candidate")

        result = self.run_cli(
            "compact",
            "candidate",
            "--depends-on",
            str(self.root.parent),
            "--note",
            "invalid ancestor dependency",
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((candidate / "payload.txt").exists())

    def test_recovery_anchor_retargeted_into_managed_storage_blocks_cleanup(self) -> None:
        external = self.root.parent / "external-recovery"
        external.mkdir()
        anchor = self.root.parent / "recovery-link"
        anchor.symlink_to(external, target_is_directory=True)
        self.run_cli("create", "source-task")
        self.run_cli("create", "candidate")
        candidate = self.root / "candidate"
        (candidate / "payload.txt").write_text("important", encoding="utf-8")
        self.run_cli("complete", "candidate", "--depends-on", str(anchor))
        external.rmdir()
        external.symlink_to(self.root / "source-task", target_is_directory=True)

        result = json.loads(self.run_cli("check", "candidate").stdout)

        self.assertFalse(result["eligible"])
        self.assertTrue(
            any(
                "recovery path must not overlap" in item
                or "recovery path must not be a symlink" in item
                for item in result["blockers"]
            )
        )

    def test_nested_mount_boundary_blocks_compaction(self) -> None:
        self.run_cli("create", "mounted")
        task = self.root / "mounted"
        nested = task / "nested"
        nested.mkdir()
        module = load_script_module()

        with mock.patch.object(module.os.path, "ismount", side_effect=lambda path: Path(path) == nested):
            blockers = module.filesystem_boundary_blockers(task)

        self.assertEqual(blockers, [f"nested filesystem boundary at {nested}"])

    def test_task_root_mount_boundary_blocks_compaction(self) -> None:
        self.run_cli("create", "root-mounted")
        task = self.root / "root-mounted"
        module = load_script_module()

        with mock.patch.object(module.os.path, "ismount", side_effect=lambda path: Path(path) == task):
            blockers = module.filesystem_boundary_blockers(task)

        self.assertEqual(blockers, [f"task root is a filesystem mount point: {task}"])

    @unittest.skipUnless(shutil.which("lsof"), "lsof is required for open-file verification")
    def test_open_file_descriptor_blocks_compaction(self) -> None:
        self.run_cli("create", "open-file")
        task = self.root / "open-file"
        payload = task / "payload.txt"
        payload.write_text("in use", encoding="utf-8")
        module = load_script_module()

        with payload.open("r", encoding="utf-8"):
            blockers = module.process_blockers(task)

        self.assertIn("a running process has an open file or cwd inside the task", blockers)

    @unittest.skipUnless(shutil.which("lsof"), "lsof is required for cwd verification")
    def test_process_cwd_blocks_compaction(self) -> None:
        self.run_cli("create", "process-cwd")
        task = self.root / "process-cwd"
        process = subprocess.Popen(["sleep", "10"], cwd=task)
        module = load_script_module()
        try:
            blockers = module.process_blockers(task)
        finally:
            process.terminate()
            process.wait(timeout=5)

        self.assertIn("a running process has an open file or cwd inside the task", blockers)

    def test_missing_lsof_blocks_compaction(self) -> None:
        self.run_cli("create", "no-lsof")
        task = self.root / "no-lsof"
        module = load_script_module()

        with mock.patch.object(module.shutil, "which", return_value=None):
            blockers = module.process_blockers(task)

        self.assertIn("open-file check failed: lsof is unavailable", blockers)

    def test_lsof_error_blocks_compaction(self) -> None:
        self.run_cli("create", "lsof-error")
        task = self.root / "lsof-error"
        module = load_script_module()
        ps_result = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        lsof_result = subprocess.CompletedProcess([], 2, stdout="", stderr="failed")

        with mock.patch.object(module.shutil, "which", return_value="/usr/sbin/lsof"):
            with mock.patch.object(module.subprocess, "run", side_effect=[ps_result, lsof_result]):
                blockers = module.process_blockers(task)

        self.assertIn("open-file check failed with exit code 2", blockers)

    def test_lsof_success_with_diagnostics_blocks_compaction(self) -> None:
        self.run_cli("create", "lsof-diagnostic")
        task = self.root / "lsof-diagnostic"
        module = load_script_module()
        ps_result = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        lsof_result = subprocess.CompletedProcess(
            [], 0, stdout="", stderr="partial traversal warning"
        )

        with mock.patch.object(module.shutil, "which", return_value="/usr/sbin/lsof"):
            with mock.patch.object(module.subprocess, "run", side_effect=[ps_result, lsof_result]):
                blockers = module.process_blockers(task)

        self.assertIn("open-file check failed with exit code 0", blockers)

    def test_process_name_containing_codex_tmp_does_not_bypass_reference_check(self) -> None:
        self.run_cli("create", "process-name")
        task = self.root / "process-name"
        module = load_script_module()
        ps_result = subprocess.CompletedProcess(
            [],
            0,
            stdout=f"4242 worker-codex-tmp --workspace {task.resolve()}\n",
            stderr="",
        )
        lsof_result = subprocess.CompletedProcess([], 1, stdout="", stderr="")

        with mock.patch.object(module.shutil, "which", return_value="/usr/sbin/lsof"):
            with mock.patch.object(module.subprocess, "run", side_effect=[ps_result, lsof_result]):
                blockers = module.process_blockers(task)

        self.assertTrue(any("running process references task" in item for item in blockers))

    def test_bare_git_repository_without_remote_blocks_compaction(self) -> None:
        self.run_cli("create", "bare-git")
        task = self.root / "bare-git"
        bare = task / "mirror.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        module = load_script_module()

        blockers = module.git_blockers(task)

        self.assertIn(f"Git repository has no remote at {bare}", blockers)

    def test_malformed_bare_git_repository_blocks_compaction(self) -> None:
        self.run_cli("create", "malformed-bare")
        task = self.root / "malformed-bare"
        bare = task / "broken.git"
        (bare / "objects").mkdir(parents=True)
        (bare / "refs").mkdir()
        (bare / "HEAD").write_text("not a git head\n", encoding="utf-8")
        module = load_script_module()

        blockers = module.git_blockers(task)

        self.assertIn(f"cannot inspect bare Git repository at {bare}", blockers)

    def test_content_change_after_compaction_request_blocks_deletion(self) -> None:
        self.write_config(complete_grace_hours=999)
        recovery = self.root.parent / "canonical"
        recovery.mkdir()
        self.run_cli("create", "changed-before-compact")
        task = self.root / "changed-before-compact"
        payload = task / "payload.txt"
        payload.write_text("first", encoding="utf-8")
        self.run_cli("complete", "changed-before-compact")
        self.run_cli(
            "compact",
            "changed-before-compact",
            "--depends-on",
            str(recovery),
            "--note",
            "restore from canonical",
        )
        payload.write_text("changed", encoding="utf-8")

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(maintenance["compaction"]["compacted"], [])
        self.assertTrue(payload.exists())
        self.assertIn(
            "task content changed after compaction was requested",
            maintenance["compaction"]["checked"][0]["blockers"],
        )

    def test_compaction_rechecks_fingerprint_after_moving_content(self) -> None:
        recovery = self.root.parent / "canonical-race"
        recovery.mkdir()
        self.run_cli("create", "changed-during-compact")
        task = self.root / "changed-during-compact"
        payload = task / "payload.txt"
        payload.write_text("original", encoding="utf-8")
        self.run_cli("complete", "changed-during-compact")
        self.run_cli(
            "compact",
            "changed-during-compact",
            "--depends-on",
            str(recovery),
            "--note",
            "restore from canonical",
        )
        module = load_script_module()
        original_replace = module.os.replace

        def replace_after_changing_source(source: object, destination: object) -> None:
            if Path(source) == payload:
                payload.write_text("replacement", encoding="utf-8")
            original_replace(source, destination)

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(module.os, "replace", side_effect=replace_after_changing_source):
                with self.assertRaises(module.LifecycleError):
                    module.compact_completed_tasks(paths, config)

        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "compact_incomplete")
        self.assertEqual(
            (task / ".codex-tmp-compacting" / "payload.txt").read_text(encoding="utf-8"),
            "replacement",
        )

    def test_compaction_rechecks_git_before_deletion_snapshot(self) -> None:
        recovery = self.root.parent / "canonical-final-git"
        recovery.mkdir()
        self.run_cli("create", "final-git-check")
        task = self.root / "final-git-check"
        (task / "payload.txt").write_text("rebuildable", encoding="utf-8")
        self.run_cli("complete", "final-git-check")
        self.run_cli(
            "compact",
            "final-git-check",
            "--depends-on",
            str(recovery),
            "--note",
            "restore from canonical",
        )
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(module, "git_blockers", side_effect=[[], ["new Git blocker"]]):
                with self.assertRaises(module.LifecycleError):
                    module.compact_completed_tasks(paths, config)

        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "compact_incomplete")
        self.assertTrue((task / ".codex-tmp-compacting" / "payload.txt").exists())

    def test_git_checks_disable_optional_locks(self) -> None:
        module = load_script_module()

        with mock.patch.dict(os.environ, {"GIT_OPTIONAL_LOCKS": "1"}, clear=False):
            environment = module.git_read_only_environment()

        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")

    def test_check_releases_global_state_lock_before_git_inspection(self) -> None:
        self.run_cli("create", "lock-scope")
        self.run_cli("complete", "lock-scope")
        module = load_script_module()
        observed: list[bool] = []

        def inspect_without_global_lock(_task: Path) -> list[str]:
            paths = module.Paths()
            with module.lifecycle_lock(paths, blocking=False) as acquired:
                observed.append(acquired)
            return []

        with (
            mock.patch.dict(os.environ, self.env, clear=False),
            mock.patch.object(module, "git_blockers", side_effect=inspect_without_global_lock),
            mock.patch.object(module.sys, "argv", [str(SCRIPT), "check", "lock-scope"]),
            mock.patch.object(module.sys, "stdout", new=io.StringIO()),
        ):
            return_code = module.main()

        self.assertEqual(return_code, 0)
        self.assertTrue(observed)
        self.assertTrue(all(observed))

    def test_interrupted_compaction_is_retried_by_maintenance(self) -> None:
        self.write_config(complete_grace_hours=999)
        recovery = self.root.parent / "canonical-repo"
        recovery.mkdir()
        self.run_cli("create", "compact-interrupted")
        task = self.root / "compact-interrupted"
        (task / "payload.txt").write_text("rebuildable", encoding="utf-8")
        self.run_cli("complete", "compact-interrupted")
        self.run_cli(
            "compact",
            "compact-interrupted",
            "--depends-on",
            str(recovery),
            "--note",
            "restore from canonical repository",
        )
        module = load_script_module()
        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(
                module, "remove_tree_same_device", side_effect=OSError("interrupted")
            ):
                with self.assertRaises(OSError):
                    module.compact_completed_tasks(paths, config)

        interrupted = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(interrupted["status"], "compact_incomplete")
        self.assertTrue((task / ".codex-tmp-compacting").exists())

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(module, "git_blockers", return_value=["new Git blocker"]):
                blocked_retry = module.compact_completed_tasks(paths, config)
        self.assertEqual(blocked_retry["compacted"], [])
        self.assertIn("new Git blocker", blocked_retry["checked"][0]["blockers"])
        self.assertTrue((task / ".codex-tmp-compacting").exists())

        tombstone_payload = task / ".codex-tmp-compacting" / "payload.txt"
        original = tombstone_payload.stat()
        original_content = tombstone_payload.read_bytes()
        tombstone_payload.unlink()
        partial_retry = json.loads(self.run_cli("maintenance").stdout)
        self.assertEqual(partial_retry["compaction"]["compacted"], [])
        self.assertIn(
            "compaction tombstone no longer matches the requested fingerprint",
            partial_retry["compaction"]["checked"][0]["blockers"],
        )
        tombstone_payload.write_bytes(original_content)
        os.utime(tombstone_payload, ns=(original.st_atime_ns, original.st_mtime_ns))

        (task / "new-after-interruption.txt").write_text("unique", encoding="utf-8")
        changed_retry = json.loads(self.run_cli("maintenance").stdout)
        self.assertEqual(changed_retry["compaction"]["compacted"], [])
        self.assertIn(
            "task received new content after compaction was interrupted",
            changed_retry["compaction"]["checked"][0]["blockers"],
        )
        (task / "new-after-interruption.txt").unlink()

        maintenance = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual(len(maintenance["compaction"]["compacted"]), 1)
        self.assertFalse((task / ".codex-tmp-compacting").exists())
        self.assertTrue((task / "RECOVERY.md").exists())

    def test_legacy_interrupted_compaction_can_attach_package_and_retry(self) -> None:
        self.write_config(complete_grace_hours=999)
        external = self.root.parent / "legacy-compact-external"
        external.mkdir()
        self.run_cli("create", "legacy-compact")
        task = self.root / "legacy-compact"
        (task / "payload.txt").write_text("remaining partial body", encoding="utf-8")
        (task / "checkpoint" / "progress.md").write_text(
            "unique recovery state", encoding="utf-8"
        )
        self.run_cli("complete", "legacy-compact")
        module = load_script_module()
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        manifest.pop("task_instance_id")
        manifest.pop("budget")
        tombstone = task / ".codex-tmp-compacting"
        tombstone.mkdir()
        for child in list(task.iterdir()):
            if child.name not in {".codex-tmp-task.json", tombstone.name}:
                child.rename(tombstone / child.name)
        manifest["status"] = "compact_incomplete"
        manifest["compaction"] = {
            "status": "compact_incomplete",
            "phase": "deleting",
            "fingerprint": manifest["fingerprint"],
            "required_paths": [str(external)],
            "recovery_note": "legacy external recovery",
            "not_before": "2000-01-01T00:00:00+00:00",
        }
        module.write_manifest(task, manifest)

        migration_result = self.run_cli(
            "migrate-legacy-compaction", "legacy-compact", check=False
        )
        self.assertEqual(migration_result.returncode, 0, migration_result.stderr)
        migrated = json.loads(migration_result.stdout)
        recovery_payload = (
            Path(migrated["recovery_package"]["path"])
            / "payload"
            / "checkpoint"
            / "progress.md"
        )
        self.assertEqual(
            recovery_payload.read_text(encoding="utf-8"), "unique recovery state"
        )
        maintenance_result = self.run_cli("maintenance", check=False)
        self.assertEqual(maintenance_result.returncode, 0, maintenance_result.stderr)
        maintenance = json.loads(maintenance_result.stdout)
        final_manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )

        self.assertTrue(migrated["ready_for_maintenance_retry"])
        self.assertEqual(len(maintenance["compaction"]["compacted"]), 1)
        self.assertFalse(tombstone.exists())
        self.assertTrue((task / "RECOVERY.md").exists())
        self.assertEqual(
            recovery_payload.read_text(encoding="utf-8"), "unique recovery state"
        )
        self.assertIsNotNone(final_manifest.get("task_instance_id"))
        self.assertEqual(final_manifest["budget"]["class"], "default")
        self.assertIsInstance(final_manifest["compaction"].get("recovery_package"), dict)
        check_result = json.loads(self.run_cli("check", "legacy-compact").stdout)
        self.assertEqual(check_result["compaction"]["blockers"], [])

    def test_recovery_reconcile_serializes_with_manifest_move(self) -> None:
        external = self.root.parent / "reconcile-move-external"
        external.mkdir()
        self.run_cli("create", "reconcile-move")
        task = self.root / "reconcile-move"
        (task / "checkpoint" / "progress.md").write_text("resume", encoding="utf-8")
        self.run_cli("complete", "reconcile-move")
        self.run_cli(
            "compact",
            "reconcile-move",
            "--depends-on",
            str(external),
            "--note",
            "barrier fixture",
        )
        module = load_script_module()
        entered_enumeration = threading.Event()
        release_enumeration = threading.Event()
        move_finished = threading.Event()
        failures: list[BaseException] = []

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            manifest = module.load_manifest(task)
            assert manifest is not None
            locations = list(module.iter_tasks(paths))
            destination = self.quarantine / "reconcile-move-quarantine"

            def paused_iter(_paths: object) -> object:
                entered_enumeration.set()
                if not release_enumeration.wait(5):
                    raise RuntimeError("fixture barrier timed out")
                yield from locations

            def reconcile() -> None:
                try:
                    module.reconcile_recovery_store(paths)
                except BaseException as exc:
                    failures.append(exc)

            def move() -> None:
                try:
                    module.move_with_transition(
                        paths, task, destination, manifest, "quarantine"
                    )
                except BaseException as exc:
                    failures.append(exc)
                finally:
                    move_finished.set()

            with mock.patch.object(module, "iter_tasks", side_effect=paused_iter):
                reconcile_thread = threading.Thread(target=reconcile)
                reconcile_thread.start()
                self.assertTrue(entered_enumeration.wait(5))
                move_thread = threading.Thread(target=move)
                move_thread.start()
                self.assertFalse(move_finished.wait(0.2))
                release_enumeration.set()
                reconcile_thread.join(5)
                move_thread.join(5)

        self.assertEqual(failures, [])
        self.assertTrue(move_finished.is_set())
        self.assertTrue(destination.exists())
        ledger = json.loads(
            (self.state / "recovery-references.json").read_text(encoding="utf-8")
        )
        reference = next(iter(next(iter(ledger["objects"].values()))["references"].values()))
        self.assertEqual(reference["state"], "active")
        self.assertIsNone(reference["released_at"])

    def test_transition_reconcile_rejects_wrong_destination_generation(self) -> None:
        self.run_cli("create", "reconcile-generation")
        task = self.root / "reconcile-generation"
        self.run_cli("complete", "reconcile-generation")
        module = load_script_module()
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        original_stat = task.stat()
        destination = self.quarantine / "reconcile-generation-quarantine"
        task.rename(destination)
        replacement = module.new_manifest(destination)
        replacement["status"] = "complete"
        replacement["transition"] = {
            "kind": "quarantine",
            "source": str(task),
            "destination": str(destination),
            "started_at": "2026-01-01T00:00:00+00:00",
            "source_device": original_stat.st_dev,
            "source_inode": original_stat.st_ino + 1,
            "task_instance_id": manifest["task_instance_id"],
        }
        module.write_manifest(destination, replacement)

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            with self.assertRaises(module.LifecycleError):
                module.reconcile_transitions(paths)

        self.assertTrue(destination.exists())
        self.assertFalse(task.exists())

    def test_same_device_removal_refuses_cross_device_child(self) -> None:
        task = self.root / "xdev"
        nested = task / "nested"
        nested.mkdir(parents=True)
        (nested / "payload.txt").write_text("keep", encoding="utf-8")
        module = load_script_module()
        expected_device = task.stat().st_dev
        original_stat = module.os.stat

        def cross_device_stat(path: object, **kwargs: object) -> object:
            if path == "nested" and kwargs.get("dir_fd") is not None:
                return mock.Mock(st_dev=expected_device + 1, st_mode=stat.S_IFDIR)
            return original_stat(path, **kwargs)

        with mock.patch.object(module.os, "stat", side_effect=cross_device_stat):
            with self.assertRaises(module.LifecycleError):
                module.remove_tree_same_device(task, expected_device)

        self.assertTrue((nested / "payload.txt").exists())

    def test_same_device_removal_refuses_replaced_same_name_entry(self) -> None:
        root = self.root.parent / "replace-race"
        root.mkdir()
        payload = root / "payload.txt"
        payload.write_text("original", encoding="utf-8")
        module = load_script_module()
        original_rename = module.os.rename
        replaced = False

        def replace_before_staging(
            source: object,
            destination: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal replaced
            if source == "payload.txt" and not replaced:
                replaced = True
                replacement = root / "replacement.txt"
                replacement.write_text("new unique content", encoding="utf-8")
                os.replace(replacement, payload)
            original_rename(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(module.os, "rename", side_effect=replace_before_staging):
            with self.assertRaises(module.LifecycleError):
                module.remove_tree_same_device(root, root.stat().st_dev, root.stat().st_ino)

        remaining = [path.read_text(encoding="utf-8") for path in root.iterdir() if path.is_file()]
        self.assertIn("new unique content", remaining)

    def test_same_device_removal_refuses_in_place_content_change(self) -> None:
        root = self.root.parent / "in-place-race"
        root.mkdir()
        payload = root / "payload.txt"
        payload.write_text("original", encoding="utf-8")
        module = load_script_module()
        original_rename = module.os.rename
        changed = False

        def change_before_staging(
            source: object,
            destination: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal changed
            if source == "payload.txt" and not changed:
                changed = True
                payload.write_text("new unique in-place content", encoding="utf-8")
            original_rename(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(module.os, "rename", side_effect=change_before_staging):
            with self.assertRaises(module.LifecycleError):
                module.remove_tree_same_device(root, root.stat().st_dev, root.stat().st_ino)

        remaining = [path.read_text(encoding="utf-8") for path in root.iterdir() if path.is_file()]
        self.assertIn("new unique in-place content", remaining)

    def test_same_device_removal_refuses_same_size_change_with_restored_mtime(self) -> None:
        root = self.root.parent / "same-size-race"
        root.mkdir()
        payload = root / "payload.txt"
        payload.write_text("original", encoding="utf-8")
        original_stat = payload.stat()
        module = load_script_module()
        original_rename = module.os.rename
        changed = False

        def change_before_staging(
            source: object,
            destination: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal changed
            if source == "payload.txt" and not changed:
                changed = True
                payload.write_text("replaced", encoding="utf-8")
                os.utime(payload, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
            original_rename(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(module.os, "rename", side_effect=change_before_staging):
            with self.assertRaises(module.LifecycleError):
                module.remove_tree_same_device(root, root.stat().st_dev, root.stat().st_ino)

        remaining = [path.read_text(encoding="utf-8") for path in root.iterdir() if path.is_file()]
        self.assertIn("replaced", remaining)

    def test_same_device_removal_never_overwrites_reappeared_name(self) -> None:
        root = self.root.parent / "reappeared-name-race"
        root.mkdir()
        payload = root / "payload.txt"
        payload.write_text("original", encoding="utf-8")
        module = load_script_module()
        original_rename = module.os.rename
        changed = False

        def replace_and_recreate_name(
            source: object,
            destination: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal changed
            if source == "payload.txt" and not changed:
                changed = True
                replacement = root / "replacement.txt"
                replacement.write_text("staged replacement", encoding="utf-8")
                os.replace(replacement, payload)
                original_rename(
                    source,
                    destination,
                    src_dir_fd=src_dir_fd,
                    dst_dir_fd=dst_dir_fd,
                )
                payload.write_text("new content at original name", encoding="utf-8")
                return
            original_rename(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(module.os, "rename", side_effect=replace_and_recreate_name):
            with self.assertRaises(module.LifecycleError):
                module.remove_tree_same_device(root, root.stat().st_dev, root.stat().st_ino)

        self.assertEqual(payload.read_text(encoding="utf-8"), "new content at original name")

    def test_launchagent_sets_homebrew_python_path(self) -> None:
        plist = Path(__file__).resolve().parents[1] / "launchd" / "com.edwardtoday.codex-tmp-lifecycle.plist"
        payload = plistlib.loads(plist.read_bytes())

        path = payload["EnvironmentVariables"]["PATH"].split(":")

        self.assertEqual(path[0], "/opt/homebrew/bin")
        self.assertIn("/usr/bin", path)

    def test_same_size_same_mtime_content_change_is_detected(self) -> None:
        self.run_cli("create", "hash-changed")
        task = self.root / "hash-changed"
        checkpoint = task / "checkpoint.txt"
        checkpoint.write_text("first", encoding="utf-8")
        original = checkpoint.stat()
        self.run_cli("complete", "hash-changed")
        checkpoint.write_text("other", encoding="utf-8")
        os.utime(checkpoint, ns=(original.st_atime_ns, original.st_mtime_ns))

        result = json.loads(self.run_cli("check", "hash-changed").stdout)
        self.assertFalse(result["eligible"])
        self.assertIn("task content changed after it was marked complete", result["blockers"])

    def test_fingerprint_framing_distinguishes_ambiguous_file_trees(self) -> None:
        self.run_cli("create", "framed-hash")
        task = self.root / "framed-hash"
        first = task / "a"
        second = task / "b"
        first.write_bytes(b"X")
        second.write_bytes(b"Yc\0Z")
        timestamp = 1_700_000_000_000_000_000
        os.utime(first, ns=(timestamp, timestamp))
        os.utime(second, ns=(timestamp, timestamp))
        self.run_cli("complete", "framed-hash")

        first.write_bytes(b"Xb\0Y")
        second.unlink()
        third = task / "c"
        third.write_bytes(b"Z")
        os.utime(first, ns=(timestamp, timestamp))
        os.utime(third, ns=(timestamp, timestamp))

        result = json.loads(self.run_cli("check", "framed-hash").stdout)
        self.assertFalse(result["eligible"])
        self.assertIn("task content changed after it was marked complete", result["blockers"])

    def test_internal_symlink_retarget_is_detected(self) -> None:
        self.run_cli("create", "symlink-changed")
        task = self.root / "symlink-changed"
        (task / "first.txt").write_text("first", encoding="utf-8")
        (task / "second.txt").write_text("second", encoding="utf-8")
        link = task / "current.txt"
        link.symlink_to("first.txt")
        self.run_cli("complete", "symlink-changed")
        link.unlink()
        link.symlink_to("second.txt")

        result = json.loads(self.run_cli("check", "symlink-changed").stdout)

        self.assertFalse(result["eligible"])
        self.assertIn("task content changed after it was marked complete", result["blockers"])

    def test_purge_revalidates_quarantined_content(self) -> None:
        self.run_cli("create", "quarantine-changed")
        task = self.root / "quarantine-changed"
        (task / "checkpoint.txt").write_text("first", encoding="utf-8")
        self.run_cli("complete", "quarantine-changed")
        self.run_cli("sweep")
        quarantined = next(self.quarantine.iterdir())
        (quarantined / "checkpoint.txt").write_text("changed", encoding="utf-8")
        self.write_config(quarantine_days=0)

        sweep = json.loads(self.run_cli("sweep").stdout)

        self.assertEqual(sweep["purged"], [])
        self.assertTrue(quarantined.exists())

    def test_purge_drains_heartbeat_queued_during_initial_revalidation(self) -> None:
        self.write_config(quarantine_days=0, session_stale_hours=168)
        self.run_cli("create", "queued-before-purge", "--session-id", "resumed-session")
        task = self.root / "queued-before-purge"
        (task / "checkpoint.txt").write_text("recover me", encoding="utf-8")
        self.run_cli("complete", "queued-before-purge")
        self.write_config(quarantine_days=999, session_stale_hours=0)
        self.run_cli("sweep")
        quarantined = next(self.quarantine.iterdir())
        self.write_config(quarantine_days=0, session_stale_hours=168)

        module = load_script_module()
        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            paths.prepare()
            config = module.load_config(paths)
            original_blockers = module.preservation_blockers
            calls = 0

            def queue_during_first_check(*args: object) -> list[str]:
                nonlocal calls
                calls += 1
                if calls == 1:
                    module.queue_hook_event(
                        paths,
                        {
                            "session_id": "resumed-session",
                            "cwd": str(task),
                            "hook_event_name": "Stop",
                        },
                    )
                    return []
                return original_blockers(*args)

            with mock.patch.object(module, "preservation_blockers", side_effect=queue_during_first_check):
                purged = module.purge_quarantine(paths, config, dry_run=False)

        self.assertEqual(purged, [])
        self.assertFalse(quarantined.exists())
        self.assertTrue(task.exists())
        restored_manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(restored_manifest["status"], "active")
        sessions = json.loads((self.state / "sessions.json").read_text(encoding="utf-8"))
        self.assertIn("resumed-session", sessions)
        self.assertEqual(list((self.state / "pending-hooks").glob("*.json")), [])

    def test_purge_final_fence_defers_when_heartbeat_arrives_after_second_drain(self) -> None:
        self.write_config(quarantine_days=0, purge_pending_hours=0, session_stale_hours=0)
        self.run_cli("create", "queued-at-final-fence")
        task = self.root / "queued-at-final-fence"
        (task / "checkpoint.txt").write_text("recover me", encoding="utf-8")
        self.run_cli("complete", "queued-at-final-fence")
        self.run_cli("sweep")
        quarantined = next(self.quarantine.iterdir())

        module = load_script_module()
        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            original_drain = module.drain_pending_hooks
            calls = 0

            def queue_after_second_drain(*args: object) -> None:
                nonlocal calls
                original_drain(*args)
                calls += 1
                if calls == 2:
                    module.queue_hook_event(
                        paths,
                        {
                            "session_id": "late-resume",
                            "cwd": str(task),
                            "hook_event_name": "SessionStart",
                        },
                    )

            with mock.patch.object(
                module, "drain_pending_hooks", side_effect=queue_after_second_drain
            ):
                purged = module.purge_quarantine(paths, config, dry_run=False)

        self.assertEqual(purged, [])
        self.assertTrue(quarantined.exists())
        self.assertEqual(len(list((self.state / "pending-hooks").glob("*.json"))), 1)
        self.run_cli("maintenance")
        self.assertTrue(task.exists())
        self.assertFalse(quarantined.exists())

    def test_hook_restores_quarantined_workspace_for_original_cwd(self) -> None:
        self.run_cli("create", "resume-quarantine", "--session-id", "old-session")
        task = self.root / "resume-quarantine"
        (task / "checkpoint.txt").write_text("recover me", encoding="utf-8")
        self.run_cli("complete", "resume-quarantine")
        self.run_cli("sweep")
        self.assertFalse(task.exists())

        self.run_cli(
            "hook",
            input_data={
                "session_id": "new-session",
                "cwd": str(task),
                "hook_event_name": "SessionStart",
            },
        )
        self.run_cli("maintenance")

        self.assertTrue(task.exists())
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "active")
        self.assertIn("new-session", manifest["owner_session_ids"])
        self.assertEqual(list(self.quarantine.iterdir()), [])

    def test_purge_requires_a_later_sweep_after_pending_state(self) -> None:
        self.write_config(quarantine_days=0, purge_pending_hours=0)
        self.run_cli("create", "two-phase-purge")
        task = self.root / "two-phase-purge"
        (task / "checkpoint.txt").write_text("done", encoding="utf-8")
        self.run_cli("complete", "two-phase-purge")

        first = json.loads(self.run_cli("sweep").stdout)
        entry = next(self.quarantine.iterdir())
        manifest = json.loads((entry / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(first["purged"], [])
        self.assertEqual(manifest["status"], "purge_pending")

        second = json.loads(self.run_cli("sweep").stdout)
        self.assertEqual(len(second["purged"]), 1)
        self.assertFalse(entry.exists())

    def test_interrupted_recursive_purge_is_marked_incomplete(self) -> None:
        self.write_config(quarantine_days=0, purge_pending_hours=0)
        self.run_cli("create", "purge-interrupted")
        task = self.root / "purge-interrupted"
        (task / "checkpoint.txt").write_text("must not look intact", encoding="utf-8")
        self.run_cli("complete", "purge-interrupted")
        self.run_cli("sweep")
        entry = next(self.quarantine.iterdir())
        module = load_script_module()

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(
                module, "remove_tree_same_device", side_effect=OSError("interrupted")
            ):
                with self.assertRaises(OSError):
                    module.purge_quarantine(paths, config, dry_run=False)

        manifest = json.loads((entry / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "purge_incomplete")
        self.assertTrue(entry.exists())

    def test_purge_uses_same_device_removal(self) -> None:
        self.write_config(quarantine_days=0, purge_pending_hours=0)
        self.run_cli("create", "purge-same-device")
        task = self.root / "purge-same-device"
        (task / "checkpoint.txt").write_text("done", encoding="utf-8")
        self.run_cli("complete", "purge-same-device")
        self.run_cli("sweep")
        entry = next(self.quarantine.iterdir())
        module = load_script_module()
        original_remove = module.remove_tree_same_device
        calls: list[tuple[Path, int, int | None]] = []

        def record_removal(
            path: Path,
            expected_device: int,
            expected_inode: int | None = None,
            expected_entries: dict[
                str, tuple[tuple[int, int, int, int, int, int], bytes | None]
            ]
            | None = None,
        ) -> None:
            calls.append((path, expected_device, expected_inode))
            original_remove(path, expected_device, expected_inode, expected_entries)

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            config = module.load_config(paths)
            with mock.patch.object(module, "remove_tree_same_device", side_effect=record_removal):
                module.purge_quarantine(paths, config, dry_run=False)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], self.quarantine.stat().st_dev)
        self.assertFalse(entry.exists())

    def test_failed_quarantine_move_rolls_back_transition(self) -> None:
        self.run_cli("create", "move-fails")
        task = self.root / "move-fails"
        self.run_cli("complete", "move-fails")
        module = load_script_module()
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        destination = self.quarantine / "failed-destination"
        original_replace = module.os.replace

        def fail_task_move(
            source: object,
            target: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            if source == task.name and target == destination.name:
                raise OSError("fixture failure")
            original_replace(
                source,
                target,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            with mock.patch.object(module.os, "replace", side_effect=fail_task_move):
                with self.assertRaises(module.LifecycleError):
                    module.move_with_transition(
                        paths, task, destination, manifest, "quarantine"
                    )

        persisted = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["status"], "complete")
        self.assertNotIn("transition", persisted)

    def test_quarantine_rejects_same_name_task_generation_swap_at_rename(self) -> None:
        self.run_cli("create", "generation-swap")
        task = self.root / "generation-swap"
        (task / "payload.txt").write_text("same", encoding="utf-8")
        self.run_cli("complete", "generation-swap")
        module = load_script_module()
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        original_instance = manifest["task_instance_id"]
        destination = self.quarantine / "generation-swap-quarantine"
        displaced = self.root / "generation-swap-old"
        original_replace = module.os.replace
        swapped = False

        def swap_at_rename(
            source: object,
            target: object,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal swapped
            if source == task.name and target == destination.name and not swapped:
                swapped = True
                task.rename(displaced)
                task.mkdir()
                replacement = module.new_manifest(task)
                replacement["status"] = "complete"
                replacement["completed_at"] = manifest["completed_at"]
                replacement["fingerprint"] = manifest["fingerprint"]
                (task / "payload.txt").write_text("same", encoding="utf-8")
                module.write_manifest(task, replacement)
            original_replace(
                source,
                target,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            with mock.patch.object(module.os, "replace", side_effect=swap_at_rename):
                with self.assertRaises(module.LifecycleError):
                    module.move_with_transition(
                        paths, task, destination, manifest, "quarantine"
                    )

        self.assertTrue(displaced.exists())
        self.assertTrue(task.exists())
        self.assertFalse(destination.exists())
        restored_manifest = json.loads(
            (task / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertNotEqual(restored_manifest["task_instance_id"], original_instance)
        displaced_manifest = json.loads(
            (displaced / ".codex-tmp-task.json").read_text(encoding="utf-8")
        )
        self.assertEqual(displaced_manifest["task_instance_id"], original_instance)

    def test_dirty_git_repository_inside_regenerable_tree_blocks_cleanup(self) -> None:
        self.run_cli("create", "nested-cache-git")
        task = self.root / "nested-cache-git"
        repository = task / "node_modules" / "dependency"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        self.run_cli("complete", "nested-cache-git")
        (repository / "untracked.txt").write_text("dirty", encoding="utf-8")

        result = json.loads(self.run_cli("check", "nested-cache-git").stdout)

        self.assertFalse(result["eligible"])
        self.assertTrue(any("dirty Git repository" in item for item in result["blockers"]))

    def test_hook_adopts_tmp_cwd_as_active_and_records_session(self) -> None:
        task = self.root / "resumable"
        task.mkdir(parents=True)
        self.run_cli(
            "hook",
            input_data={
                "session_id": "session-1",
                "cwd": str(task),
                "hook_event_name": "Stop",
            },
        )
        self.run_cli("maintenance")
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "active")
        self.assertEqual(manifest["owner_session_ids"], ["session-1"])

    def test_hook_auto_adopts_new_task_when_session_cwd_is_elsewhere(self) -> None:
        self.write_config(auto_adopt_after="2000-01-01T00:00:00+00:00")
        task = self.root / "direct-created"
        task.mkdir(parents=True)

        self.run_cli(
            "hook",
            input_data={
                "session_id": "session-1",
                "cwd": str(self.root.parent),
                "hook_event_name": "Stop",
            },
        )
        self.run_cli("maintenance")

        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "active")
        self.assertEqual(manifest["owner_session_ids"], [])
        self.assertEqual(manifest["adoption_source"], "automatic")

    def test_auto_adoption_preserves_legacy_unmanaged_tasks(self) -> None:
        legacy = self.root / "legacy"
        legacy.mkdir(parents=True)

        adopted = json.loads(self.run_cli("adopt").stdout)

        self.assertEqual(adopted["adopted"], [])
        self.assertFalse((legacy / ".codex-tmp-task.json").exists())

    def test_auto_adoption_ignores_symlink_tasks(self) -> None:
        self.write_config(auto_adopt_after="2000-01-01T00:00:00+00:00")
        outside = self.root.parent / "outside"
        outside.mkdir()
        self.root.mkdir()
        (self.root / "linked").symlink_to(outside, target_is_directory=True)

        adopted = json.loads(self.run_cli("adopt").stdout)

        self.assertEqual(adopted["adopted"], [])
        self.assertFalse((outside / ".codex-tmp-task.json").exists())

    def test_auto_adoption_excludes_manifest_from_root_git_repository(self) -> None:
        self.write_config(auto_adopt_after="2000-01-01T00:00:00+00:00")
        task = self.root / "cloned-root"
        subprocess.run(["git", "init", "-q", str(task)], check=True)

        self.run_cli("adopt")

        status = subprocess.run(
            ["git", "-C", str(task), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(status.stdout, "")
        exclude = (task / ".git" / "info" / "exclude").read_text(encoding="utf-8")
        self.assertIn(".codex-tmp-task.json", exclude.splitlines())

    def test_auto_adopted_task_is_not_quarantined_and_can_be_claimed(self) -> None:
        self.write_config(auto_adopt_after="2000-01-01T00:00:00+00:00")
        task = self.root / "orphan"
        task.mkdir(parents=True)
        self.run_cli("adopt")

        sweep = json.loads(self.run_cli("sweep").stdout)
        self.assertEqual(sweep["quarantined"], [])
        self.assertTrue(task.exists())

        self.run_cli(
            "hook",
            input_data={
                "session_id": "session-2",
                "cwd": str(task),
                "hook_event_name": "Stop",
            },
        )
        self.run_cli("maintenance")
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["owner_session_ids"], ["session-2"])

    def test_hook_only_queues_until_launchagent_dispatcher_runs(self) -> None:
        task = self.root / "producer-only"
        task.mkdir(parents=True)

        payload = json.loads(
            self.run_cli(
                "hook",
                input_data={
                    "session_id": "producer-session",
                    "cwd": str(task),
                    "hook_event_name": "Stop",
                    "secret_extra_field": "must-not-be-persisted",
                },
            ).stdout
        )

        self.assertTrue(payload["queued"])
        self.assertFalse((task / ".codex-tmp-task.json").exists())
        self.assertFalse((self.state / "background.log").exists())
        queued = next((self.state / "pending-hooks").glob("*.json"))
        stored = json.loads(queued.read_text(encoding="utf-8"))
        self.assertNotIn("secret_extra_field", stored)

        self.run_cli("maintenance")

        self.assertTrue((task / ".codex-tmp-task.json").exists())
        self.assertEqual(list((self.state / "pending-hooks").glob("*.json")), [])

    def test_inventory_reports_old_auto_adopted_active_tasks(self) -> None:
        self.write_config(
            auto_adopt_after="2000-01-01T00:00:00+00:00",
            orphan_active_hours=1,
        )
        task = self.root / "orphan"
        task.mkdir(parents=True)
        self.run_cli("adopt")
        manifest_path = task / ".codex-tmp-task.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["created_at"] = "2000-01-01T00:00:00+00:00"
        manifest["owner_session_ids"] = ["session-1"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        inventory = json.loads(self.run_cli("inventory").stdout)

        self.assertEqual(inventory["orphan_active"]["count"], 1)
        self.assertEqual(inventory["orphan_active"]["tasks"], ["orphan"])

    def test_maintenance_adopts_new_tasks(self) -> None:
        self.write_config(
            auto_adopt_after="2000-01-01T00:00:00+00:00",
            sweep_interval_hours=999,
        )
        task = self.root / "background-created"
        task.mkdir(parents=True)

        result = json.loads(self.run_cli("maintenance").stdout)

        self.assertEqual([item["status"] for item in result["adopted"]], ["active"])
        self.assertTrue((task / ".codex-tmp-task.json").exists())

    def test_sweep_dry_run_does_not_adopt_or_advance_throttle(self) -> None:
        self.write_config(auto_adopt_after="2000-01-01T00:00:00+00:00")
        task = self.root / "new-unmanaged"
        task.mkdir(parents=True)

        result = json.loads(self.run_cli("sweep", "--dry-run").stdout)

        self.assertEqual(result["adopted"], [])
        self.assertFalse((task / ".codex-tmp-task.json").exists())
        self.assertFalse((self.state / "last-sweep.json").exists())

    def test_sweep_dry_run_preserves_existing_throttle(self) -> None:
        self.state.mkdir(parents=True)
        last_sweep = self.state / "last-sweep.json"
        original = {"at": "2026-01-01T00:00:00+00:00", "dry_run": False}
        last_sweep.write_text(json.dumps(original), encoding="utf-8")

        self.run_cli("sweep", "--dry-run")

        self.assertEqual(json.loads(last_sweep.read_text(encoding="utf-8")), original)

    def test_sweep_dry_run_does_not_consume_pending_hooks(self) -> None:
        self.state.mkdir(parents=True)
        task = self.root / "pending-dry-run"
        task.mkdir(parents=True)
        lock_path = self.state / "lifecycle.lock"
        lock_path.touch()
        event = {
            "session_id": "pending-session",
            "cwd": str(task),
            "hook_event_name": "Stop",
        }
        with lock_path.open("r+", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.run_cli("hook", input_data=event)

        pending_before = list((self.state / "pending-hooks").glob("*.json"))
        self.run_cli("sweep", "--dry-run")

        self.assertEqual(len(pending_before), 1)
        self.assertEqual(list((self.state / "pending-hooks").glob("*.json")), pending_before)
        self.assertFalse((self.state / "sessions.json").exists())
        self.assertFalse((task / ".codex-tmp-task.json").exists())

    def test_concurrent_hooks_preserve_all_sessions(self) -> None:
        self.state.mkdir(parents=True)
        (self.state / "last-sweep.json").write_text(
            json.dumps({"at": "2999-01-01T00:00:00+00:00", "dry_run": False}),
            encoding="utf-8",
        )
        task = self.root / "concurrent"
        task.mkdir(parents=True)
        processes = []
        for index in range(8):
            event = {
                "session_id": f"session-{index}",
                "cwd": str(task),
                "hook_event_name": "Stop",
            }
            processes.append(
                subprocess.Popen(
                    [str(SCRIPT), "hook"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    env=self.env,
                )
            )
            assert processes[-1].stdin is not None
            processes[-1].stdin.write(json.dumps(event))
            processes[-1].stdin.close()

        for process in processes:
            process.wait(timeout=10)
            self.assertEqual(process.returncode, 0)
        self.run_cli("maintenance")
        sessions = json.loads((self.state / "sessions.json").read_text(encoding="utf-8"))
        self.assertEqual(set(sessions), {f"session-{index}" for index in range(8)})
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(manifest["owner_session_ids"]),
            {f"session-{index}" for index in range(8)},
        )

    def test_hook_queues_when_lifecycle_lock_is_busy_until_dispatcher_drains_it(self) -> None:
        self.state.mkdir(parents=True)
        task = self.root / "queued"
        task.mkdir(parents=True)
        lock_path = self.state / "lifecycle.lock"
        lock_path.touch()
        event = {
            "session_id": "queued-session",
            "cwd": str(task),
            "hook_event_name": "SessionEnd",
        }

        with lock_path.open("r+", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_cli("hook", input_data=event)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(len(list((self.state / "pending-hooks").glob("*.json"))), 1)
            self.assertFalse((self.state / "sessions.json").exists())

        self.run_cli("maintenance")
        sessions = json.loads((self.state / "sessions.json").read_text(encoding="utf-8"))
        self.assertIn("queued-session", sessions)
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertIn("queued-session", manifest["owner_session_ids"])
        self.assertEqual(list((self.state / "pending-hooks").glob("*.json")), [])

    def test_failed_hook_application_remains_in_durable_queue(self) -> None:
        module = load_script_module()
        event = {
            "session_id": "retry-session",
            "cwd": str(self.root / "retry-task"),
            "hook_event_name": "Stop",
        }
        with mock.patch.dict(os.environ, self.env, clear=False):
            paths = module.Paths()
            paths.prepare()
            config = module.load_config(paths)
            module.queue_hook_event(paths, event)
            with mock.patch.object(module, "apply_hook_event", side_effect=RuntimeError("timeout")):
                with self.assertRaises(RuntimeError):
                    module.drain_pending_hooks(paths, config)
            queued = list(self.state.glob("pending-hooks-draining-*/*.json"))
            self.assertEqual(len(queued), 1)
            module.drain_pending_hooks(paths, config)

        sessions = json.loads((self.state / "sessions.json").read_text(encoding="utf-8"))
        self.assertIn("retry-session", sessions)
        self.assertEqual(list(self.state.glob("pending-hooks-draining-*")), [])

    def test_dispatcher_restart_drains_previously_sealed_hook_queue(self) -> None:
        self.state.mkdir(parents=True)
        task = self.root / "sealed-restart"
        task.mkdir(parents=True)
        sealed = self.state / "pending-hooks-draining-crashed"
        sealed.mkdir()
        event = {
            "session_id": "sealed-session",
            "cwd": str(task),
            "hook_event_name": "Stop",
        }
        (sealed / "event.json").write_text(json.dumps(event), encoding="utf-8")

        self.run_cli("maintenance")

        sessions = json.loads((self.state / "sessions.json").read_text(encoding="utf-8"))
        manifest = json.loads((task / ".codex-tmp-task.json").read_text(encoding="utf-8"))
        self.assertIn("sealed-session", sessions)
        self.assertIn("sealed-session", manifest["owner_session_ids"])
        self.assertFalse(sealed.exists())

    def test_restore_rejects_quarantine_symlink(self) -> None:
        outside = self.root.parent / "outside-quarantine"
        outside.mkdir()
        self.quarantine.mkdir(parents=True)
        (self.quarantine / "linked-entry").symlink_to(outside, target_is_directory=True)

        result = self.run_cli("restore", "linked-entry", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(outside.exists())
        self.assertTrue((self.quarantine / "linked-entry").is_symlink())

    def test_active_and_keep_tasks_are_not_quarantined(self) -> None:
        self.run_cli("create", "active-task")
        self.run_cli("create", "kept-task")
        self.run_cli("keep", "kept-task")

        sweep = json.loads(self.run_cli("sweep").stdout)

        self.assertEqual(sweep["quarantined"], [])
        self.assertTrue((self.root / "active-task").exists())
        self.assertTrue((self.root / "kept-task").exists())

    def test_hidden_task_name_is_rejected(self) -> None:
        result = self.run_cli("create", ".hidden", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / ".hidden").exists())

    def test_launchd_wrapper_bootstraps_state_before_opening_log(self) -> None:
        home = self.root.parent / "clean-home"
        bin_dir = home / ".bin"
        bin_dir.mkdir(parents=True)
        fake = bin_dir / "codex-tmp"
        fake.write_text("#!/bin/sh\nprintf 'maintenance-ok\\n'\n", encoding="utf-8")
        fake.chmod(0o700)
        state = home / ".local" / "state" / "codex-tmp"

        result = subprocess.run(
            [str(LAUNCHD_WRAPPER)],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(home), "CODEX_TMP_STATE": str(state)},
            check=False,
        )
        plist = plistlib.loads(LAUNCHD_PLIST.read_bytes())

        self.assertEqual(result.returncode, 0)
        self.assertEqual((state / "launchd.log").read_text(encoding="utf-8"), "maintenance-ok\n")
        self.assertEqual(plist["ProgramArguments"], ["/Users/qingpei/.bin/codex-tmp-launchd"])
        self.assertNotIn("StandardOutPath", plist)
        self.assertNotIn("StandardErrorPath", plist)


if __name__ == "__main__":
    unittest.main()
