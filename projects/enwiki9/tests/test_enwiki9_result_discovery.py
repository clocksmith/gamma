"""Result discovery must tolerate neighboring JSON manifests and scalar values."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from projects.enwiki9.tools import enwiki9_evidence_matrix as evidence
from projects.enwiki9.tools import hutter_upper_bound_certificate as certificate


class ResultDiscoveryTests(unittest.TestCase):
    def test_non_object_json_is_not_a_result(self) -> None:
        values = ([], [{"program_id": "nested-not-a-result"}], "", "note", 0, 1.5, True, False, None)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            for value in values:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value))
                    self.assertIsNone(certificate.load_result(path))
                    self.assertIsNone(evidence.load_row(path))

    def test_mixed_directory_preserves_valid_driver_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory)
            candidate = results / "fixture"
            candidate.mkdir()
            unrelated = {
                "source-manifest.json": [{"path": "program.py", "sha256": "bound-source"}],
                "scalar.json": 42,
                "null.json": None,
                "metadata.json": {"schema": "unrelated-manifest"},
            }
            for name, value in unrelated.items():
                (candidate / name).write_text(json.dumps(value))
            result_path = candidate / "result.json"
            result_path.write_text(json.dumps({
                "schema": "gamma.enwiki9.driver-result.v2",
                "program_id": "fixture",
                "data_size": 1000,
                "data_sha256": "fixture-input-digest",
                "compressed_size": 400,
                "program_size": 30,
                "hutter_score": 430,
                "roundtrip_ok": True,
                "determinism": {"single_host_byte_equal": True},
            }))

            certificate_row, = certificate.iter_results(results)
            evidence_row, = evidence.iter_rows(results)
            for row in (certificate_row, evidence_row):
                self.assertEqual(row.path, result_path)
                self.assertEqual(row.program_id, "fixture")
                self.assertEqual(row.data_size, 1000)
                self.assertEqual(row.compressed_size, 400)
                self.assertEqual(row.program_size, 30)
                self.assertTrue(row.roundtrip_ok)
                self.assertTrue(row.determinism_ok)
            self.assertEqual(certificate_row.hutter_score, 430)
            self.assertEqual(evidence_row.score, 430)

    def test_evidence_legacy_object_schema_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps({
                "candidate_id": "legacy-fixture",
                "restored": {"bytes": 1000, "byte_identical_to_canonical": True},
                "archive": {"bytes": 400},
                "program": {"total_bytes": 30},
                "counted_score_bytes": 430,
            }))
            row = evidence.load_row(path)
            self.assertIsNotNone(row)
            self.assertEqual((row.program_id, row.data_size, row.score), ("legacy-fixture", 1000, 430))
            self.assertTrue(row.roundtrip_ok)
            self.assertIsNone(row.determinism_ok)


if __name__ == "__main__":
    unittest.main()
