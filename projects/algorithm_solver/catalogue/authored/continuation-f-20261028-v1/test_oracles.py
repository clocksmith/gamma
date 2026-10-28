import unittest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('continuation_f_test_oracles', Path(__file__).with_name('oracles.py'))
_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_oracle)
reference, validate_domain = _oracle.reference, _oracle.validate_domain
class References(unittest.TestCase):
    def test_triples(self):self.assertEqual(reference(3741,[[1,2,1,1,3]]),6)
    def test_paths(self):self.assertEqual(reference(3742,[[[0,1],[2,0]],1]),2);self.assertEqual(reference(3742,[[[0,1],[1,2]],1]),-1)
    def test_removal(self):self.assertEqual(reference(3746,['aaabb']),1);self.assertEqual(reference(3746,['abab']),0)
    def test_zero_outputs(self):self.assertEqual(reference(3747,[10]),9);self.assertEqual(reference(3747,[100]),90)
    def test_stable(self):self.assertEqual(reference(3748,[[3,1,2],[[0,1],[1,2],[0,2]]]),[2,3,4])
    def test_waviness(self):
        for pid in (3751,3753):self.assertEqual(reference(pid,[120,130]),3);self.assertEqual(reference(pid,[4848,4848]),2)
    def test_xor(self):self.assertEqual(reference(3755,[[3,1,3,2,0]]),4)
    def test_digits(self):self.assertEqual(reference(3756,['10203004',[[0,7],[1,3],[4,6]]]),[12340,4,9])
    def test_greater(self):self.assertEqual(reference(3759,[[3,1,2],1]),2);self.assertEqual(reference(3759,[[5,5,5],2]),0)
    def test_domains(self):
        with self.assertRaises(ValueError):validate_domain(3759,[[True],0])
        with self.assertRaises(ValueError):validate_domain(3742,[[[1]],0])
        validate_domain(3753,[10**15,10**15])
if __name__=='__main__':unittest.main()
