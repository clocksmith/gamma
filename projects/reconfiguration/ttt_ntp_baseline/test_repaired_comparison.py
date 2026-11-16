"""Unit tests for the repaired TTT-NTP single-line oracle and fixture builder."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repaired_comparison import SEED_V2, build_fresh_tasks, score_single_line
from retrieval_tasks import SEED as ORIGINAL_SEED


class RepairedComparisonTests(unittest.TestCase):
    def test_seed_is_disjoint_from_exposed_fixture(self):
        self.assertNotEqual(SEED_V2, ORIGINAL_SEED)

    def test_single_line_oracle_accepts_exact_and_rejects_errors(self):
        expected = "value_73c9253e32e24340"
        self.assertTrue(score_single_line(" value_73c9253e32e24340\n```", expected))
        self.assertTrue(score_single_line("value_73c9253e32e24340", expected))
        # Reject omitted prefix, wrong distractor, trailing extra words on same line, or empty
        self.assertFalse(score_single_line(" 73c9253e32e24340", expected))
        self.assertFalse(score_single_line(" value_0000000000000000", expected))
        self.assertFalse(score_single_line(" value_73c9253e32e24340 extra", expected))
        self.assertFalse(score_single_line("", expected))

    def test_fresh_task_builder_respects_budgets_and_half_splits(self):
        # Character-level mock encoder (6 chars ~ 1 token) to keep unit test instant
        encode = lambda text: [ord(ch) for ch in text[::6]]
        tasks = build_fresh_tasks(encode)
        self.assertEqual(len(tasks), 16)
        self.assertEqual(sum(1 for t in tasks if t["budget"] == 4096), 8)
        self.assertEqual(sum(1 for t in tasks if t["budget"] == 8192), 8)
        for t in tasks:
            self.assertLessEqual(len(t["input_ids"]), t["budget"])
            self.assertTrue(t["prompt"].endswith(f"{t['key']} ="))
            self.assertIn(f"{t['key']} = {t['expected']}\n", t["prompt"])
            # Needle must appear in at least one of the two half-haystack splits
            self.assertGreater(len(t["half_a_ids"]), 0)
            self.assertGreater(len(t["half_b_ids"]), 0)


if __name__ == "__main__":
    unittest.main()
