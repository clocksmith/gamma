"""Synthetic predict-before-observe fixtures for the separately identified replay."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClosingReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = None
        if os.environ.get('FX2_CLOSING_BUILD_DIR'):
            build = Path(os.environ['FX2_CLOSING_BUILD_DIR'])
            build.mkdir(exist_ok=False)
        else:
            cls.tmp = tempfile.TemporaryDirectory(prefix='closing-replay-')
            build = Path(cls.tmp.name)
        cls.executables = []
        for mode, flags in [('optimized', ['-O2']), ('ubsan', ['-O1', '-fsanitize=undefined', '-fno-sanitize-recover=all'])]:
            target = build / mode
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-I', str(ROOT/'lib'),
                            *flags, str(ROOT/'tests/fx2_closing_replay_v1_fixture.cpp'), '-o', str(target)],
                           check=True, timeout=45)
            cls.executables.append(target)

    @classmethod
    def tearDownClass(cls):
        if cls.tmp is not None:
            cls.tmp.cleanup()

    def check_case(self, case):
        outputs = []
        for executable in self.executables:
            for _ in range(2):
                outputs.append(subprocess.check_output([str(executable), case], timeout=10))
        self.assertTrue(all(x == outputs[0] for x in outputs))

    def test_predict_before_observe(self): self.check_case('causality')
    def test_nested_names(self): self.check_case('nested')
    def test_attributes_and_self_closing(self): self.check_case('attributes')
    def test_stop_at_first_mismatch(self): self.check_case('mismatch')
    def test_name_and_stack_bounds(self): self.check_case('bounds')
    def test_uncertain_markup(self): self.check_case('uncertain')
    def test_stored_multibyte_name(self): self.check_case('stored_tokens')


if __name__ == '__main__':
    unittest.main()
