import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def module(name):
    s=importlib.util.spec_from_file_location('python_test_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('harness');q=module('qualify')

class TransportTests(unittest.TestCase):
    def test_roundtrip_nodes(self):
        for value in ({'__list_node__':[1,2,3]},{'__tree_node__':[1,None,2,3]},{'__tree_node__':[]}):
            expected=None if value=={'__tree_node__':[]} else value
            self.assertEqual(h.encode(h.decode(value)),expected)
    def test_aliases_mutation(self):
        a=h.decode([{'__list_node__':[1,2]}]);node=a[0].next
        self.assertEqual(h.aliases(a,node),[['result','args.0.next']])
        a[0].next=None
        self.assertEqual(h.aliases(a,node),[])
    def test_large_int_bool(self):
        self.assertEqual(h.encode(10**30),{'__gamma_bigint_v1__':str(10**30)})
        self.assertIs(h.encode(True),True)
        self.assertEqual(h.decode(h.encode(10**30)),10**30)
    def test_unsafe_values(self):
        for value in ((1,2),{1,2},float('nan'),float(2**60),{1:'a'}):
            with self.assertRaises((TypeError,ValueError)):h.encode(value)
        a=[];a.append(a)
        with self.assertRaises(ValueError):h.encode(a)
    def test_node_constructor_independent(self):
        class Custom:
            def __init__(self):self.next=None;self.val=1
        self.assertEqual(h.encode(Custom()),{'__list_node__':[1]})
        self.assertEqual(h.aliases([Custom()],None),[])

class CompareTests(unittest.TestCase):
    def observation(self,value,kind):return {'result':value,'result_type':kind,'args_before':[],'args_after':[],'alias_edges':[]}
    def test_bigint_exact_bridge(self):
        n=10**30;case={'args':[],'expected':n};base=self.observation({'__gamma_bigint_v1__':str(n)},'bigint');rec=self.observation({'__gamma_bigint_v1__':str(n)},'int')
        self.assertEqual(q.compare(case,rec,base),(True,True))
        rec['result_type']='float';self.assertEqual(q.compare(case,rec,base),(False,False))
    def test_bool_not_integer(self):
        self.assertEqual(q.compare({'args':[],'expected':1},self.observation(True,'bool'),self.observation(1,'number')),(False,False))
    def test_mutation_alias_enforced(self):
        base=self.observation([1],'object');rec=self.observation([1],'list');case={'args':[],'expected':[1]}
        self.assertEqual(q.compare(case,rec,base),(True,True))
        rec['alias_edges']=[['result','args.0']];self.assertEqual(q.compare(case,rec,base),(True,False))
    def test_null_and_tuple(self):
        self.assertEqual(q.compare({'args':[],'expected':None},self.observation(None,'NoneType'),self.observation(None,'object')),(True,True))
        self.assertEqual(q.compare({'args':[],'expected':[1]},self.observation([1],'tuple'),self.observation([1],'object')),(False,False))
    def test_float_oracle_not_truthiness(self):
        base=self.observation(1.0,'number');rec=self.observation(1.00000000001,'float')
        valid,parity=q.compare({'args':[],'expected':1.0},rec,base)
        self.assertTrue(valid);self.assertFalse(parity)
        self.assertEqual(q.compare({'args':[],'expected':1.0},self.observation(2.0,'float'),base),(False,False))
    def test_encoded_marker_is_not_a_node(self):
        value={'__list_node__':[1]};case={'args':[],'expected':value};base=self.observation(value,'object')
        self.assertEqual(q.compare(case,self.observation(value,'dict'),base),(False,False))
        self.assertEqual(q.compare(case,self.observation(value,'ListNode'),base),(True,True))
    def test_protocol_failure_retained(self):
        count,errors=q.check_batch([],[],{'exit_code':1,'timed_out':False,'output_limit_exceeded':False},b'',0)
        self.assertEqual(count,0);self.assertIn('execution_or_protocol',errors[0])

if __name__=='__main__':unittest.main()
