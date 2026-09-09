"""Synthetic causality and arithmetic checks; no corpus or native parent access."""
import math
import unittest
from lib.context_edit_continuation_v1 import Continuation, core

KEY = b'ABCDEFGH'
DONOR = b'0123456789abcdefghijklmnopqrstuv'


def feed(model, data):
    for value in data:
        model.predict()
        model.observe(value)


class ContinuationTests(unittest.TestCase):
    def test_delayed_availability_and_exact_donor(self):
        model = Continuation('synthetic-raw-byte-v1')
        feed(model, KEY + DONOR[:4] + KEY)
        self.assertTrue(all(x is None for x in model.predict().values()))
        model.observe(0)
        model = Continuation('synthetic-raw-byte-v1')
        feed(model, KEY + DONOR + bytes(range(128,168)) + KEY)
        prediction = model.predict()
        self.assertEqual(prediction['D'], core.EditTransducer(DONOR).histogram())
        self.assertEqual(prediction['L'], core.LockstepTransducer(DONOR).histogram())
        self.assertEqual(model.source_start, len(KEY))
        self.assertLessEqual(model.source_start + len(DONOR), model.position)

    def test_colliding_tag_never_supplies_donor(self):
        model = Continuation('synthetic-raw-byte-v1')
        feed(model, KEY)
        model.bank[model.slot(KEY)] = (b'xxxxxxxx', DONOR, 0)
        self.assertTrue(all(x is None for x in model.predict().values()))

    def test_ordering_domain_and_episode_bound(self):
        model = Continuation('synthetic-raw-byte-v1')
        with self.assertRaises(ValueError): model.observe(0)
        model.predict()
        with self.assertRaises(ValueError): model.predict()
        with self.assertRaises(ValueError): model.observe(256)
        model.observe(0)
        feed(model, KEY + DONOR + bytes(range(128,168)) + KEY)
        feed(model, DONOR)
        self.assertIsNone(model.active)
        self.assertLessEqual(len(model.tail), 40)
        self.assertEqual(len(model.bank), 4096)
        with self.assertRaises(ValueError): Continuation('unidentified-bytes')

    def test_replay_and_constructed_insertion(self):
        left, right = [Continuation('synthetic-raw-byte-v1') for _ in range(2)]
        prefix = KEY + DONOR + bytes(range(128,168)) + KEY
        feed(left, prefix); feed(right, prefix)
        costs = dict(L=0.0, D=0.0, S=0.0)
        for value in b'!' + DONOR[:-1]:
            a, b = left.predict(), right.predict()
            self.assertEqual(a, b)
            self.assertEqual(left.state_digest(), right.state_digest())
            for arm, histogram in a.items():
                self.assertIsNotNone(histogram)
                self.assertGreater(min(histogram), 0)
                costs[arm] += math.log2(sum(histogram)) - math.log2(histogram[value])
            left.observe(value); right.observe(value)
            self.assertEqual(left.state_digest(), right.state_digest())
        self.assertLess(costs['D'], costs['L'])
        self.assertLess(costs['D'], costs['S'])
        self.assertEqual(left.triggers, 1)
        print('constructed_insertion_ideal_bits', costs)


if __name__ == '__main__':
    unittest.main()
