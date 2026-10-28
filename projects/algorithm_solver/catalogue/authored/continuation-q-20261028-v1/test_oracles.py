import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_q_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain
class References(unittest.TestCase):
    def test_ladder(self):self.assertEqual(len(reference(126,['hit','cog',['hot','dot','dog','lot','log','cog']])),2)
    def test_sum(self):self.assertEqual(reference(129,[{'values':[1,2,3],'left':[1,None,None],'right':[2,None,None],'root':0}]),25)
    def test_cuts(self):self.assertEqual(reference(132,['aab']),1)
    def test_clone(self):p={'values':[1,2],'neighbors':[[1],[0]],'root':0};self.assertEqual(reference(133,[p]),p)
    def test_random(self):p={'values':[1,1],'random':[1,0]};self.assertEqual(reference(138,[p]),p)
    def test_words(self):self.assertEqual(reference(140,['catsanddog',['cat','cats','and','sand','dog']]),['cat sand dog','cats and dog'])
    def test_cycle(self):self.assertTrue(reference(141,[{'values':[1,1],'pos':1}]))
    def test_entry(self):self.assertEqual(reference(142,[{'values':[1,1],'pos':1}]),1)
    def test_reorder(self):self.assertEqual(reference(143,[{'values':[1,1,1,1]}])['original_identity_order'],[0,3,1,2])
    def test_preorder(self):self.assertEqual(reference(144,[{'values':[],'left':[],'right':[],'root':None}]),[])
    def test_domain(self):
        with self.assertRaises(ValueError):validate_domain(129,[{'values':[1],'left':[0],'right':[None],'root':0}])
if __name__=='__main__':unittest.main()
