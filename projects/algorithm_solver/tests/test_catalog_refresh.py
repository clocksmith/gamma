"""Fresh catalog evidence boundary and explicit serving policy checks."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from algsolve.approved_library import ApprovedLibrary,build,digest
from algsolve.catalog_refresh import _validate_rows,build_catalog,run,import_public
from test_approved_library import fixture


class CatalogRefreshTests(unittest.TestCase):
    def test_policy_is_explicit_strict_and_digest_bound(self):
        e,inv,rows=fixture()
        old=ApprovedLibrary(build([e],inv,rows,evidence={}))
        self.assertNotIn('answer_policy',old.manifest)
        valid=build([e],inv,rows,evidence={},answer_policy={'public_output_contracts':True})
        self.assertTrue(ApprovedLibrary(valid).manifest['answer_policy']['public_output_contracts'])
        for policy in [{'public_output_contracts':'true'},{'public_output_contracts':1},{'unknown':True},{}]:
            with self.subTest(policy=policy),self.assertRaises(ValueError):
                build([e],inv,rows,evidence={},answer_policy=policy)
        bad=copy.deepcopy(valid);bad['answer_policy']={'public_output_contracts':'true'}
        bad['sha256']=digest({k:v for k,v in bad.items() if k!='sha256'})
        with self.assertRaises(ValueError):ApprovedLibrary(bad)

    def test_resume_rejects_duplicates_and_unknown_identities(self):
        self.assertEqual(_validate_rows([{'key':'a'}],{'a','b'}),{'a'})
        for rows in [[{'key':'a'},{'key':'a'}],[{'key':'unknown'}]]:
            with self.assertRaises(ValueError):_validate_rows(rows,{'a'})

    def test_incomplete_refresh_cannot_build_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            with patch('algsolve.catalog_refresh.check',return_value=({},[SimpleNamespace(key='pending')],{})):
                with self.assertRaisesRegex(ValueError,'Incomplete refresh'):
                    build_catalog(directory)
            self.assertFalse((directory/'approved-library.json').exists())

    def test_catalog_policy_activates_only_declared_public_comparison(self):
        from algsolve.answer import answer
        from algsolve.lookup import LookupIndex
        from test_answer import context,query
        e,inv,rows=fixture()
        e.statement='Return the answer in any order.'
        e.references[0]['code']='class Solution:\n def solve(self, nums):\n  return nums\n'
        from algsolve.approved_library import code_hash
        sha=code_hash(e.references[0]['code']);inv[0]['references'][0]['code_sha256']=sha;rows[0]['result']['code_sha256']=sha
        ctx=context();ctx.entries=[e];ctx.lookup=LookupIndex([e],ctx.lookup.embeddings)
        q=query();q.statement=e.statement;q.starter_code=e.starter_code;q.public_tests=[{'args':[[2,3]],'expected':[3,2]}]
        old=ApprovedLibrary(build([e],inv,rows,evidence={}))
        fresh=ApprovedLibrary(build([e],inv,rows,evidence={},answer_policy={'public_output_contracts':True}))
        self.assertEqual(answer(ctx,q,approved_library=old)['decision'],'abstain')
        result=answer(ctx,q,approved_library=fresh)
        self.assertEqual(result['decision'],'answered');self.assertTrue(result['attempts'][0]['public']['passed'])

    def test_public_abstention_still_scores_stored_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);entry=SimpleNamespace(key='a',references=[{'code':'stored source'}])
            (directory/'inventory.jsonl').write_text(json.dumps({'key':'a','independent_test_sets':[]})+'\n')
            (directory/'public.jsonl').write_text(json.dumps({'key':'a','result':{'decision':'abstain','code':None}})+'\n')
            (directory/'keys.json').write_text('["a"]')
            contract={'eligible':1,'test_artifact_sha256':{}}
            (directory/'contract.json').write_text(json.dumps(contract))
            with patch('algsolve.catalog_refresh.check',return_value=(contract,[entry],{})), \
                 patch('algsolve.catalog_refresh.corpus.KEYS_PATH',directory/'keys.json'), \
                 patch('algsolve.catalog_refresh.np.load',return_value=__import__('numpy').zeros((1,1))), \
                 patch('algsolve.catalog_refresh.LookupIndex'), \
                 patch('algsolve.catalog_refresh.selected_reference',return_value={'code':'stored source'}), \
                 patch('algsolve.catalog_refresh.audit.independent_score',side_effect=[{'status':'passed','verdicts':[]},{'status':'no_code','verdicts':[]}]) as scorer:
                result=run(directory,max_items=1)
            self.assertEqual(scorer.call_args_list[0].args[1],'stored source')
            self.assertIsNone(scorer.call_args_list[1].args[1])
            self.assertEqual(result['independent_status'],{'passed':1})
            self.assertEqual(result['fresh_correct'],0)

    def test_public_import_refuses_policy_and_test_identity_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/'source';src.mkdir();dst=root/'destination';dst.mkdir()
            base={key:{} for key in ['runtime_files_sha256','test_artifact_sha256','inventory_sha256','answer_policy','boundary_sha256','eligible']}
            (src/'contract.json').write_text(json.dumps(base))
            for field in ['answer_policy','test_artifact_sha256','runtime_files_sha256','inventory_sha256']:
                current=copy.deepcopy(base);current[field]={'changed':True}
                with self.subTest(field=field),patch('algsolve.catalog_refresh.check',return_value=(current,[],{})),self.assertRaisesRegex(ValueError,'binding differs'):
                    import_public(dst,src)
                self.assertFalse((dst/'public.jsonl').exists())
