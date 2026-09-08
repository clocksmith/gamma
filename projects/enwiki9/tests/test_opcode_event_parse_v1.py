import hashlib
import json
import lzma
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from lib.opcode_event_parse_v1 import event_keys, install, PARENT_SHA
from opcode_field_compact_observe_v1 import observe
from opcode_field_repair_cli_v1 import Audit


def namespace(arm):
    packed = (ROOT / 'programs/opcode_field_compact_v1/p').read_bytes()
    if hashlib.sha256(packed).hexdigest() != PARENT_SHA:
        raise ValueError('parent changed')
    ns = {'__name__': 'event_parse_synthetic'}
    exec(compile(lzma.decompress(packed), '<parent>', 'exec'), ns)
    return install(ns, packed, arm)


def execute(operation, data, arm, observed=True):
    ns = namespace(arm)
    captured = observe(ns, Audit('D')) if observed else None
    output = ns[operation](data)
    return output, captured['audit'] if captured is not None else None


class EventParseTests(unittest.TestCase):
    def test_prebyte_contexts_and_parent_decoder_preservation(self):
        ns = namespace('D')
        data = ns['oe'](b'<title>A</title><id>12</id>[[X]]\0\xff')
        ns['_limit'] = len(data)
        state, expected = ns['GST'](), []
        for byte in data:
            expected.append((state.f, state.w, state.pg, state.c))
            state.up(byte)
        self.assertEqual(event_keys(ns['GST'], data), expected)
        parent = namespace('P')
        for name in ('decompress', 'decompress_inner'):
            self.assertEqual(ns[name].__code__.co_code, parent[name].__code__.co_code)

    def test_synthetic_inverse_repeat_and_complete_witnesses(self):
        fixtures = {
            'empty': b'',
            'arbitrary': bytes(range(256)) + b'\0\xff\r\n<broken',
            'repetition': b'abcabcabcabc\n' * 16,
            'fields': b'<title>Oakford</title><text>Oakford is a town.</text>\n' * 12,
        }
        for name, raw in fixtures.items():
            with self.subTest(fixture=name):
                results = {}
                for arm in ('P', 'K', 'D'):
                    archive, enc = execute('compress', raw, arm)
                    restored, dec = execute('decompress', archive, 'P')
                    repeat, rep = execute('compress', restored, arm)
                    plain, _ = execute('compress', raw, arm, False)
                    self.assertEqual(restored, raw)
                    self.assertEqual(archive, repeat)
                    self.assertEqual(archive, plain)
                    self.assertEqual(enc, dec)
                    self.assertEqual(enc, rep)
                    results[arm] = archive, enc
                self.assertEqual(results['P'], results['K'])
                print(json.dumps({'fixture': name, 'raw_bytes': len(raw),
                                  'archives': {a: len(v[0]) for a, v in results.items()},
                                  'sha256': {a: hashlib.sha256(v[0]).hexdigest() for a, v in results.items()}}))

    def test_bad_arm_and_parent_rejected(self):
        with self.assertRaises(ValueError):
            namespace('S')
        with self.assertRaises(ValueError):
            install({}, b'wrong parent', 'D')


if __name__ == '__main__':
    unittest.main()
