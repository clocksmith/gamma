import unittest
from independent_domain_oracles import ORACLES


class OracleControls(unittest.TestCase):
    def test_direct_permutations(self):
        for args,expected in [((1,1),'1'),((3,1),'123'),((3,3),'213'),((3,6),'321'),((4,9),'2314')]:self.assertEqual(ORACLES[60](*args),expected)
    def test_numeric_grammar(self):
        for value in ['0','0089','-3E-2','1.e2','.1','+.1','4.']:self.assertTrue(ORACLES[65](value),value)
        for value in ['e','.','NaN','1e','--6','1e2.5','+','-.']:self.assertFalse(ORACLES[65](value),value)
    def test_matrix_linear_membership(self):
        self.assertTrue(ORACLES[74]([[1,1],[2,3]],2));self.assertFalse(ORACLES[74]([[1,1],[2,3]],4))
    def test_rotated_array_linear_membership(self):
        self.assertTrue(ORACLES[81]([2,3,1,1],1));self.assertFalse(ORACLES[81]([2,3,1,1],0))
    def test_bottom_up_scramble(self):
        for args,expected in [(('great','rgeat'),True),(('abcde','caebd'),False),(('ab','ba'),True),(('a','b'),False),(('abc','bca'),True)]:self.assertEqual(ORACLES[87](*args),expected)


if __name__=='__main__':unittest.main()
