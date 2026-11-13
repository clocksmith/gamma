import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from .archive_native_run import archive_run, restore_archive, GIT_SAFE_BYTES


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def sealed(body):
    # Fixtures use only integer numbers, so Python and JS canonical bytes agree.
    body["receiptSha256"] = checksum(json.dumps(body, sort_keys=True, separators=(",", ":")).encode())
    return body


class ArchiveTest(unittest.TestCase):
    def fixture(self, root):
        roots = {role: root / role for role in ("selection", "confirmation")}
        refs = {}
        for role, path in roots.items():
            path.mkdir()
            # Compressible and nontrivial bytes; enough for multiple tiny test parts.
            payload = "".join(checksum(str(i).encode()) for i in range(300))
            first = b'{"kind":"fixture-header"}\n'
            event = (json.dumps({"kind": role + "-fixture", "payload": payload}) + "\n").encode()
            (path / (role + ".jsonl")).write_bytes(first + event)
            refs[role] = {"path": role + ".jsonl", "line": 2, "byteOffset": len(first), "byteLength": len(event), "sha256": checksum(event)}
        common = {"runtimeLockSha256": "a" * 64, "stageLockSha256": "b" * 64, "continuationSha256": "c" * 64}
        selection = sealed({**common, "status": "selection_complete", "selectedCandidate": "fixture-only", "requests": [{"rawEvidence": refs["selection"]}]})
        confirmation = sealed({**common, "status": "confirmation_executed", "confirmationEvaluated": True,
                               "selection": {"selectedCandidate": "fixture-only", "receiptSha256": selection["receiptSha256"]},
                               "generated": {"requests": [{"rawEvidence": refs["confirmation"]}]},
                               "receipts": {"fixture": True}, "submissionLock": {"submissions": {"fixture": "d" * 64}}})
        (roots["selection"] / "selection-receipt.json").write_text(json.dumps(selection, indent=2) + "\n")
        (roots["confirmation"] / "confirmation-receipt.json").write_text(json.dumps(confirmation, indent=2) + "\n")
        (roots["confirmation"] / "empty.log").write_bytes(b"")
        return roots

    def test_streamed_gzip_parts_restore_exact_bytes_and_offsets_reproducibly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roots = self.fixture(root)
            original = {f"{role}/{p.name}": p.read_bytes() for role, folder in roots.items() for p in folder.iterdir()}
            first = archive_run(roots["selection"], roots["confirmation"], root / "archive-a", threshold=2000, part_bytes=1024)
            second = archive_run(roots["selection"], roots["confirmation"], root / "archive-b", threshold=2000, part_bytes=1024)
            self.assertEqual(first, second)
            journals = [entry for entry in first["files"] if entry["path"].endswith(".jsonl")]
            self.assertTrue(all(entry["encoding"] == "gzip" and len(entry["stored"]["parts"]) > 1 for entry in journals))
            self.assertTrue(all(part["bytes"] <= GIT_SAFE_BYTES for entry in first["files"] for part in entry["stored"]["parts"]))
            self.assertEqual(restore_archive(root / "archive-a")["rawEvidenceSlicesVerified"], 2)
            restored = root / "restored"
            result = restore_archive(root / "archive-a", restored)
            self.assertEqual(result["files"], len(original))
            for relative, data in original.items():
                self.assertEqual((restored / relative).read_bytes(), data)
                self.assertEqual((root / relative).read_bytes(), data)
            with self.assertRaises(ValueError):
                restore_archive(root / "archive-a", root / "archive-a" / "unsafe-restored")

    def test_incomplete_receipts_and_invalid_journal_slices_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roots = self.fixture(root)
            path = roots["confirmation"] / "confirmation-receipt.json"
            original = path.read_bytes()
            value = json.loads(original)
            value["status"] = "confirmation_incomplete"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "complete terminal"):
                archive_run(roots["selection"], roots["confirmation"], root / "archive")
            path.write_bytes(original)
            journal = roots["confirmation"] / "confirmation.jsonl"
            journal.write_bytes(journal.read_bytes()[:-1] + b"x")
            with self.assertRaisesRegex(ValueError, "slice checksum"):
                archive_run(roots["selection"], roots["confirmation"], root / "archive")
            self.assertFalse((root / "archive").exists())

    def test_archive_corruption_is_detected_before_restoration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roots = self.fixture(root)
            manifest = archive_run(roots["selection"], roots["confirmation"], root / "archive", threshold=2000, part_bytes=1024)
            part = next(entry["stored"]["parts"][0] for entry in manifest["files"] if entry["encoding"] == "gzip")
            path = root / "archive" / part["path"]
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "Stored part"):
                restore_archive(root / "archive", root / "restored")
            self.assertFalse((root / "restored").exists())


if __name__ == "__main__":
    unittest.main()
