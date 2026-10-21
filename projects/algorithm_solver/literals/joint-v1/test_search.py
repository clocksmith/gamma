"""Behavioral checks for joint source choice and exact move accounting."""
import unittest
import search as joint


class JointSearchTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
