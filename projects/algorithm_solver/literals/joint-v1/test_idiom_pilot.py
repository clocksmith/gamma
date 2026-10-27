"""Candidate provenance and reuse checks, independently of solver execution."""
import unittest
import os
from unittest.mock import patch
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import shutil
import idiom_pilot as pilot


class IdiomPoolTests(unittest.TestCase):
    def test_whitespace_cannot_disguise_single_character_entries(self):
        text = 'a + 1;\n'
        sources = {1: {'a': text}, 2: {'a': text + '\n'}}
        spans = {f'{pid}/a': ['a ', ' 1', ';\n', ' + ', '1;'] for pid in sources}
        pools, _ = pilot.admitted_pools(sources, spans)
        for name in ('assistant_seed', 'ast_spans', 'seed_ast_union'):
            self.assertTrue(all(len(piece.strip()) > 1 for piece in pools[name]))
            self.assertNotIn('a ', pools[name])
        self.assertIn('1;', pools['ast_spans'])

    def test_whole_token_windows_bridge_ast_gaps_in_both_languages(self):
        examples = {
            'javascript': ('function solve(values) {\n  let count = 0;\n'
                           '  for (const value of values) { count += value; }\n'
                           '  return count;\n}\n', ';\n  for'),
            'python': ('def solve(values):\n    count = 0\n'
                       '    for value in values:\n        count += value\n'
                       '    return count\n', '0\n    for'),
        }
        for language, (text, join) in examples.items():
            with self.subTest(language=language):
                sources = {1: {'a': text}, 2: {'a': text}}
                parsed = pilot.syntactic_spans(sources, language, Path('/usr/bin/node'),
                                               pilot.digest('/usr/bin/node'))
                bounds = {(pid, 'a'): set(parsed['boundaries'][f'{pid}/a']) for pid in sources}
                pools, _ = pilot.admitted_pools(sources, parsed['spans'], parsed['excluded_units'],
                                               language, boundaries=bounds)
                self.assertIn(join, pools['ast_spans'])
                pool = pilot.arm_pool(pools['seed_ast_union'], sources, 'strict')
                path = pilot.joint.segment(text, pilot.joint.base.trie(pool), bounds[1, 'a'])
                self.assertEqual(''.join(pool[i] for i in path), text)
                self.assertTrue(all(len(pool[i].strip()) > 1 for i in path))
                self.assertNotIn(text.index('values') + 2, bounds[1, 'a'])

    def test_partial_token_occurrences_cannot_establish_human_pool_reuse(self):
        sources = {1: {'a': 'long+2'}, 2: {'a': 'longer+2'}}
        spans = {'1/a': ['long'], '2/a': ['longer']}
        boundaries = {(1, 'a'): {0, 4, 5, 6}, (2, 'a'): {0, 6, 7, 8}}
        pools, _ = pilot.admitted_pools(sources, spans, boundaries=boundaries)
        self.assertNotIn('long', pools['ast_spans'])
        self.assertIn('long', pools['compression_fragments'])

    def test_ast_spans_keep_charged_separators_and_unicode_boundaries(self):
        source = 'function solve(longName) {\n  return "λ😀" + longName;\n}\n'
        node = os.environ.get('GAMMA_TEST_NODE') or shutil.which('node')
        if not node:
            self.skipTest('existing Node runtime required for parse-only integration')
        raw = subprocess.run([node, '--expose-internals',
                              str(Path(pilot.__file__).with_name('idiom_spans.cjs'))],
                             input=json.dumps({'sources': {'one': source}, 'max_span_bytes': 160}), text=True, capture_output=True,
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

    def test_python_complete_class_and_body_cannot_be_a_literal(self):
        text = 'class Solution:\n    x = 1\n    y = 2\n'
        parsed = pilot.python_spans({'1/a': text})
        pools, _ = pilot.admitted_pools({1: {'a': text}, 2: {'a': text + '# other\n'}},
            {'1/a': ['x = 1\n    y = 2'], '2/a': ['x = 1\n    y = 2']}, parsed['excluded_units'], 'python')
        for pool in pools.values(): self.assertNotIn('x = 1\n    y = 2', pool)

    def test_python_long_unicode_and_adjacent_spans_are_exact_without_execution(self):
        text = ('raise RuntimeError("never execute")\n'
                'def solve(values):\n'
                '    total = sum(é for é in values if é > 0)\n'
                '    count = len(values)\n'
                '    return total / max(count, 1)\n')
        with patch('builtins.exec', side_effect=AssertionError('source executed')):
            parsed = pilot.python_spans({'1/a': text})
        spans = parsed['spans']['1/a']
        pair = 'total = sum(é for é in values if é > 0)\n    count = len(values)'
        self.assertIn(pair, spans)
        self.assertTrue(all(s in text and len(s.encode()) <= 160 for s in spans))
        self.assertEqual(len(parsed['runtime_sha256']), 64)
        sources = {1: {'a': text}, 2: {'b': text + '# second problem\n'}}
        pools, owners = pilot.admitted_pools(sources, {'1/a': spans, '2/b': spans},
                                          parsed['excluded_units'], 'python')
        self.assertIn(pair, pools['ast_spans'])
        self.assertEqual(owners[pair], {1, 2})
        self.assertIn('len(', pools['assistant_seed'])
        for pool in pools.values():
            self.assertTrue(all(s.strip() not in {u.strip() for u in parsed['excluded_units']} for s in pool))

    def test_occurrence_trie_matches_nonoverlap_counts_and_distinct_problem_owners(self):
        sources = {1: {'a': 'aaaaa', 'b': 'aaaaaaaa'}, 2: {'a': 'aaaa'}, 3: {'a': 'xyz'}}
        candidates = {'aa', 'aaa', 'aaaa', 'xy', 'no'}
        owners, counts = pilot.occurrence_index(sources, candidates)
        for fragment in candidates:
            self.assertEqual(owners[fragment], {pid for pid, variants in sources.items()
                                                if any(fragment in s for s in variants.values())})
            self.assertEqual(counts[fragment], sum(max(s.count(fragment) for s in variants.values())
                                                  for variants in sources.values()))

    def test_whitespace_does_not_disguise_complete_function_body(self):
        text = 'def solve():\n    return 123\n'
        parsed = pilot.python_spans({'1/a': text})
        sources = {1: {'a': text}, 2: {'a': text + '# other\n'}}
        pools, _ = pilot.admitted_pools(sources, {'1/a': ['    return 123'], '2/a': ['    return 123']},
                                       parsed['excluded_units'], 'python')
        for pool in pools.values(): self.assertNotIn('    return 123', pool)

    def test_javascript_long_adjacent_spans_parse_without_execution(self):
        node = os.environ.get('GAMMA_TEST_NODE')
        if not node:
            self.skipTest('explicit existing Node path required')
        text = ('throw Error("never execute");\nfunction solve(values) {\n'
                '  const total = values.reduce((sum, value) => sum + value, 0);\n'
                '  const count = values.length;\n  return total / Math.max(count, 1);\n}\n')
        runtime = Path(node)
        parsed = pilot.syntactic_spans({1: {'a': text}, 2: {'b': text + '// second\n'}},
                                       'javascript', runtime, pilot.digest(runtime))
        pair = ('const total = values.reduce((sum, value) => sum + value, 0);\n'
                '  const count = values.length;')
        pools, _ = pilot.admitted_pools({1: {'a': text}, 2: {'b': text + '// second\n'}},
                                       parsed['spans'], parsed['excluded_units'])
        self.assertIn(pair, pools['ast_spans'])
        self.assertGreater(len(pair.encode()), 40)
        self.assertTrue(all(span in text for span in parsed['spans']['1/a']))
        for pool in pools.values():
            self.assertTrue(all(s.strip() not in {u.strip() for u in parsed['excluded_units']} for s in pool))

if __name__ == '__main__':
    unittest.main()
