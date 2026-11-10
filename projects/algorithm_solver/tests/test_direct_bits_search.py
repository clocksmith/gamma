"""Generic composition and independent direct-execution development checks."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth import direct_bits_search as s
from algsolve.synth import direct_bits_oracles as o
from algsolve.synth import typed_word_codec as codec
from algsolve.synth import typed_vector_program as ir


class DirectBitsSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = o.tasks()
        cls.requests = [[(c.inputs, c.expected) for c in t.train_cases] for t in cls.tasks]
        cls.result = s.synthesize(cls.requests)

    def test_finite_search_and_independent_oracles(self):
        self.assertEqual(sum(x is not None for x in self.result.selections), 24)
        self.assertIsNone(self.result.selections[0])
        self.assertIsNone(self.result.selections[1])
        self.assertEqual(self.result.candidates_tested, sum(4 * len(s.grammar()['stages'])**k for k in range(3)))
        self.assertEqual(len(self.result.trace), self.result.candidates_tested)
        for task, selection in zip(self.tasks, self.result.selections):
            if selection is None:
                continue
            with self.subTest(task=task.name):
                packet = bytes.fromhex(selection['packet_hex'])
                verdict = s.evaluate_packet(packet, [(c.inputs, c.expected) for c in task.evaluation_cases],
                                            budget=task.budget)
                self.assertTrue(verdict['passed'], verdict['failures'][:1])
                self.assertEqual(verdict['cases'], len(task.evaluation_cases))
                self.assertGreater(verdict['total_operation_units'], 0)

    def test_compositions_are_expanded_charged_and_width_invariant(self):
        complex_count = 0
        for selection in self.result.selections:
            if not selection:
                continue
            graph = codec.decode(bytes.fromhex(selection['packet_hex']))
            self.assertNotIn('recipe', ir.operation_counts(graph))
            if len(selection['plan']['stages']) == 2:
                complex_count += 1
            sizes = []
            for width in (6, 7, 8):
                packet, costs = codec.encode(graph, width, 'vector-v1')
                self.assertEqual(codec.decode(packet), graph)
                self.assertEqual(costs['packet_bits'], len(packet)*8)
                self.assertGreater(costs['numeric_and_control_selections'], 0)
                sizes.append(len(packet))
            self.assertEqual(sizes, sorted(sizes))
        self.assertGreaterEqual(complex_count, 4)

    def test_search_is_order_independent_of_request_names(self):
        # No names/descriptions are accepted. Reordering requests cannot change
        # their first matching candidate or its complete packet.
        first = s.synthesize(self.requests[2:6], candidate_limit=4000)
        second = s.synthesize(list(reversed(self.requests[2:6])), candidate_limit=4000)
        self.assertEqual(first.selections, list(reversed(second.selections)))

    def test_budget_stop_abstains_and_retains_trace(self):
        result = s.synthesize(self.requests, candidate_limit=3)
        self.assertEqual(result.candidates_tested, 3)
        self.assertEqual(len(result.trace), 3)
        self.assertTrue(any(x is None for x in result.selections))

    def test_compiler_rejects_unfrozen_surface(self):
        for stages, terminal in (([('oracle', 'sum')], 'list'),
                                 ([('distinct',)]*3, 'list'), ([], 'median')):
            with self.assertRaises(ValueError):
                s.compile_plan(stages, terminal)

    def test_checked_graph_and_packet_runners_agree_with_fresh_inputs(self):
        values = [[4, -3, 4, 1]]
        before = copy.deepcopy(values)
        graph = s.compile_plan([('map', ('mul', 'x', 'x')), ('distinct',)], 'list')
        packet, _ = codec.encode(graph, 6, 'vector-v1')
        answer, units = s.run_graph(graph, values)
        self.assertEqual(answer, [16, 9, 1])
        self.assertEqual(codec.execute(packet, values), answer)
        self.assertEqual(values, before)
        answer.append(99)
        self.assertEqual(s.run_graph(graph, values)[0], [16, 9, 1])
        with self.assertRaises(s.ExecutionFailure):
            s.run_graph(graph, values, budget=units-1)
        self.assertEqual(s.run_graph(graph, values, budget=units)[0], [16, 9, 1])


class DirectBitsReceiptTests(unittest.TestCase):
    def test_two_phase_protocol_replays_and_detects_tampering(self):
        path = Path(__file__).resolve().parents[1] / 'literals/direct-bits-development-v1/measure.py'
        spec = importlib.util.spec_from_file_location('direct_bits_measure', path)
        measure = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(measure)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # A targeted protocol test uses two tasks, independent from the
            # complete grammar/evaluation test above.
            original = o.tasks
            def subset(**kwargs): return original(**kwargs)[2:4]
            with patch.object(o, 'tasks', side_effect=subset):
                selection, _ = measure.select(root)
                self.assertTrue((root / 'selection.json').exists())
                first, _ = measure.score(root)
                second, _ = measure.score(root)
                self.assertEqual(first, second)
                self.assertEqual(first['independent_development_passed'], 2)
                self.assertEqual(first['test_executions'], 2*3*971)
                original_bytes = (root / 'selection.json').read_bytes()
                selection['source_bindings'] = {}
                (root / 'selection.json').write_text(json.dumps(selection))
                with self.assertRaisesRegex(ValueError, 'Source bindings'):
                    measure.score(root)
                (root / 'selection.json').write_bytes(original_bytes)
                with (root / 'trace.jsonl').open('ab') as stream:
                    stream.write(b'{}\n')
                with self.assertRaisesRegex(ValueError, 'Search trace changed'):
                    measure.score(root)


if __name__ == '__main__':
    unittest.main()
