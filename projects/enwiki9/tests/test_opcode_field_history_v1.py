from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.opcode_field_history_v1 import namespace, execute
from lib.opcode_field_history_v1 import side_state


def state_for(arm, raw):
    ns = namespace(arm)
    ns['_limit'] = 16384
    state = ns['GST']()
    for byte in ns['oe'](raw):
        state.up(byte)
    return ns, state


class HistoryTests(unittest.TestCase):
    def test_separated_fields_and_opcode_exclusion(self):
        _, state = state_for('D', b'<title>A</title><id>1</id><title>B')
        self.assertEqual(state.histories[1], b'AB')
        self.assertEqual(state.histories[2], b'1')
        self.assertEqual(state.body_bytes, 3)
        self.assertEqual(state.entries, 3)
        self.assertEqual(state.route, 1)

    def test_global_control_and_randomized_entries(self):
        raw = b'<title>A</title><id>1</id><title>B'
        _, g = state_for('G', raw)
        self.assertEqual(g.histories, [b'A1B'] + [b''] * 6)
        _, s = state_for('S', raw)
        _, again = state_for('S', raw)
        self.assertEqual(side_state(s), side_state(again))
        self.assertNotEqual(s.histories, state_for('D', raw)[1].histories)

    def test_zero_escape_and_capacity(self):
        _, state = state_for('D', b'<title>abc\0def</title>outside')
        self.assertEqual(state.histories[1], b'def')
        self.assertEqual(state.body_bytes, 7)
        self.assertEqual(state.route, -1)
        self.assertTrue(all(len(h) <= 3 for h in state.histories))

    def test_pretruth_keys_and_bookkeeping_identity(self):
        prefix = b'<title>A</title><id>1</id><title>'
        pns, ps = state_for('P', prefix)
        kns, ks = state_for('K', prefix)
        dns, ds = state_for('D', prefix)
        p, k, d = pns['LIT'](), kns['LIT'](), dns['LIT']()
        self.assertEqual(p.keys(ps, 1), k.keys(ks, 1))
        before = side_state(ds)
        keys = d.keys(ds, 1)
        self.assertEqual(side_state(ds), before)
        self.assertEqual(keys[8:10], ((1, 1, b'A'), (1, 1, b'A')))
        self.assertEqual(keys[:8], p.keys(ps, 1)[:8])
        self.assertEqual(keys[10:], p.keys(ps, 1)[10:])
        ds.up(0)
        self.assertEqual(d.keys(ds, 1), d.__class__.__mro__[1].keys(d, ds, 1))

    def test_exact_synthetic_inverse_repeat_and_witnesses(self):
        raw = b'<title>A\0B</title><id>12</id><title>C</title>\xff\r\n<broken'
        results = {}
        for arm in ('P', 'K', 'D', 'G', 'S'):
            archive, enc = execute('encode', raw, arm)
            restored, dec = execute('decode', archive, arm)
            repeat, rep = execute('encode', restored, arm)
            plain, _ = execute('encode', raw, arm, False)
            self.assertEqual(restored, raw)
            self.assertEqual(archive, repeat)
            self.assertEqual(archive, plain)
            self.assertEqual(enc, dec)
            self.assertEqual(enc, rep)
            results[arm] = archive, enc
        self.assertEqual(results['P'][0], results['K'][0])
        self.assertEqual(results['P'][1]['parent'], results['K'][1]['parent'])


if __name__ == '__main__':
    unittest.main()
