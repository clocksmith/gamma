import copy
import unittest

from algsolve.interface_compatibility import accepts, mismatch, filter_candidates
from algsolve.lookup import Fingerprint, feature_bonus
from test_answer import context


class InterfaceTests(unittest.TestCase):
    def test_missing_features_do_not_raise_similarity(self):
        bonus = feature_bonus(Fingerprint(), Fingerprint())
        self.assertEqual(sum(bonus.values()), 0)
        self.assertEqual(feature_bonus(Fingerprint(phrases=frozenset(['sorted'])),
                                       Fingerprint(phrases=frozenset(['sorted'])))['phrases'], 1)

    def test_recursive_types_and_unknowns(self):
        self.assertTrue(accepts('List[List[int]]', [[1, 2], []]))
        self.assertFalse(accepts('List[List[int]]', [1, 2]))
        self.assertFalse(accepts('int', True))
        self.assertTrue(accepts('float', 1))
        self.assertTrue(accepts('Optional[List[int]]', None))
        self.assertTrue(accepts('int | str', 'x'))
        self.assertTrue(accepts('Unknown', {'opaque': 1}))
        self.assertTrue(accepts('List[List[int]]', []))

    def test_public_input_and_output_reject_only_incompatibilities(self):
        entry = copy.deepcopy(context().entries[0])
        entry.starter_code = 'class Solution:\n def solve(self, nums: list[int]) -> int: pass'
        self.assertIsNone(mismatch(entry, [{'args':[[2,3]],'expected':5}]))
        self.assertEqual(mismatch(entry,[{'args':[[2],3]}]), 'argument_count')
        self.assertEqual(mismatch(entry,[{'args':[[[2]]]}]), 'argument_type')
        self.assertEqual(mismatch(entry,[{'args':[[2]],'expected':True}]), 'return_type')
        self.assertIsNone(mismatch(entry,[{'args':[[2]],'expected':[2],'compare':'arg:0'}]))
        self.assertIsNone(mismatch(entry,[{'kwargs':{'renamed':[2]},'expected':True}]))

    def test_filter_never_consults_qualification_or_executes_code(self):
        ctx = context()
        candidates = [{'key':ctx.entries[0].key,'score':.8}]
        kept, rejected = filter_candidates(candidates,ctx.lookup,[{'args':[[1,2]],'expected':3}])
        self.assertEqual(kept,candidates)
        self.assertEqual(rejected,[])
        kept, rejected = filter_candidates(candidates,ctx.lookup,[{'args':['wrong']}])
        self.assertEqual(kept,[])
        self.assertEqual(rejected,[{'key':ctx.entries[0].key,'reason':'argument_type'}])


class ExactPublicInterfaceTests(unittest.TestCase):
    def test_recognition_default_exact_rule_filters_incompatible_output(self):
        from algsolve.recognition_release import public_problem
        entry = copy.deepcopy(context().entries[0])
        entry.starter_code = 'class Solution:\n def solve(self, nums: list[int]) -> int: pass'
        query = public_problem({'query': 'Return whether an input value is present.',
                                'public_examples': [{'args': [[2, 3]], 'expected': True}]})
        self.assertEqual(query.public_tests[0]['compare'], 'return:exact')
        candidates = [{'key': entry.key, 'score': .8}]
        ctx = context()
        ctx.entries[0].starter_code = entry.starter_code
        kept, rejected = filter_candidates(candidates, ctx.lookup, query.public_tests)
        self.assertEqual(kept, [])
        self.assertEqual(rejected, [{'key': entry.key, 'reason': 'return_type'}])

    def test_exact_return_checks_structure_and_preserves_numeric_equivalence(self):
        entry = copy.deepcopy(context().entries[0])
        entry.starter_code = 'class Solution:\n def solve(self, nums: list[int]) -> list[int]: pass'
        for expected, reason in [([[1]], 'return_type'), ([True], 'return_type'),
                                 ([1.0], None), ([1.5], 'return_type')]:
            with self.subTest(expected=expected):
                example = {'args': [[2]], 'expected': expected, 'compare': 'return:exact'}
                original = copy.deepcopy(example)
                self.assertEqual(mismatch(entry, [example]), reason)
                self.assertEqual(example, original)
        # Exact output equivalence must not loosen the input declaration.
        self.assertEqual(mismatch(entry, [{'args': [[2.0]], 'expected': [2],
                                          'compare': 'return:exact'}]), 'argument_type')

    def test_nonexact_and_inplace_modes_remain_inconclusive(self):
        entry = copy.deepcopy(context().entries[0])
        entry.starter_code = 'class Solution:\n def solve(self, nums: list[int]) -> int: pass'
        for mode in ('arg:0', 'return:numeric_list_tol_1e-5', 'unknown'):
            with self.subTest(mode=mode):
                self.assertIsNone(mismatch(entry, [{'args': [[2]], 'expected': [2], 'compare': mode}]))
