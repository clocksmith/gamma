"""Deterministic request-boundary checks, not new composition evidence."""
import copy
import unittest
from algsolve.synth.typed_suby_baseline import requests_for


class PublicCompositionInputs(unittest.TestCase):
    def test_teacher_and_independent_authority_never_enter_request(self):
        pair={'uid':'dev:anonymous','problem_family':'anonymous','learning_split':'development_audit',
              'input':{'statement':'Count values','public_examples':[]},'target':{'program':'secret teacher'},
              'provenance':{'independent_tests_sha256':'private authority'}}
        requests=requests_for([pair,dict(pair, target={'different':'alternative teacher'})])
        self.assertEqual(len(requests),1)
        self.assertEqual(set(requests[0]),{'uid','problem_family','learning_split','input'})
        requests[0]['input']['statement']='mutated'
        self.assertEqual(pair['input']['statement'],'Count values')

    def test_alternative_public_input_or_split_drift_rejected(self):
        pair={'uid':'dev:anonymous','problem_family':'anonymous','learning_split':'development_fit','input':{'statement':'one'}}
        for key,value in [('learning_split','development_audit'),('input',{'statement':'other'})]:
            with self.subTest(key=key):
                other=copy.deepcopy(pair);other[key]=value
                with self.assertRaises(ValueError):requests_for([pair,other])

if __name__=='__main__':unittest.main()
