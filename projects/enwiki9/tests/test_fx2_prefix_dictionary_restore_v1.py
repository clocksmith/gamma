"""Synthetic rejection checks for the fixed-identity native dictionary helper."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class Tests(unittest.TestCase):
    def test_wrong_dictionary_and_bad_framing_never_publish(self):
        binary = os.environ['FX2_PREFIX_RESTORE_BINARY']
        for data in (b'', b'BAD!\0', b'BPD1\1 a\n', b'BPD1\1 a\n!\n',
                     b'BPD1\1 !\n', b'BPD1\1 a', b'BPD1\2', b'x' * 524289):
            with self.subTest(bytes=len(data)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, target = root/'input', root/'output'
                source.write_bytes(data)
                result = subprocess.run([binary, str(source), str(target)], timeout=5)
                self.assertEqual(result.returncode, 3)
                self.assertFalse(target.exists())

    def test_invalid_input_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root/'input', root/'output'
            source.write_bytes(b'BPD1\1 a\n')
            target.write_bytes(b'existing output')
            result = subprocess.run([os.environ['FX2_PREFIX_RESTORE_BINARY'],
                                     str(source), str(target)], timeout=5)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(target.read_bytes(), b'existing output')

    def test_argument_and_input_errors(self):
        binary = os.environ['FX2_PREFIX_RESTORE_BINARY']
        self.assertEqual(subprocess.run([binary], timeout=5).returncode, 2)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(subprocess.run([binary, str(root/'absent'),
                                             str(root/'output')], timeout=5).returncode, 2)
            self.assertFalse((root/'output').exists())


if __name__ == '__main__':
    unittest.main()
