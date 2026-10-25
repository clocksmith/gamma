import unittest
from .interpretation_gate import Facet, InterpretationEnvelope, refine, identity_decision


class InterpretationRefinement(unittest.TestCase):
    def envelope(self, ids=('one', 'unlimited'), outside=True):
        return InterpretationEnvelope(frozenset(ids), outside, 'a'*64, 'b'*64, 'c'*64)

    def test_top_retrieved_candidate_does_not_remove_omitted_sibling(self):
        e = refine(self.envelope(outside=False), {'one': Facet.SATISFIED})
        self.assertEqual(e.identities, frozenset(('one', 'unlimited')))
        self.assertEqual(identity_decision(e)['status'], 'abstain')

    def test_open_world_survives_catalogue_singleton(self):
        e = refine(self.envelope(), {'unlimited': Facet.VIOLATED})
        self.assertEqual(identity_decision(e)['reason'], 'outside_catalogue_interpretation_possible')

    def test_closed_sound_refinement_can_reach_conditional_singleton(self):
        e = refine(self.envelope(), {'unlimited': Facet.VIOLATED}, outside_verdict=Facet.VIOLATED)
        d = identity_decision(e)
        self.assertEqual(d['problem_id'], 'one')
        self.assertFalse(d['recognition_qualified'])
        self.assertEqual(d['query_sha256'], 'b'*64)

    def test_unknown_never_eliminates(self):
        e = self.envelope()
        self.assertEqual(refine(e, {'one': Facet.UNKNOWN}), e)

    def test_refinement_is_monotone_and_preserves_binding(self):
        e = refine(self.envelope(), {'unlimited': Facet.VIOLATED}, outside_verdict=Facet.VIOLATED)
        self.assertEqual(refine(e, {'one': Facet.SATISFIED}, outside_verdict=Facet.SATISFIED), e)
        with self.assertRaises(ValueError):
            refine(e, {'unlimited': Facet.SATISFIED})

    def test_empty_envelope_abstains_not_vacuous_acceptance(self):
        e = refine(self.envelope(outside=False), {'one': Facet.VIOLATED, 'unlimited': Facet.VIOLATED})
        self.assertEqual(identity_decision(e)['status'], 'abstain')

    def test_no_scores_booleans_or_string_claims(self):
        for value in (True, .99, 'satisfied', 'proved'):
            with self.assertRaises(ValueError):
                refine(self.envelope(), {'one': value})
        with self.assertRaises(TypeError):
            identity_decision({'identities': ['one'], 'complete': True})

    def test_all_small_refinements_have_subset_property(self):
        from itertools import product
        e = self.envelope(('a','b','c'))
        for values in product(Facet, repeat=4):
            r = refine(e, dict(zip(('a','b','c'), values)), outside_verdict=values[3])
            self.assertLessEqual(r.identities, e.identities)
            self.assertEqual(len(r.identities), sum(x is not Facet.VIOLATED for x in values[:3]))
