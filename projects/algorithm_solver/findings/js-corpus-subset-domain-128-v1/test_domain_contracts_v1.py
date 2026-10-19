import itertools
import unittest
from domain_contracts_v1 import reasons


class DomainContractTests(unittest.TestCase):
    def test_permutation_bounds(self):
        for args in [[1,1],[9,362880],[8,40320]]:self.assertEqual(reasons(60,args),[])
        for args in [[0,1],[10,1],[8,40321],[7,5041],[3,0],[True,1],[3,True]]:self.assertTrue(reasons(60,args))

    def test_number_string_contract(self):
        for s in ['0','e','--6','1'*20,'+-Ee.']:self.assertEqual(reasons(65,[s]),[])
        for s in ['', '1'*21, ['-.'], ' 1','١','NaN\n',True]:self.assertTrue(reasons(65,[s]))

    def test_matrix_contract(self):
        for matrix,target in [([[1,1],[2,3]],2),([[-10000]],10000),([[0]],0)]:self.assertEqual(reasons(74,[matrix,target]),[])
        for matrix,target in [([],0),([[]],0),([[1,2],[2,3]],2),([[2,1]],1),([[1],[2,3]],1),([[10001]],1),([[True]],1),([[1]],10001)]:self.assertTrue(reasons(74,[matrix,target]))

    def test_rotation_against_independent_exhaustive_definition(self):
        for length in range(1,6):
            for sequence in itertools.product([-1,0,1],repeat=length):
                values=list(sequence);ordered=sorted(values)
                expected=any(values==ordered[k:]+ordered[:k] for k in range(length))
                self.assertEqual(not reasons(81,[values,0]),expected,values)

    def test_rotation_bounds(self):
        for args in [[[],0],[[0]*5001,0],[[10001],0],[[True],0],[[1],False]]:self.assertTrue(reasons(81,args))
        self.assertEqual(reasons(81,[[10000,-10000,0],10000]),[])

    def test_scramble_contract(self):
        for args in [['a','a'],['ab','ba'],['a'*30,'b'*30]]:self.assertEqual(reasons(87,args),[])
        for args in [['a','ab'],['',''],['A','a'],['a'*31,'b'*31],['1','1']]:self.assertTrue(reasons(87,args))

    def test_unknown_contract_fails_closed(self):
        with self.assertRaises(ValueError):reasons(999,[])


if __name__=='__main__':unittest.main()
