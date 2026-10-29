import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_r22b_reference_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain,compare=_o.reference,_o.validate_domain,_o.compare
class References(unittest.TestCase):
    def test_word_filter(self):self.assertEqual(reference(745,[['WordFilter','f','f','f'],[[['ab','ba','ab']],['a','b'],['b','b'],['ba','a']]]),[None,2,-1,1])
    def test_virus(self):self.assertEqual(reference(749,[[[1]]]),0);self.assertEqual(reference(749,[[[1,0]]]),1);self.assertEqual(reference(749,[[[0,1,0]]]),2)
    def test_safe(self):
        s=reference(753,[2,3]);self.assertEqual(len(s),10);self.assertTrue(compare(753,[2,3],s,None))
        self.assertTrue(compare(753,[2,2],'00110',None));self.assertFalse(compare(753,[2,2],'0011',None));self.assertFalse(compare(753,[2,2],'00100',None))
        self.assertEqual(reference(753,[3,1]),'000')
    def test_pyramid(self):
        self.assertIs(reference(756,['AB',['ABC']]),True);self.assertIs(reference(756,['AB',['BAC']]),False);self.assertIs(reference(756,['ABA',['ABC','BAC','CCD']]),True)
    def test_intervals(self):
        self.assertEqual(reference(757,[[[0,1]]]),2);self.assertEqual(reference(757,[[[0,1],[2,3]]]),4);self.assertEqual(reference(757,[[[0,3],[1,4]]]),2)
    def test_special(self):self.assertEqual(reference(761,['1100']),'1100');self.assertEqual(reference(761,['101100']),'110010')
    def test_couples(self):self.assertEqual(reference(765,[[1,0,3,2]]),0);self.assertEqual(reference(765,[[0,3,2,1]]),1)
    def test_exact_typing(self):self.assertFalse(compare(756,['AB',['ABC']],1,True));self.assertFalse(compare(745,None,[None,0],[None,False]))
    def test_domain(self):
        for pid,args in [(761,['01']),(765,[[0,0,1,2]]),(749,[[[1,0,1]]]),(757,[[[2,2]]]),(753,[4,9]),(756,['AG',[]]),(745,[['WordFilter','f'],[[['ab']],['A','b']]])]:
            with self.assertRaises(ValueError):validate_domain(pid,args)
if __name__=='__main__':unittest.main()
