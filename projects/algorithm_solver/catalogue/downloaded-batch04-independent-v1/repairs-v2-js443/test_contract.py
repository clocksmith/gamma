import json
import unittest
import protocol as p

class Native443Contract(unittest.TestCase):
    def test_official_prefix_and_unconstrained_tail(self):
        case={'args':[['a','a','a']],'expected':['a','3']}
        record={'i':0,'result_type':'object','result':{'length':2,'prefix':['a','3']},'args_before':case['args'],'args_after':[['a','3',None]],'alias_edges':[]}
        self.assertEqual(p.compare(p.units()[0],case,record),(True,None))
        record['args_after']=[['a','a','a']]
        self.assertEqual(p.compare(p.units()[0],case,record),(False,'native_prefix_effect'))
    def test_functional_array_cannot_substitute_for_native_length(self):
        case={'args':[['a']],'expected':['a']}
        row={'result_type':'object','result':{'bad_length_type':'object'},'args_before':case['args'],'args_after':case['args'],'alias_edges':[]}
        self.assertEqual(p.compare(p.units()[0],case,row),(False,'native_length_or_prefix_result'))
    def test_partial_counts_remain_distinct(self):
        row={'i':0,'error':'example'}
        records,complete=p.observed(json.dumps(row).encode()+b'\n{"i":1',2)
        self.assertEqual(len(records),1);self.assertFalse(complete)
    def test_exact_named_adapter(self):
        self.assertIn(b'compress(chars)',p.adapter(p.units()[0]))
        self.assertNotIn(b'new Solution()',p.adapter(p.units()[0]))
        self.assertIn(b'new Solution().compress(chars)',p.adapter(p.units()[2]))

if __name__=='__main__':unittest.main()
