import unittest

from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_primaryppmd_identity_failure import (
    archive_delta,
)


class ArchiveDeltaTest(unittest.TestCase):
    def test_reports_regression(self) -> None:
        candidate = {"bytes": 174_030, "sha256": "candidate"}
        reference = {"bytes": 173_963, "sha256": "reference"}
        self.assertEqual(archive_delta(candidate, reference), 67)

    def test_rejects_identical_archive(self) -> None:
        artifact = {"bytes": 173_963, "sha256": "same"}
        with self.assertRaisesRegex(RuntimeError, "preserves archive identity"):
            archive_delta(artifact, artifact)


if __name__ == "__main__":
    unittest.main()
