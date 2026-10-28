import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_o_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain
class References(unittest.TestCase):
    def test_bitonic(self):self.assertEqual(reference(3909,[[1,3,2,1]]),1)
    def test_graph(self):self.assertEqual(reference(3910,[[1,0,1],[[0,1],[1,2]]]),2)
    def test_vowels(self):self.assertEqual(reference(3913,['leetcode']),'leetcedo')
    def test_increase(self):self.assertEqual(reference(3914,[[3,3,2,1]]),2)
    def test_alternating(self):self.assertEqual(reference(3915,[[3,5,4,2,4],1]),14)
    def test_primes(self):self.assertEqual(reference(3918,[13]),132)
    def test_moves(self):self.assertEqual(reference(3919,[[-5,-2,3],[[0,2],[2,0],[1,2]]]),[6,2,5])
    def test_words(self):self.assertEqual(reference(3926,[['a-b a--b ','a-','b'],['a-b','a','b']]),[2,1,1])
    def test_powers(self):self.assertEqual(reference(3932,[0,9,2]),4)
    def test_unique(self):self.assertEqual(reference(3934,[[1,1,2,2,1]]),2)
    def test_residues(self):self.assertEqual(reference(3937,[[1,4,2,8],3]),2)
    def test_strength(self):self.assertEqual(reference(3941,['bbB11#']),11)
    def test_rotate(self):self.assertEqual(reference(3942,[[0,2,1]]),2)
    def test_invalid(self):
        with self.assertRaises(ValueError):validate_domain(3942,[[0,0]])
if __name__=='__main__':unittest.main()
