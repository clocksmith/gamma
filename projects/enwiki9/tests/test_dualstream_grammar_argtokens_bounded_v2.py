"""Reuse the independently reported archive-cap boundary against D2GRAM02."""
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_argtokens_bounded_v2 as codec
from tools import dualstream_grammar_argtokens_v2 as parent


class ArgumentArchiveBoundTests(unittest.TestCase):
    def test_accepted_archives_and_parent_functions_are_unchanged(self):
        original = parent.encode_stream
        raw = b'<title>Oak</title><text>Oak is a town.</text>\r\n' * 5
        for mode in parent.MODES:
            self.assertEqual(codec.encode(raw, mode=mode), parent.encode(raw, mode=mode))
            self.assertEqual(codec.decode(codec.encode(raw, mode=mode)[0]), raw)
        self.assertIs(parent.encode_stream, original)

    def test_first_oversized_frame_sequence_is_not_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, target = Path(temporary)/'input', Path(temporary)/'archive'
            source.write_bytes(b'a' * 74074)
            result = subprocess.run([sys.executable,str(ROOT/'tools/dualstream_grammar_argtokens_bounded_v2.py'),
                                     'encode',str(source),str(target),'--mode','split','--frame-size','1'],
                                    capture_output=True,text=True,timeout=90)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('decoder archive bound',result.stderr)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(temporary).iterdir()),[source])

    def test_last_accepted_boundary_inverts(self):
        raw = b'a' * 74073
        archive, report = codec.encode(raw, mode='split', frame_size=1)
        self.assertEqual(len(archive),7999908)
        self.assertEqual(report['complete_archive_bytes'],len(archive))
        self.assertEqual(codec.decode(archive),raw)


if __name__ == '__main__':
    unittest.main()
