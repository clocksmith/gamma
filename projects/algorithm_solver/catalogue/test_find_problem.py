#!/usr/bin/env python3
"""Unit tests for the canonical Gamma problem index and lookup CLI."""
from __future__ import annotations

import unittest

from find_problem import (
    JSONL_PATH,
    TSV_PATH,
    build_records,
    compute_stats,
    load_records,
    render_jsonl,
    render_tsv,
    search_records,
)


class FindProblemIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = load_records()
        cls.by_key = {str(r["key"]): r for r in cls.records}
        cls.stats = compute_stats(cls.records)

    def test_index_files_exist_and_are_fresh(self) -> None:
        self.assertTrue(TSV_PATH.exists(), "PROBLEM_INDEX.tsv must exist")
        self.assertTrue(JSONL_PATH.exists(), "PROBLEM_INDEX.jsonl must exist")
        built = build_records()
        self.assertEqual(TSV_PATH.read_text(encoding="utf-8"), render_tsv(built))
        self.assertEqual(JSONL_PATH.read_text(encoding="utf-8"), render_jsonl(built))

    def test_universe_counts_and_authority_boundaries(self) -> None:
        self.assertEqual(self.stats["total_records"], 5144)
        lc = self.stats["leetcode"]
        self.assertEqual(lc["total"], 4096)
        self.assertEqual(lc["with_both_py_and_js"], 3574)
        self.assertEqual(lc["by_status"]["qualified"], 518)
        self.assertEqual(lc["by_status"]["development-executed"], 66)
        self.assertEqual(lc["by_status"]["missing-reserved"], 80)
        self.assertEqual(lc["by_status"]["missing-non-dual-or-unmapped"], 421)

        h2h = self.stats["hack2hire"]
        self.assertEqual(h2h["total"], 1048)
        self.assertEqual(h2h["coding_variants"], 805)
        self.assertEqual(h2h["coding_with_both_py_and_js"], 805)
        self.assertEqual(h2h["coding_with_study_record"], 805)

    def test_canonical_duplicate_resolution_and_study_version(self) -> None:
        # 286 must resolve to authored cohort, never quarantined, and pick latest v7 study record.
        r286 = self.by_key["leetcode:286"]
        self.assertEqual(r286["title"], "Walls and Gates")
        self.assertEqual(r286["method"], "wallsAndGates")
        self.assertEqual(r286["status"], "development-executed")
        self.assertEqual(
            r286["py_path"],
            "projects/algorithm_solver/catalogue/authored/requested-156-1940-31-20261028-v1/python/286.py",
        )
        self.assertEqual(
            r286["js_path"],
            "projects/algorithm_solver/catalogue/authored/requested-156-1940-31-20261028-v1/javascript/286.js",
        )
        self.assertTrue(
            str(r286["study_path"]).endswith(
                "approach--approach_leetcode_286_requested-156-1940-31-20261028-v1_286_v1--v7.json"
            )
        )

        # 875 is qualified in leetcode-eight-v1
        r875 = self.by_key["leetcode:875"]
        self.assertEqual(r875["status"], "qualified")
        self.assertEqual(r875["method"], "minEatingSpeed")
        self.assertEqual(
            r875["py_path"],
            "projects/algorithm_solver/catalogue/authored/leetcode-eight-v1/python/875.py",
        )

        # Repair / revision batches take precedence over earlier base batches
        r695 = self.by_key["leetcode:695"]
        self.assertIn("repair-python695-iterative-20261028-v1", str(r695["py_path"]))

        r126 = self.by_key["leetcode:126"]
        self.assertIn("continuation-q126-output-sensitive-20261028-v1", str(r126["py_path"]))

        r140 = self.by_key["leetcode:140"]
        self.assertIn("continuation-q140-output-sensitive-20261028-v1", str(r140["py_path"]))

        r17 = self.by_key["leetcode:17"]
        self.assertIn("continuation-p-js-official-20261028-v1", str(r17["js_path"]))

        r1743 = self.by_key["leetcode:1743"]
        self.assertIn("packed-path1743-v1", str(r1743["js_path"]))

    def test_search_queries_and_filters(self) -> None:
        m_id = search_records(self.records, ["286"])
        self.assertEqual(m_id[0]["key"], "leetcode:286")

        m_method = search_records(self.records, ["wallsAndGates"])
        self.assertEqual(m_method[0]["key"], "leetcode:286")

        m_title = search_records(self.records, ["Koko Eating Bananas"])
        self.assertEqual(m_title[0]["key"], "leetcode:875")

        m_sd = search_records(
            self.records, [], source="hack2hire", category="system-design", company="Meta"
        )
        self.assertGreater(len(m_sd), 10)
        self.assertTrue(all(r["category"] == "system-design" for r in m_sd))


if __name__ == "__main__":
    unittest.main()
