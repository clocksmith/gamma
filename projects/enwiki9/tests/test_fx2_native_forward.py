"""Synthetic forward-value and adjoint tests; no checkpoints or native launches."""
import unittest
import torch
from gamma_enwiki9.adapters.fx2_native_forward import attach_native_values

class NativeValueTests(unittest.TestCase):
    def test_exact_values_survive_cancellation_and_backward_routes_to_surrogate(self):
        x = torch.tensor([1e20, -1e20, 0.25], requires_grad=True)
        surrogate = 2*x
        native = torch.tensor([3.5, -0.0, 0.75])
        value = attach_native_values(surrogate, native)
        self.assertTrue(torch.equal(value.detach().view(torch.int32), native.view(torch.int32)))
        (value*torch.tensor([1., 2., 3.])).sum().backward()
        self.assertTrue(torch.equal(x.grad, torch.tensor([2., 4., 6.])))
        self.assertIsNone(native.grad)

    def test_mismatched_or_attached_native_values_fail(self):
        x = torch.zeros(2, requires_grad=True)
        with self.assertRaises(ValueError): attach_native_values(x, torch.zeros(1))
        with self.assertRaises(ValueError): attach_native_values(x, torch.zeros(2, requires_grad=True))

if __name__ == '__main__': unittest.main()
