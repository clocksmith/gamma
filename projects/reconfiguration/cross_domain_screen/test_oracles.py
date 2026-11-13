"""Focused CPU qualification: reference behavior, plausible errors, bounded code."""
import json
from pathlib import Path
import unittest

from oracles import BoundedPython, Invalid, exact_answers, score


RUNS = '''def compress_runs(items):
    out = []
    for value in items:
        if out and out[-1][0] == value:
            out[-1][1] += 1
        else:
            out.append([value, 1])
    return out
'''
INTERVALS = '''def intersect_intervals(left, right):
    return sorted([[max(a,c),min(b,d)] for a,b in left for c,d in right if max(a,c)<=min(b,d)])
'''


class OracleTests(unittest.TestCase):
    def test_independent_reference_answers(self):
        # Literals independently hand checked against fraction/CRT evaluator.
        self.assertEqual(exact_answers("arithmetic-fractions"), [313, 86, 59])
        self.assertEqual(exact_answers("arithmetic-congruences"), [192, 95, 87])
        self.assertEqual(exact_answers("text-records"), [
            {"id": "C4", "city": "Kyoto"}, {"id": "E8", "city": "Bern"},
            {"id": "A1", "city": "Accra"}, {"id": "B7", "city": "Lima"}])
        self.assertEqual(exact_answers("text-escape"), ["al|pha", "be\\ta", "", "ga|mma\\"])

    def test_correct_and_publicly_accepted_wrong_json(self):
        for task in ("arithmetic-fractions", "arithmetic-congruences", "text-records", "text-escape"):
            correct = exact_answers(task)
            self.assertTrue(score(task, json.dumps(correct))["passed"])
            wrong = list(reversed(correct))
            result = score(task, json.dumps(wrong))
            self.assertTrue(result["publicPassed"])
            self.assertFalse(result["heldoutPassed"])
            self.assertFalse(result["passed"])
        self.assertFalse(score("arithmetic-fractions", "[true,86,59]")["publicPassed"])
        self.assertFalse(score("arithmetic-fractions", "```json\n[313,86,59]\n```")["passed"])

    def test_python_references(self):
        self.assertTrue(score("python-runs", RUNS)["passed"])
        self.assertTrue(score("python-intervals", INTERVALS)["passed"])

    def test_python_plausible_wrong_answers(self):
        # Public example hardcoding passes visible case, fails reserved variants.
        result = score("python-runs", "def compress_runs(items):\n return [[4,2],[9,1]]")
        self.assertTrue(result["publicPassed"])
        self.assertFalse(result["heldoutPassed"])
        # Open-interval mistake drops touching endpoints but passes public example.
        result = score("python-intervals", INTERVALS.replace("<=", "<"))
        self.assertTrue(result["publicPassed"])
        self.assertFalse(result["heldoutPassed"])
        result = score("python-runs", "def compress_runs(items):\n return [[4,2],[9,True]]")
        self.assertFalse(result["publicPassed"])

    def test_public_phase_does_not_score_reserved_checks(self):
        result = score("python-runs", "def compress_runs(items):\n return [[4,2],[9,1]]", "public")
        self.assertTrue(result["passed"])
        self.assertNotIn("heldoutPassed", result)
        self.assertTrue(all(c["phase"] == "public" for c in result["checks"]))

    def test_code_is_bounded_and_cannot_call_host(self):
        invalid = [
            "import os\ndef compress_runs(items):\n return []",
            "def compress_runs(items):\n return open('/tmp/screen-oracle-must-not-create','w')",
            "def compress_runs(items):\n return items.__class__",
            "def compress_runs(items):\n while True:\n  pass",
            "def compress_runs(items):\n return [0]*100000000000",
            "def compress_runs(items):\n items.append(1)\n return []",
            "def compress_runs(items):\n return compress_runs(items)",
            "def compress_runs(items):\n len = []\n return len(items)",
        ]
        for source in invalid:
            with self.subTest(source=source):
                self.assertFalse(score("python-runs", source)["passed"])

    def test_task_prompt_spans_and_public_examples_match(self):
        import hashlib
        tasks = json.loads(Path(__file__).with_name("tasks.json").read_text())["tasks"]
        self.assertEqual(len({task["family"] for task in tasks}), 6)
        for task in tasks:
            prompt, span = task["prompt"], task["instructionSpan"]
            self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), task["promptSha256"])
            self.assertEqual(hashlib.sha256(prompt[span["start"]:span["end"]].encode()).hexdigest(), span["textSha256"])
            self.assertTrue(prompt[:span["start"]].strip())
            if task["id"].startswith("python-"):
                from oracles import PYTHON_CASES
                for actual, (args, expected) in zip(task["publicExamples"], PYTHON_CASES[task["id"]]["public"]):
                    self.assertEqual(actual, {"arguments": args, "expected": expected})


if __name__ == "__main__":
    unittest.main()
