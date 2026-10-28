"""Independent P source-free controls; no candidate source imports."""
from copy import deepcopy
from functools import lru_cache
import importlib.util
from itertools import product
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('p_cases',Path(__file__).with_name('cases.py'))
cases=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(cases)
o=cases.oracle


def observation(pid,args,result=None):
    if result is None:
        result=o.expected(pid,args) if pid in (17,65,87,95) else o.tuple_marker(cases.balanced(args[0])) if pid==108 else args[0] if pid in (116,117) else None
    kind='NoneType' if pid in (37,99,114) else 'bool' if pid in (65,87) else 'list' if pid in (17,95) else 'TreeNode' if pid==108 else 'Node' if o.tree_nodes(args[0],True) else 'NoneType'
    row={'i':0,'problem_id':pid,'method':o.METHODS[pid],'native_route':'official-wrapper-p-v1','result':result,'result_type':kind,'args_before':deepcopy(args),'args_after':deepcopy(args),'alias_edges':[],'node_identity':None,'node_integrity':None,'board_identity':None}
    if pid==37:
        row['args_after']=[o.expected(pid,args)];row['board_identity']={'argument_root_preserved':True,'before_shape':[9,9],'after_shape':[9,9]}
    elif pid in (99,114,116,117):
        plan=o.effect_plan(pid,args);row['node_identity']={**plan,'before':[{'id':i,**v} for i,v in enumerate(plan['before'])],'after':[{'id':i,**v} for i,v in enumerate(plan['after'])],'result_roots':[]}
        row['args_after']=[o.marker(plan['after'],0 if plan['after'] else None,pid in (116,117))]
        if pid in (116,117) and plan['after']:row['alias_edges']=[['result','args.0']]
    elif pid in (95,108):
        nodes=[];roots=[];memo={}
        for marker in result if pid==95 else [result]:
            tree=o.tree_nodes(marker)
            def build(i):
                if i is None:return None
                v=tree[i];left=build(v['left']);right=build(v['right']);key=(v['value'],left,right)
                if key not in memo:
                    index=len(nodes);memo[key]=index;nodes.append({'id':index,'value':v['value'],'left':left,'right':right})
                return memo[key]
            roots.append(build(0))
        row['node_identity']={'before':[],'after':nodes,'argument_roots':[],'result_root':None if pid==95 else roots[0],'result_roots':roots if pid==95 else []}
    if row['node_identity'] is not None:
        row['node_integrity']={'schema':'gamma.p-official-node-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'acyclic_tree_graphs':True,'forest_cross_tree_aliases_permitted':pid==95,'checked_node_count':len(row['node_identity']['after'])}
    return row


class References(unittest.TestCase):
    def test_phone_anyorder_and_multiplicity(self):
        self.assertEqual(len(o.expected(17,['7777'])),256)
        row=observation(17,['23']);row['result'].reverse();self.assertTrue(o.check_observation(17,['23'],row,'python')[0])
        row['result'][0]=row['result'][1];self.assertFalse(o.check_observation(17,['23'],row,'python')[0])
        for s in ('','1','0','23456'):
            with self.assertRaises(ValueError):o.validate(17,[s])

    def test_number_distinct_DFA_crosscheck(self):
        table={0:{'sign':1,'digit':2,'dot':3},1:{'digit':2,'dot':3},2:{'digit':2,'dot':4,'e':6},3:{'digit':5},4:{'digit':5,'e':6},5:{'digit':5,'e':6},6:{'sign':7,'digit':8},7:{'digit':8},8:{'digit':8}}
        for n in range(1,5):
            for chars in product('01+-.eEa',repeat=n):
                state=0
                for c in chars:
                    key='digit' if c in '01' else 'sign' if c in '+-' else 'dot' if c=='.' else 'e' if c in 'eE' else 'bad';state=table.get(state,{}).get(key,-1)
                self.assertEqual(o.valid_number(''.join(chars)),state in (2,4,5,8))
        for s in ('NaN','Infinity','1e+-2'):self.assertFalse(o.expected(65,[s]))
        with self.assertRaises(ValueError):o.validate(65,[' 1'])

    def test_scramble_enumeration_crosscheck(self):
        @lru_cache(None)
        def derived(s):
            if len(s)==1:return frozenset([s])
            return frozenset(x+y for k in range(1,len(s)) for a,b in ((s[:k],s[k:]),(s[k:],s[:k])) for x in derived(a) for y in derived(b))
        for n in range(1,5):
            words=[''.join(v) for v in product('ab',repeat=n)]
            for a,b in product(words,repeat=2):self.assertEqual(o.scrambled(a,b),b in derived(a))
        self.assertFalse(o.scrambled('abcde','caebd'))

    def test_sudoku_exact_cover_unique_and_effects(self):
        solved=[[str(1+(3*r+r//3+c)%9) for c in range(9)] for r in range(9)];board=deepcopy(solved);board[3][4]='.'
        self.assertEqual(o.expected(37,[board]),solved);row=observation(37,[board]);self.assertTrue(o.check_observation(37,[board],row,'python')[0])
        row['args_after'][0][0][0]='9';self.assertFalse(o.check_observation(37,[board],row,'python')[0])
        with self.assertRaises(ValueError):o.validate(37,[[['.']*9 for _ in range(9)]])
        row=observation(37,[board]);row['board_identity']['argument_root_preserved']=False;self.assertFalse(o.check_observation(37,[board],row,'python')[0])

    def test_Catalan_completeness_and_crossforest_sharing(self):
        self.assertEqual([len(o.expected(95,[n])) for n in range(1,9)],[1,2,5,14,42,132,429,1430])
        row=observation(95,[3]);self.assertTrue(o.check_observation(95,[3],row,'python')[0]);self.assertLess(len(row['node_identity']['after']),15)
        row['result'][0]=row['result'][1];self.assertFalse(o.check_observation(95,[3],row,'python')[0])

    def test_balancedBST_any_valid_shape(self):
        for tree in ({'__tree_node__':[1,None,3]},{'__tree_node__':[3,1]}):self.assertTrue(o.check_observation(108,[[1,3]],observation(108,[[1,3]],tree),'python')[0])
        self.assertFalse(o.accepts_result(108,[[1,2,3]],{'__tree_node__':[1,None,2,None,3]}))

    def test_recovery_original_topology(self):
        args=[{'__tree_node__':[1,3,None,None,2]}];row=observation(99,args);self.assertTrue(o.check_observation(99,args,row,'python')[0])
        self.assertEqual(row['args_after'],[{'__tree_node__':[3,1,None,None,2]}]);row['node_identity']['after'][0]['left']=None;self.assertFalse(o.check_observation(99,args,row,'python')[0])

    def test_flatten_preorder_physical_identity(self):
        args=[{'__tree_node__':[1,2,5,3,4,None,6]}];row=observation(114,args);self.assertTrue(o.check_observation(114,args,row,'python')[0])
        self.assertEqual(row['args_after'],[{'__tree_node__':[1,None,2,None,3,None,4,None,5,None,6]}]);row['node_identity']['after'][0]['value']=9;self.assertFalse(o.check_observation(114,args,row,'python')[0])

    def test_nextlinks_sparse_crossparent(self):
        for pid,values in ((116,[1,2,3,4,5,6,7]),(117,[1,2,3,4,None,None,7])):
            args=[{'__next_node__':values}];row=observation(pid,args);self.assertTrue(o.check_observation(pid,args,row,'python')[0]);self.assertEqual(row['node_identity']['after'][1]['next'],2)
            row['node_identity']['after'][1]['next']=None;self.assertFalse(o.check_observation(pid,args,row,'python')[0])
        with self.assertRaises(ValueError):o.validate(116,[{'__next_node__':[1,2]}])

    def test_empty_native_and_strict_void(self):
        for pid in (114,116,117):
            args=[{'__next_node__' if pid in (116,117) else '__tree_node__':[]}];row=observation(pid,args);self.assertTrue(o.check_observation(pid,args,row,'python')[0])
        args=[{'__tree_node__':[]}];row=observation(114,args);row['result_type']='object';self.assertFalse(o.check_observation(114,args,row,'python')[0])

    def test_route_and_bool_node_id_rejected(self):
        args=[{'__next_node__':[0]}];row=observation(116,args);row['native_route']='solve';self.assertFalse(o.check_observation(116,args,row,'python')[0])
        row=observation(116,args);row['node_identity']['after'][0]['id']=False;self.assertFalse(o.check_observation(116,args,row,'python')[0])

if __name__=='__main__':unittest.main()
