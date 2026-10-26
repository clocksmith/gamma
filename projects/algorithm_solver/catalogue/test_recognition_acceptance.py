import unittest
from .recognition_acceptance import evaluate


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.cohort = [dict(id=str(i), kind='positive', expected_id='leetcode:1') for i in range(100)]
        self.cohort.append(dict(id='control', kind='ambiguous'))
        self.decisions = {q['id']: dict(status='accepted', problem_id='leetcode:1') for q in self.cohort}
        self.decisions['control'] = dict(status='abstain')

    def test_abstentions_cannot_inflate_recall(self):
        for key in ('0', '1'):
            self.decisions[key] = dict(status='abstain')
        r = evaluate(self.cohort, self.decisions)
        self.assertEqual((r['precision'], r['recall']), (1, .98))
        self.assertFalse(r['meets_99_percent_point_targets'])

    def test_wrong_identity_counts_against_precision_and_recall(self):
        self.decisions['0'] = dict(status='accepted', problem_id='leetcode:2')
        self.decisions['control'] = dict(status='accepted', problem_id='leetcode:1')
        r = evaluate(self.cohort, self.decisions)
        self.assertEqual((r['false_positives'], r['false_negatives']), (2, 1))
        self.assertEqual(r['precision'], 99 / 101)
        self.assertFalse(r['meets_99_percent_point_targets'])

    def test_complete_point_pass_is_not_release_qualification(self):
        self.decisions['0'] = dict(status='abstain')
        r = evaluate(self.cohort, self.decisions)
        self.assertTrue(r['meets_99_percent_point_targets'])
        self.assertFalse(r['recognition_qualified'])
        self.assertLess(r['recall_wilson_95'][0], .99)

    def test_missing_extra_and_duplicate_cases_rejected(self):
        for cohort, decisions in [(self.cohort, {}), (self.cohort * 2, self.decisions),
                                  (self.cohort, dict(self.decisions, extra={'status': 'abstain'}))]:
            with self.assertRaises(ValueError):
                evaluate(cohort, decisions)

    def test_empty_acceptance_is_not_perfect_precision(self):
        r = evaluate(self.cohort, {q['id']: dict(status='abstain') for q in self.cohort})
        self.assertIsNone(r['precision'])
        self.assertEqual(r['recall'], 0)
        self.assertFalse(r['meets_99_percent_point_targets'])
