"""Source-free unit tests for requested-243-370-35 oracles and cases."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

_DIR = Path(__file__).resolve().parent
_ORACLES_SPEC = importlib.util.spec_from_file_location("req_243_370_oracles", _DIR / "oracles.py")
oracles = importlib.util.module_from_spec(_ORACLES_SPEC)
_ORACLES_SPEC.loader.exec_module(oracles)

_CASES_SPEC = importlib.util.spec_from_file_location("req_243_370_cases", _DIR / "cases.py")
cases = importlib.util.module_from_spec(_CASES_SPEC)
_CASES_SPEC.loader.exec_module(cases)


class TestRequested243To370Oracles(unittest.TestCase):
    def test_35_problem_ids_present(self):
        self.assertEqual(len(oracles.PROBLEM_IDS), 35)
        self.assertEqual(set(oracles.PROBLEM_IDS), set(oracles.REFERENCES.keys()))

    def test_base_and_max_cases_valid_and_non_mutating(self):
        for pid in oracles.PROBLEM_IDS:
            rows = cases.build_cases(pid, include_maximum=True)
            self.assertGreaterEqual(len(rows), 2, f"Problem {pid} needs >= 2 cases")
            for row in rows:
                before = deepcopy(row["args"])
                got = oracles.REFERENCES[pid](*row["args"])
                self.assertEqual(row["args"], before, f"Oracle {pid} mutated arguments")
                self.assertEqual(got, row["expected"], f"Oracle {pid} mismatch")

    def test_domain_validation_rejects_invalid(self):
        with self.assertRaises(ValueError):
            oracles.validate_domain(243, ["only_one"], "a", "b")
        with self.assertRaises(ValueError):
            oracles.validate_domain(247, 0)
        with self.assertRaises(ValueError):
            oracles.validate_domain(351, 5, 2)


if __name__ == "__main__":
    unittest.main()
