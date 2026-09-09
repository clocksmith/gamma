"""Synthetic observation tests; no corpus or retained archive execution."""
from pathlib import Path
import unittest

from tools.opcode_event_opportunity_observe_v1 import execute, namespace, observe_events
from tools.opcode_field_compact_observe_v1 import observe
from tools.opcode_field_repair_cli_v1 import Audit


ROOT = Path(__file__).resolve().parents[1]


class EventOpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = (ROOT / 'programs/opcode_field_compact_v1/p').read_bytes()

    def test_synthetic_inverse_repeat_records_and_parent_identity(self):
        fixtures = (b'', bytes(range(32)) + b'\xff', b'abcabcabcabc\n' * 8,
                    b'<title>Oak</title><text>Oak is a tree.</text>\n' * 4)
        seen = set()
        for raw in fixtures:
            with self.subTest(raw_bytes=len(raw)):
                parent, parent_audit = execute(self.parent, 'encode', raw)
                records = []
                archive, audit = execute(self.parent, 'encode', raw,
                                         emit=records.append, max_events=2048)
                decoded_records = []
                restored, decode_audit = execute(self.parent, 'decode', archive,
                                                 emit=decoded_records.append, max_events=2048)
                repeated_records = []
                repeat, repeat_audit = execute(self.parent, 'encode', restored,
                                               emit=repeated_records.append, max_events=2048)
                self.assertEqual(restored, raw)
                self.assertEqual(parent, archive)
                self.assertEqual(archive, repeat)
                self.assertEqual(parent_audit, audit)
                self.assertEqual(audit, decode_audit)
                self.assertEqual(audit, repeat_audit)
                self.assertEqual(records, decoded_records)
                self.assertEqual(records, repeated_records)
                if not raw:
                    self.assertEqual(records, [])
                for i, record in enumerate(records):
                    self.assertEqual(record['index'], i)
                    self.assertEqual(record['previous_event'], None if i == 0 else records[i-1]['event'])
                    self.assertEqual(sum(record['pre_counts']), record['pre_total'])
                    self.assertEqual(sum(record['post_counts']), record['post_total'])
                    self.assertEqual(record['post_total'], record['pre_total'] + 1)
                    expected = list(record['pre_counts'])
                    expected[record['event']] += 1
                    self.assertEqual(tuple(expected), record['post_counts'])
                    seen.add(record['event'])
        self.assertIn(0, seen)
        self.assertTrue(seen & {1, 2}, 'fixture must exercise actual copies')

    def test_cost_queries_do_not_advance_observer_or_add_ev_calls(self):
        ns = namespace(self.parent)
        observe(ns, Audit('D'))
        base = ns['TOK']
        calls = []

        class CountCalls(base):
            def ev(self, state):
                calls.append(1)
                return super().ev(state)

        ns['TOK'] = CountCalls
        records = []
        observe_events(ns, records.append, max_events=3)
        tok, state, coder = ns['TOK'](), ns['GST'](), ns['AC']()
        for _ in range(7):
            tok.evc(state, 0)
        self.assertEqual(len(calls), 7)
        self.assertEqual(records, [])
        self.assertEqual(tok.e[(0, 0, 0, 0)].c, [1, 1, 1])
        tok.eve(coder, state, 1)
        self.assertEqual(len(calls), 8)
        for _ in range(9):
            tok.evc(state, 2)
        tok.eve(coder, state, 0)
        self.assertEqual(len(calls), 18)
        self.assertEqual([r['previous_event'] for r in records], [None, 1])
        self.assertEqual([r['pre_counts'] for r in records], [(1, 1, 1), (1, 2, 1)])
        other = ns['TOK']()
        other.eve(coder, state, 2)
        self.assertEqual(records[-1]['index'], 0)
        self.assertIsNone(records[-1]['previous_event'])
        self.assertEqual(set(vars(tok)), {'e', 'rl', 'rd', 'clv', 'cix', 'cln', 'last'})

    def test_rescaling_records_exact_parent_update(self):
        ns = namespace(self.parent)
        records = []
        observe_events(ns, records.append, max_events=1)
        tok, state = ns['TOK'](), ns['GST']()
        model = tok.ev(state)
        model.c, model.t = [4094, 1, 1], 4096
        tok.eve(ns['AC'](), state, 0)
        self.assertEqual(records[0]['pre_counts'], (4094, 1, 1))
        self.assertEqual(records[0]['pre_total'], 4096)
        self.assertEqual(records[0]['post_counts'], (2048, 1, 1))
        self.assertEqual(records[0]['post_total'], 2050)

    def test_source_mismatch_and_observation_bounds(self):
        for packed in (b'wrong parent', self.parent[:-1] + bytes((self.parent[-1] ^ 1,))):
            with self.assertRaisesRegex(ValueError, 'parent differs'):
                execute(packed, 'encode', b'')
        with self.assertRaisesRegex(ValueError, 'unknown'):
            execute(self.parent, 'other', b'')
        for bound in (-1, True, 1.0):
            with self.assertRaisesRegex(ValueError, 'invalid'):
                observe_events(namespace(self.parent), lambda row: None, max_events=bound)
        ns, records = namespace(self.parent), []
        observe_events(ns, records.append, max_events=0)
        tok, state, coder = ns['TOK'](), ns['GST'](), ns['AC']()
        before = vars(coder).copy()
        with self.assertRaisesRegex(ValueError, 'bound exceeded'):
            tok.eve(coder, state, 0)
        self.assertEqual(tok.e, {})
        self.assertEqual(vars(coder), before)
        self.assertEqual(records, [])


if __name__ == '__main__':
    unittest.main()
