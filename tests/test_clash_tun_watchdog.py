import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "clash-tun-watchdog"
LOADER = importlib.machinery.SourceFileLoader("clash_tun_watchdog", str(SCRIPT))
SPEC = importlib.util.spec_from_loader("clash_tun_watchdog", LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ProbeClassificationTests(unittest.TestCase):
    def test_public_outage_triggers_recovery(self):
        probe = MODULE.ProbeSummary(
            public_results=(
                MODULE.ProbeResult("apple", 28, 0, "timeout"),
                MODULE.ProbeResult("cloudflare", 7, 0, "connect failed"),
            ),
            gitlab=MODULE.ProbeResult("gitlab", 0, 200, ""),
        )
        self.assertEqual("public_unreachable", probe.trigger_reason())

    def test_gitlab_certificate_failure_triggers_recovery(self):
        probe = MODULE.ProbeSummary(
            public_results=(MODULE.ProbeResult("apple", 0, 200, ""),),
            gitlab=MODULE.ProbeResult("gitlab", 60, 0, "certificate error"),
        )
        self.assertEqual("gitlab_tls", probe.trigger_reason())

    def test_gitlab_timeout_alone_does_not_disable_tun(self):
        probe = MODULE.ProbeSummary(
            public_results=(MODULE.ProbeResult("apple", 0, 200, ""),),
            gitlab=MODULE.ProbeResult("gitlab", 28, 0, "timeout"),
        )
        self.assertIsNone(probe.trigger_reason())


class StateMachineTests(unittest.TestCase):
    def test_requires_three_consecutive_failures(self):
        state = MODULE.default_state()
        for expected in (1, 2):
            action, state = MODULE.next_action(
                tun_enabled=True,
                trigger_reason="public_unreachable",
                direct_ready=False,
                state=state,
                now=100 + expected,
            )
            self.assertEqual(MODULE.Action.NONE, action)
            self.assertEqual(expected, state["consecutive_failures"])

        action, state = MODULE.next_action(
            tun_enabled=True,
            trigger_reason="public_unreachable",
            direct_ready=False,
            state=state,
            now=103,
        )
        self.assertEqual(MODULE.Action.FAIL_OPEN, action)

    def test_does_not_manage_tun_disabled_by_user(self):
        action, state = MODULE.next_action(
            tun_enabled=False,
            trigger_reason=None,
            direct_ready=True,
            state=MODULE.default_state(),
            now=100,
        )
        self.assertEqual(MODULE.Action.NONE, action)
        self.assertFalse(state["managed_fail_open"])

    def test_managed_fail_open_retries_on_next_healthy_tick(self):
        state = MODULE.default_state()
        state.update(
            {
                "managed_fail_open": True,
                "failure_reason": "public_unreachable",
                "next_retry_at": 100,
            }
        )
        action, _ = MODULE.next_action(
            tun_enabled=False,
            trigger_reason=None,
            direct_ready=True,
            state=state,
            now=100,
        )
        self.assertEqual(MODULE.Action.TRY_ENABLE, action)

    def test_managed_fail_open_waits_for_direct_connectivity(self):
        state = MODULE.default_state()
        state.update(
            {
                "managed_fail_open": True,
                "failure_reason": "gitlab_tls",
                "next_retry_at": 100,
            }
        )
        action, _ = MODULE.next_action(
            tun_enabled=False,
            trigger_reason="gitlab_tls",
            direct_ready=False,
            state=state,
            now=100,
        )
        self.assertEqual(MODULE.Action.NONE, action)


class FakeMihomoAPI:
    def __init__(self, enabled):
        self.enabled = enabled
        self.set_calls = []

    def configs(self):
        return {
            "mode": "rule",
            "tun": {
                "enable": self.enabled,
                "device": "utun1024",
                "stack": "gVisor",
                "auto-route": True,
                "auto-detect-interface": True,
            },
        }

    def version(self):
        return {"version": "test"}

    def set_tun_enabled(self, current_tun, enabled):
        self.enabled = enabled
        self.set_calls.append(enabled)


def healthy_probe():
    return MODULE.ProbeSummary(
        public_results=(MODULE.ProbeResult("apple", 0, 200, ""),),
        gitlab=MODULE.ProbeResult("gitlab", 0, 200, ""),
    )


def failed_probe():
    return MODULE.ProbeSummary(
        public_results=(
            MODULE.ProbeResult("apple", 28, 0, "timeout"),
            MODULE.ProbeResult("cloudflare", 7, 0, "connect failed"),
        ),
        gitlab=MODULE.ProbeResult("gitlab", 28, 0, "timeout"),
    )


class RunIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "watchdog"
        replacements = {
            "ROOT": self.root,
            "STATE_PATH": self.root / "state.json",
            "LOCK_PATH": self.root / "run.lock",
            "EVENTS_PATH": self.root / "events",
            "LOG_PATH": self.root / "watchdog.jsonl",
            "BOOT_PATH": self.root / "boot-id",
        }
        self.patchers = [
            mock.patch.object(MODULE, name, value) for name, value in replacements.items()
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temporary.cleanup()

    def run_with(self, api, probes):
        evidence = self.root / "events" / "test-event"
        with (
            mock.patch.object(MODULE, "MihomoAPI", return_value=api),
            mock.patch.object(
                MODULE, "network_fingerprint", return_value=("fingerprint", {})
            ),
            mock.patch.object(MODULE, "probe_connectivity", side_effect=probes),
            mock.patch.object(MODULE, "capture_snapshot", return_value=evidence),
            mock.patch.object(MODULE.time, "sleep"),
        ):
            return MODULE.run_watchdog(force_probe=True, dry_run=False)

    def test_new_boot_removes_previous_temporary_evidence(self):
        self.root.mkdir(parents=True)
        (self.root / "boot-id").write_text("previous boot\n")
        stale = self.root / "events" / "stale" / "evidence.txt"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale")
        with mock.patch.object(MODULE, "run_command", return_value="current boot\n"):
            MODULE.ensure_root()
        self.assertFalse(stale.exists())
        self.assertEqual("current boot", (self.root / "boot-id").read_text().strip())

    def test_three_failures_enter_managed_fail_open(self):
        api = FakeMihomoAPI(enabled=True)
        exit_code = self.run_with(
            api, [failed_probe(), failed_probe(), failed_probe(), healthy_probe()]
        )
        state = json.loads((self.root / "state.json").read_text())
        self.assertEqual(0, exit_code)
        self.assertEqual([False], api.set_calls)
        self.assertFalse(api.enabled)
        self.assertTrue(state["managed_fail_open"])
        self.assertEqual("public_unreachable", state["failure_reason"])

    def test_failed_enable_attempt_returns_to_fail_open(self):
        MODULE.ensure_root()
        state = MODULE.default_state()
        state.update(
            {
                "managed_fail_open": True,
                "failure_reason": "public_unreachable",
                "next_retry_at": 0,
            }
        )
        MODULE.write_state(state)
        api = FakeMihomoAPI(enabled=False)
        exit_code = self.run_with(api, [healthy_probe(), failed_probe()])
        updated = json.loads((self.root / "state.json").read_text())
        self.assertEqual(0, exit_code)
        self.assertEqual([True, False], api.set_calls)
        self.assertFalse(api.enabled)
        self.assertTrue(updated["managed_fail_open"])
        self.assertEqual(1, updated["retry_count"])


if __name__ == "__main__":
    unittest.main()
