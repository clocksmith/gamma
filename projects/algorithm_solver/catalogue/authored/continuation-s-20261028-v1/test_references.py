import importlib.util
from pathlib import Path
import unittest
S=importlib.util.spec_from_file_location('gamma_s_independent_refs',Path(__file__).with_name('oracles.py'));o=importlib.util.module_from_spec(S);S.loader.exec_module(o)

def linked(values):return {'values':values,'next':[i+1 if i+1<len(values) else None for i in range(len(values))],'head':0 if values else None}
def tree(values):return {'values':values,'left':[2*i+1 if 2*i+1<len(values) else None for i in range(len(values))],'right':[2*i+2 if 2*i+2<len(values) else None for i in range(len(values))],'root':0 if values else None}

class References(unittest.TestCase):
    def test_trees_and_complete_precondition(self):
        self.assertEqual(o.expected(199,[tree([1,2,3,4,5,6])]),[1,3,6]);self.assertEqual(o.expected(222,[tree(list(range(50)))]),50)
        with self.assertRaises(ValueError):o.validate(222,[{'values':[1,2],'left':[None,None],'right':[1,None],'root':0}])
    def test_list_pool_identity_not_equal_values(self):
        p=linked([1,2,1]);self.assertEqual(o.expected(203,[p,1]),{'head':1,'order':[1],'values':[2]});self.assertEqual(o.expected(206,[p])['order'],[2,1,0])
    def test_native_reference_state(self):
        self.assertEqual(o.expected(208,[['Trie','insert','search','startsWith'],[[],['apple'],['app'],['app']]]),[None,None,False,True])
        self.assertEqual(o.expected(211,[['WordDictionary','addWord','search'],[[],['abc'],['a..']]]),[None,None,True])
        self.assertEqual(o.expected(225,[['MyStack','push','push','pop','top','empty'],[[],[1],[2],[],[],[]]]),[None,None,None,2,1,False])
    def test_word_paths_no_cell_reuse_and_distinct(self):
        args=[[['a','b'],['c','d']],['ab','abcb','acdb']];self.assertEqual(o.expected(212,args),['ab','acdb']);self.assertFalse(o.accepts_result(212,args,['ab','ab','acdb']))
    def test_palindromic_prefix(self):
        for s,w in [('', ''),('abcd','dcbabcd'),('aacecaaa','aaacecaaa')]:self.assertEqual(o.expected(214,[s]),w)
    def test_calculator_independent_precedence(self):
        for s,w in [('1 + 1',2),(' 2-1 + 2 ',3),('(1+(4+5+2)-3)+(6+8)',23),('-(2+3)',-5),('1-(-2)',3),('-(-(-1))',-1)]:self.assertEqual(o.expected(224,[s]),w)
        for s in ('+1','1+-2','1 2','()','2147483648'):
            with self.assertRaises(ValueError):o.validate(224,[s])
    def test_effect_model_retained_removed_and_reverse(self):
        p=linked([1,2,1]);args=[p,1];plan=o.effect_plan(203,args);after=[{'value':1,'next':{'external_identity':7}},{'value':2,'next':None},{'value':1,'next':2}];record={'args_before':args,'args_after':args,'node_identity':{'before':plan['pool_before'],'after':after,'argument_roots':[0],'result_root':1,'result_order':[1]}};self.assertEqual(o.check_effects(203,args,record),(True,None));after[1]['next']=True;self.assertFalse(o.check_effects(203,args,record)[0])
    def test_all_generated_cases_and_input_effects(self):
        import copy
        spec=importlib.util.spec_from_file_location('gamma_s_test_cases',Path(__file__).with_name('cases.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
        rows=c.build_cases();self.assertEqual(sum(map(len,rows.values())),2111)
        for pid,cases in rows.items():
            for row in cases:
                before=copy.deepcopy(row['args']);self.assertTrue(o.accepts_result(pid,row['args'],row['expected']));self.assertTrue(o.exact(before,row['args']))
    def test_calculator_against_independent_constructed_values(self):
        import random
        rng=random.Random(224)
        def build(depth):
            if depth==0:
                value=rng.randint(0,30);return str(value),value
            a,x=build(depth-1);b,y=build(depth-1);op=rng.choice('+-');text='(('+a+')'+op+'('+b+'))';value=x+y if op=='+' else x-y
            return ('-('+text+')',-value) if rng.randrange(3)==0 else (text,value)
        for _ in range(128):
            text,value=build(4);self.assertEqual(o.expected(224,[text]),value)
    def test_domains_and_types(self):
        for pid,args in [(206,[{'values':[1],'next':[0],'head':0}]),(211,[['WordDictionary','search'],[[],['...']]]),(225,[['MyStack','pop'],[[],[]]])]:
            with self.assertRaises(ValueError):o.validate(pid,args)
        self.assertFalse(o.accepts_result(222,[tree([1])],True))
if __name__=='__main__':unittest.main()
