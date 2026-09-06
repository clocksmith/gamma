"""Synthetic authority tests; native execution remains in frozen gated jobs."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midas_open_observed_sha_gate_v1 as adapter


class ShaGateAuthorityTest(unittest.TestCase):
    def setUp(self):
        self.unit = json.loads((ROOT / adapter.UNIT).read_text())
        refs = [*self.unit["source_bindings"], *(self.unit[k] for k in
                ("predecessor_unit", "upstream_provenance", "build_manifest", "binary"))]
        self.inputs = {r["path"]: {**r, "sha256": "sha256:" + r["sha256"]} for r in refs}

    def test_successor_authority_and_original_driver_are_separate(self):
        adapter.validate_unit(self.unit, self.inputs)
        original_auth = adapter.original.authenticate
        driver = adapter.configured_driver()
        self.assertIs(driver.authenticate, adapter.authenticate)
        self.assertIs(adapter.original.authenticate, original_auth)
        self.assertEqual(driver.compare_matrix.__code__.co_code,
                         adapter.original.compare_matrix.__code__.co_code)
        self.assertIs(driver.observer, adapter.original.observer)

    def test_old_five_test_receipt_cannot_authorize_new_binary(self):
        self.unit["validation"]["tests_passed"] = 5
        with self.assertRaisesRegex(adapter.base.EvidenceFailure, "unit did not pass"):
            adapter.validate_unit(self.unit, self.inputs)

    def test_missing_hardware_or_scalar_parity_fails_closed(self):
        for field in ("hardware_branch_exercised", "scalar_and_hashlib_parity", "original_observer_bytes_equal"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.unit)
                changed["validation"][field] = False
                with self.assertRaisesRegex(adapter.base.EvidenceFailure, "missing SHA observer evidence"):
                    adapter.validate_unit(changed, self.inputs)

    def test_changed_source_or_predecessor_cannot_reuse_unit(self):
        for row in (self.unit["source_bindings"][0], self.unit["predecessor_unit"], self.unit["binary"]):
            with self.subTest(path=row["path"]):
                changed = copy.deepcopy(self.inputs)
                changed[row["path"]]["sha256"] = "sha256:" + "0" * 64
                with self.assertRaisesRegex(adapter.base.EvidenceFailure, "unit authority is not bound"):
                    adapter.validate_unit(self.unit, changed)

    def test_incomplete_guard_does_not_authorize_execution(self):
        self.unit["resources"]["cleanup_complete"] = False
        with self.assertRaisesRegex(adapter.base.EvidenceFailure, "unit guard is incomplete"):
            adapter.validate_unit(self.unit, self.inputs)


# Exercise the existing fake process matrix through the configured driver,
# including first probability divergence and elapsed-stop classification.
spec = importlib.util.spec_from_file_location("midas_existing_gate_tests", ROOT / "tests/test_midas_open_observed_gate.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
fixtures.runner = adapter.configured_driver()


class ShaGateMatrixTest(fixtures.ObservedGateTest):
    pass


if __name__ == "__main__":
    unittest.main()
