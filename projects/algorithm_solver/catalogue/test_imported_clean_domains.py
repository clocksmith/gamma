"""Regression tests for domain structure and statement guarantees."""
import unittest
from .imported_clean_domains import validate


class CleanDomainTests(unittest.TestCase):
    def test_valid_semantic_boundaries(self):
        for pid,args in [(934,[[[0,1],[1,0]]]),(1519,[1,[],'a']),
                         (1579,[2,[[3,1,2]]]),(2023,[['0','1'],'10']),
                         (1499,[[[0,1],[2,1]],2]),(1290,[{'__list_node__':[1]}]),
                         (3161,[[[2,1,1]]]),(3131,[[0,2],[1,3]]),
                         (3168,['EEL']), (3174,['a1']),(1416,['0',1])]:
            validate(pid,args)

    def test_structural_and_semantic_rejections(self):
        for pid,args in [(934,[[[1,1],[1,0]]]),(1519,[3,[[0,1],[1,0]],'abc']),
                         (1494,[3,[[1,2],[2,1]],2]),(1499,[[[0,1],[2,1]],1]),
                         (1579,[2,[[3,1,3]]]),(1290,[{'__list_node__':[True]}]),
                         (2236,[{'__tree_node__':[1,None,1]}]),(3161,[[[1,1],[1,1],[2,1,1]]]),
                         (3131,[[0,2],[1,4]]),(3168,['LE']),(3174,['1a']),
                         (1257,[[['Root','Child'],['Child','Root']],'Root','Child']),
                         (1360,['2020-W01-1','2020-01-01']),(282,['123',True]),(691,['abc','a']),(1360,['2026-02-29','2026-03-01'])]:
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                validate(pid,args)


if __name__=='__main__':unittest.main()
