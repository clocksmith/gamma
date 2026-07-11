from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects" / "enwiki9" / "tools" / "cmix21_gate_decider.py"
SPEC = importlib.util.spec_from_file_location("cmix21_gate_decider", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GateDeciderTests(unittest.TestCase):
    def test_terminal_guard_failure_without_driver_result_is_recordable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = "cmix21_test_ppmd21120k_v1"
            results = root / "results"
            programs = root / "programs"
            guard_path = results / candidate / "ppmd21120k_250000_determinism_rss_guard.json"
            guard_path.parent.mkdir(parents=True)
            guard_path.write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "returncode": 1,
                        "rss_guard_exceeded": False,
                        "limit_kib": 10_485_760,
                        "max_sampled_single_rss_kib": 1_248,
                        "max_sampled_tree_rss_kib": 1_248,
                        "sample_count": 2,
                    }
                )
            )

            with (
                mock.patch.object(MODULE, "REPO_ROOT", root),
                mock.patch.object(MODULE, "RESULTS", results),
                mock.patch.object(MODULE, "PROGRAMS", programs),
            ):
                decision = MODULE.decide(candidate, 250_000, guard_path, 128)

            self.assertEqual(decision["verdict"], "guard_returncode_fail")
            self.assertEqual(decision["next_action"], "record_guard_failure")
            self.assertIn("--guard-only", decision["record_failure_command"])
            self.assertNotIn("--result", decision["record_failure_command"])
            self.assertIn("apply_terminal_command", decision)

    def test_retry_command_preserves_terminal_guard_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = "cmix21_test_ppmd21120k_v1"
            results = root / "results"
            guard_path = results / candidate / "ppmd21120k_250000_determinism_rss_guard.json"
            guard_path.parent.mkdir(parents=True)
            guard_path.write_text(json.dumps({"status": "complete", "returncode": 1}))

            with (
                mock.patch.object(MODULE, "REPO_ROOT", root),
                mock.patch.object(MODULE, "RESULTS", results),
            ):
                command = MODULE.command_for_gate(candidate, 250_000)

            guard_index = command.index("--guard-json") + 1
            label_index = command.index("--label") + 1
            self.assertTrue(command[guard_index].endswith("_attempt2_rss_guard.json"))
            self.assertTrue(command[label_index].endswith("_attempt2"))

    def test_decider_selects_latest_retry_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = "cmix21_test_ppmd21120k_v1"
            results = root / "results"
            programs = root / "programs"
            result_dir = results / candidate
            result_dir.mkdir(parents=True)
            base = result_dir / "ppmd21120k_250000_determinism_rss_guard.json"
            retry = result_dir / "ppmd21120k_250000_determinism_attempt2_rss_guard.json"
            base.write_text(json.dumps({"status": "complete", "returncode": 1}))
            retry.write_text(json.dumps({"status": "running", "returncode": None}))

            with (
                mock.patch.object(MODULE, "REPO_ROOT", root),
                mock.patch.object(MODULE, "RESULTS", results),
                mock.patch.object(MODULE, "PROGRAMS", programs),
            ):
                decision = MODULE.decide(candidate, 250_000, base, 128)

            self.assertEqual(decision["verdict"], "running")
            self.assertTrue(decision["rss_guard_json"].endswith("_attempt2_rss_guard.json"))


if __name__ == "__main__":
    unittest.main()
