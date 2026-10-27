"""Source-free controls for nonunique word witnesses and independent optima."""
import copy
import itertools
import unittest
from . import request_git_queue07_semantic_oracles as o


def enumerate_legal(pid, args):
    words, groups = args
    answers = []
    for length in range(1, len(words) + 1):
        for chosen in itertools.combinations(range(len(words)), length):
            okay = True
            for a, b in zip(chosen, chosen[1:]):
                if groups[a] == groups[b]: okay = False
                if pid == 2901:
                    if len(words[a]) != len(words[b]): okay = False
                    elif len([k for k in range(len(words[a])) if words[a][k] != words[b][k]]) != 1: okay = False
            if okay: answers.append([words[i] for i in chosen])
    return answers


def tiny_inputs(pid):
    for n in range(1, 5):
        for words in itertools.permutations(('a', 'b', 'aa', 'ab'), n):
            for groups in itertools.product((0, 1) if pid == 2900 else range(1, min(n, 2) + 1), repeat=n):
                yield [list(words), list(groups)]


class OracleTests(unittest.TestCase):
    def test_current_official_tied_examples(self):
        for pid, args, choices in (
            (2900, [['e', 'a', 'b'], [0, 0, 1]], [['e', 'b'], ['a', 'b']]),
            (2901, [['bab', 'dab', 'cab'], [1, 2, 2]], [['bab', 'dab'], ['bab', 'cab']])):
            self.assertEqual(o.optimum_length(pid, args), 2)
            for choice in choices: self.assertTrue(o.legal_witness(pid, args, choice))
        self.assertEqual(o.reference(2900, [['z', 'abc', 'yy'], [0, 1, 0]]), ['z', 'abc', 'yy'])

    def test_independent_subset_enumeration_controls_every_small_input(self):
        for pid in o.IDS:
            for args in tiny_inputs(pid):
                optimum = max(map(len, enumerate_legal(pid, args)))
                self.assertEqual(o.optimum_length(pid, args), optimum)
                self.assertEqual(o.exhaustive_optimum(pid, args), optimum)
                answer = o.reference(pid, args)
                self.assertEqual(len(answer), optimum)
                self.assertTrue(o.legal_witness(pid, args, answer))

    def test_longer_binary_runs_against_exhaustive_subsets(self):
        for n in range(5, 9):
            for groups in itertools.product((0, 1), repeat=n):
                args = [list('abcdefgh'[:n]), list(groups)]
                self.assertEqual(o.optimum_length(2900, args), 1 + sum(a != b for a, b in zip(groups, groups[1:])))
                self.assertEqual(len(o.reference(2900, args)), o.exhaustive_optimum(2900, args))

    def test_complete_exact_domain_rejections(self):
        shared = [(), [], [['a']], [['a'], [1], 1], [[], []], [['a', 'a'], [1, 1]],
                  [['A'], [1]], [['é'], [1]], [['a1'], [1]], [['a' * 11], [1]],
                  [[1], [1]], [['a'], [True]], [['a'], [1.0]], [('a',), [1]],
                  [['a'], (1,)], [['a', 'b'], [1]], [['a'], ['1']]]
        for pid in o.IDS:
            for args in shared:
                with self.subTest(pid=pid, args=args), self.assertRaises(ValueError): o.validate(pid, args)
        for pid, args in ((2900, [o.gray_words(101), [0] * 101]), (2900, [['a'], [2]]),
                          (2901, [['a'], [0]]), (2901, [['a'], [2]]),
                          (2901, [o.gray_words(1000) + ['z'], [1] * 1001])):
            with self.assertRaises(ValueError): o.validate(pid, args)

    def test_maximum_shapes_and_boundaries(self):
        for pid, n, start in ((2900, 100, 0), (2901, 1000, 1)):
            words = o.gray_words(n); args = [words, [start + i % 2 for i in range(n)]]
            self.assertEqual(o.optimum_length(pid, args), n)
            self.assertEqual(o.reference(pid, args), words)
            self.assertEqual(o.optimum_length(pid, [words, [start] * n]), 1)
        with self.assertRaises(ValueError): o.exhaustive_optimum(2901, [o.gray_words(13), [1] * 13])

    def test_reference_preserves_inputs_and_allocates_container(self):
        for pid, groups in ((2900, [0, 1, 0]), (2901, [1, 2, 1])):
            args = [['aa', 'ab', 'bb'], groups]; before = copy.deepcopy(args)
            answer = o.reference(pid, args)
            self.assertEqual(args, before); self.assertIs(type(answer), list)
            self.assertIsNot(answer, args[0]); self.assertTrue(all(type(word) is str for word in answer))

    def test_legality_is_separate_from_optimum(self):
        for pid, groups in ((2900, [0, 1, 0]), (2901, [1, 2, 1])):
            args = [['aa', 'ab', 'bb'], groups]
            self.assertTrue(o.legal_witness(pid, args, ['aa'])); self.assertEqual(o.optimum_length(pid, args), 3)
            for answer in ([], ['aa', 'aa'], ['bb', 'aa'], ['zz'], [0, 1], [True], ('aa',), {'0': 'aa'}):
                self.assertFalse(o.legal_witness(pid, args, answer))

    def test_unknown_policy_identity_and_definition_fail_closed(self):
        for pid, policy in ((2902, 'problem:2902'), ('2900', 'problem:2900'), (2900.0, 'problem:2900'),
                            (True, 'problem:2900'), (2900, 'exact'), (2900, 'problem:2901'),
                            (2900, 'problem:02900'), (2900, 'problem:2900:extra')):
            with self.assertRaises(ValueError): o.require_policy(pid, policy)
        for pid in o.IDS:
            with self.assertRaises(ValueError): o.build_cases(pid, b'wrong official definition')

    def artifact(self):
        cases = [{'args': [['bab', 'dab', 'cab'], [1, 2, 2]], 'expected': ['bab', 'cab']}]
        return cases, o.build_optimum_artifact(2901, cases, 'problem:2901')

    def check(self, cases, artifact, **overrides):
        cb, ab = o.encoded(cases), o.encoded(artifact)
        options = {'cases_sha256': o.sha(cb), 'optimum_sha256': o.sha(ab)}; options.update(overrides)
        return o.validate_optimum_artifact(2901, 'problem:2901', cb, ab, **options)

    def test_optimum_artifact_round_trip_and_alternative_witness(self):
        cases, artifact = self.artifact(); self.assertEqual(self.check(cases, artifact), cases)
        cases[0]['expected'] = ['bab', 'dab']; alternate = o.build_optimum_artifact(2901, cases, 'problem:2901')
        self.assertNotEqual(artifact['cases_sha256'], alternate['cases_sha256'])
        self.assertEqual(artifact['rows'], alternate['rows']); self.assertEqual(self.check(cases, alternate), cases)

    def test_artifact_pins_schema_and_recomputed_optimum_are_mandatory(self):
        cases, artifact = self.artifact()
        for options in ({'cases_sha256': '0' * 64}, {'optimum_sha256': '0' * 64}):
            with self.assertRaises(ValueError): self.check(cases, artifact, **options)
        for field, value in [('problem_id', 2900), ('comparison_policy', 'exact'), ('definition_sha256', '0' * 64),
                             ('cases_sha256', '0' * 64), ('case_count', True), ('schema', 'unknown')]:
            broken = copy.deepcopy(artifact); broken[field] = value
            with self.assertRaises(ValueError): self.check(cases, broken)
        for field, value in (('optimal_length', 1), ('optimal_length', True), ('args_sha256', '0' * 64), ('index', True), ('index', 1)):
            broken = copy.deepcopy(artifact); broken['rows'][0][field] = value
            with self.assertRaises(ValueError): self.check(cases, broken)
        broken = copy.deepcopy(artifact); broken['rows'].append(broken['rows'][0])
        with self.assertRaises(ValueError): self.check(cases, broken)
        broken = copy.deepcopy(cases); broken[0]['args'][1][1] = 1
        with self.assertRaises(ValueError): self.check(broken, artifact)

    def test_forged_expected_cannot_establish_optimum(self):
        cases, _ = self.artifact()
        for bad in ([], ['bab'], ['bab', 'dab', 'cab'], ['bab', 'bab'], ['unknown'], [0, 1], ['cab', 'bab']):
            cases[0]['expected'] = bad
            with self.assertRaises(ValueError): o.build_optimum_artifact(2901, cases, 'problem:2901')

    def test_noncanonical_encoding_cannot_hide_duplicate_keys(self):
        cases, artifact = self.artifact(); cb, ab = o.encoded(cases), o.encoded(artifact)
        bad = ab.replace(b'"problem_id":2901', b'"problem_id":2900,"problem_id":2901')
        with self.assertRaises(ValueError):
            o.validate_optimum_artifact(2901, 'problem:2901', cb, bad, cases_sha256=o.sha(cb), optimum_sha256=o.sha(bad))

    def test_finite_design_is_deterministic_and_has_no_duplicate_inputs(self):
        for pid in o.IDS:
            first = o.case_design(pid); self.assertEqual(first, o.case_design(pid)); cases, categories = first
            self.assertEqual(len(cases), len(categories))
            self.assertEqual(len(cases), len({o.encoded(case['args']) for case in cases}))
            for case in cases: self.assertTrue(o.legal_witness(pid, case['args'], case['expected']))


if __name__ == '__main__': unittest.main()
