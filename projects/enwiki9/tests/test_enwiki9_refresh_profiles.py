"""Refresh selection, failure propagation, and explicit inventory reuse."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import enwiki9_normalize_receipts as normalize
import enwiki9_status_receipt as status


class RefreshProfilesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects/enwiki9"
        self.root.mkdir(parents=True)
        self.inventory = self.root / "candidate_inventory.json"
        self.inventory.write_text(json.dumps({
            "project_root": "projects/enwiki9",
            "generated_at": "2020-01-01T00:00:00+00:00",
            "summary": {"program_directories": 7},
        }))
        for module in (normalize, status):
            self.enterContext(patch.object(module, "ROOT", self.root))
            self.enterContext(patch.object(module, "REPO_ROOT", self.root.parent.parent))

    def runner(self, failure=None):
        self.calls = []

        def run(command):
            self.calls.append(command)
            return {"command": command, "returncode": int(failure in command) if failure else 0,
                    "stdout": "", "stderr": ""}

        self.enterContext(patch.object(normalize, "run_command", side_effect=run))

    def test_routine_runs_only_dependencies_and_discloses_omitted_views(self):
        self.runner()
        receipt = normalize.normalize()
        self.assertTrue(receipt["ok"])
        generators = normalize.selected_commands("routine")
        self.assertEqual({Path(c[1]).name for c in generators}, normalize.ROUTINE_TOOLS)
        self.assertTrue(receipt["not_refreshed"])
        self.assertIn("may be stale", receipt["historical_view_notice"])
        self.assertFalse(any("candidate_audit.py" == Path(c[1]).name for c in self.calls))
        self.assertFalse(any("backfill_run_ledger.py" == Path(c[1]).name for c in self.calls))
        self.assertTrue(any(c[1].endswith("enwiki9_doc_lint.py") for c in self.calls))

    def test_full_audits_once_and_reuses_one_digest_in_status_and_check(self):
        self.runner()
        receipt = normalize.normalize("full")
        self.assertTrue(receipt["ok"])
        self.assertEqual([], receipt["not_refreshed"])
        self.assertEqual(1, sum(c[1].endswith("/candidate_audit.py") for c in self.calls))
        statuses = [c for c in self.calls if c[1].endswith("/enwiki9_status_receipt.py")]
        self.assertEqual(2, len(statuses))
        digest = hashlib.sha256(self.inventory.read_bytes()).hexdigest()
        for command in statuses:
            self.assertEqual(digest, command[command.index("--candidate-audit-sha256") + 1])

    def test_failed_audit_stops_before_reading_previous_snapshot(self):
        self.runner("projects/enwiki9/tools/candidate_audit.py")
        receipt = normalize.normalize("full")
        self.assertFalse(receipt["ok"])
        self.assertEqual(1, len(self.calls))
        self.assertTrue(receipt["checks_requested"])
        self.assertFalse(receipt["checks_run"])

    def test_failed_generator_stops_and_cli_returns_failure(self):
        self.runner("projects/enwiki9/tools/hutter_run_ledger.py")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = normalize.main(["--json"])
        self.assertEqual(1, code)
        self.assertFalse(json.loads(output.getvalue())["ok"])
        self.assertEqual(2, len(self.calls))

    def test_missing_snapshot_cannot_report_success_or_start_an_implicit_audit(self):
        self.inventory.unlink()
        self.runner()
        receipt = normalize.normalize()
        self.assertFalse(receipt["ok"])
        self.assertIn("Inventory unavailable", receipt["error"])
        self.assertEqual([], self.calls)

    def test_skip_check_retains_refresh_notice(self):
        self.runner()
        receipt = normalize.normalize(skip_check=True)
        self.assertTrue(receipt["ok"])
        self.assertFalse(receipt["checks_run"])
        self.assertEqual(len(normalize.ROUTINE_TOOLS), len(self.calls))
        self.assertIn("may be stale", receipt["historical_view_notice"])

    def test_snapshot_is_hash_verified_but_never_claimed_fresh(self):
        digest = hashlib.sha256(self.inventory.read_bytes()).hexdigest()
        with patch.object(status.subprocess, "run", side_effect=AssertionError("duplicate scan")):
            state = status.candidate_audit_summary_state(self.inventory, digest)
        self.assertEqual(0, state["returncode"])
        self.assertEqual(7, state["summary"]["program_directories"])
        self.assertEqual("not_revalidated", state["freshness"])
        self.assertIn("not live occupancy", state["notice"])

    def test_replaced_snapshot_is_rejected_without_silent_rescan(self):
        digest = hashlib.sha256(self.inventory.read_bytes()).hexdigest()
        self.inventory.write_text(self.inventory.read_text() + "\n")
        with patch.object(status.subprocess, "run", side_effect=AssertionError("silent rescan")):
            state = status.candidate_audit_summary_state(self.inventory, digest)
        self.assertEqual(1, state["returncode"])
        self.assertIn("digest mismatch", state["error"])
        self.assertNotIn("summary", state)

    def test_malformed_wrong_project_and_naive_timestamp_fail_closed(self):
        cases = ["[]", "{}", "not json", json.dumps({
            "project_root": "other", "summary": {}, "generated_at": "2020-01-01T00:00:00Z",
        }), json.dumps({
            "project_root": "projects/enwiki9", "summary": {}, "generated_at": "2020-01-01",
        })]
        for raw in cases:
            with self.subTest(raw=raw):
                self.inventory.write_text(raw)
                state = status.candidate_audit_summary_state(
                    self.inventory, hashlib.sha256(self.inventory.read_bytes()).hexdigest())
                self.assertEqual(1, state["returncode"])
                self.assertNotIn("summary", state)

    def test_failed_status_validation_does_not_replace_existing_output(self):
        out = self.root / "status.json"
        out.write_text("previous")
        with patch.object(status, "receipt", return_value={
            "candidate_audit": {"returncode": 1, "error": "replaced inventory"},
        }), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1, status.main(["--json-out", str(out)]))
        self.assertEqual("previous", out.read_text())

    def test_missing_digest_and_missing_snapshot_fail_closed(self):
        self.assertEqual(1, status.candidate_audit_summary_state(self.inventory)["returncode"])
        self.assertEqual(1, status.candidate_audit_summary_state(None, "a" * 64)["returncode"])

    def test_fresh_audit_invalid_json_cannot_return_success(self):
        for raw in ("not JSON", "[]", "{}"):
            with self.subTest(raw=raw), patch.object(status.subprocess, "run", return_value=
                    SimpleNamespace(returncode=0, stdout=raw, stderr="")):
                self.assertEqual(1, status.candidate_audit_summary_state()["returncode"])


if __name__ == "__main__":
    unittest.main()
