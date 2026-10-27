"""Candidate provenance and reuse checks, independently of solver execution."""
import unittest
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import idiom_pilot as pilot


class IdiomPoolTests(unittest.TestCase):
    def test_partial_token_occurrences_cannot_establish_human_pool_reuse(self):
        sources = {1: {'a': 'long+2'}, 2: {'a': 'longer+2'}}
        spans = {'1/a': ['long'], '2/a': ['longer']}
        boundaries = {(1, 'a'): {0, 4, 5, 6}, (2, 'a'): {0, 6, 7, 8}}
        pools, _ = pilot.admitted_pools(sources, spans, boundaries)
        self.assertNotIn('long', pools['ast_spans'])
        self.assertIn('long', pools['compression_fragments'])

    def test_ast_spans_keep_charged_separators_and_unicode_boundaries(self):
        source = 'function solve(longName) {\n  return "λ😀" + longName;\n}\n'
        raw = subprocess.run(['/usr/bin/node', '--expose-internals',
                              str(Path(pilot.__file__).with_name('idiom_spans.cjs'))],
                             input=json.dumps({'one': source}), text=True, capture_output=True,
                             timeout=10, check=True)
        result = json.loads(raw.stdout)
        spans, boundaries = result['spans']['one'], set(result['boundaries']['one'])
        self.assertIn('\n}\n', spans)
        self.assertIn('longName)', spans)
        self.assertIn(len(source), boundaries)
        self.assertNotIn(source.index('longName') + 4, boundaries)
        self.assertNotIn(source.index('😀'), boundaries)
        self.assertTrue(all(piece in source for piece in spans))

    def test_arm_pools_never_restore_a_letter_or_digit_alphabet(self):
        sources = {1: {'a': 'alpha9+beta1;\n'}}
        pool = ['alpha', 'beta', 'a', '9', '9+', '1;']
        strict = pilot.arm_pool(pool, sources, 'strict')
        fallback = pilot.arm_pool(pool, sources, 'punctuation_fallback')
        self.assertTrue(all(len(piece) > 1 for piece in strict))
        self.assertEqual({piece for piece in fallback if len(piece) == 1}, {'+', ';', '\n'})
        self.assertEqual(fallback[:len(strict)], strict)

    def test_bundle_seeding_covers_complementary_pieces_before_ranked_distractions(self):
        sources = {1: {'a': 'ab' * 10 + 'cd'}}
        pool = [f'absent{i}' for i in range(20)] + ['ab', 'cd']
        initial = pilot.seed_vocabulary(sources, pool, 4)
        self.assertTrue({'ab', 'cd'} <= set(initial))
        self.assertEqual(len(initial), 16)
        self.assertEqual(pilot.joint.evaluate(sources, initial, 4, alphabet=[])['coverage'], 1)

    def test_pilot_thresholds_do_not_evaluate_original_population_gate(self):
        sources = {1: {'a': 'abababcdcdcd'}}
        state = pilot.joint.evaluate(sources, ['ab', 'cd'], 4, alphabet=[])
        result = pilot.metrics(state, sources, defaultdict(set), 4)
        self.assertTrue(result['pilot_numeric_thresholds_met'])
        self.assertFalse(result['original_population_gate_evaluated'])
        self.assertFalse(result['milestone_qualified'])

    def test_distinct_variants_are_not_distinct_problem_reuse(self):
        sources = {1: {'a': 'x.length+1', 'b': 'x.length+2'}, 2: {'a': 'yy'}}
        spans = {'1/a': ['x.length'], '1/b': ['x.length'], '2/a': []}
        pools, _ = pilot.admitted_pools(sources, spans)
        self.assertNotIn('x.length', pools['ast_spans'])
        self.assertNotIn('.length', pools['assistant_seed'])

    def test_exact_seed_machine_union_and_compression_pools_remain_separate(self):
        sources = {1: {'a': 'x.length+1'}, 2: {'a': 'x.length+2'}}
        spans = {'1/a': ['x.length'], '2/a': ['x.length']}
        pools, owners = pilot.admitted_pools(sources, spans)
        self.assertIn('x.length', pools['ast_spans'])
        self.assertIn('.length', pools['assistant_seed'])
        self.assertEqual(set(pools['seed_ast_union']), set(pools['assistant_seed']) | set(pools['ast_spans']))
        self.assertEqual(owners['x.length'], {1, 2})
        self.assertIn('leng', pools['compression_fragments'])
        self.assertNotIn('leng', pools['seed_ast_union'])

    def test_machine_span_not_present_in_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact source span'):
            pilot.admitted_pools({1: {'a': 'ab'}}, {'1/a': ['not present']})

    def test_whole_program_and_whitespace_only_multichar_entries_are_banned(self):
        sources = {1: {'a': 'xy  z'}, 2: {'a': 'xy  z!'}}
        pools, _ = pilot.admitted_pools(sources, {'1/a': ['xy  z', '  '], '2/a': ['xy  z', '  ']})
        for pool in pools.values():
            self.assertNotIn('xy  z', pool)
            self.assertTrue(all(fragment.strip() for fragment in pool))

    def test_comparisons_retain_singleton_storage_tradeoff_and_regressions(self):
        rows = []
        for width in range(4, 9):
            def metric(a, b, singleton, package):
                return {'coverage': 2, 'literal_bits': (a + b) * width,
                        'singleton_bits': singleton * width, 'package_bytes': package,
                        'programs': {'1': {'selections': a}, '2': {'selections': b}}}
            for name, m in [('assistant_seed', metric(10, 10, 10, 100)),
                            ('ast_spans', metric(8, 12, 1, 110)),
                            ('seed_ast_union', metric(9, 10, 10, 99)),
                            ('compression_fragments', metric(15, 15, 20, 200))]:
                rows.append({'width': width, 'pool': name, 'final': m})
        result = pilot.comparisons(rows)
        ast = next(row for row in result if row.get('pool') == 'ast_spans')
        self.assertEqual((ast['fewer_selections'], ast['more_selections']), (1, 1))
        pareto = next(row for row in result if 'pareto_pools' in row)
        self.assertEqual(pareto['pareto_pools'], ['ast_spans', 'seed_ast_union'])


if __name__ == '__main__':
    unittest.main()
