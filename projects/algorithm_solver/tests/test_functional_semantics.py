import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from algsolve import test_corrections
from algsolve.judge import judge
from algsolve.judge.functional_semantics import topological_order


class FunctionalSemanticsTests(unittest.TestCase):
    def test_multiple_valid_orders_duplicates_missing_vertices_and_wrong_edges(self):
        args = [4, [[1,0], [2,0], [3,1], [3,2]]]
        for valid in [[0,1,2,3], [0,2,1,3]]:
            self.assertTrue(topological_order(args, valid))
        for invalid in [[], [0,1,1,3], [0,1,2], [1,0,2,3], [0,1,3,2], [False,1,2,3]]:
            self.assertFalse(topological_order(args, invalid))
        self.assertTrue(topological_order([2, [[0,1], [1,0]]], []))
        self.assertFalse(topological_order([2, [[0,1], [1,0]]], [0,1]))
        self.assertTrue(topological_order([0, []], []))

    def test_semantic_comparison_requires_result_and_does_not_trust_expected_order(self):
        test = judge.FunctionalTest(args=[3, [[1,0], [2,0]]], expected=[0,2,1], validator='topological_order')
        self.assertTrue(judge._matches(test, {'result': [0,1,2]}))
        self.assertFalse(judge._matches(test, {'args_after': [0,1,2]}))
        self.assertFalse(judge._matches(test, {'result': [2,0,1]}))
        self.assertFalse(judge._matches(test, {'error': 'broken', 'result': [0,1,2]}))

    def test_invalid_test_contract_fails_before_sandbox_dispatch(self):
        for test in [judge.FunctionalTest(args=[2, [[2,0]]], validator='topological_order'),
                     judge.FunctionalTest(args=[2, []], validator='invented')]:
            with patch.object(judge.sandbox, 'run_python', side_effect=AssertionError('dispatched')):
                verdict = judge.judge_functional('', {}, [test])
            self.assertFalse(verdict.passed)
            self.assertEqual(verdict.reason, judge.CHECKER_ERROR)

    def test_correction_preserves_raw_cases_and_expected_outputs_and_rejects_drift(self):
        case = {'args': [['a','b','e'], [[0,3]]], 'expected': [2], 'compare': 'return'}
        sha = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
        problem = SimpleNamespace(uid='lcd:2559', slug='count-vowel-strings-in-ranges')
        with patch.object(test_corrections, 'VOWEL_RANGE_CORRECTIONS', {0: (sha, 0)}):
            repaired = test_corrections.apply(problem, [case])
            self.assertEqual(case['args'][1], [[0,3]])
            self.assertEqual(repaired[0]['args'][1], [[0,2]])
            self.assertEqual(repaired[0]['expected'], case['expected'])
            with self.assertRaises(ValueError):
                test_corrections.apply(problem, repaired)
        wrong = dict(case, expected=[3])
        sha = hashlib.sha256(json.dumps(wrong, sort_keys=True).encode()).hexdigest()
        with patch.object(test_corrections, 'VOWEL_RANGE_CORRECTIONS', {0: (sha, 0)}):
            with self.assertRaisesRegex(ValueError, 'oracle'):
                test_corrections.apply(problem, [wrong])


if __name__ == '__main__':
    unittest.main()
