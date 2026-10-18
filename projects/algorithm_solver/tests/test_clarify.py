import copy
import unittest

from algsolve.clarify import ClarificationSession, load_profiles
from algsolve.clarification_evaluation import drive, load_dialogues, summarize


class ClarificationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_profiles()

    def session(self, keys, **options):
        return ClarificationSession('My described problem.', [{'key': key} for key in keys], self.catalog, **options)

    def test_house_question_explains_a_real_difference_and_retains_unknowns(self):
        session = self.session(['lc:house-robber-ii', 'lc:house-robber', 'lc:unprofiled'])
        step = session.next_step()
        self.assertEqual(step['facet'], 'layout')
        self.assertIn('adjacency', step['question'])
        self.assertEqual({x['value'] for x in step['options']}, {'line', 'circle', 'tree', 'other', 'unsure'})
        self.assertEqual(step['unprofiled_candidates'], ['lc:unprofiled'])
        narrowed = session.answer(step['question_id'], 'line')
        self.assertEqual(narrowed['decision'], 'confirm')
        self.assertEqual(narrowed['candidate']['key'], 'lc:house-robber')
        self.assertEqual(narrowed['unprofiled_candidates'], ['lc:unprofiled'])

    def test_no_identity_is_accepted_without_bound_explicit_confirmation(self):
        session = self.session(['lc:house-robber'])
        step = session.next_step()
        step = session.answer(step['question_id'], 'circle')
        self.assertEqual(step['decision'], 'confirm')
        with self.assertRaises(ValueError):
            session.answer(step['question_id'], 'yes', reviewed_statement_sha256='different')
        self.assertEqual(session.next_step(), step)
        result = session.answer(step['question_id'], 'yes', reviewed_statement_sha256=step['candidate']['statement_sha256'])
        self.assertEqual(result['key'], 'lc:house-robber-ii')
        self.assertEqual(result['selection_basis'], 'user_confirmed_statement')
        self.assertIsNone(result['code'])
        self.assertIsNone(result['example_passed'])

    def test_stale_cross_session_and_invalid_choices_cannot_change_state(self):
        first = self.session(['lc:house-robber'])
        second = self.session(['lc:house-robber'])
        a, b = first.next_step(), second.next_step()
        for token, value in ((a['question_id'], 'line'), (b['question_id'], 'not-an-option')):
            with self.assertRaises(ValueError):
                second.answer(token, value)
        self.assertEqual(second.next_step(), b)
        second.answer(b['question_id'], 'circle')
        with self.assertRaises(ValueError):
            second.answer(b['question_id'], 'line')

    def test_unsure_other_rejection_and_cancellation_never_guess(self):
        for reply in ('other', 'unsure'):
            session = self.session(['lc:house-robber'])
            result = session.answer(session.next_step()['question_id'], reply)
            self.assertEqual(result['decision'], 'abstain')
            self.assertIsNone(result['key'])
        session = self.session(['lc:house-robber'])
        step = session.answer(session.next_step()['question_id'], 'line')
        result = session.answer(step['question_id'], 'no')
        self.assertEqual(result['reason'], 'statement_rejected')
        session = self.session(['lc:house-robber'])
        step = session.next_step()
        self.assertEqual(session.cancel()['reason'], 'cancelled')
        with self.assertRaises(ValueError):
            session.answer(step['question_id'], 'line')

    def test_question_budget_and_unknown_contracts_abstain(self):
        session = self.session(['lc:best-time-to-buy-and-sell-stock'], max_questions=1)
        step = session.next_step()
        self.assertEqual(step['facet'], 'transactions')
        result = session.answer(step['question_id'], 'unlimited')
        self.assertEqual(result['reason'], 'question_budget_exhausted')
        unknown = self.session(['lc:unprofiled']).next_step()
        self.assertEqual(unknown['decision'], 'abstain')
        self.assertEqual(unknown['unprofiled_candidates'], ['lc:unprofiled'])

    def test_missing_fact_is_not_treated_as_a_negative_requirement(self):
        catalog = copy.deepcopy(self.catalog)
        profiles = [p for p in catalog['profiles'] if p['facts']['family'] == 'houses']
        profiles[1]['facts'].pop('layout')
        catalog['profiles'] = profiles
        session = ClarificationSession('Houses.', [{'key': 'lc:house-robber'}], catalog)
        self.assertEqual(session.next_step()['reason'], 'contracts_do_not_distinguish_candidates')

    def test_duplicate_semantic_contracts_are_not_arbitrarily_selected(self):
        catalog = copy.deepcopy(self.catalog)
        a = next(p for p in catalog['profiles'] if p['key'] == 'lc:house-robber')
        b = copy.deepcopy(a)
        b['key'] = 'lc:equivalent-or-incomplete-contract'
        catalog['profiles'] = [a, b]
        session = ClarificationSession('Houses.', [{'key': a['key']}], catalog)
        self.assertEqual(session.next_step()['decision'], 'abstain')

    def test_allocation_budget_keeps_omitted_alternatives_visible(self):
        session = self.session(['lc:house-robber'], max_candidates=1)
        step = session.next_step()
        self.assertEqual(step['decision'], 'confirm')
        self.assertEqual(len(step['omitted_candidates']), 2)

    def test_driver_uses_requirement_values_not_expected_identity(self):
        session = self.session(['lc:house-robber'])
        result = drive(session, {'layout': 'circle'}, 'yes')
        self.assertEqual(result['key'], 'lc:house-robber-ii')
        row = {'kind': 'fixture', 'expected_key': 'lc:house-robber', 'result': result,
               'history': session.history, 'machine_seconds': .2, 'dialogue_seconds': .001}
        report = summarize([row])
        self.assertEqual(report['overall']['wrong_acceptances'], 1)
        self.assertEqual(report['overall']['correct_selected_identity'], 0)
        self.assertEqual(report['genuine_absent_algorithm_cases'], 0)
        self.assertIsNone(report['human_journey_time'])

    def test_returned_prompts_cannot_mutate_live_session(self):
        session = self.session(['lc:house-robber'])
        step = session.next_step()
        step['options'].append({'value': 'injected', 'label': 'Injected'})
        with self.assertRaises(ValueError):
            session.answer(step['question_id'], 'injected')

    def test_development_dialogues_are_loaded_without_implying_qualification(self):
        document, cases = load_dialogues()
        self.assertEqual(document['partition'], 'development')
        self.assertEqual(len(cases), 28)
        self.assertEqual(sum(c['kind'] == 'unsupported_variant' for c in cases), 4)
