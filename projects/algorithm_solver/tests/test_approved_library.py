import copy
import unittest
from unittest.mock import patch

from algsolve.approved_library import ApprovedLibrary, build, code_hash
from algsolve.answer import answer
from test_answer import context, query


def fixture():
    entry = context().entries[0]
    ref = entry.references[0]
    ref.update(uid='source:max', source='fixture')
    sha = code_hash(ref['code'])
    inventory = [{'key': entry.key, 'identity_valid': True, 'provenance_present': True,
                  'interface_compatible': True, 'references': [{'code_sha256': sha}],
                  'independent_test_sets': [{'uid': 'source:max', 'tests': 5, 'sha256': 'test-fixture'}]}]
    result = [{'key': entry.key, 'accepted_and_correct': True, 'result': {'code_sha256': sha},
               'stored_solution': {'status': 'passed', 'verdicts': [
                   {'passed': True, 'tests_total': 5, 'tests_passed': 5}]}}]
    return entry, inventory, result


class ApprovedLibraryTests(unittest.TestCase):
    def test_exact_statement_skips_embedding_but_still_executes_public_gate(self):
        from algsolve.judge.judge import Verdict
        entry, inventory, rows = fixture()
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={}))
        ctx = context()
        ctx.entries[0] = entry
        q = query(3)
        q.statement, q.starter_code = entry.statement, entry.starter_code
        with patch.object(ctx.embedder, 'encode', side_effect=AssertionError('Exact lookup must not embed')), \
                patch('algsolve.answer.validate.judge_problem', return_value=Verdict(True, None, 1, 1, 0)) as check:
            result = answer(ctx, q, approved_library=catalog)
        self.assertEqual(result['decision'], 'answered')
        self.assertTrue(result['match']['exact_statement_and_interface'])
        check.assert_called_once()

    def test_duplicate_exact_text_and_changed_internal_whitespace_are_not_exact(self):
        import numpy as np
        from algsolve.lookup import LookupIndex
        ctx = context()
        text = ctx.entries[0].query_text()
        self.assertIsNone(ctx.lookup.exact_key(text.replace('the maximum', 'the  maximum')))
        other = copy.deepcopy(ctx.entries[0]); other.key = 'lc:other'
        index = LookupIndex([ctx.entries[0], other], np.array([[1., 0.], [1., 0.]]))
        self.assertIsNone(index.exact_key(text))

    def test_editor_generated_starter_preserves_exact_problem_identity(self):
        from algsolve.editor_execution import query_problem
        ctx = context(); entry = ctx.entries[0]
        q = query_problem({'statement':entry.statement, 'entry':entry.entry, 'params':entry.params,
                           'starter_code':'class Solution:\n    def solve(self, nums):\n        pass\n'})
        self.assertEqual(ctx.lookup.exact_problem_key(q), entry.key)
        q.params = [['target', 'int']]
        self.assertIsNone(ctx.lookup.exact_problem_key(q))

    def test_sibling_tie_cannot_be_approved_by_shared_examples(self):
        import numpy as np
        from algsolve.lookup import LookupIndex
        entry, inventory, rows = fixture()
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={}))
        other = copy.deepcopy(entry); other.slug += '-ii'; other.key += '-ii'
        index = LookupIndex([entry, other], np.array([[1., 0.], [1., 0.]]))
        scores = [{'key': entry.key, 'score': 1.2}, {'key': other.key, 'score': 1.19}]
        self.assertFalse(catalog.identity_check(entry, scores, index)['accepted'])
        scores[1]['score'] = 1.1
        self.assertTrue(catalog.identity_check(entry, scores, index)['accepted'])
        scores[1]['score'] = 1.2
        self.assertTrue(catalog.identity_check(entry, scores, index, exact=True)['accepted'])

    def test_statement_only_binding_comes_from_selected_source_not_oracle(self):
        from algsolve.judge.judge import Verdict
        from algsolve.recognition_release import public_problem
        q = public_problem({'query':'Return the largest value.', 'public_examples':[{'args':[[2,3]], 'expected':3}],
                            'signature':{'method':'oracle_sentinel'}, 'private_checks':['secret']})
        self.assertEqual(q.entry, {})
        self.assertEqual(q.starter_code, '')
        ctx = context()
        with patch('algsolve.answer.validate.judge_problem', return_value=Verdict(True,None,1,1,0)) as check:
            result = answer(ctx, q)
        self.assertEqual(check.call_args.args[0].entry, ctx.entries[0].entry)
        self.assertNotIn('oracle_sentinel', result['code'])
        self.assertEqual(result['answer_interface'], {'class':'Solution', 'method':'solve'})
        self.assertNotIn('secret', str(check.call_args))

    def test_complete_evidence_is_bound_to_source_and_provenance(self):
        entry, inventory, rows = fixture()
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={'fixture': True}))
        self.assertTrue(catalog.check(entry)['approved'])
        for field in ('statement', 'starter_code', 'attribution', 'references'):
            changed = copy.deepcopy(entry)
            if field == 'references':
                changed.references[0]['code'] += '\n# changed'
            elif field == 'attribution':
                changed.attribution = ['someone else']
            else:
                setattr(changed, field, getattr(changed, field) + 'changed')
            self.assertEqual(catalog.check(changed)['reason'], 'source_changed_since_qualification')

    def test_incomplete_and_duplicate_audits_cannot_create_catalog(self):
        entry, inventory, rows = fixture()
        for result in ([], rows + rows):
            with self.assertRaises(ValueError):
                build([entry], inventory, result, evidence={})

    def test_missing_failed_empty_or_wrong_identity_is_never_approved(self):
        for mode in ('missing', 'failed', 'empty', 'identity', 'changed_code'):
            entry, inventory, rows = fixture()
            if mode in ('missing', 'failed'):
                rows[0]['stored_solution']['status'] = mode
            elif mode == 'empty':
                rows[0]['stored_solution']['verdicts'] = []
            elif mode == 'identity':
                rows[0]['accepted_and_correct'] = False
            else:
                rows[0]['result']['code_sha256'] = 'different'
            manifest = build([entry], inventory, rows, evidence={})
            self.assertFalse(ApprovedLibrary(manifest).check(entry)['approved'], mode)

    def test_manifest_tampering_is_rejected(self):
        entry, inventory, rows = fixture()
        manifest = build([entry], inventory, rows, evidence={})
        manifest['approved'][entry.key]['code_sha256'] = 'different'
        with self.assertRaises(ValueError):
            ApprovedLibrary(manifest)

    def test_unapproved_top_match_does_not_run_or_fall_through(self):
        entry, inventory, rows = fixture()
        rows[0]['stored_solution']['status'] = 'missing_independent_tests'
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={}))
        ctx = context()
        with patch('algsolve.answer.check_stored') as run:
            result = answer(ctx, query(3), approved_library=catalog)
        self.assertEqual(result['reason'], 'stored_answer_not_approved')
        self.assertIsNone(result['code'])
        run.assert_not_called()
        with self.assertRaises(ValueError):
            answer(ctx, query(3), approved_library=catalog, allow_generation=True)

    def test_query_identity_conflict_never_reaches_public_judge(self):
        entry, inventory, rows = fixture()
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={}))
        q = query(3); q.slug = 'sum'
        with patch('algsolve.answer.check_stored') as run:
            result = answer(context(), q, approved_library=catalog)
        self.assertEqual(result['reason'], 'query_identity_conflict')
        run.assert_not_called()

    def test_approved_reference_still_requires_query_public_checks(self):
        from algsolve.judge.judge import Verdict, WRONG_ANSWER
        entry, inventory, rows = fixture()
        catalog = ApprovedLibrary(build([entry], inventory, rows, evidence={}))
        ctx = context()
        ctx.entries[0] = entry
        with patch('algsolve.answer.validate.judge_problem', return_value=Verdict(False, WRONG_ANSWER, 1, 0, 0)):
            result = answer(ctx, query(), approved_library=catalog)
        self.assertIsNone(result['code'])
        self.assertTrue(result['source']['qualification']['approved'])
        self.assertIsNone(result['independent_tests_passed'])


if __name__ == '__main__':
    unittest.main()
