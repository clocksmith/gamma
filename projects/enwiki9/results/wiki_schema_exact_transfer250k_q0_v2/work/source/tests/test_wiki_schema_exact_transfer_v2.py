"""Reuse the sealed transfer checks and admit real empty runtime modules."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import test_wiki_schema_exact_transfer as reference


runner = reference.load("schema_transfer_v2_test_runner",
    reference.ROOT / "tools/wiki_schema_exact_transfer250k_q0_v2.py")


class SchemaTransferV2Tests(reference.SchemaTransferTests):
    def setUp(self):
        # Existing checks resolve their runner through their defining module.
        # Patch only during each test; retain the original suite and v1 source.
        patch = mock.patch.object(reference, "runner", runner)
        patch.start()
        self.addCleanup(patch.stop)

    def runtime_plan(self, empty):
        paths = {Path(p).resolve() for p in (sys.executable, "/usr/bin/prlimit", "/usr/bin/timeout")}
        paths.add(empty)
        return {"schema": "gamma.enwiki9.wiki-schema-exact-gate-plan.v1",
            "candidate_id": runner.ID, "populations": runner.POPULATIONS,
            "codec_options": runner.OPTIONS, "resources": runner.CAPS,
            "phase_wall_seconds": runner.PHASE_STOP,
            "python_executable": str(Path(sys.executable).resolve()),
            "runtime_files": [runner.file_record(p) for p in sorted(paths)]}

    def test_empty_runtime_module_is_hash_bound_and_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "__init__.py"
            empty.write_bytes(b"")
            plan = self.runtime_plan(empty)
            with mock.patch.object(runner, "observed_runtime_paths", return_value={str(empty)}):
                result = runner.verify_runtime(plan)
            record = next(row for row in result["declared_files"] if row["path"] == str(empty))
            self.assertEqual(record["bytes"], 0)
            self.assertEqual(record["sha256"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            self.assertFalse(result["child_runtime_closure_complete"])
            self.assertIsNone(result["complete_submission_package_bytes"])

    def test_empty_runtime_module_size_and_hash_drift_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "__init__.py"
            empty.write_bytes(b"")
            plan = self.runtime_plan(empty)
            record = next(row for row in plan["runtime_files"] if row["path"] == str(empty))
            for field, value in (("bytes", 1), ("sha256", "0" * 64)):
                with self.subTest(field=field):
                    original = record[field]
                    record[field] = value
                    with self.assertRaisesRegex(ValueError, "bound runtime changed"):
                        runner.verify_runtime(plan)
                    record[field] = original
            empty.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "bound runtime changed"):
                runner.verify_runtime(plan)


if __name__ == "__main__":
    unittest.main()
