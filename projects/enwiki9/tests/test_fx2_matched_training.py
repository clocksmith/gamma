"""Boundary and target alignment checks for native-forward training windows."""
import unittest
import numpy as np
from gamma_enwiki9.adapters.fx2_matched_training import windows, loss

class WindowTests(unittest.TestCase):
    def test_rejects_invented_or_crossed_reset(self):
        t=np.arange(8,dtype='u1');m=np.array([1,0,0,2,1,0,0,0],dtype='u1');p=np.zeros((8,205),dtype='<f2')
        with self.assertRaises(ValueError):windows(t,m,p,[1],0,1)
        with self.assertRaises(ValueError):windows(t,m,p,[0],1,2)
        a=windows(t,m,p,[4],1,2)[0]
        self.assertEqual(a[0].tolist(),[4,5,6,7])
    def test_loss_excludes_warmup_and_pairs_next_truth(self):
        import torch
        p=torch.full((4,205),.5,requires_grad=True)
        tokens=np.array([0,3,8,9],dtype='u1')
        v=loss(p,tokens,1,2);self.assertEqual(v.item(),1.)
        v.backward();indices=p.grad.nonzero().tolist()
        self.assertEqual(indices,[[1,8],[2,9]])
