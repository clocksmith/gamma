"""Synthetic inverse and causality gates, using the existing arithmetic fixture."""
import hashlib
import json
import unittest

from projects.enwiki9.lib import predictor as codec
from projects.enwiki9.lib.residual_ratio_v1 import Q, ResidualRatio, normalized


class FixturePredictor(codec.Predictor):
    """Uniform raw-byte parent for correctness only; no trained FX2 substitute."""
    def __init__(self, arm):
        super().__init__(codec.RAW_MSB)
        self.calibration = ResidualRatio(256, arm)
        self.prefix = 1
        self.weights = None
        self.probabilities = hashlib.sha256()
        self.boundaries = hashlib.sha256()

    def _predict(self):
        if self.prefix == 1:
            self.weights = self.calibration.predict([256] * 256)
        depth = self.prefix.bit_length() - 1
        start = (self.prefix - (1 << depth)) << (8 - depth)
        width = 1 << (8 - depth)
        total = sum(self.weights[start:start + width])
        one = sum(self.weights[start + width // 2:start + width])
        p = max(1, min(65535, one * Q // total))
        self.probabilities.update(p.to_bytes(2, 'little'))
        return p

    def _update(self, bit):
        self.prefix = self.prefix * 2 + bit
        if self.prefix >= 256:
            self.calibration.observe(self.prefix - 256)
            self.prefix, self.weights = 1, None
        # Include the current bit prefix, pending symbol distribution, histories
        # and pending bit prediction. The fixture coder calls updates identically.
        self.boundaries.update(self.serialize())

    def _export_state(self):
        return dict(calibration=json.loads(self.calibration.serialize()),
                    prefix=self.prefix, weights=self.weights)

    @classmethod
    def restore(cls, payload, frontend=codec.RAW_MSB):
        value = json.loads(payload)
        frontend.require(codec.Frontend(**value['frontend']))
        state = value['model']
        result = cls(state['calibration']['arm'])
        result.calibration = ResidualRatio.restore(codec.canonical(state['calibration']))
        result.position, result._pending = value['position'], value['pending']
        result.prefix, result.weights = state['prefix'], state['weights']
        return result


def comparison(raw):
    if len(raw) > 4096:
        raise ValueError('synthetic raw input ceiling')
    outputs = {}
    for arm in ('P', 'K', 'D', 'S'):
        encoder, decoder, repeat = (FixturePredictor(arm) for _ in range(3))
        archive = codec.encode(raw, encoder)
        restored = codec.decode(archive, decoder, maximum_bytes=4096)
        repeated = codec.encode(raw, repeat)
        assert raw == restored and archive == repeated
        assert encoder.serialize() == decoder.serialize() == repeat.serialize()
        assert encoder.probabilities.digest() == decoder.probabilities.digest() == repeat.probabilities.digest()
        assert encoder.boundaries.digest() == decoder.boundaries.digest() == repeat.boundaries.digest()
        outputs[arm] = dict(archive=archive, restored=restored, repeat=repeated,
                            probability_sha256=encoder.probabilities.hexdigest(),
                            boundary_sha256=encoder.boundaries.hexdigest(),
                            boundaries=encoder.position,
                            terminal_state=encoder.serialize())
    assert outputs['P']['archive'] == outputs['K']['archive']
    assert outputs['P']['probability_sha256'] == outputs['K']['probability_sha256']
    return outputs


class RatioTests(unittest.TestCase):
    def test_normalization_conserves_mass_and_ties(self):
        self.assertEqual(normalized([1, 1, 1]), [21846, 21845, 21845])
        self.assertEqual(sum(normalized([65535] + [1] * 255)), Q)

    def test_initial_identity_and_truth_order(self):
        model = ResidualRatio(3)
        with self.assertRaises(ValueError): model.observe(1)
        self.assertEqual(model.predict([1, 10, 100]), (1, 10, 100))
        with self.assertRaises(ValueError): model.predict([1, 10, 100])
        before = model.serialize()
        with self.assertRaises(ValueError): model.observe(3)
        self.assertEqual(before, model.serialize())
        model.observe(0)
        self.assertEqual(model.observed, [Q, 0, 0])
        self.assertEqual(sum(model.expected), Q)

    def test_fixed_update_and_decay(self):
        m = ResidualRatio(2)
        for _ in range(256): m.predict([1, 1]); m.observe(0)
        self.assertEqual(m.observed, [128 * Q, 0])
        self.assertEqual(m.expected, [64 * Q, 64 * Q])
        self.assertEqual(m.predict([600, 600]), (1000, 200))

    def test_ratio_clipping_and_positive_counts(self):
        m = ResidualRatio(2)
        for _ in range(255): m.predict([1, 65535]); m.observe(0)
        self.assertEqual(m.predict([65535, 1]), (262140, 1))

    def test_invalid_inputs_leave_state_unchanged(self):
        m = ResidualRatio(2)
        for bad in ([0, 2], [True, 2], [1.0, 2], [1], [1, 65536]):
            before = m.serialize()
            with self.assertRaises(ValueError): m.predict(bad)
            self.assertEqual(before, m.serialize())

    def test_checkpoint_across_pending_and_decay(self):
        for arm in ('P', 'K', 'D', 'S'):
            m = ResidualRatio(3, arm)
            for i in range(1025):
                if i in (0, 255, 256, 511, 512, 1024):
                    self.assertEqual(ResidualRatio.restore(m.serialize()).serialize(), m.serialize())
                m.predict([1, 3, 7])
                resumed = ResidualRatio.restore(m.serialize())
                m.observe(i % 3); resumed.observe(i % 3)
                self.assertEqual(m.serialize(), resumed.serialize())

    def test_malformed_checkpoint_rejected(self):
        m = ResidualRatio(2)
        value = json.loads(m.serialize())
        for key, bad in [('position', -1), ('position', True), ('position', 1),
                         ('observed', [Q, 0]), ('expected', [0]),
                         ('pending', [0, 1]), ('version', True), ('size', 257)]:
            changed = dict(value); changed[key] = bad
            with self.assertRaises(ValueError): ResidualRatio.restore(codec.canonical(changed))
        for bad in (b'x' * 16385, b'[]', b'{', m.serialize() + b' '):
            with self.assertRaises(ValueError): ResidualRatio.restore(bad)

    def test_future_suffix_cannot_change_prefix(self):
        a, b = ResidualRatio(2), ResidualRatio(2)
        for x in [0, 1, 0] * 100:
            self.assertEqual(a.predict([1, 2]), b.predict([1, 2]))
            a.observe(x); b.observe(x)
        self.assertEqual(a.predict([1, 2]), b.predict([1, 2]))
        a.observe(0); b.observe(1)
        self.assertNotEqual(a.state_digest(), b.state_digest())

    def test_fixture_exact_repeats_and_complete_state(self):
        for raw in (b'', bytes(range(256)), b'A' * 512):
            rows = comparison(raw)
            if raw == b'A' * 512:
                self.assertLess(len(rows['D']['archive']), len(rows['P']['archive']))
                self.assertLess(len(rows['D']['archive']), len(rows['S']['archive']))


if __name__ == '__main__': unittest.main()
