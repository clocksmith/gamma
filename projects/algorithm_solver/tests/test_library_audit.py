import tempfile
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from algsolve.library_audit import (audit_one, check_seal, digest, exact_query,
                                   independent_score, inventory_entry, original_for, sha)
from algsolve.library_audit import summarize
from algsolve.recognition_boundary import exclusion_closure
from algsolve.recognition_metrics import wilson
from algsolve.records import Problem
from algsolve.splits import IndexEntry


class BoundaryTests(unittest.TestCase):
    def test_alias_closure_is_transitive_in_both_directions(self):
        def entry(key, uid):
            return dict(key='lc:'+key, slug=key, members=[uid], judge_uid=uid)
        entries = [entry('reserved', 'a'), entry('renamed', 'b'),
                   entry('renamed-ii', 'c'), entry('safe', 'd')]
        reservation = {'reservation': {'pool': [dict(key='lc:reserved', family='reserved',
                                                     members=['a'], judge_uid='a')]}}
        metadata = [dict(uid=r['judge_uid'], slug=r['slug']) for r in entries]
        aliases = {'pairs': [dict(index_key='lc:renamed', pool_uid='a')]}
        result = exclusion_closure(entries, metadata, reservation, aliases)
        self.assertEqual(set(result['keys']), {'lc:reserved', 'lc:renamed', 'lc:renamed-ii'})
        self.assertEqual(set(result['uids']), {'a', 'b', 'c'})


class LibraryAuditTests(unittest.TestCase):
    def setUp(self):
        self.problem = Problem(uid='source:1', source='source', source_id='1', title='One', slug='one',
                               statement='Original.', io_mode='functional', entry={'class':'Solution','method':'f'},
                               params=[['x','int']], evidence_ceiling='independent_tests_passed',
                               hidden_tests_path='tests/one.json', public_tests=[{'args':[1],'expected':2}])
        self.entry = IndexEntry(key='lc:one', slug='one', title='One', statement='Indexed statement.',
                                starter_code='class Solution:\n def f(self, x: int) -> int: ...',
                                entry=self.problem.entry, params=self.problem.params, tags=[], difficulty='Easy',
                                members=['source:1'], judge_uid='source:1',
                                references=[{'uid':'source:1','source':'source','code':'CODE','validated':True}],
                                license=['license'], attribution=['source'])
        self.problems = {'source:1':self.problem}

    @patch('algsolve.library_audit.load_hidden_tests', return_value=[])
    def test_empty_tests_never_qualify_as_independent(self, load):
        inventory = inventory_entry(self.entry, self.problems, {})
        self.assertEqual(inventory['independent_coverage'], 'missing_independent_tests')
        with patch('algsolve.library_audit.validate.judge_problem') as judge:
            score = independent_score(self.entry, 'CODE', self.problems, inventory)
            self.assertEqual(score['status'], 'missing_independent_tests')
            judge.assert_not_called()

    def test_incompatible_interface_cannot_borrow_an_oracle(self):
        self.problem.params = [['x','str']]
        self.assertEqual(original_for(self.entry, self.problems), (None, []))
        query = exact_query(self.entry, None)
        self.assertEqual(query.statement, self.entry.statement)
        self.assertFalse(query.hidden_tests_path)

    def test_actual_query_preserves_indexed_text_without_private_inputs(self):
        self.problem.reference_solutions = ['SECRET']
        query = exact_query(self.entry, self.problem)
        self.assertEqual(query.query_text(), self.entry.query_text())
        self.assertEqual(query.public_tests, self.problem.public_tests)
        self.assertEqual(query.reference_solutions, [])
        self.assertFalse(query.hidden_tests_path)

    @patch('algsolve.library_audit.independent_score', return_value={'status':'passed','verdicts':[]})
    def test_wrong_identity_is_wrong_even_when_available_tests_pass(self, score):
        result = {'decision':'answered','code':'CODE','seconds':.1,
                  'match':{'key':'lc:sibling','candidates':[{'key':'lc:sibling'},{'key':'lc:one'}]}}
        inventory = {'family':'one','historical_verified':True}
        with patch('algsolve.library_audit.answer', return_value=result) as route:
            row = audit_one(self.entry, object(), self.problems, inventory)
        route.assert_called_once()
        self.assertTrue(row['wrong_acceptance'])
        self.assertFalse(row['accepted_and_correct'])
        self.assertTrue(row['top_five'])

    def test_test_identity_change_fails_closed(self):
        inventory = {'independent_coverage':'available', 'independent_test_sets':[
            {'uid':'source:1','sha256':digest([{'args':[1],'expected':2}])}]}
        with patch('algsolve.library_audit.load_hidden_tests', return_value=[{'args':[1],'expected':3}]):
            with self.assertRaisesRegex(ValueError, 'changed after seal'):
                independent_score(self.entry,'CODE',self.problems,inventory)

    def test_wilson_empty_and_zero_success_do_not_claim_certainty(self):
        self.assertIsNone(wilson(0,0))
        low, high = wilson(0,10)
        self.assertAlmostEqual(low,0)
        self.assertGreater(high,.2)

    def test_report_corrects_checker_classification_without_rewriting_receipts(self):
        score = {'status':'failed','verdicts':[{'passed':False,'reason':'checker_error','tests_total':1}]}
        row = {'key':'lc:one','historical_gap':False,'accepted':True,'identity_correct':True,
               'wrong_acceptance':True,'accepted_unqualified':False,'accepted_and_correct':False,
               'stored_solution':score,'returned_solution':score}
        inventory = {'key':'lc:one','historical_verified':True,'identity_valid':True,
                     'provenance_present':True,'interface_compatible':True}
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            original = json.dumps(row)+'\n'
            (directory/'answers.jsonl').write_text(original)
            (directory/'inventory.jsonl').write_text(json.dumps(inventory)+'\n')
            with patch('algsolve.recognition_metrics.summarize_results', side_effect=lambda rows: rows[0]):
                result = summarize(directory)
            self.assertFalse(result['metrics']['wrong_acceptance'])
            self.assertTrue(result['metrics']['accepted_unqualified'])
            self.assertEqual(result['reclassified_evidence_records'],2)
            self.assertEqual((directory/'answers.jsonl').read_text(),original)


if __name__ == '__main__':
    unittest.main()
