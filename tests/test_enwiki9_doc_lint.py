from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects" / "enwiki9" / "tools" / "enwiki9_doc_lint.py"
SPEC = importlib.util.spec_from_file_location("enwiki9_doc_lint", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DocLintTests(unittest.TestCase):
    def test_null_active_gate_and_gate_decision_are_supported(self) -> None:
        certificate = {
            "proof_status": {
                "has_10_95_constructive_upper_bound": False,
                "has_full_corpus_constructive_result": False,
            },
            "top_status": [
                {
                    "label": "active candidate",
                    "program_id": "candidate_v1",
                    "status": "not started",
                }
            ],
        }
        status = {
            "has_10_95_constructive_upper_bound": False,
            "has_full_corpus_constructive_result": False,
            "active_gate": None,
            "gate_decision": None,
            "operator_summary": {
                "candidate": "candidate_v1",
                "scope_bytes": None,
                "gate_verdict": None,
                "gate_next_action": None,
                "heavy_lock_held": False,
                "active_scorer_observed": False,
                "active_cmix_mode": None,
                "driver_result_present": False,
                "rss_guard_status": None,
                "rss_samples": None,
                "binary_10gib_guard_kib": 10_485_760,
                "decimal_10gb_guard_kib": 9_765_625,
                "single_rss_margin_kib": None,
                "max_sampled_single_decimal_10gb_margin_kib": None,
                "latest_sample_single_decimal_10gb_margin_kib": None,
                "safe_to_launch_heavy_gate": True,
                "terminal_verdict_present": False,
                "command_source": "none",
                "has_full_corpus_constructive_result": False,
                "has_10_95_constructive_upper_bound": False,
                "claim_rule": "No prefix row proves 10.95%.",
            },
        }
        findings: list[object] = []

        with mock.patch.object(MODULE, "load_json", side_effect=[certificate, status]):
            MODULE.check_certificate_and_status(findings)

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
