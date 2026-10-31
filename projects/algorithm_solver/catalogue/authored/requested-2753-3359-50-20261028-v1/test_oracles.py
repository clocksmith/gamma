"""Source-free unit tests for requested-2753-3359-50 oracles and cases."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

_DIR = Path(__file__).resolve().parent
_ORACLES_SPEC = importlib.util.spec_from_file_location("req_2753_3359_oracles", _DIR / "oracles.py")
oracles = importlib.util.module_from_spec(_ORACLES_SPEC)
_ORACLES_SPEC.loader.exec_module(oracles)

_CASES_SPEC = importlib.util.spec_from_file_location("req_2753_3359_cases", _DIR / "cases.py")
cases = importlib.util.module_from_spec(_CASES_SPEC)
_CASES_SPEC.loader.exec_module(cases)


class TestRequested2753To3359Oracles(unittest.TestCase):
    def test_50_problem_ids_present(self):
        self.assertEqual(len(oracles.PROBLEM_IDS), 50)
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
            oracles.validate_domain(2753, [0, 0, 0], 5)
        with self.assertRaises(ValueError):
            oracles.validate_domain(2864, "0000")
        with self.assertRaises(ValueError):
            oracles.validate_domain(2930, 0)


if __name__ == "__main__":
    unittest.main()
