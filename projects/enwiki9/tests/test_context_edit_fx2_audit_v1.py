import struct
import unittest
from lib.context_edit_fixture_v1 import Fixture
from tools.context_edit_fx2_audit_v1 import Adapter, evaluate


class AdapterTest(unittest.TestCase):
    def test_unchanged_fixture_prediction_and_state_parity(self):
        donor = b'0123456789abcdefghijklmnopqrstuv'
        raw = b'ABCDEFGH' + donor + bytes(range(128, 168)) + b'ABCDEFGH!' + donor[:-1]
        fixtures = {a: Fixture(a) for a in ('P', 'K', 'L', 'D', 'S')}
        adapter = Adapter()
        for value in raw:
            for bit in range(7, -1, -1):
                expected = {a: f.predict() for a, f in fixtures.items()}
                self.assertEqual(adapter.predict(expected['P']), expected)
                truth = (value >> bit) & 1
                for f in fixtures.values():
                    f.update(truth)
                adapter.observe(truth)
            snapshot = adapter.expert.snapshot()
            snapshot['frontend'] = 'synthetic-raw-byte-v1'
            self.assertEqual(snapshot, fixtures['P'].expert.snapshot())
            self.assertEqual({a: vars(m) for a, m in adapter.mixtures.items()},
                             {a: vars(m) for a, m in fixtures['P'].mixtures.items()})

    def test_order_and_invalid_truth(self):
        a = Adapter()
        with self.assertRaises(ValueError): a.observe(0)
        with self.assertRaises(ValueError): a.predict(65536)
        a.predict(32768)
        with self.assertRaises(ValueError): a.predict(32768)
        with self.assertRaises(ValueError): a.observe(2)
        a.observe(0)

    def test_coordinates_and_no_opportunity(self):
        raw = b'ab'
        rows = b''.join(struct.pack('<7I', 0, 32768, 0, 0, 0, 0, (v >> b) & 1)
                        for v in raw for b in range(7, -1, -1))
        report = evaluate(raw, rows)
        self.assertTrue(report['P_K_identity'])
        self.assertFalse(report['diagnostic_predicate_passed'])
        self.assertEqual(report['triggers'], 0)
        self.assertEqual(report['ideal_saved_bits']['D'], 0)
        with self.assertRaises(ValueError): evaluate(raw, rows[:-1])
        with self.assertRaises(ValueError): evaluate(b'xb', rows)


if __name__ == '__main__':
    unittest.main()
