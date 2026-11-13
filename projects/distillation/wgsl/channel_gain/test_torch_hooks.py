import unittest

try:
    import torch
except ImportError:
    torch = None

from projects.distillation.wgsl.channel_gain.torch_hooks import EnergyCollector, GainApplicator


@unittest.skipIf(torch is None, 'optional torch not installed')
class HookTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(47)
        class Toy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.gate = torch.nn.Linear(2, 4, bias=False)
                self.up = torch.nn.Linear(2, 4, bias=False)
                self.down = torch.nn.Linear(4, 2, bias=False)
            def activation(self, x):
                return torch.nn.functional.silu(self.gate(x)) * self.up(x)
            def forward(self, x):
                return self.down(self.activation(x))
        self.model = Toy().eval()
        self.modules = {'late': self.model.down}
        self.x = torch.tensor([[[1., 2.], [3., 4.], [5., 6.], [7., 8.]]])
        self.original = {k: v.detach().clone() for k, v in self.model.state_dict().items()}

    def test_energy_is_post_swiglu_and_exact_span(self):
        expected = self.model.activation(self.x)[0, 1:3].float().square().mean(0)
        with EnergyCollector(self.modules, token_count=4, start=1, stop=3, template_positions=[0, 3]) as collector:
            actual_output = self.model(self.x)
            energy = collector.export()['late']
        torch.testing.assert_close(torch.tensor(energy), expected)
        torch.testing.assert_close(actual_output, self.model(self.x))
        self.assertEqual(len(self.model.down._forward_pre_hooks), 0)

    def test_same_frozen_gain_hash_for_both_arms_and_weights_unchanged(self):
        gains = {'late': [1., 2., .5, 1.]}
        baseline = self.model(self.x)
        full = GainApplicator(self.modules, gains, phase='re-prefill')
        decode = GainApplicator(self.modules, gains, phase='decode')
        self.assertEqual(full.gain_hash, decode.gain_hash)
        gains['late'][0] = 999  # Caller mutation cannot alter the frozen state.
        with full:
            transformed = self.model(self.x)
            token = self.model(self.x[:, -1:])
            torch.testing.assert_close(transformed, self.model.down.weight.new_tensor([1., 2., .5, 1.])
                                       .mul(self.model.activation(self.x)) @ self.model.down.weight.T)
        with decode:
            torch.testing.assert_close(self.model(self.x[:, -1:]), token)
        self.assertEqual(full.gain_hash, decode.gain_hash)
        self.assertFalse(torch.equal(transformed, baseline))
        torch.testing.assert_close(self.model(self.x), baseline)
        for key, value in self.model.state_dict().items():
            self.assertTrue(torch.equal(value, self.original[key]))
        self.assertEqual(len(self.model.down._forward_pre_hooks), 0)

    def test_decode_prefill_and_overlap_fail_without_leaking_hooks(self):
        with GainApplicator(self.modules, {'late': [1]*4}, phase='decode'):
            with self.assertRaisesRegex(RuntimeError, 'already belongs'):
                with EnergyCollector(self.modules, token_count=4, start=1, stop=3, template_positions=[0, 3]):
                    pass
            with self.assertRaisesRegex(ValueError, 'multi-token'):
                self.model(self.x)
        self.assertEqual(len(self.model.down._forward_pre_hooks), 0)
        with self.assertRaisesRegex(ValueError, 'channel count'):
            with GainApplicator(self.modules, {'late': [1]*3}, phase='decode'):
                self.model(self.x[:, -1:])
        self.assertEqual(len(self.model.down._forward_pre_hooks), 0)

    def test_collector_refuses_chunks_repeated_calls_and_missing_layer(self):
        with EnergyCollector(self.modules, token_count=4, start=1, stop=3, template_positions=[0, 3]) as collector:
            with self.assertRaisesRegex(RuntimeError, 'not every'):
                collector.export()
            with self.assertRaisesRegex(ValueError, 'full prefill'):
                self.model(self.x[:, :2])
            self.model(self.x)
            with self.assertRaisesRegex(RuntimeError, 'exactly one'):
                self.model(self.x)
        self.assertEqual(len(self.model.down._forward_pre_hooks), 0)


if __name__ == '__main__':
    unittest.main()
