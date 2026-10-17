import copy
import random
import unittest

from algsolve.synth import call_graph as graph
from algsolve.synth import call_graph_pairs, training_pairs
from unittest.mock import patch


def target(nodes, answer):
    return {'schema': graph.SCHEMA, 'vocabulary_sha256': graph.vocabulary_hash(),
            'nodes': nodes, 'answer': answer}


def node(operator, arguments, output='out'):
    return {'operator': operator, 'arguments': arguments, 'output': output}


def execute(value, params, *args):
    compiled = graph.compile_graph(value, method='solve', params=params)
    namespace = {}
    # Only fixed, repository-owned fixtures execute in this process. Proposed
    # problem solutions go through the existing Linux sandbox, never this helper.
    exec(compiled.source, namespace)
    return namespace['Solution']().solve(*args)


class CallGraphTests(unittest.TestCase):
    def test_window_contract_against_independent_slice_oracle(self):
        rng = random.Random(52)
        value = target([node('window_sums', ['values', 'width'])], 'out')
        for size in range(30):
            values = [rng.randrange(-100, 101) for _ in range(size)]
            for width in range(size + 3):
                before = list(values)
                expected = [sum(values[i:i+width]) for i in range(size-width+1)]
                self.assertEqual(execute(value, ['values', 'width'], values, width), expected)
                self.assertEqual(values, before)
        for width in [-1, 1.2, True]:
            with self.assertRaises(ValueError):
                execute(value, ['values', 'width'], [1, 2], width)

    def test_composed_graph_preserves_port_order_and_permutation_semantics(self):
        value = target([node('adjacency', ['n', 'edges', 'True', 'False'], 'adj'),
                        node('bfs', ['n', 'adj', '[start]'], 'dist')], 'dist')
        self.assertEqual(execute(value, ['n', 'edges', 'start'], 4, [[0,1], [1,2]], 0), [0,1,2,-1])
        self.assertEqual(execute(value, ['n', 'edges', 'start'], 4, [[1,0], [2,1]], 0), [0,-1,-1,-1])

    def test_parameters_change_algorithm_behavior(self):
        value = target([node('lis_length', ['values', 'strict'])], 'out')
        self.assertEqual(execute(value, ['values', 'strict'], [2,2,2], True), 1)
        self.assertEqual(execute(value, ['values', 'strict'], [2,2,2], False), 3)

    def test_binding_scope_cannot_be_hidden_in_glue(self):
        value = target([node('prefix_sums', ['values'])], 'sum(x for x in out)')
        self.assertEqual(execute(value, ['values'], [2,3]), 7)
        for source in ['sum(x for x in later)', 'x + sum(x for x in out)',
                       'sum(out for out in values)', 'c_lis_length(values)',
                       'values.clear()', 'out.__class__', '__import__("os")',
                       'out + [0]' * 20]:
            invalid = copy.deepcopy(value); invalid['answer'] = source
            with self.assertRaises(ValueError, msg=source):
                graph.compile_graph(invalid, method='solve', params=['values'])

    def test_unused_algorithms_future_bindings_shadowing_and_versions_fail_closed(self):
        value = target([node('prefix_sums', ['values'])], 'out')
        variants = [dict(value, answer='sum(values)'), dict(value, vocabulary_sha256='stale'),
                    dict(value, nodes=[node('prefix_sums', ['future'])]),
                    dict(value, nodes=[node('prefix_sums', ['values'], 'values')]),
                    dict(value, nodes=[node('prefix_sums', ['values', 'values'])]),
                    dict(value, nodes=[node('invented', ['values'])])]
        for invalid in variants:
            with self.assertRaises(ValueError):
                graph.compile_graph(invalid, method='solve', params=['values'])

    def test_unpermitted_proposal_cannot_reach_tests_or_compiler(self):
        with patch.object(call_graph_pairs, 'load_hidden_tests', side_effect=AssertionError('leak')), \
             patch.object(graph, 'compile_graph', side_effect=AssertionError('compile')):
            pair, verdict = call_graph_pairs.qualify({'uid': 'protected'}, {}, {})
        self.assertIsNone(pair)
        self.assertEqual(verdict['reason'], 'not_permitted_development')

    def test_sibling_families_and_alternative_patterns_stay_in_one_partition(self):
        pairs = [{'uid': 'a', 'pattern_sha256': 'x', 'problem_family': 'stock'},
                 {'uid': 'b', 'pattern_sha256': 'y', 'problem_family': 'stock'},
                 {'uid': 'c', 'pattern_sha256': 'y', 'problem_family': 'other'}]
        training_pairs.assign_splits(pairs)
        self.assertEqual(len({p['split_group_sha256'] for p in pairs}), 1)


if __name__ == '__main__':
    unittest.main()
