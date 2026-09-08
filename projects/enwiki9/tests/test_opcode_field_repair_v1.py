"""Synthetic inversion, prefix causality and noninterference checks."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT/'programs/opcode_field_repair250k_q0_v1'
spec = importlib.util.spec_from_file_location('field_codec_test', CANDIDATE/'field_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
sys.path.insert(0, str(ROOT))
from tools.opcode_field_repair_cli_v1 import Audit


class CodecTests(unittest.TestCase):
    def test_complete_pairs_and_escaped_zero(self):
        f = codec.Field()
        for byte, expected in [(0,0),(15,1),(120,1),(0,1),(16,0),(0,0),(255,0),(15,0)]:
            f.up(byte)
            self.assertEqual(f.f, expected)
        self.assertFalse(f.pending)

    def test_six_routes_and_unrecognized_opcode(self):
        for opening, closing, expected in [(15,16,1),(17,18,2),(9,10,3),(11,12,4),(13,14,5),(1,2,6)]:
            f = codec.Field()
            for b in (0,opening): f.up(b)
            self.assertEqual(f.f,expected)
            for b in (0,closing): f.up(b)
            self.assertEqual(f.f,0)
        f = codec.Field();f.up(0)
        with self.assertRaisesRegex(ValueError,'unknown opcode'):f.up(40)

    def test_only_field_changes_in_byte_state(self):
        raw = b'<title>List of A</title><text xml:space="preserve">{{cite|title=x}}[[Category:Z]]</text>\0\x0f'
        parent = codec.untouched(CANDIDATE)
        modeled = parent['oe'](raw)
        base = parent['GST']()
        altered,_ = codec.private(CANDIDATE,'D',len(modeled))
        d = altered['GST']()
        differences = 0
        for b in modeled:
            base.up(b);d.up(b)
            for key,value in base.__dict__.items():
                if key != 'f':self.assertEqual(getattr(d,key),value,key)
            differences += base.f != d.f
        self.assertGreater(differences,0)

    def test_exact_inverses_and_full_shared_witnesses(self):
        fixtures = [b'',bytes(range(256)),b'<title>x</title>\0\x0f',
                    b'<broken a="&amp;">\xff\xfe\r\n\t  Mixed CASE',
                    (b'<page><title>Oakford</title><id>42</id><text xml:space="preserve">Oakford is a town.</text></page>\n')*12]
        for raw in fixtures:
            with self.subTest(bytes=len(raw)):
                original = codec.untouched(CANDIDATE)['compress'](raw)
                rows = {}
                for arm in 'PKD':
                    archive, enc = codec.encode(raw,arm,candidate_root=CANDIDATE,audit=Audit(arm))
                    restored, dec = codec.decode(archive,arm,candidate_root=CANDIDATE,audit=Audit(arm))
                    repeat, rep = codec.encode(restored,arm,candidate_root=CANDIDATE,audit=Audit(arm))
                    self.assertEqual(raw,restored)
                    self.assertEqual(archive,repeat)
                    self.assertEqual(enc,dec)
                    self.assertEqual(enc,rep)
                    rows[arm]=(archive,enc)
                self.assertEqual(rows['P'][0],original)
                self.assertEqual(rows['P'][0],rows['K'][0])
                self.assertEqual(rows['P'][1]['audit'],rows['K'][1]['audit'])

    def test_trailing_truncated_and_length_bombs(self):
        archive,_=codec.encode(b'<title>foo</title>'*4,candidate_root=CANDIDATE)
        invalid=[b'',archive+b'\0',archive[:-1],struct.pack('>II',1000001,2)+archive[8:],
                 struct.pack('>II',1,3000000)+archive[8:]]
        for bad in invalid:
            with self.subTest(length=len(bad)):
                with self.assertRaises(ValueError):codec.decode(bad,candidate_root=CANDIDATE)

    def test_each_operation_constructs_fresh_models(self):
        raw=b'<title>x</title><id>123</id>'
        p,_=codec.encode(raw,'P',candidate_root=CANDIDATE)
        codec.encode(raw*2,'D',candidate_root=CANDIDATE)
        again,_=codec.encode(raw,'P',candidate_root=CANDIDATE)
        self.assertEqual(p,again)


if __name__ == '__main__':
    unittest.main()
