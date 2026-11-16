"""Bounded tests of original comparison extraction; no model or corpus run."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("trace_restore", PROJECT / "tools/verify_attention_trace_restore.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class TraceRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="attention-restore-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Change only an in-memory population bound for a three-row test.
        # The production verifier requires the real 151210-row candidate.
        source = (PROJECT / "tools/fx2_attention_anchor250k_v1.py").read_bytes()
        self.source = source.replace(b"N=151210", b"N=3")
        self.compare = VERIFIER.original_comparison(self.source + b"\nraise RuntimeError('driver must not execute')\n",
                                                    "synthetic-bounded-original-comparison.py", 3)
        self.parent, self.child = self.root / "parent", self.root / "child"
        self.parent.write_bytes(b"\0" * (3 * 205 * 2))
        self.child.write_bytes(self.parent.read_bytes())

    def test_original_function_retains_row_semantics_without_driver_import(self):
        data = bytearray(self.child.read_bytes())
        data[2 * 205 * 2:2 * 205 * 2 + 2] = struct.pack("<e", 0.5)
        self.child.write_bytes(data)
        report = self.compare(self.parent, self.child, [0])
        self.assertEqual(report["rows"], 3)
        self.assertEqual(report["changed_rows"], 1)
        self.assertEqual(report["first_changed_row"]["row"], 2)
        self.assertEqual(report["same_pre_boundary_rows"], 2)
        self.assertEqual(report["treatment_sha256"], hashlib.sha256(data).hexdigest())

    def test_prefix_nonfinite_and_truncation_fail(self):
        for index, word, message in ((0, 0x3800, "prefix changed"), (2 * 205 * 2, 0x7c00, "nonfinite")):
            data = bytearray(self.parent.read_bytes())
            data[index:index + 2] = struct.pack("<H", word)
            self.child.write_bytes(data)
            with self.assertRaisesRegex(ValueError, message):
                self.compare(self.parent, self.child, [0])
        self.child.write_bytes(self.parent.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, "population differs"):
            self.compare(self.parent, self.child, [0])

    def test_incomplete_candidate_and_changed_population_cannot_verify(self):
        with self.assertRaisesRegex(ValueError, "both reviewed"):
            VERIFIER.verify({"families": []}, self.root, self.root)
        with self.assertRaisesRegex(ValueError, "row-count declaration differs"):
            VERIFIER.original_comparison(self.source, "synthetic.py", 4)


if __name__ == "__main__":
    unittest.main()
