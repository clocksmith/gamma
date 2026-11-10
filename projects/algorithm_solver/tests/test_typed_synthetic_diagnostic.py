import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from algsolve.synth import typed_codec
from algsolve.synth import typed_synthetic_diagnostic as diagnostic


class SyntheticDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = diagnostic.run_diagnostic()
        cls.rows = {row['case']: row for row in cls.result['cases']}

    def test_evidence_class_and_scope_stay_explicit(self):
        self.assertEqual(self.result['evidence_class'], 'authored_synthetic_fault_injection_only')
        for flag in ['protected_data_read', 'model_used', 'trained', 'native_judge_used',
                     'frozen_model_comparison_recreated', 'development_qualified',
                     'protected_scoring_authorized', 'autonomous_loop_ready']:
            self.assertIs(self.result[flag], False)
        self.assertEqual(len(self.result['fixtures']), 2)
        self.assertEqual(len(self.rows), 14)
        self.assertEqual({row['axis'] for row in self.rows.values()},
                         {'control', 'structural', 'binding', 'operation', 'combined'})

    def test_structural_repairs_and_interior_empty_limit_are_separate(self):
        for name in ['structure-root-cycle', 'structure-sibling-cycle', 'structure-missing-root-children']:
            row = self.rows[name]
            self.assertIsNone(row['raw']['graph'])
            self.assertTrue(row['constrained']['fixture_checks']['passed'])
            self.assertEqual(len(row['constrained']['correction']['edits']), 1)
        hole = self.rows['structure-interior-empty']
        self.assertIsNone(hole['raw']['graph'])
        self.assertIsNone(hole['constrained']['graph'])
        self.assertEqual(hole['constrained']['fixture_checks']['status'], 'not_executed_invalid_graph')
        self.assertNotIn('include_interior_empty', self.result['correction_policy'])

    def test_binding_failures_include_scope_type_and_semantic_errors(self):
        for name in ['binding-unknown', 'binding-escaped-branch-local', 'binding-wrong-type']:
            row = self.rows[name]
            self.assertIsNone(row['raw']['graph'])
            self.assertTrue(row['constrained']['fixture_checks']['passed'])
            self.assertEqual(row['constrained']['correction']['edits'][0]['field'], 'binding')
        row = self.rows['binding-valid-but-wrong']
        self.assertIsNotNone(row['raw']['graph'])
        self.assertFalse(row['raw']['fixture_checks']['passed'])
        self.assertEqual(row['raw']['graph'], row['constrained']['graph'])
        self.assertEqual(row['constrained']['correction']['reason'], 'already_valid')

    def test_operation_schema_errors_are_not_valid_wrong_algorithms(self):
        for name in ['operation-wrong-arity', 'operation-wrong-result-type']:
            row = self.rows[name]
            self.assertIsNone(row['raw']['graph'])
            self.assertTrue(row['constrained']['fixture_checks']['passed'])
            self.assertEqual(row['constrained']['correction']['edits'][0]['field'], 'op')
        row = self.rows['operation-valid-but-wrong']
        self.assertFalse(row['raw']['fixture_checks']['passed'])
        self.assertEqual(row['raw']['graph'], row['constrained']['graph'])
        self.assertEqual(row['constrained']['correction']['attempts'], [])
        self.assertTrue(row['raw']['fixture_checks']['checks'][0]['passed'])
        self.assertFalse(row['raw']['fixture_checks']['checks'][1]['passed'])

    def test_two_coordinate_repair_is_charged_and_preserves_literals(self):
        row = self.rows['combined-structure-binding']
        repair = row['constrained']['correction']
        self.assertEqual(len(repair['edits']), 2)
        self.assertTrue(row['constrained']['fixture_checks']['passed'])
        self.assertEqual(row['raw_codes']['bits'], repair['final_codes']['bits'])
        self.assertGreater(len(repair['attempts']), 1)

    def test_captures_and_lossless_score_recipe_are_verifiable(self):
        descriptor = self.result['prediction_descriptor']
        for row in self.rows.values():
            self.assertEqual(typed_codec.digest(row['raw_codes']), row['raw_sha256'])
            scores = diagnostic.scores_from_recipe(row['raw_codes'], row['injected_edits'],
                                                   descriptor['slots'], len(descriptor['types']))
            self.assertEqual(typed_codec.digest(scores), row['scores_sha256'])
            fixed = copy.deepcopy(row)
            receipt = fixed.pop('fixed_decisions_sha256')
            fixed.pop('outcome')
            for route in ['raw', 'constrained']:
                fixed[route].pop('fixture_checks')
            self.assertEqual(typed_codec.digest(fixed), receipt)

    def test_every_decision_precedes_expected_value_checks(self):
        corrections = []
        checks = []
        original_correct = diagnostic.correct
        original_check = diagnostic.check_graph

        def correct(*args, **kwargs):
            self.assertFalse(checks)
            self.assertEqual(len(args), 5)  # codec, raw, logits, params, bounds only
            corrections.append(1)
            return original_correct(*args, **kwargs)

        def check(*args, **kwargs):
            self.assertEqual(len(corrections), 14)
            checks.append(1)
            return original_check(*args, **kwargs)

        with patch.object(diagnostic, 'correct', correct), patch.object(diagnostic, 'check_graph', check):
            repeated = diagnostic.run_diagnostic()
        self.assertEqual(repeated['summary'], self.result['summary'])
        self.assertEqual(len(checks), 28)

    def test_summary_counts_invalid_and_valid_wrong_separately(self):
        totals = self.result['summary']['all']
        self.assertEqual(totals['cases'], 14)
        self.assertEqual(totals['raw'], {'valid': 4, 'passes_authored_checks': 2,
                                        'valid_but_fails_authored_checks': 2, 'invalid_not_executed': 10})
        self.assertEqual(totals['constrained'], {'valid': 13, 'passes_authored_checks': 11,
                                                'valid_but_fails_authored_checks': 2, 'invalid_not_executed': 1})
        self.assertEqual(totals['useful_on_authored_checks'], 9)
        self.assertEqual(totals['harmful_on_authored_checks'], 0)

    def test_report_and_artifacts_are_explicit_and_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'run'
            diagnostic.write_result(output, self.result)
            saved = json.loads((output / 'diagnostic.json').read_text())
            self.assertEqual(saved['summary'], self.result['summary'])
            report = (output / 'report.md').read_text()
            self.assertIn('not the frozen model comparison', report)
            self.assertIn('operation-valid-but-wrong', report)
            with self.assertRaises(FileExistsError):
                diagnostic.write_result(output, self.result)
            self.assertEqual(saved, json.loads((output / 'diagnostic.json').read_text()))


if __name__ == '__main__':
    unittest.main()
