import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_n_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain
class References(unittest.TestCase):
    def test_peaks(self):self.assertEqual(reference(3891,[[2,1,1,3]]),2)
    def test_digits(self):self.assertEqual(reference(3895,[[12,54,32,22],2]),4)
    def test_primes(self):self.assertEqual(reference(3896,[[1,2,3,4]]),3)
    def test_segments(self):self.assertEqual(reference(3897,[[1,2],[1,0]]),14)
    def test_angles(self):self.assertTrue(_o.compare(3899,reference(3899,[[3,4,5]]),[36.869897646,53.130102354,90]));self.assertEqual(reference(3899,[[2,4,2]]),[])
    def test_swap(self):self.assertEqual(reference(3900,['100001']),4)
    def test_queries(self):self.assertEqual(reference(3901,[[4,8,12,16],2,[[0,3],[2,6]]]),1)
    def test_stable(self):self.assertEqual(reference(3904,[[5,0,1,4],3]),3)
    def test_flood(self):self.assertEqual(reference(3905,[2,2,[[0,0,1],[1,1,2]]]),[[1,2],[2,2]])
    def test_path(self):self.assertEqual(reference(3906,[8,10,'DDDRRR']),2)
    def test_domains(self):
        with self.assertRaises(ValueError):validate_domain(3906,[1,9,'DDDDRR'])
if __name__=='__main__':unittest.main()
