import importlib.util
from pathlib import Path
import unittest
S=importlib.util.spec_from_file_location('gamma_t_independent_refs',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)

def linked(values):return {'values':values,'next':[i+1 if i+1<len(values) else None for i in range(len(values))],'head':0 if values else None}
def bst():return {'values':[2,1,3],'left':[1,None,None],'right':[2,None,None],'root':0}
class References(unittest.TestCase):
    def test_premium_membership_not_replaced(self):
        self.assertEqual(set(o.REQUESTED_IDS)-set(o.IDS),{243,245})
        for pid in (243,245):
            with self.assertRaises(ValueError):o.validate(pid,[])
    def test_digitDP_against_literal_decimal_enumeration(self):
        total=0
        for n in range(2001):
            total+=str(n).count('1');self.assertEqual(o.expected(233,[n]),total)
        self.assertEqual(o.expected(233,[10**9]),900000001)
    def test_BST_value_order_and_originalLCA(self):
        p=bst();self.assertEqual(o.expected(230,[p,2]),2);self.assertEqual(o.expected(235,[p,1,2]),{'original_id':0,'value':2});self.assertEqual(o.expected(235,[p,0,1]),{'original_id':0,'value':2})
        with self.assertRaises(ValueError):o.validate(235,[p,True,2])
    def test_generalLCA_postorder_vs_explicit_paths(self):
        p={'values':[50,99,-2,5,6],'left':[1,3,None,None,None],'right':[2,4,None,None,None],'root':0}
        paths={};todo=[(p['root'],[])]
        for i,path in todo:
            paths[i]=path+[i]
            todo.extend((j,path+[i]) for j in (p['left'][i],p['right'][i]) if j is not None)
        for a in range(5):
            for b in range(5):
                if a==b:continue
                same=[x for x,y in zip(paths[a],paths[b]) if x==y][-1];self.assertEqual(o.expected(236,[p,a,b])['original_id'],same)
    def test_invert_pool_mirror_and_identity(self):
        p=bst();plan=o.effect_plan(226,[p]);self.assertEqual(plan['after'][0],{'value':2,'left':2,'right':1});self.assertEqual(plan['result_root'],0);self.assertEqual(o.expected(226,[p]),{'original_id':0,'value':2})
    def test_palindrome_post_links_restored(self):
        for values,wanted in [([1],True),([1,2],False),([1,2,1],True),([1,2,2,1],True)]:
            p=linked(values);self.assertEqual(o.expected(234,[p]),wanted);self.assertEqual(o.effect_plan(234,[p])['before'],o.effect_plan(234,[p])['after'])
    def test_delete_onlynode_copy_successor_not_target_identity(self):
        p=linked([4,5,1,9]);args=[p,1];wanted=o.expected(237,args);self.assertEqual(wanted,{'return':None,'head':0,'order':[0,1,3],'values':[4,1,9]});plan=o.effect_plan(237,args);self.assertEqual(plan['argument_roots'],[1]);self.assertEqual(plan['fixture_roots'],[0]);self.assertEqual(plan['after'][1],{'value':1,'next':3});self.assertEqual(plan['after'][2],plan['before'][2])
        with self.assertRaises(ValueError):o.validate(237,[p,3])
    def test_queue_reference_fifo_and_exacttypes(self):
        args=[['MyQueue','push','push','peek','pop','empty'],[[],[1],[2],[],[],[]]];self.assertEqual(o.expected(232,args),[None,None,None,1,1,False]);self.assertFalse(o.accepts_result(232,args,[None,None,None,True,1,False]))
    def test_effect_models_reject_clone_or_wrong_actual_argument(self):
        args=[bst(),1,2];plan=o.effect_plan(235,args);identity={k:plan[k] for k in ('before','after','argument_roots','fixture_roots','result_root','result_order')};record={'args_before':args,'args_after':args,'node_identity':identity};self.assertEqual(o.check_effects(235,args,record),(True,None));identity['result_root']=True;self.assertFalse(o.check_effects(235,args,record)[0])
    def test_generated_population_and_no_mutation(self):
        import copy
        spec=importlib.util.spec_from_file_location('gamma_t_test_cases',Path(__file__).with_name('cases.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);data=c.build_cases();self.assertEqual(set(data),set(o.IDS));self.assertEqual(sum(map(len,data.values())),2174)
        for pid,rows in data.items():
            for row in rows:
                before=copy.deepcopy(row['args']);self.assertTrue(o.accepts_result(pid,row['args'],row['expected']));self.assertTrue(o.exact(before,row['args']))
    def test_domains(self):
        for pid,args in [(233,[-1]),(230,[bst(),4]),(234,[linked([])]),(232,[['MyQueue','pop'],[[],[]]])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
if __name__=='__main__':unittest.main()
