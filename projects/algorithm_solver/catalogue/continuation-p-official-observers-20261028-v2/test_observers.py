"""Synthetic classes only. Never load a numbered candidate source."""
import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('p_observer_toy_controls',Path(__file__).with_name('harness.py'))
h=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(h)

class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right
class Node:
    def __init__(self,val=0,left=None,right=None,next=None):self.val,self.left,self.right,self.next=val,left,right,next

def call(pid,args,method):
    Solution=type('Solution',(),{h.METHODS[pid]:method})
    return h.observe({'Solution':Solution,'TreeNode':TreeNode,'Node':Node},pid,{'args':args})

class ObserverTests(unittest.TestCase):
    def test_three_value_wrappers(self):
        for pid,args,value in [(17,['23'],['ad','ae']),(65,['1'],True),(87,['a','a'],True)]:
            r=call(pid,args,lambda self,*values:value)
            self.assertEqual(r['result'],value);self.assertEqual(r['args_before'],r['args_after'])
            self.assertEqual(r['native_route'],'official-wrapper-p-v1')
    def test_no_solution_injection_or_solve_fallback(self):
        with self.assertRaises(TypeError):h.observe({'solve':lambda x:True},65,{'args':['1']})
    def test_board_rows_may_be_replaced(self):
        board=[['.']*9 for _ in range(9)]
        def method(self,value):value[0]=['1']*9
        r=call(37,[board],method)
        self.assertEqual(r['result_type'],'NoneType');self.assertTrue(r['board_identity']['argument_root_preserved']);self.assertEqual(r['args_after'][0][0],['1']*9)
    def test_official_void_return_rejected(self):
        with self.assertRaises(TypeError):call(37,[[['.']*9 for _ in range(9)]],lambda self,board:board)
    def test_recover_records_original_node_ids_and_value_swap(self):
        def method(self,root):root.val,root.left.val=root.left.val,root.val
        r=call(99,[{'__tree_node__':[1,2,3]}],method)
        before,after=r['node_identity']['before'],r['node_identity']['after']
        self.assertEqual([row['id'] for row in after],[0,1,2]);self.assertEqual(r['args_after'],[{'__tree_node__':[2,1,3]}])
        self.assertEqual([(r['left'],r['right']) for r in before],[(r['left'],r['right']) for r in after])
    def test_flatten_records_original_preorder_chain(self):
        def method(self,root):root.right,root.left=root.left,None
        r=call(114,[{'__tree_node__':[1,2]}],method)
        self.assertEqual(r['node_identity']['after'],[{'id':0,'value':1,'left':None,'right':1},{'id':1,'value':2,'left':None,'right':None}])
        self.assertIsNone(r['result'])
    def test_connect_both_routes_original_root_and_next(self):
        def method(self,root):root.left.next=root.right;return root
        for pid in (116,117):
            r=call(pid,[{'__next_node__':[1,2,3]}],method)
            self.assertEqual(r['node_identity']['result_root'],0);self.assertEqual(r['node_identity']['after'][1]['next'],2)
            self.assertEqual(r['alias_edges'],[['result','args.0']])
    def test_connect_replacement_root_rejected(self):
        with self.assertRaises(ValueError):call(117,[{'__next_node__':[1]}],lambda self,root:Node(1))
    def test_forest_allows_cross_tree_shared_subtrees(self):
        def method(self,n):shared=TreeNode(1);return [TreeNode(2,shared),TreeNode(3,shared)]
        r=call(95,[3],method)
        self.assertEqual(r['node_integrity']['checked_node_count'],3)
        self.assertEqual(r['node_identity']['after'][0]['left'],r['node_identity']['after'][2]['left'])
    def test_internal_alias_and_cycle_rejected(self):
        def alias(self,n):child=TreeNode(1);return [TreeNode(2,child,child)]
        def cycle(self,n):root=TreeNode(1);root.left=root;return [root]
        for method in (alias,cycle):
            with self.assertRaises(ValueError):call(95,[2],method)
    def test_balanced_tree_wire_is_observed_not_canonicalized(self):
        r=call(108,[[1,2]],lambda self,nums:TreeNode(1,None,TreeNode(2)))
        self.assertEqual(r['result'],{'__tree_node__':[1,None,2]});self.assertEqual(r['args_after'],[[1,2]])
    def test_node_field_and_class_changes_rejected(self):
        def extra(self,root):root.extra=1
        with self.assertRaises(TypeError):call(99,[{'__tree_node__':[1]}],extra)
        def patch(self,root):TreeNode.marker=1
        try:
            with self.assertRaises(TypeError):call(99,[{'__tree_node__':[1]}],patch)
        finally:del TreeNode.marker
    def test_next_cycle_rejected(self):
        def method(self,root):root.next=root;return root
        with self.assertRaises(ValueError):call(117,[{'__next_node__':[1]}],method)
    def test_detached_original_nodes_remain_observed(self):
        def method(self,root):root.left=None
        r=call(99,[{'__tree_node__':[2,1]}],method)
        self.assertEqual(len(r['node_identity']['after']),2)
        self.assertEqual(r['node_identity']['after'][1]['value'],1)
    def test_null_tree_stays_native_null(self):
        r=call(117,[{'__next_node__':[]}],lambda self,root:root)
        self.assertEqual(r['node_identity']['argument_roots'],[None]);self.assertEqual(r['alias_edges'],[])

if __name__=='__main__':unittest.main()
