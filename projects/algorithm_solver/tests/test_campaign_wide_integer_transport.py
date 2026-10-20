"""Portable tests for the extended 738 integer interface."""
import unittest
from algsolve import campaign_738_integer as g
class WideIntegerTests(unittest.TestCase):
    def test_decimal_resource_boundary(self):
        self.assertEqual(g.integer({g.TAG:'9'*1024}),10**1024-1)
        for text in ['9'*1025,'0'*1024,'-1','+1','1e30','1.0']:
            with self.subTest(text=text[:20]),self.assertRaises(ValueError):g.integer({g.TAG:text})
    def test_bigint_input_can_return_safe_number(self):
        value=9007199254740992;result=8999999999999999
        row=dict(i=0,result={g.TAG:str(result)},args_before=[{g.TAG:str(value)}],args_after=[{g.TAG:str(value)}],argument_runtime_types=['bigint'],result_runtime_type='number',input_object_count=0,returned_input_ids=[],input_node_values_preserved=True)
        raw=g.compact(row)+'\n'+g.compact({'done':1})+'\n'
        self.assertEqual(g.decode_stdout(raw,{'args':[value]})[0]['result'],result)
        row['argument_runtime_types']=['number']
        with self.assertRaises(ValueError):g.decode_stdout(g.compact(row)+'\n'+g.compact({'done':1}),{'args':[value]})
if __name__=='__main__':unittest.main()
