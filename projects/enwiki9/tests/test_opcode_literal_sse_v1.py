import hashlib
import json
import lzma
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from lib.opcode_literal_sse_v1 import install, PARENT_SHA
from opcode_field_repair_cli_v1 import Audit


def namespace(arm):
    packed = (ROOT / 'programs/opcode_field_compact_v1/p').read_bytes()
    ns = {'__name__': 'literal_sse_synthetic'}
    exec(compile(lzma.decompress(packed), '<parent>', 'exec'), ns)
    return install(ns, packed, arm)


def observer():
    path = ROOT / 'tools/opcode_field_compact_observe_v1.py'
    source = path.read_text()
    old = 'tuple(self.sse[bucket])'
    if source.count(old) != 1:
        raise ValueError('observer SSE site differs')
    source = source.replace(old, 'None if bucket not in self.sse else tuple(self.sse[bucket])')
    ns = dict(__name__='literal_sse_test_observer', __file__=str(path))
    exec(compile(source, str(path), 'exec'), ns)
    return ns['observe']


def execute(operation, data, arm, observed=True):
    ns = namespace(arm)
    capture = observer()(ns, Audit('D')) if observed else None
    out = ns[operation](data)
    return out, capture['audit'] if observed else None


class LiteralSSETests(unittest.TestCase):
    def test_only_sse_changes_on_copied_training(self):
        models = {}
        for arm in ('K', 'D'):
            ns = namespace(arm); ns['_limit'] = 20
            lit, st = ns['LIT'](), ns['GST']()
            for byte in b'abcabc':
                prefix = 1
                for index in range(8):
                    bit = (byte >> (7-index)) & 1
                    _, keys, bucket, mixed, stretches, weights = lit.predict(st, prefix, index)
                    lit.update(keys, bucket, mixed, stretches, weights, bit)
                    prefix = (prefix << 1) | bit
                st.up(byte)
            models[arm] = lit
        self.assertEqual(models['K'].tt, models['D'].tt)
        self.assertEqual(models['K'].W, models['D'].W)
        self.assertTrue(models['K'].sse)
        self.assertFalse(models['D'].sse)
        self.assertEqual(models['D'].copied_bit_updates, 48)

    def test_original_prefix_estimator(self):
        costs = {}
        for arm in ('P', 'K', 'D'):
            ns = namespace(arm)
            data = ns['oe'](b'<title>Oak</title>Oak Oak Oak\x00')
            ns['_limit'] = len(data)
            costs[arm] = ns['lit_prefix'](data)
        self.assertEqual(costs['P'], costs['K'])
        self.assertEqual(costs['P'], costs['D'])

    def test_exact_synthetic_archives_and_witnesses(self):
        fixtures = dict(empty=b'', arbitrary=bytes(range(256))+b'\0\xff<broken',
                        copies=(b'alpha beta gamma delta\n'*12+b'alpha beta delta gamma\n'*8),
                        xml=b'<title>Oakford</title><text>Oakford is a town.</text>\n'*12)
        for name, raw in fixtures.items():
            outputs = {}
            for arm in ('P', 'K', 'D'):
                with self.subTest(fixture=name, arm=arm):
                    archive, enc = execute('compress', raw, arm)
                    restored, dec = execute('decompress', archive, arm)
                    repeat, rep = execute('compress', restored, arm)
                    plain, _ = execute('compress', raw, arm, False)
                    self.assertEqual(restored, raw)
                    self.assertEqual(archive, repeat)
                    self.assertEqual(archive, plain)
                    self.assertEqual(enc, dec)
                    self.assertEqual(enc, rep)
                    outputs[arm] = archive, enc
            self.assertEqual(outputs['P'], outputs['K'])
            print(json.dumps(dict(fixture=name, raw_bytes=len(raw), archive_bytes={a:len(v[0]) for a,v in outputs.items()}, archive_sha256={a:hashlib.sha256(v[0]).hexdigest() for a,v in outputs.items()})))

    def test_bad_bindings(self):
        with self.assertRaises(ValueError): install({}, b'wrong', 'D')
        with self.assertRaises(ValueError): namespace('S')


if __name__ == '__main__':
    unittest.main()
