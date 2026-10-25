"""Synthetic metadata mechanism tests, not informal-recognition evaluation."""
import copy
import unittest

from .recognition_bridge import RecognitionBridge
from .retrieval import KnownCatalogue
from . import test_catalogue


class RecognitionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_catalogue.Catalogue().fixture()
        self.library = KnownCatalogue(*self.fixture)
        self.identities = {'index:a': ['a'], 'index:b': ['b']}
        self.bridge = RecognitionBridge(self.library, self.identities)
        self.match = {'decision': 'match', 'key': 'index:a',
                      'candidates': [{'key': 'index:a', 'score': .9},
                                     {'key': 'index:b', 'score': .8}],
                      'identity_check': {'accepted': True}}
        self.boundary = {'key': 'index:a', 'accepted': True}

    def retrieve(self, match=None, boundary=None):
        return self.bridge.retrieve(self.match if match is None else match,
                                    boundary_check=self.boundary if boundary is None else boundary)

    def test_same_identity_returns_both_independently_qualified_languages(self):
        value = self.retrieve()
        self.assertEqual(value['problem_id'], 'a')
        self.assertEqual(set(value['implementations']), {'javascript', 'python'})
        self.assertEqual(value['clarification_questions'], [])
        for language in ('javascript', 'python'):
            self.assertEqual(self.library.select_language(value, language)['problem_id'], 'a')
        self.assertNotIn('code', value)
        self.assertNotIn('example_passed', value)

    def test_existing_confidence_and_identity_fail_closed(self):
        for change in ({'decision': 'abstain'}, {'identity_check': {}},
                       {'identity_check': {'accepted': 1}}, {'identity_check': {'accepted': False}}):
            value = self.retrieve(dict(self.match, **change))
            self.assertEqual(value['status'], 'abstain')
            self.assertEqual(value['clarification_questions'], [])

    def test_boundary_must_accept_and_bind_same_candidate(self):
        for boundary in ({}, {'key': 'index:a', 'accepted': 1},
                         {'key': 'index:a', 'accepted': False},
                         {'key': 'index:b', 'accepted': True}):
            self.assertEqual(self.retrieve(boundary=boundary)['reason'], 'boundary_not_accepted')

    def test_match_must_bind_top_candidate(self):
        for change in ({'key': 'index:b'}, {'key': []}, {'candidates': []},
                       {'candidates': [None]}, {'candidates': 'index:a'}):
            self.assertEqual(self.retrieve(dict(self.match, **change))['status'], 'abstain')

    def test_unavailable_and_ambiguous_metadata_never_redirect(self):
        for identities, reason in (({}, 'candidate_identity_unavailable'),
                                  ({'index:a': 'a'}, 'candidate_identity_unavailable'),
                                  ({'index:a': [None]}, 'candidate_identity_unavailable'),
                                  ({'index:a': ['a', 'b']}, 'candidate_identity_ambiguous'),
                                  ({'index:a': ['unknown']}, 'unknown_problem_identity')):
            bridge = RecognitionBridge(self.library, identities)
            self.assertEqual(bridge.retrieve(self.match, boundary_check=self.boundary)['reason'], reason)

    def test_missing_language_does_not_change_recognition(self):
        u, c, r = self.fixture
        c['problems'][0]['implementations']['python'] = {'status': 'missing', 'reason': 'not authored'}
        self.bridge = RecognitionBridge(KnownCatalogue(u, c, r), self.identities)
        value = self.retrieve()
        self.assertEqual(value['problem_id'], 'a')
        self.assertEqual(set(value['implementations']), {'javascript'})
        self.assertEqual(self.library.select_language(value, 'python')['status'], 'abstain')

    def test_no_qualified_implementation_abstains_not_runner_up(self):
        u, c, r = self.fixture
        for language in ('javascript', 'python'):
            c['problems'][0]['implementations'][language] = {'status': 'blocked', 'reason': 'missing evidence'}
        self.bridge = RecognitionBridge(KnownCatalogue(u, c, r), self.identities)
        self.assertEqual(self.retrieve()['reason'], 'no_qualified_implementation')

    def test_protected_identity_stays_unavailable(self):
        from .catalogue import digest
        u, c, r = self.fixture
        u['protected_problem_ids'] = ['a']; c['universe_sha256'] = digest(u)
        for language in ('javascript', 'python'):
            c['problems'][0]['implementations'][language] = {'status': 'protected', 'reason': 'authority required'}
        self.bridge = RecognitionBridge(KnownCatalogue(u, c, r), self.identities)
        self.assertEqual(self.retrieve()['reason'], 'no_qualified_implementation')

    def test_ambiguity_is_not_resolved_by_available_language(self):
        u, c, r = self.fixture
        for language in ('javascript', 'python'):
            c['problems'][1]['implementations'][language] = {'status': 'missing', 'reason': 'not authored'}
        self.bridge = RecognitionBridge(KnownCatalogue(u, c, r), {'index:a': ['a', 'b']})
        self.assertEqual(self.retrieve()['reason'], 'candidate_identity_ambiguous')

    def test_input_and_output_mutations_do_not_change_identity_or_catalogue(self):
        self.identities['index:a'][0] = 'b'
        before = copy.deepcopy(self.match)
        value = self.retrieve(); value['implementations'].clear()
        self.assertEqual(self.match, before)
        self.assertEqual(self.retrieve()['problem_id'], 'a')
        self.assertEqual(len(self.retrieve()['implementations']), 2)

    def test_stale_qualification_cannot_enter_bridge(self):
        u, c, r = self.fixture
        c['problems'][0]['implementations']['python']['source_sha256'] = 'c' * 64
        with self.assertRaises(ValueError):
            RecognitionBridge(KnownCatalogue(u, c, r), self.identities)


if __name__ == '__main__':
    unittest.main()
