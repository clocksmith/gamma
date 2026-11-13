import math
import unittest

from projects.distillation.wgsl.channel_gain.rule import (
    channel_energy, derive_gains, permuted_gains, random_gains,
    shuffled_context, without_instruction,
)


class ChannelGainTests(unittest.TestCase):
    def test_exact_span_excludes_template_and_outside_activations(self):
        activations = [[float('nan'), 99], [2, -3], [4, 5], [float('inf'), 99]]
        self.assertEqual(channel_energy(activations, start=1, stop=3, template_positions=[0, 3]), (10, 17))
        with self.assertRaisesRegex(ValueError, 'chat-template'):
            channel_energy(activations, start=0, stop=3, template_positions=[0, 3])

    def test_formula_clipping_and_geometric_normalization(self):
        state = derive_gains([5, 0, 2], [1, 1, 1], beta=.5, clip=1, epsilon=1)
        self.assertEqual(state.clipped_scores, (1, -.5, .5))
        expected = [math.exp(1/3), math.exp(-5/12), math.exp(1/12)]
        for actual, wanted in zip(state.gains, expected):
            self.assertAlmostEqual(actual, wanted)
        self.assertAlmostEqual(sum(math.log(g) for g in state.gains), 0)
        self.assertNotAlmostEqual(sum(state.gains)/3, 1)
        inverse = derive_gains([5, 0, 2], [1, 1, 1], beta=-.5, clip=1, epsilon=1)
        for positive, negative in zip(state.gains, inverse.gains):
            self.assertAlmostEqual(positive * negative, 1)

    def test_zero_beta_and_zero_reference_are_well_defined(self):
        self.assertEqual(derive_gains([4, 2], [0, 0], beta=0, clip=2, epsilon=.01).gains, (1, 1))
        state = derive_gains([1e308, 0], [0, 0], beta=.1, clip=2, epsilon=1e-300)
        self.assertEqual(state.clipped_scores, (2, 0))
        self.assertTrue(all(math.isfinite(g) for g in state.gains))
        self.assertEqual(derive_gains([0, 0], [0, 0], beta=1, clip=1e-308, epsilon=1e-308).clipped_scores, (0, 0))

    def test_invalid_inputs_fail_closed(self):
        for args in [dict(beta=1, clip=0, epsilon=1), dict(beta=1, clip=1, epsilon=0),
                     dict(beta=float('nan'), clip=1, epsilon=1), dict(beta=True, clip=1, epsilon=1)]:
            with self.assertRaises(ValueError):
                derive_gains([1], [1], **args)
        for energy in [[], [-1], [float('inf')]]:
            with self.assertRaises(ValueError):
                derive_gains(energy, [1], beta=1, clip=1, epsilon=1)
        with self.assertRaises(ValueError):
            derive_gains([1, 0], [0, 1], beta=1000, clip=1, epsilon=1)

    def test_controls_are_deterministic_and_do_not_mutate_input(self):
        tokens = [100, 11, 12, 13, 14, 15, 101]
        kwargs = dict(start=1, stop=6, template_positions=[0, 6])
        shuffled = shuffled_context(tokens, **kwargs, seed=47)
        self.assertEqual(shuffled, shuffled_context(tokens, **kwargs, seed=47))
        self.assertEqual(shuffled[0], 100)
        self.assertEqual(shuffled[-1], 101)
        self.assertCountEqual(shuffled[1:-1], tokens[1:-1])
        self.assertNotEqual(tuple(tokens), shuffled)
        self.assertEqual(without_instruction(tokens, **kwargs), (100, 101))
        self.assertEqual(tokens, [100, 11, 12, 13, 14, 15, 101])
        state = derive_gains([1, 2, 4, 8], [2]*4, beta=.2, clip=2, epsilon=.1)
        permuted = permuted_gains(state.gains, seed=47)
        self.assertCountEqual(permuted, state.gains)
        random = random_gains(state.gains, seed=47)
        self.assertEqual(random, random_gains(state.gains, seed=47))
        self.assertNotEqual(random, random_gains(state.gains, seed=11))
        self.assertAlmostEqual(sum(math.log(g) for g in random), 0)
        self.assertAlmostEqual(sum(math.log(g)**2 for g in random), sum(v*v for v in state.log_gains))
        self.assertEqual(random_gains([1, 1], seed=47), (1, 1))


if __name__ == '__main__':
    unittest.main()
