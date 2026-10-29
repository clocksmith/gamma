"""Source-free unit tests for requested-156-1940-31 oracles and cases."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

_DIR = Path(__file__).resolve().parent
_ORACLES_SPEC = importlib.util.spec_from_file_location("req_156_1940_oracles", _DIR / "oracles.py")
oracles = importlib.util.module_from_spec(_ORACLES_SPEC)
_ORACLES_SPEC.loader.exec_module(oracles)

_CASES_SPEC = importlib.util.spec_from_file_location("req_156_1940_cases", _DIR / "cases.py")
cases = importlib.util.module_from_spec(_CASES_SPEC)
_CASES_SPEC.loader.exec_module(cases)


class TestRequested156To1940Oracles(unittest.TestCase):
    def test_31_problem_ids_present(self):
        self.assertEqual(len(oracles.PROBLEM_IDS), 31)
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
            oracles.validate_domain(159, "")
        with self.assertRaises(ValueError):
            oracles.validate_domain(163, [1], 10, 5)
        with self.assertRaises(ValueError):
            oracles.validate_domain(1692, 3, 5)


if __name__ == "__main__":
    unittest.main()
