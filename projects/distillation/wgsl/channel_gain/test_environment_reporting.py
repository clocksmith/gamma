"""CPU-only checks for descriptive environment provenance, not model results."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .environment_reporting import environment_markdown, load_environment
from .report_confirmation import build_report


class EnvironmentTests(unittest.TestCase):
    def fixture(self):
        evidence = {"provenance": {"files": {"runtimeLock": {"sha256": "a" * 64}, "stageLock": {"sha256": "b" * 64}}}}
        event = {"schema": "gamma.reconfiguration-environment-event/v1", "status": "observed",
                 "eventId": "provider-retired", "observedAt": "2026-11-13T12:47:24Z",
                 "previousLineSha256": None, "targetInputFileSha256": {"runtimeLock": "a" * 64, "stageLock": "b" * 64},
                 "host": "jupiter", "device": "CPU_FIXTURE_ONLY", "kind": "provider_retired",
                 "description": "CPU fixture only", "isolationQualification": "unknown",
                 "sources": [{"path": "fixture.json", "sha256": "c" * 64}]}
        return evidence, event

    def load(self, events, evidence):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "environment.jsonl"
            path.write_bytes(b"".join(json.dumps(e).encode() + b"\n" for e in events))
            return load_environment(path, evidence)

    def test_observed_overlap_and_append_only_chain(self):
        evidence, event = self.fixture()
        overlap = {**event, "eventId": "parallel-27b", "observedAt": "2026-11-13T13:00:00Z",
                   "previousLineSha256": hashlib.sha256(json.dumps(event).encode() + b"\n").hexdigest(),
                   "kind": "overlap", "isolationQualification": "contended",
                   "interval": {"startedAt": "2026-11-13T12:59:00Z", "endedAt": None}}
        result = self.load([event, overlap], evidence)
        self.assertEqual(result["isolationQualification"], "contended")
        self.assertEqual(result["eventCount"], 2)
        self.assertIn("cannot apportion", "\n".join(environment_markdown(result)))
        mutated = {**event, "description": "rewritten after observation"}
        with self.assertRaisesRegex(ValueError, "hash chain"):
            self.load([mutated, overlap], evidence)

    def test_wrong_run_template_and_unearned_isolation_rejected(self):
        evidence, event = self.fixture()
        wrong = copy.deepcopy(event)
        wrong["targetInputFileSha256"]["stageLock"] = "d" * 64
        for row in (wrong, {**event, "status": "template-not-observed"},
                    {**event, "isolationQualification": "isolated"}):
            with self.assertRaises(ValueError):
                self.load([row], evidence)
        self.assertEqual(self.load([event], evidence)["isolationQualification"], "unknown")

    def test_environment_cannot_change_frozen_result_or_quality(self):
        evidence = {"arms": {}, "taskIds": [], "setup": {"selectionTargetMet": False},
                    "costs": {"rawCost": 123}, "memory": {}, "provenance": {}, "limitations": []}
        frozen_result = {"cacheArms": {}, "decision": "not_confirmed"}
        protocol = {"selection": {"primaryCacheArm": "mlp_base_cache"}}
        with patch("projects.distillation.wgsl.channel_gain.report_confirmation.evaluate_confirmation", return_value=frozen_result) as evaluator:
            original = build_report(protocol, evidence)
            with_environment = build_report(protocol, evidence, {"provided": True, "isolationQualification": "contended"})
        for key in original:
            if key != "environment":
                self.assertEqual(original[key], with_environment[key])
        self.assertEqual(evaluator.call_args.args, (protocol, evidence))
        self.assertEqual(original["environment"]["isolationQualification"], "unknown")


if __name__ == "__main__":
    unittest.main()
