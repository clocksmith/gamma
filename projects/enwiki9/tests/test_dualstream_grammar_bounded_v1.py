"""Independent-review regression and unchanged accepted-archive behavior."""
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_bounded_v1 as codec
from tools import dualstream_grammar_v1 as parent

# Run every sealed synthetic fixture against the repaired public interface.
spec = importlib.util.spec_from_file_location('grammar_bounded_parent_fixtures',
    ROOT / 'tests/test_dualstream_grammar_v1.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
fixtures.codec = codec
ParentFixtures = fixtures.DualStreamGrammarTest


class ArchiveBoundRepair(unittest.TestCase):
    def test_reviewer_first_failing_fixture_is_rejected_before_cap(self):
        output = io.BytesIO()
        with self.assertRaisesRegex(parent.CodecError, 'decoder archive bound'):
            codec.encode_stream(io.BytesIO(b'a' * 74074), output, 74074, 'split', 1)
        self.assertEqual(len(output.getvalue()), 24 + 74073 * 108)
        self.assertLessEqual(len(output.getvalue()), parent.MAX_ARCHIVE)

    def test_last_accepted_fixture_inverts_and_matches_parent(self):
        raw = b'a' * 74073
        archive, report = codec.encode(raw, mode='split', frame_size=1)
        self.assertEqual(len(archive), 7999908)
        self.assertEqual(report['complete_archive_bytes'], len(archive))
        self.assertEqual(parent.decode(archive), raw)
        self.assertEqual(parent.encode(raw, mode='split', frame_size=1)[0], archive)

    def test_parent_globals_and_accepted_archives_are_unchanged(self):
        original = parent.encode_stream
        raw = b'<x>Same  bytes &amp; \xff</x>\r\n' * 9
        for mode in (*parent.MODES, 'auto'):
            self.assertEqual(codec.encode(raw, mode=mode), parent.encode(raw, mode=mode))
        self.assertIs(parent.encode_stream, original)
        self.assertIs(parent.main.__globals__['encode_stream'], original)
        self.assertIsNot(codec.main.__globals__, parent.main.__globals__)

    def test_file_command_refuses_partial_archive_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'raw', Path(directory)/'archive'
            source.write_bytes(b'a' * 74074)
            result = subprocess.run([sys.executable, str(ROOT/'tools/dualstream_grammar_bounded_v1.py'),
                'encode', str(source), str(target), '--mode', 'split', '--frame-size', '1'],
                capture_output=True, text=True, timeout=90)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('decoder archive bound', result.stderr)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [source])

    def test_short_target_write_is_an_explicit_failure(self):
        class ShortWriter:
            def write(self, data):
                return len(data) - 1
        with self.assertRaisesRegex(parent.CodecError, 'short archive write'):
            codec.encode_stream(io.BytesIO(b''), ShortWriter(), 0)


if __name__ == '__main__':
    unittest.main()
