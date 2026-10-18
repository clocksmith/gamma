import copy
import json
from pathlib import Path
import tempfile
import unittest

from algsolve.natural_description import DEFAULT_DATASET, evaluate_case, load_dataset, score, summarize


class NaturalDescriptionTests(unittest.TestCase):
    def test_recognizer_gets_only_authored_text(self):
        received = []
        case = {'id': 'example', 'family': 'pair', 'kind': 'informal',
                'query': 'Find the requested positions.',
                'expected': {'action': 'match', 'keys': ['lc:two-sum']}}

        def recognize(text):
            received.append(text)
            return {'decision': 'match', 'key': 'lc:two-sum', 'candidates': []}

        row = evaluate_case(case, recognize)
        self.assertEqual(received, [case['query']])
        self.assertTrue(row['correct_match'])
        self.assertGreaterEqual(row['seconds'], 0)

    def test_passing_tests_never_make_a_sibling_identity_correct(self):
        result = score({'action': 'match', 'keys': ['lc:house-robber-ii']},
                       {'decision': 'match', 'key': 'lc:house-robber',
                        'example_passed': True, 'independent_tests_passed': True,
                        'candidates': [{'key': 'lc:house-robber'}, {'key': 'lc:house-robber-ii'}]})
        self.assertFalse(result['decision_correct'])
        self.assertTrue(result['wrong_match'])
        self.assertTrue(result['top5_contains_identity'])

    def test_abstention_does_not_count_as_a_clarification(self):
        result = score({'action': 'clarify', 'keys': []},
                       {'decision': 'abstain', 'key': None, 'candidates': [{'key': 'lc:two-sum'}]})
        self.assertFalse(result['decision_correct'])
        self.assertFalse(result['wrong_match'])
        self.assertTrue(result['clarification_needed'])
        self.assertFalse(result['clarification_requested'])

    def test_equivalent_keys_are_allowed_but_abstentions_are_not_matches(self):
        expected = {'action': 'match', 'keys': ['lc:first', 'lc:equivalent']}
        self.assertTrue(score(expected, {'decision': 'match', 'key': 'lc:equivalent'})['correct_match'])
        with self.assertRaises(ValueError):
            score(expected, {'decision': 'abstain', 'key': 'lc:first'})

    def test_dataset_rejects_protected_duplicate_and_invalid_annotations(self):
        data = load_dataset(DEFAULT_DATASET)
        alternatives = []
        protected = copy.deepcopy(data)
        protected['partition'] = 'protected'
        alternatives.append(protected)
        duplicate = copy.deepcopy(data)
        duplicate['cases'].append(duplicate['cases'][0])
        alternatives.append(duplicate)
        missing = copy.deepcopy(data)
        missing['cases'][0]['expected']['keys'] = []
        alternatives.append(missing)
        clarification = copy.deepcopy(data)
        clarification['cases'][0]['expected'] = {'action': 'clarify', 'keys': []}
        alternatives.append(clarification)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'cases.json'
            for candidate in alternatives:
                with self.subTest(candidate=candidate['cases'][0]['expected']):
                    path.write_text(json.dumps(candidate))
                    with self.assertRaises(ValueError):
                        load_dataset(path)

    def test_report_keeps_wrong_acceptance_and_missing_clarifications_visible(self):
        cases = [
            {'id': 'known', 'family': 'f', 'kind': 'informal', 'query': 'known',
             'expected': {'action': 'match', 'keys': ['lc:right']}},
            {'id': 'unclear', 'family': 'f', 'kind': 'underspecified', 'query': 'unclear',
             'expected': {'action': 'clarify', 'keys': []}},
            {'id': 'outside', 'family': 'o', 'kind': 'out_of_domain', 'query': 'outside',
             'expected': {'action': 'abstain', 'keys': []}},
        ]
        rows = [evaluate_case(case, lambda _: {'decision': 'match', 'key': 'lc:wrong'}) for case in cases]
        report = summarize(rows)
        self.assertEqual(report['overall']['wrong_match'], 3)
        self.assertEqual(report['overall']['match_targets'], 1)
        self.assertEqual(report['overall']['clarification_needed'], 1)
        self.assertEqual(report['overall']['decision_correct'], 0)
        self.assertEqual(report['by_kind']['out_of_domain']['queries'], 1)
        with self.assertRaises(ValueError):
            summarize([])
