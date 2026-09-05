"""Native coder correctness only; the counting model is not the MIDAS parent."""

from pathlib import Path
import importlib.util
import random
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NativeMidasCodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("g++")
        if compiler is None:
            raise unittest.SkipTest("g++ is required; no dependency installation")
        cls.directory = tempfile.TemporaryDirectory(prefix="gamma-native-midas-codec-")
        cls.binary = Path(cls.directory.name) / "fixture"
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
             str(ROOT / "tests/native/midas_codec_fixture.cpp"), "-o", str(cls.binary)],
            check=True, capture_output=True, text=True, timeout=60,
        )
        cls.schedule_binary = Path(cls.directory.name) / "schedule_fixture"
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
             str(ROOT / "tests/native/midas_schedule_fixture.cpp"), "-o",
             str(cls.schedule_binary)],
            check=True, capture_output=True, text=True, timeout=60,
        )
        spec = importlib.util.spec_from_file_location(
            "gamma_native_midas_reference_predictor", ROOT / "lib/predictor.py")
        cls.reference = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.reference
        spec.loader.exec_module(cls.reference)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_native_state_and_inverse_known_answers(self):
        result = subprocess.run([str(self.binary), "selftest"], check=True,
                                capture_output=True, text=True, timeout=60)
        self.assertIn("checkpoints", result.stdout)
        self.assertIn("passed", result.stdout)

    def test_causal_scheduler_with_sentinel_backend(self):
        result = subprocess.run([str(self.schedule_binary)], check=True,
                                capture_output=True, text=True, timeout=60)
        self.assertIn("sentinel-only", result.stdout)
        self.assertIn("passed", result.stdout)

    def test_native_payload_matches_independent_python_coder(self):
        rng = random.Random(123)
        populations = [b"", bytes(range(256)), b"a" * 8192,
                       bytes(rng.randrange(256) for _ in range(4096)),
                       ("<page><title>Gamma</title>caf\u00e9\n</page>" * 40).encode()]
        with tempfile.TemporaryDirectory(prefix="gamma-native-midas-inverse-") as directory:
            root = Path(directory)
            for number, raw in enumerate(populations):
                with self.subTest(population=number):
                    source, archive, inverse = [root / name for name in ("input", "archive", "inverse")]
                    source.write_bytes(raw)
                    subprocess.run([str(self.binary), "encode", str(source), str(archive)],
                                   check=True, capture_output=True, timeout=60)
                    native = archive.read_bytes()
                    self.assertEqual(native[:6], b"GMAC\x01\x01")
                    reference = self.reference.encode(
                        raw, self.reference.CountingPredictor(order=8))
                    self.assertEqual(native[36:], reference[12:])
                    subprocess.run([str(self.binary), "decode", str(archive), str(inverse)],
                                   check=True, capture_output=True, timeout=60)
                    self.assertEqual(inverse.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
