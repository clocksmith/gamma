"""Reuse all sealed observer tests, plus independent SHA padding/alignment vectors."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midas_open_boundary_observer_sha_v1 as accelerated

spec = importlib.util.spec_from_file_location("bound_observer_tests", ROOT / "tests/test_midas_open_boundary_observer.py")
original_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original_tests)


class AcceleratedObserverTest(original_tests.BoundaryObserverTest):
    @classmethod
    def setUpClass(cls):
        replacement = patch.object(original_tests, "observer", accelerated)
        replacement.start(); cls.addClassCleanup(replacement.stop)
        super().setUpClass()

    def test_sha_vectors_padding_unaligned_inputs_and_scalar_fallback(self):
        built = accelerated.parent.build_cpp_cached(
            sources=(ROOT / "tests/midas_observer_sha256_fixture.cpp", *accelerated.SOURCES[1:]),
            flags=accelerated.parent.FLAGS, cache_dir=self.work / "hash-cache", timeout_seconds=120)
        execution = subprocess.run(["/usr/bin/timeout", "30", "/usr/bin/prlimit", "--as=536870912", "--cpu=30",
                                    "--fsize=33554432", str(built.binary)], check=True, capture_output=True, text=True,
                                   timeout=35, env={"PATH":"/usr/bin:/bin", "LC_ALL":"C"})
        expected_sizes = [*range(131), 511, 512, 513, 1000, 4096, 32768, 1048576]
        rows = [line.split() for line in execution.stdout.splitlines()]
        self.assertEqual([int(row[0]) for row in rows], expected_sizes)
        for (size, actual), n in zip(rows, expected_sizes, strict=True):
            raw = bytes((i * 17 + (i >> 7) + 3) & 255 for i in range(1, n + 1))
            self.assertEqual(actual, hashlib.sha256(raw).hexdigest(), size)
        (self.work / "sha-vectors.json").write_text(json.dumps({"schema":"midas_observer_sha_vectors_v1", "vectors":rows,
            "scalar_parity":True, "python_hashlib_parity":True, "hardware_branch_exercised":True, "over_bound_rejected":True}, indent=2)+"\n")


if __name__ == "__main__":
    unittest.main()
