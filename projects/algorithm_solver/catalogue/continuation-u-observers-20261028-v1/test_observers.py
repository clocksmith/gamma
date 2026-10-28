"""Synthetic U257 native/host controls; never opens or executes candidate files."""
import copy
import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
def load(name):
    s=importlib.util.spec_from_file_location('u_test_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('harness');c=load('host_check')
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right
class Solution:
    def binaryTreePaths(self,root):return ['1->2','1->2']
ARGS=[{'values':[1,2,2],'left':[1,None,None],'right':[2,None,None],'root':0}]
class Controls(unittest.TestCase):
    def row(self,cls=Solution,ctor=TreeNode):return h.observe({'Solution':cls,'TreeNode':ctor},257,{'args':ARGS})
    def test_original_method_constructor_and_duplicate_paths(self):
        r=self.row();self.assertEqual(r['result'],['1->2','1->2']);self.assertEqual(c.check_observation(257,ARGS,r,'python'),(True,None))
    def test_unordered_multiset_not_set(self):
        r=self.row();r['result']=['1->2'];self.assertFalse(c.check_observation(257,ARGS,r,'python')[0]);r['result']=['1->2']*3;self.assertFalse(c.check_observation(257,ARGS,r,'python')[0])
    def test_wrong_result_types(self):
        r=self.row()
        for value in ([True],[1],{'1->2':2},None):
            r['result']=value;self.assertFalse(c.check_observation(257,ARGS,r,'python')[0])
    def test_readonly_original_value_and_pointers(self):
        for key,value in [('value',7),('left',2)]:
            r=self.row();r['node_identity']['after'][0][key]=value;self.assertFalse(c.check_observation(257,ARGS,r,'python')[0])
    def test_mutation_observed_not_hidden(self):
        class Mutator:
            def binaryTreePaths(self,root):root.val=7;return ['1->2','1->2']
        self.assertFalse(c.check_observation(257,ARGS,self.row(Mutator),'python')[0])
    def test_wrong_constructor_defaults_rejected(self):
        class Wrong:
            def __init__(self,val=7,left=None,right=None):self.val,self.left,self.right=val,left,right
        with self.assertRaises((TypeError,ValueError)):self.row(ctor=Wrong)
    def test_solve_fallback_rejected(self):
        class Wrong:
            def solve(self,root):return []
        with self.assertRaises(TypeError):self.row(Wrong)
    def test_strict_ids_and_blocked_never_construct(self):
        for pid in (True,257.0,246,259):
            with self.assertRaises(ValueError):h.observe({},pid,{'args':ARGS})
    def test_native_integrity_cannot_be_truthy_integer(self):
        r=self.row();r['entry_integrity']['original_export_unchanged']=1;self.assertFalse(c.check_observation(257,ARGS,r,'python')[0])
    def test_distinct_value_paths_can_be_reordered(self):
        args=copy.deepcopy(ARGS);args[0]['values'][2]=3
        row=load('plan').successful_record(257,args,['1->3','1->2'],'python',c.reference)
        self.assertTrue(c.check_observation(257,args,row,'python')[0])
    def test_bad_tree_indices_and_aliases_rejected(self):
        for field,values in [('left',[True,None,None]),('right',[1,None,None])]:
            args=copy.deepcopy(ARGS);args[0][field]=values
            with self.assertRaises((TypeError,ValueError)):h.observe({'Solution':Solution,'TreeNode':TreeNode},257,{'args':args})
if __name__=='__main__':unittest.main()
