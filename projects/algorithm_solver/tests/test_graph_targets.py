import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from algsolve.synth import graph_targets as graph, render, training_pairs as pairs

V = 'frozen-vocabulary'
PARAMS = ['n', 'edges']
COMPOSITION = {'stages': [{'skeleton': 'mst', 'inputs': PARAMS, 'output': 'cost',
                         'holes': {'n': 'n', 'edges': 'edges', 'result': 'total'}}], 'answer': 'cost'}


def target():
    return graph.encode(COMPOSITION, method='solve', params=PARAMS, vocabulary_sha256=V)


class GraphTargetTests(unittest.TestCase):
    def test_round_trip_retains_executable_source_and_empty_slots(self):
        value = target()
        compiled = graph.compile_target(value, method='solve', params=PARAMS, vocabulary_sha256=V)
        self.assertEqual(compiled.source, render.render(COMPOSITION, method='solve', params=PARAMS).source)
        self.assertEqual(value['slots'][1:], [{'component': 'EMPTY'}, {'component': 'EMPTY'}])
        self.assertEqual(value['slots'][0]['bindings'][1]['source'], {'input': 1})
        self.assertEqual(value['slots'][0]['parameters']['edges']['ast']['op'], 'Expression')

    def test_invalid_bindings_versions_and_empty_slots_fail_closed(self):
        mutations = [lambda g: g.update(vocabulary_sha256='other'),
                     lambda g: g['slots'][0]['bindings'][0].update(source={'slot': 1}),
                     lambda g: g['slots'][1].update(output='hidden'),
                     lambda g: g['slots'].reverse(),
                     lambda g: g['slots'][0].update(component='invented')]
        for mutate in mutations:
            value = target(); mutate(value)
            with self.assertRaises((ValueError, TypeError)):
                graph.compile_target(value, method='solve', params=PARAMS, vocabulary_sha256=V)

    def test_hole_payload_cannot_bypass_grammar_or_resource_bounds(self):
        value = target()
        value['slots'][0]['parameters']['n'] = graph.ast_parameter("__import__('os').system('true')", 'expr')
        with self.assertRaises(ValueError):
            graph.compile_target(value, method='solve', params=PARAMS, vocabulary_sha256=V)
        value = target()
        value['slots'][0]['parameters']['n'] = graph.ast_parameter('+'.join(['n'] * 30), 'expr')
        with self.assertRaises(ValueError):
            graph.compile_target(value, method='solve', params=PARAMS, vocabulary_sha256=V)
        with self.assertRaises(ValueError):
            graph.tree_from_data({'op': 'NotAnOperator', 'fields': {}})

    def test_generic_code_holes_are_not_graph_training_success(self):
        generic = {'stages': [{'skeleton': 'formula', 'inputs': ['n'], 'output': 'result', 'holes': {'value': 'n'}}], 'answer': 'result'}
        with self.assertRaisesRegex(ValueError, 'algorithm-specific'):
            graph.encode(generic, method='solve', params=['n'], vocabulary_sha256=V)

    def test_splits_keep_problem_alternatives_and_shared_patterns_together(self):
        values = [{'uid': 'a', 'pattern_sha256': 'x'}, {'uid': 'a', 'pattern_sha256': 'y'},
                  {'uid': 'b', 'pattern_sha256': 'y'}, {'uid': 'c', 'pattern_sha256': 'z'}]
        pairs.assign_splits(values)
        self.assertEqual(len({r['split_group_sha256'] for r in values[:3]}), 1)
        self.assertNotEqual(values[0]['split_group_sha256'], values[3]['split_group_sha256'])
        reversed_values = [dict(uid=r['uid'], pattern_sha256=r['pattern_sha256']) for r in reversed(values)]
        pairs.assign_splits(reversed_values)
        self.assertEqual(list(reversed(reversed_values)), values)

    def test_pattern_ignores_parameter_spelling_but_preserves_graph_structure(self):
        a = target(); b = target()
        b['slots'][0]['parameters']['n'] = graph.ast_parameter('vertex_count', 'expr')
        self.assertEqual(pairs.pattern(a), pairs.pattern(b))
        b['slots'][0]['bindings'][0]['source'] = {'slot': 0}
        self.assertNotEqual(pairs.pattern(a), pairs.pattern(b))

    def test_unpermitted_rows_never_read_hidden_tests_or_invoke_judge(self):
        with patch.object(pairs, 'load_hidden_tests', side_effect=AssertionError('leak')):
            result, reason = pairs.candidate({'uid': 'heldout'}, {}, {}, V,
                                             check=lambda *a: self.fail('judge called'))
        self.assertIsNone(result)
        self.assertEqual(reason, 'not_permitted_development')

    def test_policy_excludes_reserved_siblings_and_rejects_index_leakage(self):
        def entry(slug, uid):
            return SimpleNamespace(key='lc:' + slug, slug=slug, members=[uid])
        entries = [entry('allowed', 'a'), entry('reserved', 'b'), entry('reserved-ii', 'c')]
        problems = {uid: SimpleNamespace(uid=uid, slug=slug) for slug, uid in
                    [('allowed', 'a'), ('reserved', 'b'), ('reserved-ii', 'c'), ('heldout', 'h')]}
        manifest = {'solving': {'lcd': ['h']}, 'recognition': [], 'recognition_dev': []}
        confirmation = {'source_sha256': pairs.mine.digest([e.__dict__ for e in entries]),
                        'confirmation_keys': ['lc:reserved']}
        with patch.object(pairs.splits, 'solving_pools', return_value={'lcd': [problems['h']]}):
            self.assertEqual(set(pairs.policy(entries, problems, manifest, confirmation, {'a', 'b', 'c'})), {'a'})
            with self.assertRaisesRegex(ValueError, 'differs'):
                pairs.policy(entries, problems, manifest, dict(confirmation, source_sha256='stale'), {'a'})
            leaked = entries + [entry('heldout', 'alias')]
            current = dict(confirmation, source_sha256=pairs.mine.digest([e.__dict__ for e in leaked]))
            with self.assertRaisesRegex(ValueError, 'alias'):
                pairs.policy(leaked, problems, manifest, current, {'a'})

    def test_old_audit_claim_requires_new_source_bound_independent_receipt(self):
        problem = SimpleNamespace(uid='dev', statement='Minimum spanning tree.', starter_code='',
            params=[['n', 'int'], ['edges', 'list']], entry={'method': 'solve'}, public_tests=[{'args': [1, []], 'expected': 0}],
            evidence_ceiling='independent_tests_passed')
        entry = SimpleNamespace(key='lc:dev', license=['fixture'], attribution=['fixture'])
        row = {'uid': 'dev', 'composition': copy.deepcopy(COMPOSITION), 'label': 'demonstrated_expressible',
               'vocabulary_sha256': 'old'}
        def check(p, c):
            compiled = render.render(c, method='solve', params=PARAMS)
            return {'ok': True, 'evidence': 'independent_tests_passed', 'rendered': {'source_sha256': graph.source_hash(compiled)},
                    'public': {'passed': True, 'tests_passed': 1}, 'hidden': {'passed': True, 'tests_passed': 3}}
        with patch.object(pairs, 'load_hidden_tests', return_value=[{'secret': 'do not export'}]):
            result, reason = pairs.candidate(row, {'dev': entry}, {'dev': problem}, V, check=check)
            self.assertIsNone(reason)
            self.assertNotIn('secret', str(result))
            self.assertEqual(result['target']['vocabulary_sha256'], V)
            result, reason = pairs.candidate(row, {'dev': entry}, {'dev': problem}, V, check=lambda *a: {'ok': False})
            self.assertEqual(reason, 'fresh_validation_failed')
            bad = check(problem, COMPOSITION); bad['rendered']['source_sha256'] = 'forged'
            with self.assertRaisesRegex(ValueError, 'bound'):
                pairs.candidate(row, {'dev': entry}, {'dev': problem}, V, check=lambda *a: bad)


if __name__ == '__main__': unittest.main()
