import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_l_reference_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain
class References(unittest.TestCase):
    def test_digit_sum(self):self.assertEqual(reference(3855,[1,2,2]),66)
    def test_split(self):self.assertEqual(reference(3857,[4]),6)
    def test_or(self):self.assertEqual(reference(3858,[[[3,5],[6,4]]]),5)
    def test_frequency(self):self.assertEqual(reference(3859,[[1,2,1,2,2],2,2]),2)
    def test_balance(self):self.assertEqual(reference(3862,[[2,8,2,2,5]]),2)
    def test_sort(self):self.assertEqual(reference(3863,['card']),2);self.assertEqual(reference(3863,['gf']),-1);self.assertEqual(reference(3863,['cba']),3)
    def test_partition(self):self.assertEqual(reference(3864,['1010',2,1]),6)
    def test_gcd(self):self.assertEqual(reference(3867,[[3,6,2,8]]),5)
    def test_swaps(self):self.assertEqual(reference(3868,[[10,10],[20,20]]),1)
    def test_fancy(self):self.assertEqual(reference(3869,[12340,12341]),1)
    def test_domain(self):
        with self.assertRaises(ValueError):validate_domain(3859,[[1],2,1])
if __name__=='__main__':unittest.main()
