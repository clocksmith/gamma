"""Unit and non-copy verification tests for Track B1 v4 (`query_swiglu_fastweight_v4`)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

THIS_DIR = Path(__file__).resolve().parent
V1_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v1"
V2_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v2"
V3_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v3"
for d in (THIS_DIR, V1_DIR, V2_DIR, V3_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from regex_baseline_v4 import lookup_support_answer  # noqa: E402
from tasks import build_dev_family_tasks, build_holdout_family_tasks  # noqa: E402
from tasks_v2 import V2_DOMAINS  # noqa: E402
from tasks_v3 import V3_DOMAINS  # noqa: E402
from tasks_v4 import V4_DOMAINS, build_v4_unseen_tasks  # noqa: E402


class TestFastWeightV4TasksAndProtocol(unittest.TestCase):
    def test_v4_domains_strictly_disjoint_from_v1_v2_v3(self) -> None:
        v1_doms = {t["domain"] for t in build_dev_family_tasks(1, 1) + build_holdout_family_tasks(2, 1)}
        self.assertEqual(len(set(V4_DOMAINS) & v1_doms), 0)
        self.assertEqual(len(set(V4_DOMAINS) & set(V2_DOMAINS)), 0)
        self.assertEqual(len(set(V4_DOMAINS) & set(V3_DOMAINS)), 0)

    def test_seed_guard_enforced(self) -> None:
        with self.assertRaises(ValueError):
            build_v4_unseen_tasks(seed=999999)

    def test_confirmation_suite_shape_and_non_copy_regex_ceiling(self) -> None:
        tasks = build_v4_unseen_tasks(seed=1040001, queries_per_specialty=8)
        self.assertEqual(len(tasks), 96)
        specialties = {t["specialty_id"] for t in tasks}
        self.assertEqual(len(specialties), 12)

        regex_hits = 0
        for t in tasks:
            self.assertTrue(t["prompt"].startswith(t["support_text"]))
            self.assertTrue(t["bare_prompt"].startswith(t["header_text"]))
            self.assertNotEqual(t["specialty_id"], t["wrong_specialty_id"])
            # Query phrase must not appear verbatim in support_text
            self.assertNotIn(t["query_line"], t["support_text"])
            rx = lookup_support_answer(t["support_text"], t["query_line"])
            if str(rx["answer"]).strip().lower() == t["expected"].strip().lower():
                regex_hits += 1

        regex_acc = regex_hits / float(len(tasks))
        self.assertLessEqual(
            regex_acc,
            0.50,
            f"Standalone lexical/regex lookup exceeded 50% ceiling ({regex_hits}/96 = {regex_acc:.3f})",
        )

    def test_protocol_lock_sha256_integrity(self) -> None:
        import hashlib

        proto = json.loads((THIS_DIR / "protocol_v4.json").read_text(encoding="utf-8"))
        repo_root = THIS_DIR.parents[2]
        mapping = {
            "adapter_py": repo_root / "gamma" / "fastweight" / "adapter.py",
            "doppler_fastweight_mjs": repo_root / "gamma" / "fastweight" / "doppler_fastweight.mjs",
            "pytorch_engine_py": repo_root / "gamma" / "engines" / "native" / "pytorch_engine.py",
            "regex_baseline_v4_py": THIS_DIR / "regex_baseline_v4.py",
            "evaluate_doppler_v4_mjs": THIS_DIR / "evaluate_doppler_v4.mjs",
            "evaluate_v4_mps_py": THIS_DIR / "evaluate_v4_mps.py",
        }
        for key, path in mapping.items():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, proto["frozen_code_sha256"][key], f"SHA-256 drift in {key}")


if __name__ == "__main__":
    unittest.main()
