"""Fixed toy classes/functions and host-checker controls, never candidate files."""
import copy
import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('q_toy_observer',HERE/'harness.py');check=load('q_toy_host_check',HERE/'host_check.py')
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right
class ListNode:
    def __init__(self,val=0,next=None):self.val,self.next=val,next
class GraphNode:
    def __init__(self,val=0,neighbors=None):self.val,self.neighbors=val,[] if neighbors is None else neighbors
class RandomNode:
    def __init__(self,val,next=None,random=None):self.val,self.next,self.random=val,next,random
# Actual source classes use the name Node for both unrelated per-problem types.
GraphNode.__name__='Node';RandomNode.__name__='Node'
GRAPH={'values':[1,2,3],'neighbors':[[1,2],[0,2],[0,1]],'root':0}
RANDOM={'values':[7,7],'random':[1,0]}
TREE={'values':[1,2,3],'left':[1,None,None],'right':[2,None,None],'root':0}

def observe(pid,args,method):
    solution=type('Solution',(),{h.METHODS[pid]:method})
    return h.observe({'Solution':solution,'TreeNode':TreeNode,'ListNode':ListNode,'Node':GraphNode if pid==133 else RandomNode},pid,{'args':args})

def graph_clone(self,root):
    a,b,c=GraphNode(1),GraphNode(2),GraphNode(3)
    a.neighbors=[c,b];b.neighbors=[c,a];c.neighbors=[b,a]
    return a

def random_clone(self,head):
    a,b=RandomNode(7),RandomNode(7);a.next=b;a.random=b;b.random=a;return a

def reorder_four(self,head):
    b=head.next;c=b.next;d=c.next;head.next=d;d.next=b;b.next=c;c.next=None

class ObserverTests(unittest.TestCase):
    def accepted(self,pid,args,method):
        record=observe(pid,args,method);self.assertEqual(check.check_observation(pid,args,record,'python'),(True,None));return record
    def test_ordinary_unordered_distinct_results(self):
        self.accepted(126,['aa','bb',['ab','ba','bb']],lambda self,*args:[['aa','ba','bb'],['aa','ab','bb']])
        self.accepted(140,['aa',['a','aa']],lambda self,*args:['aa','a a'])
        self.accepted(132,['aab'],lambda self,s:1)
    def test_duplicate_ladders_and_sentences_rejected(self):
        for pid,args,result in [(126,['a','c',['b','c']],[['a','c'],['a','c']]),(140,['a',['a']],['a','a'])]:
            record=observe(pid,args,lambda self,*args:result)
            self.assertFalse(check.check_observation(pid,args,record,'python')[0])
    def test_ordinary_input_alias_rejected(self):
        args=['a',['a']];record=observe(140,args,lambda self,s,words:words)
        self.assertTrue(record['alias_edges']);self.assertFalse(check.check_observation(140,args,record,'python')[0])
    def test_graph_permuted_neighbors_and_cycles_preserved(self):
        self.accepted(133,[GRAPH],graph_clone)
    def test_graph_input_alias_and_shallow_clone_rejected(self):
        with self.assertRaises(ValueError):observe(133,[GRAPH],lambda self,node:node)
        def shallow(self,node):result=GraphNode(1);result.neighbors=node.neighbors;return result
        with self.assertRaises(ValueError):observe(133,[GRAPH],shallow)
    def test_graph_collapsed_missing_and_duplicate_edges_rejected(self):
        record=observe(133,[GRAPH],graph_clone)
        for change in ('collapsed','missing','duplicate'):
            bad=copy.deepcopy(record);rows=bad['node_identity']['clone_pool']
            if change=='collapsed':rows[1]['value']=rows[2]['value']
            elif change=='missing':rows[0]['neighbors'].pop()
            else:rows[0]['neighbors']=[rows[0]['neighbors'][0]]*2
            bad['result']['__clone_pool__']=rows
            self.assertFalse(check.check_observation(133,[GRAPH],bad,'python')[0],change)
    def test_graph_input_mutation_rejected(self):
        def method(self,node):node.val=99;return graph_clone(self,node)
        record=observe(133,[GRAPH],method)
        self.assertFalse(check.check_observation(133,[GRAPH],record,'python')[0])
    def test_graph_empty_adjacency_container_alias_rejected(self):
        def method(self,node):return GraphNode(node.val,node.neighbors)
        with self.assertRaises(ValueError):observe(133,[{'values':[1],'neighbors':[[]],'root':0}],method)
    def test_random_clone_duplicate_values_and_random_cycles(self):
        self.accepted(138,[RANDOM],random_clone)
    def test_random_clone_original_alias_and_wrong_topology_rejected(self):
        with self.assertRaises(ValueError):observe(138,[RANDOM],lambda self,head:head)
        record=observe(138,[RANDOM],random_clone);rows=record['node_identity']['clone_pool'];rows[0]['random']=0
        record['result']['__clone_pool__']=rows
        self.assertFalse(check.check_observation(138,[RANDOM],record,'python')[0])
    def test_head_only_cycle_abi_and_original_entry(self):
        args=[{'values':[1,1,1],'pos':1}]
        self.accepted(141,args,lambda self,head:True)
        record=self.accepted(142,args,lambda self,head:head.next)
        self.assertEqual(record['node_identity']['result_original_index'],1)
    def test_equal_value_cycle_entry_clone_rejected(self):
        with self.assertRaises(ValueError):observe(142,[{'values':[1,1],'pos':1}],lambda self,head:ListNode(1))
    def test_wrong_original_entry_and_boolean_index_rejected(self):
        args=[{'values':[1,1,1],'pos':1}]
        record=observe(142,args,lambda self,head:head.next.next)
        self.assertFalse(check.check_observation(142,args,record,'python')[0])
        record=observe(142,args,lambda self,head:head.next);record['node_identity']['result_original_index']=True
        self.assertFalse(check.check_observation(142,args,record,'python')[0])
    def test_reorder_same_pool_and_linear_primitive_equivalence(self):
        args=[{'values':[1,2,3,4]}];record=self.accepted(143,args,reorder_four)
        self.assertEqual(record['result']['original_identity_order'],[0,3,1,2])
        root,pool=h.models.materialize(143,args[0],ListNode);reorder_four(None,root)
        self.assertEqual(h.linear_reordered(root,pool,None),h.models.reordered(root,pool,None))
    def test_reorder_new_lost_nodes_and_nonvoid_rejected(self):
        args=[{'values':[1,2,3,4]}]
        def new(self,head):head.next=ListNode(4)
        def lost(self,head):head.next=None
        for method in (new,lost,lambda self,head:head):
            with self.assertRaises((ValueError,TypeError)):observe(143,args,method)
    def test_readonly_tree_values_and_topology(self):
        self.accepted(129,[TREE],lambda self,root:25)
        self.accepted(144,[TREE],lambda self,root:[1,2,3])
        def mutate(self,root):root.val=9;return 25
        record=observe(129,[TREE],mutate)
        self.assertFalse(check.check_observation(129,[TREE],record,'python')[0])
    def test_null_models(self):
        self.accepted(133,[{'values':[],'neighbors':[],'root':None}],lambda self,node:None)
        self.accepted(138,[{'values':[],'random':[]}],lambda self,head:None)
        self.accepted(142,[{'values':[],'pos':-1}],lambda self,head:None)
        self.accepted(144,[{'values':[],'left':[],'right':[],'root':None}],lambda self,root:[])
    def test_fresh_original_solution_receivers(self):
        class Solution:
            def __init__(self):self.count=0
            def minCut(self,text):self.count+=1;return self.count
        for _ in range(2):
            record=h.observe({'Solution':Solution},132,{'args':['aab']})
            self.assertEqual(record['result'],1)
    def test_large_certificates_without_candidate_execution(self):
        self.assertEqual(check.expected(132,['a'*2000]),0)
        self.assertEqual(check.expected(132,['ab'*1000]),1)
        self.assertEqual(check.expected(140,['a'*20,['a']]),[' '.join(['a']*20)])
    def test_fifty_thousand_node_identity_scan_is_iterative(self):
        # A source-free observer primitive control, no candidate algorithm.
        root,pool=h.models.materialize(143,{'values':[1]*50000},ListNode)
        result=h.linear_reordered(root,pool,None)
        self.assertEqual(result['original_identity_order'],list(range(50000)))
        self.assertEqual(len(result['values']),50000)

    def test_existing_finite_case_expectations_remain_supported(self):
        generator=load('q_original_finite_case_owner',HERE.parent/'authored/continuation-q-20261028-v1/cases.py')
        total=0
        for pid in check.METHODS:
            for row in generator.build_cases(pid,include_maximum=True):
                self.assertTrue(check.exact(check.expected(pid,row['args']),row['expected']),(pid,row.get('category')))
                total+=1
        self.assertGreater(total,1000)

    def test_wrong_native_class_and_field_rejected(self):
        def method(self,head):head.extra=True;return head
        with self.assertRaises(TypeError):observe(142,[{'values':[1],'pos':0}],method)

if __name__=='__main__':unittest.main()
