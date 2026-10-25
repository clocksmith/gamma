"""Host-only baseline transport and evidence tests; no candidate execution."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_replay as b
class BaselineReplayTests(unittest.TestCase):
    def test_exact_integer_transport(self):
        self.assertEqual(b.tag([True,2**53-1,2**53]),[True,2**53-1,{'__gamma_bigint_v1__':str(2**53)}])
        self.assertEqual(b.tag([True,0,-2],True),[True,{'__gamma_bigint_v1__':'0'},{'__gamma_bigint_v1__':'-2'}])
    def test_historical_parity_types(self):
        self.assertTrue(b.exact(1,1.0));self.assertFalse(b.exact(True,1));self.assertFalse(b.exact([1],(1,)))
        self.assertFalse(b.exact({'args_after':[1]},{'args_after':[2]}))
    def test_protocol_fails_closed(self):
        self.assertEqual(b.parse(b'{"i":0,"result":1}\n{"done":1}',1)[0]['result'],1)
        for raw in (b'{"i":0,"i":0}\n{"done":1}',b'{"i":true}\n{"done":1}',b'{"i":0}\n{"done":true}',b'{"i":0,"result":NaN}\n{"done":1}'):
            with self.assertRaises(ValueError):b.parse(raw,1)
    def test_protected_id_fails_before_input_read(self):
        with self.assertRaisesRegex(ValueError,'outside permitted'):b.load_inputs(Path('/unused'),[99999999])
    def test_host_oracle_normalization(self):
        rules=b.module('test_baseline_rules',b.LIT/'admission500-v1/qualify_rules.py')
        self.assertEqual(rules.normalize({'__gamma_bigint_v1__':str(2**70)}),2**70)
        self.assertIsNone(rules.normalize({'__list_node__':[]}))
        valid,_=rules.judge_case({'args':[],'expected':2**70},{'result':{'__gamma_bigint_v1__':str(2**70)},'result_type':'bigint'})
        self.assertTrue(valid)
        valid,_=rules.judge_case({'args':[],'expected':2**70},{'result':{'__gamma_bigint_v1__':str(2**70)},'result_type':'number'})
        self.assertFalse(valid)
if __name__=='__main__':unittest.main()
