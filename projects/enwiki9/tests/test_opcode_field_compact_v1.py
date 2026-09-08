"""Synthetic equivalence and corruption checks, with no corpus reads."""
import hashlib
import importlib.util
import lzma
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import opcode_field_compact_build_v1 as build
import opcode_field_compact_observe_v1 as witness
from opcode_field_repair_cli_v1 import Audit


FIXTURES = {
    'empty': b'',
    'one': b'x',
    'arbitrary': bytes(range(256)) * 3,
    'escaped-zero': b'\0\xff\0\x0f<id>27</id>\0' * 32,
    'all-fields': (b'<page><title>Oakford</title><id>123</id>'
                   b'<timestamp>2004-01-01</timestamp><username>Case</username>'
                   b'<comment>  preserve &amp; CR\r\n</comment>'
                   b'<text xml:space="preserve">Oakford is a town.</text></page>\n') * 24,
    'copies': b'<title>Repeated</title>\n' + b'abcdefgh abcdefgh\n' * 128,
    'malformed-xml': b'<text x="<title>">\xff\xc0\r\n<id>not-normalized &amp; <broken' * 24,
}


class CompactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='compact-unit-')
        cls.path = Path(cls.tmp.name)
        cls.files = build.bundle()
        for name, data in cls.files.items():
            (cls.path / name).write_bytes(data)
        cls.compact = witness.load(cls.path / 'program.py')
        spec = importlib.util.spec_from_file_location('confirmed_field_reference', build.PARENT/'field_codec.py')
        cls.parent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.parent)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_fixture_archives_and_complete_witnesses(self):
        for name, raw in FIXTURES.items():
            with self.subTest(name=name):
                old, report = self.parent.encode(raw, 'D', candidate_root=build.PARENT, audit=Audit('D'))
                plain = self.compact.compress(raw)
                encoded, enc = witness.execute(self.compact, 'encode', raw)
                decoded, dec = witness.execute(self.compact, 'decode', encoded)
                repeated, rep = witness.execute(self.compact, 'encode', decoded)
                self.assertEqual(old, plain)
                self.assertEqual(plain, encoded)
                self.assertEqual(encoded, repeated)
                self.assertEqual(raw, decoded)
                self.assertEqual(raw, self.compact.decompress(plain))
                self.assertEqual(report['audit'], enc)
                self.assertEqual(enc, dec)
                self.assertEqual(dec, rep)

    def test_packed_source_is_exact_and_build_repeats(self):
        self.assertEqual(build.bundle(), self.files)
        self.assertEqual(lzma.decompress(self.files['p']), build.source())
        self.assertLess(sum(map(len, self.files.values())), 15403)
        self.assertEqual(set(self.files), {'p', 'program.py'})

    def test_relocated_loader_needs_only_counted_files(self):
        relocated = self.path / 'relocated'
        relocated.mkdir()
        for name, data in self.files.items():
            (relocated / name).write_bytes(data)
        mod = witness.load(relocated/'program.py')
        raw = FIXTURES['escaped-zero']
        archive = mod.compress(raw)
        self.assertEqual(archive, self.compact.compress(raw))
        self.assertEqual(mod.decompress(archive), raw)

    def test_missing_required_file_rejected(self):
        missing = self.path / 'missing'
        missing.mkdir()
        (missing/'program.py').write_bytes(self.files['program.py'])
        with self.assertRaises(FileNotFoundError):
            witness.load(missing/'program.py')

    def test_declared_length_and_payload_guards(self):
        raw = FIXTURES['copies']
        archive = self.compact.compress(raw)
        bad = [b'', archive[:8], archive[:-3], archive+b'\0',
               struct.pack('>II', 1000001, 1)+archive[8:],
               struct.pack('>II', 1, 3)+archive[8:],
               struct.pack('>II', len(raw)+1, struct.unpack('>II',archive[:8])[1])+archive[8:]]
        for value in bad:
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                self.compact.decompress(value)
        with self.assertRaises(ValueError):
            self.compact.compress(b'x'*1000001)

    def test_field_protocol_and_invalid_opcodes(self):
        ns = self.compact.namespace()
        field = ns['Field']()
        for byte in [0,15]:field.up(byte)
        self.assertEqual(field.f,1)
        for byte in [0,255,15]:field.up(byte)
        self.assertEqual((field.f,field.pending),(1,False))
        for byte in [0,16]:field.up(byte)
        self.assertEqual(field.f,0)
        field.up(0)
        with self.assertRaises(ValueError):field.up(0)

    def test_fresh_namespace_does_not_inherit_state(self):
        raw = b'<title>A</title><id>32</id>'
        first = self.compact.compress(raw)
        self.compact.compress(FIXTURES['all-fields'])
        self.assertEqual(first,self.compact.compress(raw))


if __name__ == '__main__':
    unittest.main(verbosity=2)
