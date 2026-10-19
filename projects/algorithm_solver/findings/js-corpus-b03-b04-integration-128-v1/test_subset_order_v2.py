import copy
import itertools
import json
from types import SimpleNamespace
import unittest
from algsolve.judge import judge, sandbox
import subset_order_v2 as contract


def problem(uid='lcd:78', slug='subsets', method='subsets'):
    return SimpleNamespace(uid=uid, slug=slug, entry={'method': method})


def score(expected, observed, mode='return:unordered_outer'):
    raw=(json.dumps({'i':0,'result':observed})+'\n'+json.dumps({'done':1})+'\n').encode()
    result=sandbox.SandboxResult(0,None,raw,b'',0)
    return judge._score_functional(result,[judge.FunctionalTest(expected=expected,compare=mode)])


class SubsetOrderContractTests(unittest.TestCase):
    def test_independently_enumerated_powersets_accept_outer_permutations(self):
        for values in [[1,2,3],[2,1],[-1,0,1],[1,1,2],[0]]:
            expected=[]
            for count in range(len(values)+1):
                for row in itertools.combinations(values,count):
                    if list(row) not in expected:expected.append(list(row))
            self.assertTrue(score(expected,expected[::-1]).passed)
            self.assertTrue(score(expected,expected[1:]+expected[:1]).passed)

    def test_missing_extra_and_duplicate_subsets_fail(self):
        expected=[[],[1],[2],[1,2]]
        for bad in [expected[:-1],expected+[[3]],expected+[[1]],[[1],[1],[2],[1,2]]]:
            self.assertFalse(score(expected,bad).passed)

    def test_types_inner_order_and_multiplicity_remain_strict(self):
        for wanted,actual in [([[1]],[[True]]),([[1]],[[1.0]]),([[1,2]],[[2,1]]),([[1,1]],[[1]]),([[]],[]),([[]],{})]:
            self.assertFalse(score(wanted,actual).passed)

    def test_raw_oracle_is_unchanged(self):
        raw=[{'args':[[1,2]],'expected':[[],[1],[2],[1,2]],'compare':'return'}]
        before=copy.deepcopy(raw);tests=contract.prepare(problem(),raw)
        self.assertEqual(raw,before);self.assertEqual(tests[0].expected,before[0]['expected'])
        self.assertEqual(tests[0].compare,'return:unordered_outer')

    def test_scope_requires_all_three_identity_fields(self):
        raw=[{'args':[[1]],'expected':[[],[1]]}]
        for p in [problem(uid='lcd:999'),problem(slug='other'),problem(method='other')]:
            with self.assertRaises(ValueError):contract.prepare(p,raw)
        self.assertEqual(contract.prepare(problem('lcd:90','subsets-ii','subsetsWithDup'),raw)[0].compare,'return:unordered_outer')

    def test_unrelated_ordered_arrays_stay_ordered(self):
        self.assertFalse(score([[1],[2]],[[2],[1]],mode='return').passed)

    def test_protocol_failure_not_reclassified(self):
        for stdout,reason in [(b'{"i":0,"result":[]}\n','incomplete'),(b'{"done":1}\n','missing_result')]:
            result=sandbox.SandboxResult(0,None,stdout,b'',0)
            verdict=judge._score_functional(result,[judge.FunctionalTest(expected=[],compare='return:unordered_outer')])
            self.assertFalse(verdict.passed);self.assertEqual(verdict.reason,reason)

    def test_unsupported_call_contracts_fail_closed(self):
        for raw in [[],[{'args':[],'expected':[],'compare':'arg:0'}],[{'args':[],'expected':[],'kwargs':{'x':1}}]]:
            with self.assertRaises(ValueError):contract.prepare(problem(),raw)


if __name__=='__main__':unittest.main()
