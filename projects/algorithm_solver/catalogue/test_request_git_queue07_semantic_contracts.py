"""Source-free acceptance tests for the two narrowly assigned semantic owners."""
import copy
import itertools
import unittest
from . import imported_result_contracts as execution
from . import verify_imported_semantics as replay
from .test_request_git_queue07_semantic_oracles import enumerate_legal, tiny_inputs

OWNERS = (execution, replay)


def accepted(owner, pid, args, answer, expected=None):
    if owner is execution:
        return owner.semantic_value(pid, args, answer, expected)
    return owner.result_valid(pid, args, answer, expected)


def observation(args, answer, language):
    return {'result': copy.deepcopy(answer), 'result_type': 'list' if language == 'python' else 'object',
            'args_before': copy.deepcopy(args), 'args_after': copy.deepcopy(args), 'alias_edges': []}


class SemanticOwnerTests(unittest.TestCase):
    def test_every_small_subsequence_against_independent_subset_enumeration(self):
        for pid in (2900, 2901):
            for args in tiny_inputs(pid):
                legal = enumerate_legal(pid, args); optimum = max(map(len, legal))
                best = {tuple(answer) for answer in legal if len(answer) == optimum}
                words = args[0]
                for size in range(len(words) + 1):
                    for answer in itertools.combinations(words, size):
                        for owner in OWNERS:
                            self.assertEqual(accepted(owner, pid, args, list(answer), []), answer in best)

    def test_both_optimum_ties_and_nonunique_expected_are_accepted(self):
        for pid, args, choices in (
            (2900, [['e', 'a', 'b'], [0, 0, 1]], [['e', 'b'], ['a', 'b']]),
            (2901, [['bab', 'dab', 'cab'], [1, 2, 2]], [['bab', 'dab'], ['bab', 'cab']])):
            for owner in OWNERS:
                for answer in choices:
                    for language in ('javascript', 'python'):
                        case = {'args': args, 'expected': choices[0]}
                        self.assertIsNone(owner.compare(pid, case, observation(args, answer, language), language))
                    self.assertTrue(accepted(owner, pid, args, answer, ['invented']))
                self.assertFalse(accepted(owner, pid, args, choices[0][:1], choices[0][:1]))

    def test_witness_type_membership_order_and_duplicates(self):
        for pid, args in ((2900, [['aa', 'ab', 'bb'], [0, 1, 0]]),
                          (2901, [['aa', 'ab', 'bb'], [1, 2, 1]])):
            for answer in ([], ['aa'], ['aa', 'aa', 'bb'], ['bb', 'ab', 'aa'], ['aa', 'zz', 'bb'],
                           [0, 1, 2], [True], ('aa', 'ab', 'bb'), 'aa', {'0': 'aa'}, [['aa']]):
                for owner in OWNERS: self.assertFalse(accepted(owner, pid, args, answer, answer))

    def test_2901_all_adjacency_constraints_and_2900_no_hamming_rule(self):
        mutants = [([['a', 'ab'], [1, 2]], ['a', 'ab']),
                   ([['aa', 'ab'], [1, 1]], ['aa', 'ab']),
                   ([['aa', 'bb'], [1, 2]], ['aa', 'bb']),
                   ([['aa', 'ab'], [1, 2]], ['aa', 'aa'])]
        for owner in OWNERS:
            for args, answer in mutants: self.assertFalse(accepted(owner, 2901, args, answer, answer))
            args = [['z', 'abc', 'yy'], [0, 1, 0]]
            self.assertTrue(accepted(owner, 2900, args, args[0], []))

    def test_input_domain_types_and_duplicate_words_rejected(self):
        for pid in (2900, 2901):
            for args in (None, (), [], [['a']], [['a'], [1], 1], [['a'], [True]], [['a'], [1.0]],
                         [['a', 'a'], [1, 1]], [['A'], [1]], [['é'], [1]], [['a' * 11], [1]],
                         [[True], [1]], [('a',), [1]], [['a'], (1,)], [['a', 'b'], [1]]):
                for owner in OWNERS: self.assertFalse(accepted(owner, pid, args, ['a'], ['a']))
        for owner in OWNERS:
            self.assertFalse(accepted(owner, 2900, [['a'], [2]], ['a']))
            self.assertFalse(accepted(owner, 2901, [['a'], [0]], ['a']))
            self.assertFalse(accepted(owner, 2901, [['a'], [2]], ['a']))

    def test_language_type_effects_and_mutable_alias_failures(self):
        for pid, groups in ((2900, [0, 1]), (2901, [1, 2])):
            args = [['a', 'b'], groups]; case = {'args': args, 'expected': ['a', 'b']}
            for owner in OWNERS:
                for language in ('javascript', 'python'):
                    record = observation(args, ['a', 'b'], language)
                    self.assertIsNone(owner.compare(pid, case, record, language))
                    for field in ('args_before', 'args_after'):
                        bad = copy.deepcopy(record); bad[field][1][0] = True
                        self.assertEqual(owner.compare(pid, case, bad, language), 'input_effects')
                    bad = copy.deepcopy(record); bad['alias_edges'] = [['result', 'args.0']]
                    self.assertEqual(owner.compare(pid, case, bad, language), 'return_aliases')
                    bad = copy.deepcopy(record); bad['result_type'] = 'tuple'
                    self.assertEqual(owner.compare(pid, case, bad, language), 'result_type')
                    bad = copy.deepcopy(record); bad['error'] = 'failed'
                    self.assertEqual(owner.compare(pid, case, bad, language), 'candidate_error')

    def test_explicit_helper_identity_allowlists(self):
        args = [['a'], [1]]
        for pid in (True, 2900.0, '2900', 2899, 2902, None):
            self.assertFalse(execution.unequal_group_witness(pid, args, ['a']))
            self.assertFalse(replay.alternating_word_witness(pid, args, ['a']))

    def test_ordinary_fallback_and_existing_semantic_contracts_unchanged(self):
        for owner in OWNERS:
            self.assertTrue(accepted(owner, 1, [3], 7, 7))
            self.assertFalse(accepted(owner, 1, [3], True, 1))
            self.assertTrue(accepted(owner, 1606, [], [2, 1], [1, 2]))
            self.assertFalse(accepted(owner, 1606, [], [1, 1, 2], [1, 2]))
            self.assertTrue(accepted(owner, 767, ['aab'], 'aba', 'aba'))
            self.assertFalse(accepted(owner, 767, ['aab'], 'aab', 'aba'))

    def test_repeated_calls_do_not_retain_state(self):
        for owner in OWNERS:
            for _ in range(4):
                self.assertTrue(accepted(owner, 2901, [['aa', 'ab', 'bb'], [1, 2, 1]], ['aa', 'ab', 'bb']))
                self.assertFalse(accepted(owner, 2901, [['aa', 'ab', 'bb'], [1, 1, 1]], ['aa', 'ab', 'bb']))
                self.assertTrue(accepted(owner, 2901, [['aa', 'ab', 'bb'], [1, 1, 1]], ['bb']))


if __name__ == '__main__': unittest.main()
