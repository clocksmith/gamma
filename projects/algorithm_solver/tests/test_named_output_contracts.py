from dataclasses import replace
import unittest
from algsolve import validate
from algsolve.named_output_contracts import bind,declared
from test_public_contracts import problem

class NamedOutputContractsTests(unittest.TestCase):
    def test_complete_named_clauses(self):
        for text in ['Return the two integers in any order.','The paths may be returned in any order.',
                     'Notice that you can return the substrings in any order.',
                     'You may return the values in any order.','Return all such possible sentences in any order.',
                     'Return a list that contains the names of high-access employees with any order you want.',
                     'The input array is sorted. Return the values in any order.']:
            with self.subTest(text=text):self.assertTrue(declared(text))

    def test_conditional_quoted_input_only_and_conflicting_clauses_rejected(self):
        for text in ['Return the values in any order that satisfies the conditions.',
                     'If feasible, return the values in any order.',
                     'Return the values in any order if a solution exists.',
                     'Do not return the values in any order.','"Return the values in any order."',
                     'Example 1:\nReturn the values in any order.','The input values can be in any order.',
                     'Return the values in any order. Return the values sorted.',
                     'Return the values in any order. You must return them in ascending order.',
                     'Return the values in any order. The values must be sorted.',
                     'Return the values in any order. The returned values must be sorted.',
                     'Return the values in any order. They must be in ascending order.',
                     'Return the values in any order. The resulting values are sorted.',
                     'Return the values in any order. Keep their original order.',
                     'Return the values in any order. Do not reorder the returned values.',
                     'Return the values in any order. The values have to be sorted.',
                     'Return the values in any order. The names need to be in ascending order.',
                     'Return the values in any order. You must not reorder the values.',
                     'Return the values in any order. You must preserve the original order.',
                     'Return the values in any order\nif the ordering condition holds.',
                     'Return the values in any order\nprovided that the ordering condition holds.',
                     'Return the values in any order\nthat satisfies the constraints.',
                     'Return a list that contains the names of employees when available with any order you want.',
                     'Return a valid matrix in any order.','Return the head of a linked list in any order.']:
            with self.subTest(text=text):self.assertFalse(declared(text))

    def test_explicit_comparison_and_data_remain_unchanged(self):
        q=problem('Return the paths in any order.');before=q.to_json();candidate=bind(q)
        self.assertEqual(q.to_json(),before)
        self.assertEqual(candidate.public_tests[0]['expected'],q.public_tests[0]['expected'])
        self.assertEqual(candidate.public_tests[0]['compare'],'return:unordered_outer')
        for comparison in ['return:exact','arg:0','return:distinct_int_rows']:
            p=replace(q,public_tests=[dict(q.public_tests[0],compare=comparison)])
            self.assertIs(bind(p),p)
        for value in [1,'text',{'a':1}]:
            p=replace(q,public_tests=[dict(q.public_tests[0],expected=value)]);self.assertIs(bind(p),p)

    def test_actual_judge_retains_inner_order_multiplicity_types_and_length(self):
        p=bind(problem('Return the paths in any order.'))
        for value,passed in [('[[3,4],[1,2]]',True),('[[2,1],[3,4]]',False),
                             ('[[1,2],[1,2]]',False),('[[True,2],[3,4]]',False),
                             ('[[1.0,2],[3,4]]',False),('[[1,2]]',False)]:
            with self.subTest(value=value):
                source='class Solution:\n def solve(self):\n  return '+value+'\n'
                verdict=validate.judge_problem(p,source,p.public_tests,wall_seconds=3)
                self.assertEqual(verdict.passed,passed,verdict)

class NamedLookupTests(unittest.TestCase):
    def test_old_or_mismatched_adapter_catalog_is_rejected(self):
        from types import SimpleNamespace
        from algsolve.named_lookup import check_adapter,adapter_record
        for record in [None,dict(adapter_record(),id='other'),dict(adapter_record(),module_sha256='0'*64)]:
            with self.subTest(record=record),self.assertRaises(ValueError):
                check_adapter(SimpleNamespace(manifest={} if record is None else {'query_adapter':record}))
        check_adapter(SimpleNamespace(manifest={'query_adapter':adapter_record()}))

    def test_wrapper_returns_only_manifest_bound_stored_code(self):
        import numpy as np
        from algsolve.approved_library import ApprovedLibrary,build,digest,code_hash
        from algsolve.named_lookup import adapter_record,answer
        from algsolve.lookup import LookupIndex
        from test_approved_library import fixture
        from test_answer import context,query
        e,inv,rows=fixture();e.statement='Return the values in any order.'
        e.references[0]['code']='class Solution:\n def solve(self, nums):\n  return nums\n'
        sha=code_hash(e.references[0]['code']);inv[0]['references'][0]['code_sha256']=sha;rows[0]['result']['code_sha256']=sha
        ctx=context();ctx.entries=[e];ctx.lookup=LookupIndex([e],ctx.lookup.embeddings)
        q=query();q.statement=e.statement;q.starter_code=e.starter_code;q.public_tests=[{'args':[[2,3]],'expected':[3,2]}]
        manifest=build([e],inv,rows,evidence={},answer_policy={'public_output_contracts':True})
        body={k:v for k,v in manifest.items() if k!='sha256'};body['query_adapter']=adapter_record()
        catalog=ApprovedLibrary(dict(body,sha256=digest(body)))
        result=answer(ctx,q,approved_library=catalog)
        self.assertEqual(result['decision'],'answered');self.assertEqual(result['code'],e.references[0]['code'])
        self.assertNotIn('compare',q.public_tests[0])
        q.statement='Return the values in any order. They must be in ascending order.'
        # No declaration accepted, so the ordinary exact expected ordering fails.
        e.statement=q.statement;ctx.lookup=LookupIndex([e],ctx.lookup.embeddings)
        manifest=build([e],inv,rows,evidence={},answer_policy={'public_output_contracts':True})
        body={k:v for k,v in manifest.items() if k!='sha256'};body['query_adapter']=adapter_record()
        catalog=ApprovedLibrary(dict(body,sha256=digest(body)))
        self.assertTrue(catalog.check(e)['approved'])
        self.assertEqual(answer(ctx,q,approved_library=catalog)['decision'],'abstain')
