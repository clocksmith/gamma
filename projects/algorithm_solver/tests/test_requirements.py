import unittest
from algsolve.requirements import extract
from algsolve.clarify import ClarificationSession, load_profiles


class RequirementsTests(unittest.TestCase):
    def test_negated_sorted_does_not_turn_into_sorted(self):
        facts = extract('The list is not sorted in ascending order. Give zero-based positions.')
        self.assertEqual(facts['facts']['ordering'],'arbitrary')
        self.assertFalse(facts['conflicts'])
        self.assertNotIn('ordering',extract('What ordering does the list use?')['facts'])

    def test_conflicting_requirements_stay_visible(self):
        result = extract('Use zero-based positions. Return one-based positions.')
        self.assertIn('indexing',result['conflicts'])
        self.assertNotIn('indexing',result['facts'])

    def test_silence_does_not_mean_free_transactions(self):
        facts = extract('I can buy once for maximum profit.')['facts']
        self.assertEqual(facts['transactions'],'one')
        self.assertNotIn('fee',facts)
        self.assertNotIn('cooldown',facts)

    def test_existing_facts_skip_redundant_question_but_keep_confirmation(self):
        session = ClarificationSession('Houses around a closed block.',[{'key':'lc:house-robber'}],
                                       load_profiles(),facts={'layout':'circle'})
        step = session.next_step()
        self.assertEqual(step['decision'],'confirm')
        self.assertEqual(step['candidate']['key'],'lc:house-robber-ii')
        self.assertEqual(session.questions,0)

    def test_unsupported_combination_does_not_become_nearest_profile(self):
        session = ClarificationSession('Stock.',[{'key':'lc:best-time-to-buy-and-sell-stock'}],
                                       load_profiles(),facts={'fee':'per_trade','cooldown':'one_day'})
        self.assertEqual(session.next_step()['decision'],'abstain')


if __name__ == '__main__': unittest.main()
