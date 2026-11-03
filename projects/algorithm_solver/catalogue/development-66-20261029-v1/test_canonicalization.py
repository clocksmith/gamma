#!/usr/bin/env python3
"""Focused unit and receipt-contract tests for measure_canonicalization.py (Task 1.2)."""

from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_canonicalization as mc  # noqa: E402


class TestCanonicalization(unittest.TestCase):
    def test_python_nonlocal_and_nested_capture_avoidance(self):
        src = (
            '"""Docstring stripped in formatted and compact_palette."""\n'
            "def solve(root: list[int]) -> int:\n"
            "    total = 0\n"
            "    def helper(node: int) -> int:\n"
            "        nonlocal total\n"
            "        step = node + 1\n"
            "        total += step\n"
            "        return total\n"
            "    return helper(len(root))\n"
        )
        out = mc.canonicalize_python(src)
        self.assertTrue(out["formatted"]["ast_verified"])
        self.assertTrue(out["compact_palette"]["ast_verified"])
        self.assertTrue(out["compact_palette"]["binding_fingerprint_verified"])
        # Execute all three variants and verify identical output
        for variant in ("raw", "formatted", "compact_palette"):
            ns: dict = {}
            exec(out[variant]["source"], ns)
            self.assertEqual(ns["solve"]([10, 20, 30]), 4)

    def test_python_comprehension_and_global_preservation(self):
        src = (
            "MOD = 1000000007\n"
            "def solve(values):\n"
            "    filtered = [val % MOD for val in values if val > 0]\n"
            "    return sum(filtered) % MOD\n"
            "class Solution:\n"
            "    def numPerms(self, values):\n"
            "        return solve(values)\n"
        )
        out = mc.canonicalize_python(src)
        cmp_src = out["compact_palette"]["source"]
        # Top-level exports MOD, solve, Solution and method numPerms must remain intact
        self.assertIn("MOD=1000000007", cmp_src)
        self.assertIn("def solve(", cmp_src)
        self.assertIn("class Solution:", cmp_src)
        self.assertIn("def numPerms(", cmp_src)
        for variant in ("raw", "formatted", "compact_palette"):
            ns: dict = {}
            exec(out[variant]["source"], ns)
            self.assertEqual(ns["solve"]([-3, 4, 5]), 9)
            self.assertEqual(ns["Solution"]().numPerms([-3, 4, 5]), 9)

    def test_receipt_results_json_invariants(self):
        receipt_path = HERE / "runs" / "canonicalization-9-20261102" / "results.json"
        self.assertTrue(receipt_path.exists(), "runs/canonicalization-9-20261102/results.json must exist")
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "gamma.development-canonicalization-projection.v1")
        self.assertEqual(data["qualification"], "unknown")
        self.assertEqual(data["sample"]["revised_ids"], [156, 280, 286, 340, 903])
        self.assertEqual(data["sample"]["control_ids"], [250, 270, 737, 1214])
        self.assertEqual(data["sample"]["total_module_variants_tested"], 54)
        self.assertTrue(data["sample"]["all_variants_passed_execution_and_abi"])
        self.assertTrue(data["sample"]["authored_files_untouched"])
        self.assertEqual(len(data["problems"]), 9)
        for prob in data["problems"]:
            for lang in ("python", "javascript"):
                lrow = prob["languages"][lang]
                for variant in ("raw", "formatted", "compact_palette"):
                    vrow = lrow[variant]
                    self.assertTrue(vrow["ast_verified"])
                    self.assertTrue(vrow["binding_fingerprint_verified"])
                    self.assertEqual(vrow["pure_cases_passed"], vrow["pure_cases_total"])
                    self.assertGreater(vrow["pure_cases_total"], 0)
                    self.assertEqual(vrow["abi_checks_passed"], vrow["abi_checks_total"])
                    self.assertGreater(vrow["abi_checks_total"], 0)
                self.assertLess(
                    lrow["compact_palette"]["utf8_bytes"],
                    lrow["formatted"]["utf8_bytes"],
                )
                self.assertLess(
                    lrow["compact_palette"]["utf8_bytes"],
                    lrow["raw"]["utf8_bytes"],
                )

    def test_qualification_eligibility_dry_run_invariants(self):
        elig_path = HERE / "QUALIFICATION-ELIGIBILITY-v1.json"
        self.assertTrue(elig_path.exists(), "QUALIFICATION-ELIGIBILITY-v1.json must exist")
        data = json.loads(elig_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "gamma.development-66-qualification-eligibility-plan.v1")
        self.assertEqual(data["qualification"], "unknown")
        self.assertEqual(data["status_changes_made"], 0)
        self.assertEqual(data["admissions_changed"], 0)
        self.assertEqual(data["candidate_executions_performed"], 0)
        agg = data["development_66_summary"]
        self.assertEqual(agg["total_problems"], 66)
        self.assertEqual(agg["total_candidate_sources"], 132)
        self.assertEqual(agg["gate_authorized_problems"], 66)
        self.assertEqual(agg["nonreserved_boundary_problems"], 66)
        self.assertEqual(agg["already_qualified_in_status_v4"], 0)
        self.assertEqual(agg["inventory_lcd_test_sets_available_count"], 63)
        self.assertEqual(agg["inventory_lcd_missing_ids"], [280, 286, 911])
        self.assertEqual(agg["public_graphql_free_ids"], [903, 911])
        self.assertEqual(sum(t["count"] for t in agg["tiers"].values()), 66)
        self.assertEqual(sum(t["source_pairs"] for t in agg["tiers"].values()), 132)
        self.assertEqual(len(data["problems"]), 66)


if __name__ == "__main__":
    unittest.main()
