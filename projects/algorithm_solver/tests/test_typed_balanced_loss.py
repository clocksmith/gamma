import math
import unittest
import torch
from algsolve.synth.typed_balanced_loss import balanced_literal_loss, per_example_balanced_loss
from algsolve.synth.typed_predictor import per_example_loss


class BalancedLiteralLossTests(unittest.TestCase):
    def test_zero_logits_keep_initial_scale_and_ignored_examples_zero(self):
        labels=torch.tensor([[1,0,0,-100],[0,0,0,-100],[1,1,-100,-100],[-100]*4])
        logits=torch.zeros_like(labels,dtype=torch.float64,requires_grad=True)
        losses=balanced_literal_loss(logits,labels)
        torch.testing.assert_close(losses,torch.tensor([math.log(2)]*3+[0.],dtype=torch.float64))
        losses.sum().backward()
        self.assertTrue(torch.equal(logits.grad[labels==-100],torch.zeros_like(logits.grad[labels==-100])))

    def test_class_gradient_mass_is_balanced_despite_sparse_positives(self):
        labels=torch.tensor([[1]+[0]*128]);logits=torch.zeros_like(labels,dtype=torch.float64,requires_grad=True)
        balanced_literal_loss(logits,labels).sum().backward()
        self.assertAlmostEqual(abs(logits.grad[0,0].item()),logits.grad[0,1:].sum().item())
        self.assertAlmostEqual(abs(logits.grad[0,0].item()),.25)
        self.assertTrue(torch.all(logits.grad[0,1:]>0))

    def test_examples_and_classes_use_separate_denominators(self):
        labels=torch.tensor([[1,0,0,-100],[1,1,0,0]])
        values=torch.tensor([[2.,-1.,3.,100.],[-3.,1.,-2.,4.]])
        raw=torch.nn.functional.binary_cross_entropy_with_logits(values,labels.clamp_min(0).float(),reduction='none')
        expected=torch.stack([.5*(raw[0,0]+raw[0,1:3].mean()),.5*(raw[1,:2].mean()+raw[1,2:].mean())])
        torch.testing.assert_close(balanced_literal_loss(values,labels),expected)

    def test_nonliteral_head_loss_and_gradients_unchanged(self):
        labels={'op':torch.tensor([[1,-100]]),'bits':torch.tensor([[[1,0],[0,-100]]])}
        op=torch.tensor([[[.2,.3],[1.,-1.]]],requires_grad=True)
        bits=torch.tensor([[[1.,-.5],[.4,5.]]],requires_grad=True)
        total=per_example_balanced_loss({'op':op,'bits':bits},labels)
        expected=per_example_loss({'op':op},labels)+balanced_literal_loss(bits,labels['bits'])
        torch.testing.assert_close(total,expected)
        total.sum().backward();first=op.grad.clone();op.grad=None
        per_example_loss({'op':op},labels).sum().backward()
        torch.testing.assert_close(first,op.grad)

    def test_rejects_invalid_labels_and_shape(self):
        for bad in [torch.tensor([[2]]),torch.tensor([[-1]])]:
            with self.subTest(labels=bad.tolist()),self.assertRaises(ValueError):balanced_literal_loss(torch.zeros(1,1),bad)
        with self.assertRaises(ValueError):balanced_literal_loss(torch.zeros(1,2),torch.zeros(1,1))


if __name__=='__main__':unittest.main()
