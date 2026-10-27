"""Behavioral checks for joint source choice and exact move accounting."""
import unittest
from contextlib import redirect_stdout
from io import StringIO
from itertools import product
import search as joint


class JointSearchTests(unittest.TestCase):
    def test_aggregate_gate_failure_cannot_beat_a_feasible_partial_dictionary(self):
        sources = {1: {'a': 'ab' * 12}, 2: {'a': 'cd' * 12}, 3: {'a': 'x' * 40 + '!'}}
        one = joint.evaluate(sources, ['ab'], 4, alphabet=[], allow_partial=True)
        two_plus_failure = joint.evaluate(sources, ['ab', 'cd', 'x', '!'], 4, alphabet=[], allow_partial=True)
        self.assertEqual(two_plus_failure['within_32_selections'], 2)
        self.assertGreater(two_plus_failure['singleton_bit_share'], .1)
        self.assertLess(joint.cost(one, 'compact'), joint.cost(two_plus_failure, 'compact'))

    def test_joint_choice_can_choose_compliant_qualified_variant_over_shorter_one(self):
        sources = {1: {'short': 'abcdefghij!', 'shared': 'ab' * 12}}
        vocab = ['abcdefghij', 'ab', '!']
        default = joint.evaluate(sources, vocab, 4, alphabet=[])
        compact = joint.evaluate(sources, vocab, 4, default, alphabet=[], source_objective='compact')
        self.assertEqual(default['chosen'][1], 'short')
        self.assertEqual(compact['chosen'][1], 'shared')
        self.assertEqual(compact['within_32_selections'], 1)

    def test_lexical_boundaries_prevent_partial_identifiers_and_literals(self):
        sources = {1: {'a': 'foobar+12'}}
        pieces = ['foo', 'bar', '+', '1', '2']
        raw = joint.evaluate(sources, pieces, 4, alphabet=[], allow_partial=True)
        self.assertEqual(raw['coverage'], 1)
        boundaries = {(1, 'a'): {0, 6, 7, 9}}
        checked = joint.evaluate(sources, pieces, 4, raw, alphabet=[], allow_partial=True,
                                 boundaries=boundaries)
        self.assertEqual(checked['coverage'], 0)
        self.assertEqual(checked['uncovered'][1, 'a']['prefix_characters'], 0)
        fixed = joint.evaluate(sources, ['foobar', '+12'], 4, checked, alphabet=[],
                               boundaries=boundaries)
        self.assertEqual(fixed['selections'], 2)

    def test_gate_objective_cannot_buy_coverage_with_character_paths(self):
        sources = {1: {'a': 'abababababababababab!'}, 2: {'a': 'xxxxxxxxxxxxxxxxxxxx?'}}
        compact = joint.evaluate(sources, ['ab', '!'], 4, alphabet=[], allow_partial=True)
        alphabet = joint.evaluate(sources, list('abx!?'), 4, alphabet=[], allow_partial=True)
        self.assertEqual((compact['coverage'], alphabet['coverage']), (1, 2))
        self.assertLess(joint.cost(compact, 'compact'), joint.cost(alphabet, 'compact'))
        self.assertEqual(compact['within_32_selections'], 1)
        self.assertEqual(alphabet['singleton_compliant_programs'], 0)

    def test_shortest_path_is_not_padded_to_pass_singleton_gate(self):
        text = 'abcdefghij!'
        state = joint.evaluate({1: {'a': text}}, ['abcdefghij', 'ab', 'cd', 'ef', 'gh', 'ij', '!'],
                               4, alphabet=[])
        self.assertEqual(state['selections'], 2)
        self.assertEqual(state['singleton_bit_share'], .5)
        self.assertEqual(state['singleton_compliant_programs'], 0)

    def test_zero_coverage_keeps_progress_without_claiming_complete_source(self):
        sources = {1: {'a': 'abcdefgh!'}}
        first = joint.evaluate(sources, ['ab'], 4, alphabet=[], allow_partial=True)
        next_step = joint.evaluate(sources, ['ab', 'cd'], 4, alphabet=[], allow_partial=True)
        self.assertLess(joint.cost(next_step, 'compact'), joint.cost(first, 'compact'))
        self.assertEqual(next_step['coverage'], 0)

    def test_complementary_additions_change_source_only_together(self):
        sources = {1: {'a': 'aaaaaa', 'b': 'bcdefg'}}
        initial = joint.evaluate(sources, ['aa'], 7)
        for fragment in ['bcd', 'efg']:
            alone = joint.evaluate(sources, ['aa', fragment], 7, initial)
            self.assertEqual(alone['selections'], 3)
            self.assertEqual(alone['chosen'][1], 'a')
        both = joint.evaluate(sources, ['aa', 'bcd', 'efg'], 7, initial)
        self.assertEqual(both['selections'], 2)
        self.assertEqual(both['chosen'][1], 'b')

    def test_incremental_parsing_matches_full_after_add_remove(self):
        sources = {1: {'a': 'ababxyz', 'b': 'xyzxyza'}, 2: {'a': 'zzzzabcd'}}
        initial = joint.evaluate(sources, ['ab', 'xyz', 'zz'], 8)
        vocab = set(initial['vocab']) - {'ab'} | {'abcd', 'yzxy'}
        self.assertEqual(joint.evaluate(sources, vocab, 8, initial), joint.evaluate(sources, vocab, 8))

    def test_package_cost_includes_dictionary_headers_and_padding(self):
        sources = {1: {'a': 'abcdefghij'}, 2: {'a': 'abcxyz'}}
        state = joint.evaluate(sources, ['ab'], 7)
        raw = joint.base.dictionary_bytes(state['vocab'])
        encoded = []
        for pid, variant in state['chosen'].items():
            ids = [state['vocab'].index(s) for s in state['parsed'][(pid, variant)]]
            encoded.append(joint.base.encode(state['vocab'], ids, 7))
        self.assertEqual(state['package_bytes'], len(raw) + sum(map(len, encoded)))

    def test_variant_duplicates_do_not_create_cross_problem_reuse(self):
        sources = {1: {'a': 'abcdef', 'b': 'abcdef!'}, 2: {'a': 'zyxwvu'}}
        state = joint.evaluate(sources, [], 7)
        self.assertEqual(joint.proposals(sources, state, 100), [])

    def test_unused_removal_preserves_selections(self):
        sources = {1: {'a': 'ababcc'}, 2: {'a': 'ababdd'}}
        state = joint.evaluate(sources, ['ab', 'absent'], 7)
        pruned, removed = joint.prune(sources, state, 7)
        self.assertEqual(removed, ['absent'])
        self.assertEqual(pruned['selections'], state['selections'])
        self.assertLess(pruned['package_bytes'], state['package_bytes'])
        self.assertTrue(set(joint.base.ALPHABET).issubset(pruned['vocab']))

    def test_whole_program_and_overbudget_rejected(self):
        with self.assertRaisesRegex(ValueError, 'whole-program'):
            joint.evaluate({1: {'a':'abcdefgh'}}, ['abcdefgh'], 7)
        with self.assertRaisesRegex(ValueError, 'budget'):
            joint.evaluate({1: {'a':'abcdefgh'}}, [f'xx{i}' for i in range(40)], 7)

    def test_order_does_not_change_exact_result(self):
        sources = {1: {'a': 'abcdefabcdef'}}
        self.assertEqual(joint.evaluate(sources, ['abc', 'ab', 'def'], 7),
                         joint.evaluate(sources, ['def', 'abc', 'ab', 'abc'], 7))

    def test_payload_improvement_can_increase_complete_storage(self):
        sources = {1: {'a': 'abcdefghi!' }, 2: {'a': 'abcdefghi?'}}
        initial = joint.evaluate(sources, ['abc','def','ghi'], 8)
        proposed = joint.evaluate(sources, ['abc','def','ghi','abcdefghi'], 8, initial)
        self.assertLess(joint.cost(proposed, 'input'), joint.cost(initial, 'input'))
        self.assertGreater(joint.cost(proposed, 'storage'), joint.cost(initial, 'storage'))

    def test_explicit_alphabet_supports_all_widths_and_preserves_default(self):
        sources = {1: {'a': 'ababab!'}}
        for width in range(4, 13):
            state = joint.evaluate(sources, ['ab', '!'], width, alphabet=[])
            self.assertEqual(state['selections'], 4)
            self.assertEqual(state['literal_bits'], width * 4)
            self.assertEqual(state['singleton_bits'], width)
            self.assertEqual(state['singleton_bit_share'], .25)
            self.assertEqual(state['median_selections'], 4)
            self.assertEqual(state['p95_selections'], 4)
        self.assertTrue(set(joint.base.ALPHABET) <= set(joint.evaluate(sources, [], 7)['vocab']))

    def test_unmatched_suffix_is_not_skipped_or_counted_as_covered(self):
        sources = {1: {'a': 'abXab'}, 2: {'a': 'ababa'}}
        state = joint.evaluate(sources, ['ab', 'a'], 4, alphabet=[], allow_partial=True)
        self.assertEqual(state['coverage'], 1)
        self.assertEqual(state['chosen'], {2: 'a'})
        self.assertEqual(state['uncovered'][1, 'a'], {
            'prefix_characters': 2, 'prefix': ('ab',),
            'uncovered_characters': 3, 'uncovered_utf8_bytes': 3})
        self.assertEqual(state['selections'], 3)

    def test_longest_prefix_then_minimum_path_agrees_with_brute_force(self):
        vocab = ['a', 'ab', 'b', 'ba']
        tree = joint.base.trie(vocab)
        def paths(text, offset=0, path=()):
            yield offset, path
            for i, fragment in enumerate(vocab):
                if text.startswith(fragment, offset):
                    yield from paths(text, offset + len(fragment), path + (i,))
        for size in range(6):
            for chars in product('abX', repeat=size):
                text = ''.join(chars)
                expected = min(paths(text), key=lambda row: (-row[0], len(row[1]), row[1]))
                self.assertEqual(joint.representable_prefix(text, tree), expected)

    def test_partial_source_choice_never_selects_uncovered_cheaper_variant(self):
        sources = {1: {'short': 'X', 'covered': 'abab!'}}
        state = joint.evaluate(sources, ['ab', '!'], 4, alphabet=[], allow_partial=True)
        self.assertEqual(state['chosen'], {1: 'covered'})
        empty = joint.evaluate(sources, ['X?'], 4, alphabet=[], allow_partial=True)
        self.assertLess(joint.cost(state, 'input'), joint.cost(empty, 'input'))
        self.assertIsNone(empty['median_selections'])

    def test_incremental_cache_cannot_hide_source_or_coverage_changes(self):
        initial = joint.evaluate({1: {'a': 'abab!'}}, ['ab', '!'], 4, alphabet=[], allow_partial=True)
        changed = {1: {'a': 'abX!'}, 2: {'a': 'ababab!'}}
        self.assertEqual(joint.evaluate(changed, ['ab', '!'], 4, initial, alphabet=[], allow_partial=True),
                         joint.evaluate(changed, ['ab', '!'], 4, alphabet=[], allow_partial=True))

    def test_small_dictionary_packet_storage_is_exact(self):
        state = joint.evaluate({1: {'a': 'abab!'}}, ['ab', '!'], 5, alphabet=[])
        sequence = [state['vocab'].index(s) for s in state['parsed'][1, 'a']]
        packet = joint.base.encode(state['vocab'], sequence, 5)
        dictionary = joint.base.dictionary_bytes(state['vocab'])
        self.assertEqual(joint.base.decode(dictionary, packet), 'abab!')
        self.assertEqual(state['package_bytes'], len(dictionary) + len(packet))

    def test_invalid_literal_and_width_fail_closed(self):
        for vocab, width in [([''], 4), (['a'], True), (['a'], 3), (['a'], 13)]:
            with self.assertRaises(ValueError):
                joint.evaluate({1: {'a': 'aa'}}, vocab, width, alphabet=[])

    def test_changed_literal_id_order_invalidates_cached_tie(self):
        sources = {1: {'a': 'aaa'}}
        initial = joint.evaluate(sources, [], 4, alphabet=['a', 'aa'])
        self.assertEqual(initial['parsed'][1, 'a'], ('a', 'aa'))
        changed = joint.evaluate(sources, [], 4, initial, alphabet=['aa', 'a'])
        self.assertEqual(changed['parsed'][1, 'a'], ('aa', 'a'))
        self.assertEqual(changed, joint.evaluate(sources, [], 4, alphabet=['aa', 'a']))

    def test_partial_parent_does_not_relax_a_strict_child(self):
        sources = {1: {'a': 'abX'}}
        initial = joint.evaluate(sources, ['ab'], 4, alphabet=[], allow_partial=True)
        with self.assertRaisesRegex(ValueError, 'unrepresentable'):
            joint.evaluate(sources, ['ab'], 4, initial, alphabet=[])

    def test_uncovered_search_keeps_dictionary_format_valid(self):
        sources = {1: {'a': 'xxx'}}
        initial = joint.evaluate(sources, ['a', 'b'], 4, alphabet=[], allow_partial=True)
        limits = {'rounds_per_start': 2, 'trials_per_start': 40, 'seconds_per_start': 5,
                  'removal_shortlist': 2, 'addition_shortlist': 2,
                  'pair_removal_sets': 2, 'pair_addition_shortlist': 2}
        final, _ = joint.improve(sources, initial, 4, 'input', limits,
                                alphabet=[], allow_partial=True, candidate_pool=['a', 'b'])
        self.assertEqual(final['coverage'], 0)
        self.assertTrue(final['vocab'])
        self.assertEqual(final['dictionary_bytes'], len(joint.base.dictionary_bytes(final['vocab'])))


    def test_singleton_objective_and_pareto_cannot_reward_ratio_padding(self):
        state = {'coverage': 240, 'allow_partial': True, 'singleton_bits': 80,
                 'literal_bits': 800, 'package_bytes': 300, 'singleton_bit_share': .1}
        padded = dict(state, literal_bits=1600, package_bytes=400, singleton_bit_share=.05)
        self.assertGreater(joint.cost(padded, 'singleton'), joint.cost(state, 'singleton'))
        self.assertGreater(joint.pareto_vector(padded), joint.pareto_vector(state))
        worse = dict(state, singleton_bits=88, literal_bits=1600, singleton_bit_share=.055)
        self.assertGreater(joint.cost(worse, 'singleton'), joint.cost(state, 'singleton'))
        with self.assertRaises(ValueError): joint.cost(state, 'ratio')

    def test_absolute_singleton_reduction_and_full_costs_at_each_width(self):
        sources = {i: {'a': 'abcabc!'} for i in range(1, 241)}
        for width in range(4, 13):
            with self.subTest(width=width):
                before = joint.evaluate(sources, list('abc!'), width, alphabet=[])
                after = joint.evaluate(sources, list('abc!') + ['abc'], width, alphabet=[])
                self.assertEqual(after['coverage'], 240)
                self.assertEqual((before['selections'], after['selections']), (1680, 720))
                self.assertEqual((before['singleton_bits'], after['singleton_bits']), (1680 * width, 240 * width))
                self.assertLess(joint.cost(after, 'singleton'), joint.cost(before, 'singleton'))
                self.assertEqual(after['source_utf8_bytes'], 1680)
                self.assertEqual(after['packet_header_bytes'], 41 * 240)
                self.assertEqual(after['packet_bytes'] * 8,
                    after['packet_header_bytes'] * 8 + after['literal_bits'] + after['payload_padding_bits'])
                self.assertEqual(after['package_bytes'], after['packet_bytes'] + after['dictionary_bytes'])

    def test_search_accepts_reused_span_for_absolute_singleton_reduction(self):
        sources = {i: {'a': 'abcabc!'} for i in range(1, 241)}
        initial = joint.evaluate(sources, list('abc!'), 4, alphabet=[], allow_partial=True)
        limits = {'rounds_per_start': 1, 'trials_per_start': 40, 'seconds_per_start': 5,
                  'removal_shortlist': 2, 'addition_shortlist': 2,
                  'pair_removal_sets': 2, 'pair_addition_shortlist': 2}
        with redirect_stdout(StringIO()):
            final, trace = joint.improve(sources, initial, 4, 'singleton', limits,
                alphabet=[], allow_partial=True, candidate_pool=['abc'])
        self.assertEqual(final['coverage'], 240)
        self.assertEqual(final['singleton_bits'], 960)
        self.assertEqual(final['selections'], 720)
        self.assertIsNotNone(trace['rounds'][0]['accepted'])

if __name__ == '__main__':
    unittest.main()
