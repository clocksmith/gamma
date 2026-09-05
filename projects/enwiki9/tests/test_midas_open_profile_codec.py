"""Bounded real-predictor integration, not a corpus or architecture-selection gate."""

import os
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2"
SOURCES = ("adam_update.cpp", "midpoint_kernels.cpp", "transformer_backward.cpp",
           "profile_backward.cpp", "profile_artifacts.cpp", "profile_forward.cpp",
           "profile_state.cpp", "tensor_container.cpp")
FLAGS = ("-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-mavx2", "-mfma",
         "-fno-fast-math", "-ffp-contract=off")


def fixture_limits():
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))


class OpenProfileCodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("g++")
        if compiler is None:
            raise unittest.SkipTest("g++ required; no installation")
        cls.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-open-profile-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = Path(cls.directory.name) / "open-profile-fixture"
        compiled = subprocess.run(
            [compiler, *FLAGS, str(ROOT / "tests/native/midas_open_profile_codec_fixture.cpp"),
             *(str(CORE / name) for name in SOURCES), "-o", str(cls.binary)],
            capture_output=True, text=True, timeout=120, preexec_fn=fixture_limits)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)

    def run_fixture(self, *arguments):
        result = subprocess.run([str(self.binary), *arguments], capture_output=True,
                                text=True, timeout=120, preexec_fn=fixture_limits,
                                env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_real_parent_and_causal_full_updates(self):
        result = self.run_fixture("selftest")
        self.assertIn("real open profile parent", result.stdout)
        self.assertIn("passed", result.stdout)
        print(result.stdout, end="")
        raw = bytes((17 * i + 3) & 255 for i in range(65))
        artifacts = {"raw_hex": raw.hex(), "raw_sha256": hashlib.sha256(raw).hexdigest(), "arms": {}}
        for line in result.stdout.splitlines():
            if not line.startswith("arm="):
                continue
            fields = dict(item.split("=", 1) for item in line.split())
            archive = bytes.fromhex(fields["archive_hex"])
            self.assertEqual(len(archive), int(fields["archive_bytes"]))
            self.assertEqual(int(fields["raw_bytes"]), len(raw))
            self.assertEqual(fields["inverse"], "exact")
            self.assertEqual(fields["repeat"], "exact")
            artifacts["arms"]["PKFS"[int(fields["arm"])]] = {
                "archive_hex": archive.hex(), "archive_bytes": len(archive),
                "archive_sha256": hashlib.sha256(archive).hexdigest(),
                "inverse_sha256": artifacts["raw_sha256"], "repeat_identical": True}
        self.assertEqual(set(artifacts["arms"]), set("PKFS"))
        print("FINITE_ARCHIVES_JSON=" + json.dumps(artifacts, sort_keys=True))

    def test_bounded_kernel_diagnostic(self):
        result = self.run_fixture("kernel")
        record = json.loads(result.stdout.removeprefix("KERNEL_JSON="))
        self.assertEqual(record["raw_bytes"], 65)
        self.assertEqual(record["archive_bytes"], 105)
        self.assertTrue(record["inverse_exact"])
        self.assertFalse(record["qualification"])
        self.assertGreater(record["encode_cpu_seconds"], 0)
        self.assertGreater(record["decode_cpu_seconds"], 0)
        record["inherited_cpu_affinity"] = sorted(os.sched_getaffinity(0))
        record["thread_policy"] = "one calling thread; no parallel math library"
        record["binary_bytes"] = self.binary.stat().st_size
        record["binary_sha256"] = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        record["scope"] = "single synthetic 65-byte parent encode/decode, including initialization and the full update/rebuild at byte 64; not an isolated eligibility measurement"
        print("KERNEL_DIAGNOSTIC_JSON=" + json.dumps(record, sort_keys=True))

    def test_separate_process_parent_inverse_without_source_file(self):
        with tempfile.TemporaryDirectory(prefix="gamma-midas-open-inverse-") as directory:
            root = Path(directory)
            source, archive, inverse = [root / name for name in ("source", "archive", "inverse")]
            raw = b"Gamma open parent\x00\xff"
            source.write_bytes(raw)
            self.run_fixture("encode", "P", str(source), str(archive))
            source.unlink()  # A private synthetic input; the decoder gets only the archive.
            self.run_fixture("decode", "P", str(archive), str(inverse))
            self.assertEqual(inverse.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
