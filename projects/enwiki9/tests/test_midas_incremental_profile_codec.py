"""Fixed synthetic incremental/reference identity; no corpus or qualification credit."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_midas_open_profile_codec import CORE, FLAGS, ROOT, SOURCES, fixture_limits


class IncrementalProfileCodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("g++")
        if compiler is None:
            raise unittest.SkipTest("g++ required; no installation")
        cls.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-incremental-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = Path(cls.directory.name) / "incremental-fixture"
        compiled = subprocess.run(
            [compiler, *FLAGS, str(ROOT / "tests/native/midas_incremental_profile_codec_fixture.cpp"),
             str(ROOT / "lib/midas_profile_incremental_forward.cpp"),
             *(str(CORE / name) for name in SOURCES if name != "profile_forward.cpp"),
             "-o", str(cls.binary)], capture_output=True, text=True,
            timeout=120, preexec_fn=fixture_limits)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)

    def run_fixture(self, *arguments):
        result = subprocess.run([str(self.binary), *arguments], capture_output=True, text=True,
                                timeout=120, preexec_fn=fixture_limits,
                                env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_exact_incremental_reference_identity(self):
        result = self.run_fixture("selftest")
        self.assertIn("checkpoint replay passed", result.stdout)
        print(result.stdout, end="")
        artifacts = []
        retained = json.loads((ROOT / "operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json").read_text())
        # Retained hashes are checked independently of the linked reference.
        known = {"P": "b42868fca6dce9d28652b6e27249df60f62506f56f60a9ace6df63ff40dd010e",
                 "K": "b42868fca6dce9d28652b6e27249df60f62506f56f60a9ace6df63ff40dd010e",
                 "F": "4db5dec01cd26e87d63de549c5c3250c42e3da979fe785812d1b71796c3417ad",
                 "S": "246317ec4aa9ff5f0eeb23b58788a92b96c4a727db8f7b10e76fec671ad569a0"}
        self.assertEqual({arm: item["archive_sha256"]
                          for arm, item in retained["finite_artifacts"]["arms"].items()}, known)
        for line in result.stdout.splitlines():
            if not line.startswith("arm="):
                continue
            fields = dict(item.split("=", 1) for item in line.split())
            archive = bytes.fromhex(fields["archive_hex"])
            digest = hashlib.sha256(archive).hexdigest()
            size = int(fields["raw_bytes"])
            raw = bytes((17 * i + 3) & 255 for i in range(size))
            self.assertEqual(len(archive), int(fields["archive_bytes"]))
            if size == 65:
                self.assertEqual(digest, known[fields["arm"]])
                self.assertEqual(fields["archive_hex"],
                                 retained["finite_artifacts"]["arms"][fields["arm"]]["archive_hex"])
            artifacts.append({**fields, "archive_sha256": digest, "raw_hex": raw.hex(),
                              "raw_sha256": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(len(artifacts), 8)
        print("INCREMENTAL_ARCHIVES_JSON=" + json.dumps(artifacts, sort_keys=True))

    def test_paired_kernel_diagnostic(self):
        result = self.run_fixture("kernel")
        records = []
        for line in result.stdout.splitlines():
            record = json.loads(line.removeprefix("KERNEL_JSON="))
            self.assertEqual(record["raw_bytes"], 129)
            self.assertTrue(record["inverse_exact"])
            self.assertFalse(record["qualification"])
            record["inherited_cpu_affinity"] = sorted(os.sched_getaffinity(0))
            record["thread_policy"] = "one calling thread; no parallel math library"
            record["binary_bytes"] = self.binary.stat().st_size
            record["binary_sha256"] = hashlib.sha256(self.binary.read_bytes()).hexdigest()
            record["scope"] = "shared-host 129-byte F encode/decode including initialization, midpoint and segment updates, memory rebuilds and cache resets; peak RSS is cumulative for this process"
            records.append(record)
        self.assertEqual([r["backend"] for r in records], ["reference", "incremental"])
        self.assertEqual(records[0]["archive_bytes"], records[1]["archive_bytes"])
        print("INCREMENTAL_KERNEL_JSON=" + json.dumps(records, sort_keys=True))

    def test_separate_process_cross_inverse(self):
        with tempfile.TemporaryDirectory(prefix="gamma-midas-incremental-inverse-") as directory:
            source, archive, inverse = [Path(directory) / name for name in ("source", "archive", "inverse")]
            raw = bytes((17 * i + 3) & 255 for i in range(129))
            source.write_bytes(raw)
            self.run_fixture("incremental", "encode", "F", str(source), str(archive))
            source.unlink()  # Private synthetic fixture only; decoder cannot read it.
            self.run_fixture("reference", "decode", "F", str(archive), str(inverse))
            self.assertEqual(inverse.read_bytes(), raw)
            inverse.unlink()
            self.run_fixture("incremental", "decode", "F", str(archive), str(inverse))
            self.assertEqual(inverse.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
