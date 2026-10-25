import unittest
from .benchmark_known_spec import benchmark, distribution


class DeliveryTiming(unittest.TestCase):
    def test_nearest_rank_tail(self):
        self.assertEqual(distribution(list(range(1, 21))),
                         {'count': 20, 'median_seconds': 10.5, 'p95_seconds': 19})
        self.assertIsNone(distribution([])['p95_seconds'])

    def test_bounds_reject_before_configuration_access(self):
        for kwargs in ({'max_requests': 0}, {'max_requests': True},
                       {'max_wall': 0}, {'max_wall': 301}):
            with self.assertRaises(ValueError):
                benchmark('/not-opened', 'a' * 64, **kwargs)
