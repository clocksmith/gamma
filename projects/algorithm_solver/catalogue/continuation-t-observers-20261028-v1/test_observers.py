"""T synthetic protocol toys only, never imports a candidate source."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('t_toy_observer','harness.py');host=load('t_toy_host','host_check.py')
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val=val;self.left=left;self.right=right
class ListNode:
    def __init__(self,val=0,next=None):self.val=val;self.next=next

def required_tree():
    class TreeNode:
        def __init__(self,x):self.val=x;self.left=None;self.right=None
    return TreeNode
def required_list():
    class ListNode:
        def __init__(self,x):self.val=x;self.next=None
    return ListNode
class MyQueue:
    # Abstract FIFO toy, not stack-only candidate algorithm evidence.
    def __init__(self):self.items=[]
    def push(self,x):self.items.append(x)
    def pop(self):return self.items.pop(0)
    def peek(self):return self.items[0]
    def empty(self):return not self.items
TREE={'values':[2,1,3],'left':[1,None,None],'right':[2,None,None],'root':0}
class Toys(unittest.TestCase):
    def accepted(self,pid,args,namespace):
        record=h.observe(namespace,pid,{'args':args});self.assertEqual(host.check_observation(pid,args,record,'python'),(True,None));return record
    def test_226_mirror_original_pool(self):
        class Solution:
            def invertTree(self,root):root.left,root.right=root.right,root.left;return root
        self.accepted(226,[TREE],{'Solution':Solution,'TreeNode':TreeNode})
    def test_226_empty(self):
        class Solution:
            def invertTree(self,root):return root
        self.accepted(226,[{'values':[],'left':[],'right':[],'root':None}],{'Solution':Solution,'TreeNode':TreeNode})
    def test_230_readonly(self):
        class Solution:
            def kthSmallest(self,root,k):return root.val
        self.accepted(230,[TREE,2],{'Solution':Solution,'TreeNode':TreeNode})
    def test_232_state_and_types(self):
        args=[['MyQueue','push','push','peek','pop','empty','pop','empty'],[[],[1],[2],[],[],[],[],[]]]
        self.accepted(232,args,{'MyQueue':MyQueue})
    def test_233_scalar(self):
        class Solution:
            def countDigitOne(self,n):return 6
        self.accepted(233,[13],{'Solution':Solution})
    def test_234_restored_original_pool(self):
        class Solution:
            def isPalindrome(self,head):return True
        self.accepted(234,[{'values':[1,2,1],'next':[1,2,None],'head':0}],{'Solution':Solution,'ListNode':ListNode})
    def test_235_original_p_alias(self):
        class Solution:
            def lowestCommonAncestor(self,root,p,q):return p
        record=self.accepted(235,[TREE,0,2],{'Solution':Solution,'TreeNode':required_tree()})
        self.assertIn(['result','args.1'],record['alias_edges']);self.assertIn(['result','args.0'],record['alias_edges'])
    def test_236_original_nonroot_p(self):
        class Solution:
            def lowestCommonAncestor(self,root,p,q):return p
        p={'values':[10,30,20,40],'left':[1,3,None,None],'right':[2,None,None,None],'root':0}
        self.accepted(236,[p,1,3],{'Solution':Solution,'TreeNode':required_tree()})
    def test_237_only_target_native_argument(self):
        class Solution:
            def deleteNode(self,node):
                self.seen=node.val
                if node.val!=2:raise AssertionError('only originaltarget passed')
                node.val=3;node.next=node.next.next
        p={'values':[1,2,3,4],'next':[1,2,3,None],'head':0}
        record=self.accepted(237,[p,1],{'Solution':Solution,'ListNode':required_list()})
        self.assertEqual(record['node_identity']['argument_roots'],[1]);self.assertEqual(record['node_identity']['fixture_roots'],[0]);self.assertEqual(record['result']['order'],[0,1,3])
    def test_premium_ids_excluded(self):
        for pid in (243,245):
            with self.assertRaises(ValueError):h.observe({},pid,{'args':[]})
    def test_lca_equalvalued_clone_rejected(self):
        cls=required_tree()
        class Solution:
            def lowestCommonAncestor(self,root,p,q):return cls(p.val)
        with self.assertRaises(ValueError):h.observe({'Solution':Solution,'TreeNode':cls},235,{'args':[TREE,0,2]})
    def test_palindrome_unrestored_links_rejected(self):
        class Solution:
            def isPalindrome(self,head):head.next=None;return True
        p={'values':[1,2,1],'next':[1,2,None],'head':0};record=h.observe({'Solution':Solution,'ListNode':ListNode},234,{'args':[p]});self.assertFalse(host.check_observation(234,[p],record,'python')[0])
    def test_237_actual_void_required(self):
        class Solution:
            def deleteNode(self,node):node.val=3;node.next=None;return node
        p={'values':[1,2,3],'next':[1,2,None],'head':0}
        with self.assertRaises(TypeError):h.observe({'Solution':Solution,'ListNode':required_list()},237,{'args':[p,1]})
    def test_selected_copy_next_not_tailshift_variant(self):
        class Solution:
            def deleteNode(self,node):node.val=3;node.next.val=4;node.next.next=None
        p={'values':[1,2,3,4],'next':[1,2,3,None],'head':0};record=h.observe({'Solution':Solution,'ListNode':required_list()},237,{'args':[p,1]});self.assertFalse(host.check_observation(237,[p,1],record,'python')[0])
    def test_wrong_queue_void(self):
        class BadQueue:
            def push(self,x):return 0
        with self.assertRaises(TypeError):h.observe({'MyQueue':BadQueue},232,{'args':[['MyQueue','push'],[[],[1]]]})
    def test_no_fallback(self):
        with self.assertRaises(TypeError):h.observe({'solve':lambda x:6},233,{'args':[13]})
    def test_exact_pointer_aliases(self):
        class Solution:
            def lowestCommonAncestor(self,root,p,q):return p
        args=[TREE,0,2];record=h.observe({'Solution':Solution,'TreeNode':required_tree()},235,{'args':args});record['alias_edges']=[['result','args.0.pool.0']];self.assertFalse(host.check_observation(235,args,record,'python')[0])
    def test_packet_strips_expected(self):
        self.assertEqual(host.packet(233,[{'args':[13],'expected':6}])['calls'],[{'args':[13]}])
if __name__=='__main__':unittest.main()
