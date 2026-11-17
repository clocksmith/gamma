"""Unit tests for FastWeight v3 unseen task suite (`tasks_v3.py`)."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

THIS_DIR = Path(__file__).resolve().parent
V1_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v1"
V2_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v2"
for d in (THIS_DIR, V1_DIR, V2_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from tasks import build_dev_family_tasks, build_holdout_family_tasks
from tasks_v2 import V2_DOMAINS
from tasks_v3 import V3_DOMAINS, build_v3_unseen_tasks


class TestFastWeightV3Tasks(unittest.TestCase):
    def test_v3_domains_strictly_disjoint_from_v1_and_v2(self) -> None:
        v1_doms = {t["domain"] for t in build_dev_family_tasks(1, 1) + build_holdout_family_tasks(2, 1)}
        self.assertEqual(len(set(V3_DOMAINS) & v1_doms), 0)
        self.assertEqual(len(set(V3_DOMAINS) & set(V2_DOMAINS)), 0)
        tasks = build_v3_unseen_tasks(seed=12345, count_per_domain=4)
        self.assertEqual(len(tasks), 24)
        for t in tasks:
            self.assertTrue(t["prompt"].startswith(t["context_text"]))


if __name__ == "__main__":
    unittest.main()
