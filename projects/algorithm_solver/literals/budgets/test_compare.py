"""Behavioral controls for literal selection, admission, and fixed-width export."""
import json
from pathlib import Path
import tempfile
import unittest

from compare import admissible, export, measure, optimize, score, trim_to_budget


class BudgetTests(unittest.TestCase):
    def test_choose_shortest_complete_alternative(self):
        state = measure(["ab", "cd", "a", "bc"], {"1": {"a": "abcd", "b": "abc"}})
        self.assertEqual(state["programs"]["1"]["arm"], "a")
        self.assertEqual(len(state["programs"]["1"]["sequence"]), 2)

    def test_no_incomplete_coverage(self):
        state = measure(["hello"], {"1": {"a": "hello world"}})
        self.assertEqual(state["programs"], {})

    def test_whole_program_and_near_whole_rejected(self):
        source = "function solve(x) {\nreturn x + 1;\n}\n"
        sources = {"1": {"a": source}}
        self.assertFalse(admissible(source, sources))
        self.assertFalse(admissible(source[:-2], sources))
        self.assertTrue(admissible("return x + 1;\n", sources))
        self.assertFalse(admissible("unrelated", sources))

    def test_large_shared_helper_admitted_without_parameterization(self):
        helper = "function count(x) {\nlet n = 0;\nfor (const a of x) n++;\nreturn n;\n}\n"
        sources = {"1": {"a": helper + "function solve(x) { return count(x); }\n"},
                   "2": {"a": helper + "function solve(x) { return count(x) > 1; }\n"}}
        self.assertTrue(admissible(helper, sources))

    def test_shared_merge_resegments_and_keeps_coverage(self):
        sources = {"1": {"a": "a\nb\nc\n"}, "2": {"a": "a\nb\nd\n"}}
        seed = measure(["a\n", "b\n", "c\n", "d\n"], sources)
        result, trace, _ = optimize(seed, sources, 4)
        self.assertEqual(len(result["programs"]), 2)
        self.assertLess(score(result), score(seed))
        self.assertTrue(trace)
        self.assertTrue(all(admissible(s, sources) for s in result["literals"]))

    def test_budget_cap_never_gets_free_fallback(self):
        sources = {"1": {"a": "ab!"}, "2": {"a": "ac!"}, "3": {"a": "ad!"}}
        seed = measure(["a", "b", "c", "d", "!"], sources)
        result = trim_to_budget(seed, sources, 3)
        self.assertEqual(len(result["programs"]), 1)
        self.assertLessEqual(len(result["literals"]), 3)

    def test_packet_accounting_and_width(self):
        sources = {"1": {"a": "a\nb\nc\n"}, "2": {"a": "a\nb\nd\n"}}
        state = measure(["a\n", "b\n", "c\n", "d\n"], sources)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            result = export(state, sources, 16, out, "test")
            self.assertEqual(result["selection_bits"], 24)
            self.assertEqual(result["padding_bits"], 8)
            self.assertEqual(result["framing_bytes"], 82)
            actual = (out / "dictionary.ltd").stat().st_size + sum(
                p.stat().st_size for p in (out / "programs").glob("*.ltv"))
            self.assertEqual(result["total_package_bytes"], actual)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(manifest["programs"]["1"]["sequence"], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
