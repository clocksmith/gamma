import time
import unittest
from types import SimpleNamespace

from algsolve.synth import typed_program as ir
from algsolve.synth.typed_base_search import search
from algsolve.synth.bits_pilot import EvaluationReader, PoolReader


class BaseSearchTests(unittest.TestCase):
    def test_finds_a_public_consistent_fold_and_validates_it(self):
        result = search([['nums', 'List[int]']], 'int', [{'args': [[1, 2, 3]], 'expected': 6}, {'args': [[5]], 'expected': 5}],
                        deadline=time.perf_counter() + 2)
        self.assertEqual(result['reason'], 'public_consistent')
        self.assertEqual(ir.execute(result['graph'], {'nums': [4, 4]}), 8)
        self.assertGreater(result['candidates'], 0)

    def test_unsupported_signature_stays_in_the_denominator(self):
        result = search([['s', 'str']], 'int', [{'args': ['ab'], 'expected': 2}], deadline=time.perf_counter() + 2)
        self.assertEqual(result['reason'], 'unsupported_signature')
        self.assertIsNone(result['graph'])

    def test_expired_deadline_stops_before_any_candidate(self):
        result = search([['a', 'int']], 'int', [{'args': [1], 'expected': 1}], deadline=time.perf_counter() - 1)
        self.assertEqual((result['reason'], result['candidates']), ('search_budget', 0))


class EvaluationReaderTests(unittest.TestCase):
    def test_requires_authorization_and_seal_before_independent_tests(self):
        plan = {'rows': [{'uid': 'u', 'split': 'heldout_family', 'key': 'lc:u'}]}
        with self.assertRaises(PermissionError):
            EvaluationReader(SimpleNamespace(), plan, {'authorized': False})
        reader = EvaluationReader(SimpleNamespace(), plan, {'authorized': True})
        with self.assertRaises(PermissionError):
            reader.independent_tests('u')


class PoolReaderTests(unittest.TestCase):
    def test_refuses_an_unfrozen_pool_or_missing_authorization(self):
        pool = {'status': 'draft_not_frozen', 'rows': [{'uid': 'lcd:1'}]}
        with self.assertRaises(PermissionError):
            PoolReader(SimpleNamespace(dataset_path='/nonexistent'), pool, {'authorized': True})
        with self.assertRaises(PermissionError):
            PoolReader(SimpleNamespace(dataset_path='/nonexistent'), dict(pool, status='frozen', frozen_by='owner'), {'authorized': False})


if __name__ == '__main__':
    unittest.main()
