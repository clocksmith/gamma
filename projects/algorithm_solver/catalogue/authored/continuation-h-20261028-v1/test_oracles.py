import unittest
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('continuation_h_test_oracles', Path(__file__).with_name('oracles.py'))
_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_oracle)
reference, validate_domain = _oracle.reference, _oracle.validate_domain
class References(unittest.TestCase):
    def test_swaps(self):self.assertEqual(reference(3781,[[2,1,5,2,3],'01010']),7)
    def test_delete(self):self.assertEqual(reference(3784,['abc',[10,5,8]]),13)
    def test_split(self):self.assertEqual(reference(3788,[[10,-1,3,-4,-5]]),17);self.assertEqual(reference(3788,[[-7,-5,3]]),-2)
    def test_items(self):self.assertEqual(reference(3789,[3,2,1,3,2]),3);self.assertEqual(reference(3789,[5,4,15,0,0]),0)
    def test_repunits(self):self.assertEqual(reference(3790,[7]),6);self.assertEqual(reference(3790,[2]),-1)
    def test_balanced(self):self.assertEqual(reference(3791,[1,100]),9);self.assertEqual(reference(3791,[120,129]),1)
    def test_distinct(self):self.assertEqual(reference(3795,[[2,2,3,1],4]),2)
    def test_squares(self):self.assertEqual(reference(3799,[['able','area','echo','also']]),[['able','area','echo','also'],['area','able','also','echo']])
    def test_binary_cost(self):self.assertEqual(reference(3800,['00','11',10,2,2]),4);self.assertEqual(reference(3800,['01','10',10,2,2]),2)
    def test_merges(self):self.assertEqual(reference(3801,[[[1,3,5],[2,4],[6,7,8]]]),18);self.assertEqual(reference(3801,[[[1],[1]]]),2)
    def test_invalid(self):
        with self.assertRaises(ValueError):validate_domain(3801,[[[2,1],[1]]])
        with self.assertRaises(ValueError):validate_domain(3781,[[True],'1'])
if __name__=='__main__':unittest.main()
