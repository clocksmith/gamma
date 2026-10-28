"""R inert toy controls only; no authored candidate sources are loaded."""
import unittest
import harness

class ListNode:
    def __init__(self,val=0,next=None):self.val=val;self.next=next
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val=val;self.left=left;self.right=right

def call(pid,ns,args):return harness.observe(ns,pid,{'args':args})
def shared(roots=(0,1)):
    return {'__list_graph__':{'nodes':[{'value':7,'next':1},{'value':7,'next':None}],'argument_roots':list(roots)}}

class Controls(unittest.TestCase):
    def test147_relinks_original_nodes(self):
        class Solution:
            def insertionSortList(self,head):
                second=head.next;second.next=head;head.next=None;return second
        r=call(147,{'Solution':Solution,'ListNode':ListNode},[{'__list_node__':[2,1]}])
        self.assertEqual(r['result'],{'__list_node__':[1,2]});self.assertEqual(r['node_identity']['result_root'],1)
        self.assertEqual(r['args_after'],[{'__list_node__':[2]}])
    def test147_clones_forbidden(self):
        class Solution:
            def insertionSortList(self,head):return ListNode(1,ListNode(2))
        with self.assertRaises(ValueError):call(147,{'Solution':Solution,'ListNode':ListNode},[{'__list_node__':[2,1]}])
    def test147_dropped_original_forbidden(self):
        class Solution:
            def insertionSortList(self,head):head.next=None;return head
        with self.assertRaises(ValueError):call(147,{'Solution':Solution,'ListNode':ListNode},[{'__list_node__':[1,2]}])
    def test147_values_fixed_per_identity(self):
        class Solution:
            def insertionSortList(self,head):head.val=0;return head
        with self.assertRaises(ValueError):call(147,{'Solution':Solution,'ListNode':ListNode},[{'__list_node__':[1]}])
    def test160_original_two_heads_shared_tail(self):
        class Solution:
            def getIntersectionNode(self,a,b):return b
        r=call(160,{'Solution':Solution,'ListNode':ListNode},[shared()]);self.assertEqual(r['node_identity']['result_root'],1)
        self.assertEqual(r['node_identity']['before'],r['node_identity']['after']);self.assertEqual(r['alias_edges'],[['result','args.1']])
    def test160_same_root_alias_and_no_intersection(self):
        class Solution:
            def getIntersectionNode(self,a,b):return a
        r=call(160,{'Solution':Solution,'ListNode':ListNode},[shared((0,0))]);self.assertEqual(r['alias_edges'],[['result','args.0'],['result','args.1']])
        class NoneSolution:
            def getIntersectionNode(self,a,b):return None
        r=call(160,{'Solution':NoneSolution,'ListNode':ListNode},[shared()]);self.assertIsNone(r['result']);self.assertEqual(r['result_type'],'NoneType')
    def test160_mutation_and_fabrication_rejected(self):
        class Solution:
            def getIntersectionNode(self,a,b):a.next=None;return b
        with self.assertRaises(ValueError):call(160,{'Solution':Solution,'ListNode':ListNode},[shared()])
        class Clone:
            def getIntersectionNode(self,a,b):return ListNode(7)
        with self.assertRaises(ValueError):call(160,{'Solution':Clone,'ListNode':ListNode},[shared()])
    def test160_cycle_input_rejected(self):
        wire=shared();wire['__list_graph__']['nodes'][1]['next']=0
        class Solution:
            def getIntersectionNode(self,a,b):return None
        with self.assertRaises(ValueError):call(160,{'Solution':Solution,'ListNode':ListNode},[wire])
    def test173_source_constructor_and_tree_preserved(self):
        class BSTIterator:
            def __init__(self,root):self.root=root
            def hasNext(self):return True
            def next(self):return self.root.val
        args=[['BSTIterator','hasNext','next'],[[{'__tree_node__':[3]}],[],[]]]
        r=call(173,{'BSTIterator':BSTIterator,'TreeNode':TreeNode},args)
        self.assertEqual(r['result'],[None,True,3]);self.assertEqual(r['native_method_return_types'],['constructed','bool','int'])
        self.assertEqual(r['node_identity']['before'],r['node_identity']['after'])
    def test173_constructor_tree_mutation_forbidden(self):
        class BSTIterator:
            def __init__(self,root):root.val+=1
            def next(self):return 0
            def hasNext(self):return True
        with self.assertRaises(ValueError):call(173,{'BSTIterator':BSTIterator,'TreeNode':TreeNode},[['BSTIterator'],[[{'__tree_node__':[3]}]]])
    def test146_fresh_native_receiver_per_trace(self):
        class LRUCache:
            def __init__(self,capacity):self.data={}
            def put(self,key,value):self.data[key]=value
            def get(self,key):return self.data.get(key,-1)
        ns={'LRUCache':LRUCache}
        self.assertEqual(call(146,ns,[['LRUCache','put','get'],[[1],[2,7],[2]]])['result'],[None,None,7])
        self.assertEqual(call(146,ns,[['LRUCache','get'],[[1],[2]]])['result'],[None,-1])
    def test146_reused_receiver_rejected(self):
        held=[]
        class LRUCache:
            def __new__(cls,capacity):
                if not held:held.append(object.__new__(cls))
                return held[0]
            def __init__(self,capacity):pass
            def get(self,key):return -1
            def put(self,key,value):pass
        ns={'LRUCache':LRUCache};args=[['LRUCache'],[[1]]];call(146,ns,args)
        with self.assertRaises(TypeError):call(146,ns,args)
    def test155_void_and_strict_return_types(self):
        class MinStack:
            def __init__(self):self.values=[]
            def push(self,value):self.values.append(value)
            def pop(self):self.values.pop()
            def top(self):return self.values[-1]
            def getMin(self):return min(self.values)
        args=[['MinStack','push','getMin','top','pop'],[[],[-2],[],[],[]]]
        self.assertEqual(call(155,{'MinStack':MinStack},args)['result'],[None,None,-2,-2,None])
        class Bad:
            def push(self,value):return 0
        with self.assertRaises(TypeError):call(155,{'MinStack':Bad},[['MinStack','push'],[[],[1]]])
    def test_native_receiver_slots_need_no_weakref_support(self):
        class LRUCache:
            __slots__=('data',)
            def __init__(self,capacity):self.data={}
            def get(self,key):return self.data.get(key,-1)
            def put(self,key,value):self.data[key]=value
        args=[['LRUCache','get'],[[1],[2]]]
        self.assertEqual(call(146,{'LRUCache':LRUCache},args)['result'],[None,-1])
        self.assertEqual(call(146,{'LRUCache':LRUCache},args)['result'],[None,-1])

    def test188_original_Solution_and_readonly_observation(self):
        class Solution:
            def maxProfit(self,k,prices):return 7
        args=[1,[0,7]];r=call(188,{'Solution':Solution},args);self.assertEqual(r['result'],7);self.assertEqual(r['args_before'],r['args_after'])
        with self.assertRaises(TypeError):call(188,{'solve':lambda *a:7},args)
    def test_node_class_descriptor_tampering_rejected(self):
        class LocalNode:
            def __init__(self,val=0,next=None):self.val=val;self.next=next
        class Solution:
            def insertionSortList(self,head):LocalNode.extra=1;return head
        with self.assertRaises(TypeError):call(147,{'Solution':Solution,'ListNode':LocalNode},[{'__list_node__':[1]}])
    def test_blocked_and_constructor_fallback_rejected(self):
        for pid in (156,159,161,163):
            with self.assertRaises(ValueError):call(pid,{},[])
        class Solution:
            def insertionSortList(self,head):return head
        with self.assertRaises(TypeError):call(147,{'Solution':Solution},[{'__list_node__':[1]}])

if __name__=='__main__':unittest.main()
