import unittest
import importlib.util as _importlib_util
from pathlib import Path as _Path
_spec = _importlib_util.spec_from_file_location('gamma_continuation_j_oracles_' + __name__, _Path(__file__).with_name('oracles.py'))
_oracles = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_oracles)
reference = _oracles.reference
validate_domain = _oracles.validate_domain
class References(unittest.TestCase):
    def test_rotate(self):self.assertEqual(reference(3819,[[1,-2,3,-4],3]),[3,-2,1,-4]);self.assertEqual(reference(3819,[[-1],3]),[-1])
    def test_tree(self):self.assertEqual(reference(3820,[4,[[0,1],[0,2],[0,3]],1,2,3]),3)
    def test_unrank(self):self.assertEqual(reference(3821,[4,2]),9)
    def test_reduce(self):self.assertEqual(reference(3824,[[3,7,5]]),3)
    def test_lis(self):self.assertEqual(reference(3825,[[2,3,6]]),3);self.assertEqual(reference(3825,[[0,0]]),0)
    def test_game(self):self.assertEqual(reference(3828,[[1,5,2]]),2)
    def test_alternating(self):self.assertEqual(reference(3830,[[3,2,1,2,3,2,1]]),4)
    def test_merge(self):self.assertEqual(reference(3834,[[3,1,1,2]]),[3,4]);self.assertEqual(reference(3834,[[2,2,4]]),[8])
    def test_cost(self):self.assertEqual(reference(3835,[[1,3,2],4]),5)
    def test_pairs(self):self.assertEqual(reference(3836,[[-3,-2],[1,2],2]),-7)
    def test_invalid(self):
        with self.assertRaises(ValueError):validate_domain(3821,[2,50])
        with self.assertRaises(ValueError):validate_domain(3820,[4,[[0,1],[1,0],[2,3]],0,1,2])
if __name__=='__main__':unittest.main()
