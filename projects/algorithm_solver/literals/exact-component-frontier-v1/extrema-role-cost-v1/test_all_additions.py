import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from verify_all_additions import audit

spec=importlib.util.spec_from_file_location('public_frontier',Path(__file__).resolve().parents[1]/'frontier.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

class AuditTests(unittest.TestCase):
    def check(self,cost):
        class Graph:
            def __init__(self,texts):self.texts=texts
            def score(self,vocabulary,materialize):return {k:cost for k in self.texts}
        state={'f':f,'best':{'vocabulary':['a','b','ab']},'accelerator':SimpleNamespace(Graph=Graph)}
        additions={'role':{'public':{'key':'public:role','source':'ab','sha256':hashlib.sha256(b'ab').hexdigest()}}}
        return audit(state,additions)
    def test_exact_unselected_path(self):
        r=self.check({'selections':1,'characters':0});self.assertTrue(r[0]['packet_decoded_exactly'])
    def test_inflated_cost_rejected(self):
        with self.assertRaisesRegex(ValueError,'cost mismatch'):self.check({'selections':8,'characters':0})
    def test_wrong_singleton_cost_rejected(self):
        with self.assertRaisesRegex(ValueError,'cost mismatch'):self.check({'selections':1,'characters':1})
    def test_false_unreachable_rejected(self):
        with self.assertRaisesRegex(ValueError,'cost mismatch'):self.check(None)

if __name__=='__main__':unittest.main()
