import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).parent

def load(name):
    s=importlib.util.spec_from_file_location('gamma_requested589_reference_'+name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load('oracles');C=load('cases')

class References(unittest.TestCase):
    def test_known_results(self):
        examples=[(600,[5],5),(606,[[1,2,3,None,4]],'1(2()(4))(3)'),(617,[[1,3,2,5],[2,1,3,None,4,None,7]],[3,4,5,5,4,None,7]),(623,[[4,2,6,3,1,5],1,2],[4,1,1,2,None,None,6,3,1,5]),(623,[[4,2],9,3],[4,2,None,9,9]),(629,[3,1],2),(630,[[[100,200],[200,1300],[1000,1250],[2000,3200]]],3),(632,[[[4,10,15,24,26],[0,9,12,20],[5,18,22,30]]],[20,24]),(637,[[3,9,20,None,None,15,7]],[3.,14.5,11.]),(639,['**'],96),(653,[[5,3,6,2,4,None,7],9],True),(654,[[3,2,1,6,0,5]],[6,3,5,None,2,0,None,None,1]),(662,[[1,3,2,5,3,None,9]],4),(664,['aba'],2),(671,[[2,2,5,None,None,5,7]],5),(675,[[[1,2,3],[0,0,4],[7,6,5]]],6),(679,[[4,1,8,7]],True),(689,[[1,2,1,2,6,7,5,1],2],[0,3,5]),(690,[[[1,5,[2,3]],[2,3,[]],[3,3,[]]],1],11),(699,[[[1,2],[2,3],[6,1]]],[2,5,5]),(719,[[1,3,1],1],0),(725,[[1,2,3],5],[[1],[2],[3],[],[]])]
        for pid,args,want in examples:
            with self.subTest(pid=pid):self.assertEqual(O.reference(pid,args),want)
    def test_all_ids_have_bounded_and_maximum_cases(self):
        for pid in O.IDS:
            with self.subTest(pid=pid):
                rows=C.build_cases(pid,True);self.assertTrue(rows);self.assertTrue(any(r['category']=='analytic-maximum' for r in rows))
    def test_invalid_domains(self):
        for pid,args in [(600,[0]),(629,[1001,0]),(639,['x']),(654,[[1,1]]),(719,[[1],1]),(725,[[1],51]),(622,[['MyCircularQueue'],[[0]]])]:
            with self.subTest(pid=pid),self.assertRaises(ValueError):O.validate_domain(pid,args)
if __name__=='__main__':unittest.main()
