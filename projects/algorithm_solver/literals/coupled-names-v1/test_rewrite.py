import json
import subprocess
import unittest
import rewrite as r

ALPHABET=[chr(i) for i in range(32,127)]+['\n']
class CoupledTests(unittest.TestCase):
    def rec(self,text):return r.records({'x':text})['x']
    def value(self,text):
        return subprocess.check_output(['node','-e',text+';console.log(JSON.stringify(solve(2,3,4)))'],text=True).strip()
    def test_two_name_barrier(self):
        text='function solve(a,b){return a+b}';vocab=ALPHABET+['x+y']
        rec=self.rec(text)
        old,stats=r.ordinary(text,rec,vocab)
        self.assertEqual(old,text)
        new,stats=r.coupled(text,rec,vocab)
        self.assertIn('x+y',new);self.assertEqual(self.value(text),self.value(new));self.assertEqual(stats['moves'],1)
    def test_three_name_barrier(self):
        text='function solve(a,b,c){return a+b*c}';vocab=ALPHABET+['x+y*z']
        new,stats=r.coupled(text,self.rec(text),vocab)
        self.assertIn('x+y*z',new);self.assertEqual(self.value(text),self.value(new))
    def test_repeat_binding_consistency(self):
        text='function solve(a,b){return a+b+a}';rec=self.rec(text)
        found,_,_=r.proposals(text,rec,ALPHABET+['x+y+z'])
        self.assertEqual(found,{})
    def test_never_splits_long_identifier(self):
        text='function solve(alpha,beta){return alpha+beta}'
        found,_,_=r.proposals(text,self.rec(text),ALPHABET+['ha+x+y'])
        self.assertEqual(found,{})
    def test_simultaneous_swap_not_rejected_early(self):
        text='function solve(a,b){return a+b}'
        found,_,_=r.proposals(text,self.rec(text),ALPHABET+['b+a'])
        self.assertTrue(found)
    def test_capture_rejected(self):
        text='function solve(a,b){return a+b}'
        found,_,_=r.proposals(text,self.rec(text),ALPHABET+['x+x'])
        self.assertFalse(found)
    def test_whole_body_rejected_before_acceptance(self):
        text='function solve(a,b){return a+b}'
        new,stats=r.coupled(text,self.rec(text),ALPHABET+['return x+y'])
        self.assertEqual(new,text);self.assertEqual(stats['moves'],0)
    def test_state_and_trial_caps_preserve_source(self):
        text='function solve(a,b){return a+b}';rec=self.rec(text)
        new,stats=r.coupled(text,rec,ALPHABET+['x+y'],state_limit=0)
        self.assertEqual(new,text);self.assertEqual(stats['caps'],1)
        new,stats=r.coupled(text,rec,ALPHABET+['x+y'],proposal_limit=0)
        self.assertEqual(new,text)
    def test_reflection_guard(self):
        text='function solve(a,b){return eval("a+b")}'
        new,stats=r.optimize(text,self.rec(text),ALPHABET+['x+y'],mode='coupled')
        self.assertEqual(new,text)

if __name__=='__main__':unittest.main()
