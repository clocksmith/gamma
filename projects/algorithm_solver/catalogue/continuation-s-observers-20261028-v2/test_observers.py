"""Synthetic protocol toys only. Never imports a numbered candidate source."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('s_toy_harness','harness.py');check=load('s_toy_host','host_check.py')
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val=val;self.left=left;self.right=right
class ListNode:
    def __init__(self,val=0,next=None):self.val=val;self.next=next
class Trie:
    def __init__(self):self.words=set()
    def insert(self,word):self.words.add(word)
    def search(self,word):return word in self.words
    def startsWith(self,prefix):return any(word.startswith(prefix) for word in self.words)
class WordDictionary:
    def __init__(self):self.words=set()
    def addWord(self,word):self.words.add(word)
    def search(self,word):return any(len(word)==len(w) and all(a=='.' or a==b for a,b in zip(word,w)) for w in self.words)
class MyStack:
    # Abstract toy state, NOT a candidate queue-only implementation.
    def __init__(self):self.items=[]
    def push(self,x):self.items.append(x)
    def pop(self):return self.items.pop()
    def top(self):return self.items[-1]
    def empty(self):return not self.items
TREE={'values':[1,2,3],'left':[1,None,None],'right':[2,None,None],'root':0}
LIST={'values':[1,2,1,3],'next':[1,2,3,None],'head':0}
class Toys(unittest.TestCase):
    def accepted(self,pid,args,namespace):
        record=h.observe(namespace,pid,{'args':args});self.assertEqual(check.check_observation(pid,args,record,'python'),(True,None));return record
    def test_199_readonly(self):
        class Solution:
            def rightSideView(self,root):return [root.val,root.right.val]
        self.accepted(199,[TREE],{'Solution':Solution,'TreeNode':TreeNode})
    def test_222_complete(self):
        class Solution:
            def countNodes(self,root):return 3
        self.accepted(222,[TREE],{'Solution':Solution,'TreeNode':TreeNode})
    def test_203_original_retained_with_unconstrained_removed_edges(self):
        class Solution:
            def removeElements(self,head,val):
                kept=head.next;removed=kept.next;last=removed.next;kept.next=last;head.next=ListNode(9);removed.next=removed;return kept
        record=self.accepted(203,[LIST,1],{'Solution':Solution,'ListNode':ListNode})
        self.assertEqual(record['node_identity']['result_order'],[1,3]);self.assertIsInstance(record['node_identity']['after'][0]['next'],dict)
    def test_206_same_pool(self):
        class Solution:
            def reverseList(self,head):
                b=head.next;c=b.next;c.next=b;b.next=head;head.next=None;return c
        packet={'values':[1,1,1],'next':[1,2,None],'head':0}
        self.accepted(206,[packet],{'Solution':Solution,'ListNode':ListNode})
    def test_clone_rejected(self):
        class Solution:
            def reverseList(self,head):return ListNode(head.val)
        with self.assertRaises(ValueError):h.observe({'Solution':Solution,'ListNode':ListNode},206,{'args':[{'values':[1],'next':[None],'head':0}]})
    def test_tree_mutation_rejected(self):
        class Solution:
            def rightSideView(self,root):root.left.val=9;return [1,3]
        record=h.observe({'Solution':Solution,'TreeNode':TreeNode},199,{'args':[TREE]});self.assertFalse(check.check_observation(199,[TREE],record,'python')[0])
    def test_designs(self):
        samples={208:[['Trie','insert','search','search','startsWith'],[[],['apple'],['apple'],['app'],['app']]],211:[['WordDictionary','addWord','search','search'],[[],['bad'],['.ad'],['b..']]],225:[['MyStack','push','push','top','pop','empty'],[[],[1],[2],[],[],[]]]}
        for pid,args in samples.items():self.accepted(pid,args,{'Trie':Trie,'WordDictionary':WordDictionary,'MyStack':MyStack})
    def test_fresh_class_receivers(self):
        args=[['Trie','search'],[[],['a']]]
        self.accepted(208,args,{'Trie':Trie});self.accepted(208,args,{'Trie':Trie})
    def test_wrong_primitive_type(self):
        class BadTrie(Trie):
            def insert(self,word):return None
            def search(self,word):return 1
            def startsWith(self,prefix):return False
        with self.assertRaises(TypeError):h.observe({'Trie':BadTrie},208,{'args':[['Trie','search'],[[],['a']]]})
    def test_no_solve_fallback(self):
        with self.assertRaises(TypeError):h.observe({'solve':lambda *x:0},214,{'args':['a']})
    def test_board_readonly_unordered_distinct(self):
        class Solution:
            def findWords(self,board,words):return ['ab','a']
        self.accepted(212,[[['a','b']],['a','ab','z']],{'Solution':Solution})
    def test_legal_board_result_alias(self):
        class Solution:
            def findWords(self,board,words):return words
        record=self.accepted(212,[[['a']],['a']],{'Solution':Solution});self.assertEqual(record['alias_edges'],[['result','args.1']])
    def test_scalar_routes(self):
        class Solution:
            def shortestPalindrome(self,s):return 'aaacecaaa'
            def calculate(self,s):return 3
        self.accepted(214,['aacecaaa'],{'Solution':Solution});self.accepted(224,['(1+2)'],{'Solution':Solution})
    def test_inherited_method_rejected(self):
        class Parent:
            def calculate(self,s):return 3
        class Solution(Parent):pass
        with self.assertRaises(TypeError):h.observe({'Solution':Solution},224,{'args':['(1+2)']})
    def test_return_type_forgery_rejected(self):
        class Solution:
            def calculate(self,s):return 3
        args=['(1+2)'];record=h.observe({'Solution':Solution},224,{'args':args});record['result_type']='bool';self.assertFalse(check.check_observation(224,args,record,'python')[0])
    def test_integrity_forgery_rejected(self):
        class Solution:
            def calculate(self,s):return 3
        args=['(1+2)'];record=h.observe({'Solution':Solution},224,{'args':args});record['entry_integrity']['fresh_receiver']=False;self.assertFalse(check.check_observation(224,args,record,'python')[0])
    def test_packet_strips_expected(self):
        packet=check.packet(224,[{'args':['(1+2)'],'expected':3,'private_witness':'host-only'}]);self.assertEqual(packet['calls'],[{'args':['(1+2)']}])
if __name__=='__main__':unittest.main()
