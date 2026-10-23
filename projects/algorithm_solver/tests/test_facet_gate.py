"""Developer-exposed checks for the opt-in facet gate; no benchmark qualification."""
import hashlib
import unittest
from unittest.mock import patch

from algsolve.facet_gate import FacetGate, answer_with_facet_gate, parse
from test_required_facets import Approved, fixture

STOCK = dict(transactions='unlimited', fee='none', cooldown='none')


def doc(statement, facts=STOCK, required=None, defaults=None, completeness='reviewed'):
    return {'schema_version': 1, 'absence_defaults': defaults if defaults is not None else {'fee': 'none', 'cooldown': 'none'},
            'compatible': [['ordering', 'sorted', 'arbitrary']],
            'contracts': [{'source_key': 'a', 'family': 'stock', 'statement_sha256': hashlib.sha256(statement.encode()).hexdigest(),
                           'facts': dict(facts), 'required_facets': list(required if required is not None else facts),
                           'completeness': completeness}]}


class Grammar(unittest.TestCase):
    def test_absence_list_is_not_an_alternative_and_negates_its_terms(self):
        p = parse('Unlimited trades with no fees or cooldown.')
        self.assertEqual(p['facts'], STOCK)
        self.assertEqual(p['uncertain'], [])

    def test_adjacent_or_makes_the_phrase_uncertain(self):
        for text in ('You can do one or two transactions.', 'Buy once or twice.', 'Either one trade or unlimited trades.'):
            with self.subTest(text=text):
                p = parse(text)
                self.assertNotIn('transactions', p['facts'])
                self.assertIn('transactions', p['uncertain'])

    def test_distant_or_and_trailing_fallback_do_not(self):
        self.assertEqual(parse('Find the shortest consecutive slice whose sum reaches or exceeds the target.')['facts'],
                         {'output': 'shortest_window', 'relation': 'at_least'})
        self.assertEqual(parse('Return the two positions, or -1 if none.')['facts'], {'output': 'positions'})

    def test_hedges_and_opening_conditionals_but_not_permission(self):
        self.assertIn('fee', parse('If there is a fee, it is charged per trade.')['uncertain'])
        self.assertIn('transactions', parse('Maybe unlimited transactions.')['uncertain'])
        self.assertEqual(parse('You may complete at most two transactions.')['facts'], {'transactions': 'two'})

    def test_negated_positive_value_is_not_evidence(self):
        self.assertNotIn('cooldown', parse('There is never a cooldown period after selling.')['facts'])
        self.assertEqual(parse('without a cooldown')['facts'], {'cooldown': 'none'})

    def test_negated_absence_phrase_is_uncertain(self):
        for text in ('It is not true that there are no fees.', 'It is false that there is no cooldown.', 'There are not no fees.'):
            with self.subTest(text=text):
                p = parse(text)
                self.assertEqual(p['facts'], {})
                self.assertEqual(len(p['uncertain']), 1)
        facts = parse('The array is not circular and no deletions are allowed.')['facts']
        self.assertEqual((facts['layout'], facts['deletion']), ('line', 'none'))

    def test_multiple_or_repeated_trades_are_not_unlimited(self):
        for text in ('I can repeatedly buy and sell.', 'You may make multiple trades.', 'Several transactions are fine.'):
            with self.subTest(text=text):
                self.assertNotIn('transactions', parse(text)['facts'])
        self.assertEqual(parse('Multiple trades, at most three transactions.')['facts']['transactions'], 'bounded_other')

    def test_exactly_one_forbids_zero_trades(self):
        p = parse('You must complete exactly one transaction, even if it loses money.')
        self.assertEqual((p['facts']['transactions'], p['facts']['zero_trade']), ('one', 'forbidden'))
        self.assertEqual(parse('Buy once and sell later, or do nothing.')['facts']['zero_trade'], 'allowed')

    def test_two_certain_values_conflict(self):
        self.assertEqual(parse('Unlimited transactions. Buy once.')['conflicts'], {'transactions': ['one', 'unlimited']})


class Gate(unittest.TestCase):
    def setUp(self):
        self.context, self.query, _ = fixture('Unlimited transactions. Return maximum profit.')
        self.entry = self.context.entries[0]

    def check(self, text, **kw):
        return FacetGate(doc(self.entry.statement, **kw)).check(text, self.entry)

    def test_trade_count_never_defaults(self):
        r = self.check('Hold at most one share. No fees or cooldown. Maximum profit.')
        self.assertEqual((r['reason'], r['missing']), ('facet_gate_missing', ['transactions']))

    def test_add_on_features_default_only_when_unmentioned(self):
        r = self.check('Unlimited transactions. Maximum profit.')
        self.assertTrue(r['accepted'])
        self.assertEqual(r['settled'], {'transactions': 'explicit', 'fee': 'absent_add_on', 'cooldown': 'absent_add_on'})
        self.assertEqual(self.check('Unlimited transactions. If there is a fee, it is per trade.')['reason'], 'facet_gate_missing')
        self.assertEqual(self.check('Unlimited transactions. If a fee is charged per trade, subtract it.')['reason'], 'facet_gate_uncertain')
        self.assertEqual(self.check('Unlimited transactions with a transaction fee of 2.')['reason'], 'facet_gate_contradiction')

    def test_defaults_cannot_cover_output_count_or_duplicates(self):
        for facet in ('transactions', 'duplicates', 'output', 'holding', 'connectivity', 'relation'):
            with self.subTest(facet=facet), self.assertRaises((ValueError, KeyError)):
                FacetGate(doc(self.entry.statement, defaults={facet: 'x'}))

    def test_compatible_value_is_not_a_contradiction(self):
        r = self.check('The array is sorted in ascending order. Return the two indices.',
                       facts=dict(output='positions', ordering='arbitrary'), required=['output', 'ordering'])
        self.assertTrue(r['accepted'], r)

    def test_unbound_and_unreviewed_sources_abstain(self):
        gate = FacetGate(doc('other statement'))
        self.assertEqual(gate.check('anything', self.entry)['reason'], 'facet_gate_unbound_source')
        r = self.check('Unlimited transactions. No fees or cooldown.', completeness='unreviewed')
        self.assertEqual(r['reason'], 'facet_gate_unreviewed_source')
        self.assertTrue(self.check('anything at all', facts={}, required=[])['accepted'])  # reviewed: no facet changes the answer

    def test_strict_document_never_settles_by_silence(self):
        r = self.check('Unlimited transactions. Maximum profit.', defaults={})
        self.assertEqual((r['reason'], r['missing']), ('facet_gate_missing', ['cooldown', 'fee']))

    def test_reviewer_counterexamples_abstain(self):
        for text in ('Buy and sell any number of times. A brokerage charge is subtracted on every sale.',
                     'Buy and sell any number of times. It is not true that there are no fees.'):
            for defaults in ({}, {'fee': 'none', 'cooldown': 'none'}):
                with self.subTest(text=text, defaults=defaults):
                    self.assertFalse(self.check(text, defaults=defaults)['accepted'])


class Route(unittest.TestCase):
    def test_rejection_abstains_without_execution_or_replacement(self):
        context, query, _ = fixture('Hold one share at most. No fees or cooldown. Maximum profit.')
        gate = FacetGate(doc(context.entries[0].statement))
        with patch('algsolve.answer.check_stored') as execute:
            result = answer_with_facet_gate(context, query, Approved(), gate)
        self.assertEqual(result['decision'], 'abstain')
        self.assertEqual(result['reason'], 'facet_gate_missing')
        self.assertEqual(result['match']['key'], 'a')  # the lower-ranked source never replaces it
        execute.assert_not_called()

    def test_complete_request_still_needs_public_execution(self):
        context, query, _ = fixture('Unlimited transactions. No fees or cooldown. Return maximum profit.')
        gate = FacetGate(doc(context.entries[0].statement))
        with patch('algsolve.answer.check_stored') as execute:
            verdict = type('R', (), {'passed': False, 'reason': 'wrong_answer', 'to_dict': lambda self: {'passed': False}})()
            execute.return_value = ('code', verdict)
            result = answer_with_facet_gate(context, query, Approved(), gate)
        execute.assert_called()
        self.assertEqual(result['decision'], 'abstain')


if __name__ == '__main__':
    unittest.main()
