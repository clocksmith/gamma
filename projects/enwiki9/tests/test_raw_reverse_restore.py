"""Verify restoration from plain files: the verifier has no Git/network dependency."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("raw_reverse_restore", PROJECT / "tools/verify_raw_reverse_restore.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def tracked_source(relative):
    path = PROJECT / relative
    if path.exists():
        return path.read_bytes()
    # Sparse developer checkout only: current-tree metadata, never a historical
    # commit fetch. A normal/fresh clone contains these kept tracked files.
    return subprocess.check_output(["git", "-C", str(PROJECT), "show", f"HEAD:projects/enwiki9/{relative}"],
                                   env={**os.environ, "GIT_NO_LAZY_FETCH": "1"})


class RestoredPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="raw-reverse-restoration-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project, self.restored = self.root / "source", self.root / "restored"
        for relative in VERIFIER.PINNED_SHA256:
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(tracked_source(relative))
        self.codec = types.ModuleType("original_codec_fixture")
        source = (self.project / "tools/raw_reverse_bz2_v1.py").read_bytes()
        exec(compile(source, "original_codec_fixture.py", "exec"), self.codec.__dict__)
        raw = (self.project / "operations/evidence/fixtures/dualstream_opening250k_v1.raw").read_bytes()
        output = self.restored / "projects/enwiki9/results/raw_reverse_bz2250k_q0_v1"
        output.mkdir(parents=True)
        for arm in ("P", "K", "D"):
            archive, _ = self.codec.encode(raw, arm)
            for suffix, data in (("raw", raw), ("rbz", archive), ("repeat.rbz", archive)):
                (output / f"{arm}.{suffix}").write_bytes(data)

    def test_exact_original_bytes_verify_without_git_repository(self):
        result = VERIFIER.verify(self.project, self.restored)
        self.assertTrue(result["verified"])
        self.assertEqual(len(result["restored_files"]), 9)
        self.assertEqual(result["original_decoder_inverses"], 6)
        self.assertEqual(result["original_encoder_repeats"], 6)
        self.assertFalse(result["historical_timing_reproduced"])
        self.assertFalse((self.project / ".git").exists())

    def test_restored_corruption_fails(self):
        path = self.restored / "projects/enwiki9/results/raw_reverse_bz2250k_q0_v1/P.raw"
        path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "Restored artifact bytes differ"):
            VERIFIER.verify(self.project, self.restored)

    def test_changed_original_source_is_rejected_before_execution(self):
        path = self.project / "tools/raw_reverse_bz2_v1.py"
        path.write_text("raise RuntimeError('must not execute')\n")
        with self.assertRaisesRegex(ValueError, "Tracked original metadata/source bytes differ"):
            VERIFIER.verify(self.project, self.restored)


if __name__ == "__main__":
    unittest.main()
