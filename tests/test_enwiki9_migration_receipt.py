from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "projects" / "enwiki9" / "tools" / "enwiki9_migration_receipt.py"
)
SPEC = importlib.util.spec_from_file_location("enwiki9_migration_receipt", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def observed(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(payload),
        "md5": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "blake2b": hashlib.blake2b(payload).hexdigest(),
    }


class MigrationReceiptTests(unittest.TestCase):
    def test_compare_manifest_waits_when_manifest_is_absent(self) -> None:
        result = MODULE.compare_manifest({}, None)
        self.assertEqual(result["status"], "pending_source_manifest")
        self.assertIs(result["accepted"], False)

    def test_compare_manifest_accepts_both_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            archive = tmp_path / "enwik9.zip"
            corpus = tmp_path / "enwik9"
            archive.write_bytes(b"archive")
            corpus.write_bytes(b"corpus")
            rows = {"enwik9.zip": observed(archive), "enwik9": observed(corpus)}
            manifest = tmp_path / "source-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "name": name,
                                "size_bytes": row["size_bytes"],
                                "md5": row["md5"],
                                "sha256": row["sha256"],
                            }
                            for name, row in rows.items()
                        ]
                    }
                )
            )

            result = MODULE.compare_manifest(rows, manifest)

            self.assertEqual(result["status"], "accepted")
            self.assertIs(result["accepted"], True)

    def test_compare_manifest_rejects_missing_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            archive = tmp_path / "enwik9.zip"
            corpus = tmp_path / "enwik9"
            archive.write_bytes(b"archive")
            corpus.write_bytes(b"corpus")
            rows = {"enwik9.zip": observed(archive), "enwik9": observed(corpus)}
            manifest = tmp_path / "source-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        name: {
                            "size_bytes": row["size_bytes"],
                            "md5": row["md5"],
                        }
                        for name, row in rows.items()
                    }
                )
            )

            result = MODULE.compare_manifest(rows, manifest)

            self.assertEqual(result["status"], "source_manifest_mismatch")
            self.assertIs(result["accepted"], False)

    def test_destination_requires_existing_path_and_free_space(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            missing = tmp_path / "missing"
            result = MODULE.destination_inventory(missing, 1)
            self.assertIs(result["ready"], False)
            self.assertEqual(result["reason"], "destination directory does not exist")

            ready = MODULE.destination_inventory(tmp_path, 1)
            self.assertIs(ready["ready"], True)
            self.assertTrue(
                ready["layout"]["portable_proof_build"]["path"].endswith(
                    "build/portable-proof"
                )
            )


if __name__ == "__main__":
    unittest.main()
