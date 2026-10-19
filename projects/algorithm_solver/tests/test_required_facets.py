"""Developer-exposed synthetic behavior checks; no benchmark qualification."""
import copy
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from algsolve.answer import answer
from algsolve.lookup import LookupIndex
from algsolve.records import Problem
from algsolve.required_facets import RequiredFacets, answer_with_required_facets
from algsolve.routes import Budget, Context
from algsolve.splits import IndexEntry


FACTS = dict(transactions='unlimited', fee='none', cooldown='none', output='profit')
COMPLETE = 'Unlimited transactions. No fees or cooldown. Return maximum profit.'


def contract(statement, facts=FACTS):
    return dict(statement_sha256=hashlib.sha256(statement.encode()).hexdigest(),
                facts=facts.copy(), required_facets=list(facts))


class Approved:
    def identity_check(self, *args, **kwargs):
        return {'accepted': True}

    def check(self, entry):
        return {'approved': True}


def fixture(text=COMPLETE):
    source = IndexEntry('a', 'a', 'A', 'Stored stock specification', '',
                        {'class': 'Solution', 'method': 'profit'}, [['prices', 'List[int]']],
                        [], '', [], references=[{'code': 'fixture', 'validated': True}])
    other = copy.deepcopy(source)
    other.key, other.slug, other.statement = 'b', 'b', 'Second source'
    entries = [source, other]
    lookup = LookupIndex(entries, np.zeros((2, 1)))
    candidates = [{'key': 'a', 'score': .9}, {'key': 'b', 'score': .7}]
    lookup.scored_candidates = lambda *args: copy.deepcopy(candidates)
    context = Context(generator=None, embedder=SimpleNamespace(encode=lambda *a, **kw: np.zeros((1, 1))),
                      lookup=lookup, thresholds={'min_score': .6, 'min_margin': .01},
                      classifier=None, entries=entries, budget=Budget(1, 1, 0, 30, 5, 1, 1, 10))
    query = Problem('user:1', 'user', '1', '', '', text, 'functional',
                    public_tests=[{'args': [[2, 5]], 'expected': 3}])
    return context, query, RequiredFacets([contract(source.statement)])


PASS = SimpleNamespace(passed=True, reason='passed', to_dict=lambda: {'passed': True})


class RequiredFacetBehavior(unittest.TestCase):
    def test_missing_each_stock_requirement_cannot_be_filled_by_source_or_examples(self):
        clauses = ['Unlimited transactions.', 'No fees.', 'No cooldown.', 'Return maximum profit.']
        for i, facet in enumerate(FACTS):
            with self.subTest(facet=facet):
                context, query, gate = fixture(' '.join(c for j, c in enumerate(clauses) if i != j))
                with patch('algsolve.answer.check_stored') as execute:
                    result = answer_with_required_facets(context, query, Approved(), gate)
                self.assertEqual(result['reason'], 'required_facets_missing')
                self.assertIn(facet, result['match']['identity_check']['required_facets']['missing'])
                execute.assert_not_called()

    def test_rank_silence_and_alternative_semantics_fail_even_without_a_sibling(self):
        facts = dict(output='kth', updates='batch', duplicates='occurrences')
        for text, reason in [
                ('Return kth largest in one fixed array.', 'required_facets_missing'),
                ('Return kth largest in one fixed array. Count each distinct value once.', 'required_facets_contradiction'),
                ('Return kth largest in one fixed array. Maybe counting duplicate occurrences separately.', 'required_facets_uncertain')]:
            with self.subTest(text=text):
                context, query, _ = fixture(text)
                context.lookup.scored_candidates = lambda *a: [{'key': 'a', 'score': .99}]
                gate = RequiredFacets([contract(context.entries[0].statement, facts)])
                self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], reason)

    def test_complete_query_still_requires_approval_and_public_execution(self):
        context, query, gate = fixture()
        with patch('algsolve.answer.check_stored', return_value=('code', PASS)) as execute:
            result = answer_with_required_facets(context, query, Approved(), gate)
        self.assertEqual(result['decision'], 'answered')
        self.assertEqual(execute.call_count, 1)
        with patch.object(Approved, 'check', return_value={'approved': False}), patch('algsolve.answer.check_stored') as execute:
            self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], 'stored_answer_not_approved')
            execute.assert_not_called()

    def test_stale_or_unknown_selected_source_does_not_promote_next_candidate(self):
        context, query, _ = fixture()
        gate = RequiredFacets([contract('stale source'), contract(context.entries[1].statement)])
        with patch('algsolve.answer.check_stored') as execute:
            result = answer_with_required_facets(context, query, Approved(), gate)
        self.assertEqual(result['reason'], 'required_facets_unbound_source')
        self.assertEqual(result['source']['key'], 'a')
        self.assertEqual(result['match']['candidates'], [{'key': 'a', 'score': .9}, {'key': 'b', 'score': .7}])
        execute.assert_not_called()

    def test_conflict_uncertainty_and_contradiction_do_not_execute(self):
        for text, reason in [
                (COMPLETE + ' Buy once.', 'required_facets_conflict'),
                ('Unlimited transactions. No fees. Maybe no cooldown. Maximum profit.', 'required_facets_uncertain'),
                ('Buy once. No fees or cooldown. Maximum profit.', 'required_facets_contradiction')]:
            with self.subTest(text=text):
                context, query, gate = fixture(text)
                with patch('algsolve.answer.check_stored') as execute:
                    self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], reason)
                    execute.assert_not_called()

    def test_exact_missing_examples_and_default_route_are_unchanged(self):
        context, query, gate = fixture()
        gate.check = lambda *a: (_ for _ in ()).throw(AssertionError('guard bypass expected'))
        with patch('algsolve.answer.check_stored', return_value=('code', PASS)):
            self.assertEqual(answer(context, query, approved_library=Approved())['decision'], 'answered')
            query.statement = context.entries[0].statement
            self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['decision'], 'answered')
        query.public_tests = []
        self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], 'query_has_no_public_examples')

    def test_prior_identity_and_numeric_rejections_survive(self):
        context, query, gate = fixture()
        with patch.object(Approved, 'identity_check', return_value={'accepted': False, 'reason': 'sibling_ambiguous'}):
            self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], 'sibling_ambiguous')
        context.thresholds['min_score'] = .95
        self.assertEqual(answer_with_required_facets(context, query, Approved(), gate)['reason'], 'identity_not_confident')

    def test_malformed_contract_and_missing_library_rejected(self):
        for change in [dict(required_facets=[]), dict(required_facets=['unknown']), dict(statement_sha256='bad')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                RequiredFacets([dict(contract('source'), **change)])
        with self.assertRaises(ValueError):
            RequiredFacets([contract('source'), contract('source', dict(FACTS, fee='per_trade'))])
        context, query, gate = fixture()
        with self.assertRaises(ValueError):
            answer_with_required_facets(context, query, None, gate)


if __name__ == '__main__':
    unittest.main()
