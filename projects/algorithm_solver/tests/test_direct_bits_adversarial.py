"""Adversarial direct BITS boundaries; authored inputs only, no corpus access."""
import copy
import hashlib
import unittest
from unittest.mock import patch

from algsolve.synth import direct_bits_search as search
from algsolve.synth import typed_word_codec as codec
from algsolve.synth import typed_vector_program as ir


class DirectBitsAdversarialTests(unittest.TestCase):
    def packet(self, stages=(), terminal='sum'):
        return codec.encode(search.compile_plan(stages, terminal), 6, 'vector-v1')[0]

    def test_first_match_is_not_repaired_after_evaluation_failure(self):
        # Empty training is ambiguous between identity and many transformations.
        result = search.synthesize([[(([[]]), [])]], candidate_limit=100)
        selected = copy.deepcopy(result.selections[0])
        self.assertEqual(selected['ordinal'], 0)
        packet = bytes.fromhex(selected['packet_hex'])
        evaluation = search.evaluate_packet(packet, [(([[1, 2]]), [2, 1])])
        self.assertFalse(evaluation['passed'])
        self.assertEqual(result.selections[0], selected)
        self.assertEqual(result.candidates_tested, 1)

    def test_packet_and_case_evidence_bind_exact_values(self):
        packet = self.packet()
        first = search.evaluate_packet(packet, [(([[2, 3]]), 5)])
        second = search.evaluate_packet(packet, [(([[2, 3]]), 6)])
        self.assertTrue(first['passed'])
        self.assertFalse(second['passed'])
        self.assertEqual(first['packet_sha256'], hashlib.sha256(packet).hexdigest())
        self.assertNotEqual(first['case_set_sha256'], second['case_set_sha256'])
        self.assertEqual(first['observations_sha256'], second['observations_sha256'])

    def test_budget_failure_is_charged_and_later_cases_still_run(self):
        report = search.evaluate_packet(self.packet(), [(([[1, 2]]), 3), (([[]]), 0)], budget=5)
        self.assertFalse(report['passed'])
        self.assertEqual(report['passed_cases'], 1)
        empty_only = search.evaluate_packet(self.packet(), [(([[]]), 0)], budget=5)
        self.assertGreater(report['total_operation_units'], empty_only['total_operation_units'])
        self.assertGreaterEqual(report['max_case_operation_units'], 5)

    def test_search_charges_failed_candidate_execution(self):
        # Valid graph, but squaring this valid 128-bit input overflows the runtime.
        graph = search.compile_plan([('map', ('mul', 'x', 'x'))], 'list')
        with patch.object(search, 'candidates', return_value=iter([({}, graph)])):
            result = search.synthesize([[(([[1 << 100]]), [0])]], candidate_limit=1)
        self.assertIsNone(result.selections[0])
        self.assertEqual(result.training_executions, 1)
        self.assertIsNotNone(result.trace[0]['failure'])
        self.assertGreater(result.training_operation_units, 0)

    def test_public_graph_execution_rejects_unknown_statement(self):
        graph = search.compile_plan([], 'list')
        graph['body'] = [{'op': 'silently-ignore-me'}]
        with self.assertRaises(ir.Invalid):
            search.run_graph(graph, [[1]])

    def test_bool_is_not_an_integer_answer(self):
        report = search.evaluate_packet(self.packet(), [(([[1]]), True)])
        self.assertFalse(report['passed'])

    def test_empty_evidence_and_invalid_candidate_bounds_fail_closed(self):
        for limit in (True, 0, -1, search.MAX_CANDIDATES + 1):
            with self.assertRaises(ValueError):
                search.synthesize([[(([[]]), [])]], candidate_limit=limit)
        with self.assertRaises(ValueError):
            search.synthesize([[]])
        with self.assertRaises(ValueError):
            search.evaluate_packet(self.packet(), [])


class DirectBitsReceiptAdversarialTests(unittest.TestCase):
    def test_null_selection_cannot_claim_a_pass_or_hide_a_trace_match(self):
        import importlib.util
        import json
        from pathlib import Path
        import tempfile
        from algsolve.synth import direct_bits_oracles as oracles
        path = Path(__file__).resolve().parents[1] / 'literals/direct-bits-development-v1/measure.py'
        spec = importlib.util.spec_from_file_location('direct_bits_measure_adversarial', path)
        measure = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(measure)
        original = oracles.tasks
        def subset(**kwargs):
            return original(**kwargs)[2:3]
        with tempfile.TemporaryDirectory() as directory, patch.object(oracles, 'tasks', side_effect=subset):
            root = Path(directory)
            decision, _ = measure.select(root)
            for status in ('independent_development_passed', 'search_exhausted'):
                with self.subTest(status=status):
                    if (root / 'evaluation.json').exists():
                        (root / 'evaluation.json').unlink()
                    altered = copy.deepcopy(decision)
                    altered['rows'][0]['selection'] = None
                    altered['rows'][0]['status'] = status
                    (root / 'selection.json').write_text(json.dumps(altered))
                    with self.assertRaises(ValueError):
                        measure.score(root)
                    if (root / 'evaluation.json').exists():
                        (root / 'evaluation.json').unlink()


if __name__ == '__main__':
    unittest.main()
