"""Source-free model, transition and contract controls; no candidate imports."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('native_continuation_reference', Path(__file__).with_name('oracles.py'))
o = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(o)


class NativeReferenceTests(unittest.TestCase):
    def test_exam_official_example(self):
        args = [['ExamTracker', 'record', 'totalScore', 'record', 'totalScore', 'totalScore', 'totalScore', 'totalScore'],
                [[], [1, 98], [1, 1], [5, 99], [1, 3], [1, 5], [3, 4], [2, 5]]]
        self.assertEqual(o.reference(3709, args), [None, None, 98, None, 98, 197, 0, 99])

    def test_auction_official_example(self):
        args = [['AuctionSystem', 'addBid', 'addBid', 'getHighestBidder', 'updateBid', 'getHighestBidder', 'removeBid', 'getHighestBidder', 'getHighestBidder'],
                [[], [1, 7, 5], [2, 7, 6], [7], [1, 7, 8], [7], [2, 7], [7], [3]]]
        self.assertEqual(o.reference(3815, args), [None, None, None, 2, None, 1, None, 1, -1])

    def test_rides_official_examples(self):
        examples = [
            ([['RideSharingSystem', 'addRider', 'addDriver', 'addRider', 'matchDriverWithRider', 'addDriver', 'cancelRider', 'matchDriverWithRider', 'matchDriverWithRider'],
              [[], [3], [2], [1], [], [5], [3], [], []]],
             [None, None, None, None, [2, 3], None, None, [5, 1], [-1, -1]]),
            ([['RideSharingSystem', 'addRider', 'addDriver', 'addDriver', 'matchDriverWithRider', 'addRider', 'cancelRider', 'matchDriverWithRider'],
              [[], [8], [8], [6], [], [2], [2], []]],
             [None, None, None, None, [8, 8], None, None, [-1, -1]]),
        ]
        for args, answer in examples: self.assertEqual(o.reference(3829, args), answer)

    def test_exam_inclusive_endpoints_gaps_and_large_exact_sum(self):
        args = [['ExamTracker', 'record', 'record', 'totalScore', 'totalScore', 'totalScore'],
                [[], [1, 10**9], [10**9, 10**9], [1, 10**9], [2, 10**9-1], [10**9, 10**9]]]
        self.assertEqual(o.reference(3709, args), [None, None, None, 2*10**9, 0, 10**9])
        operations = ['ExamTracker'] + ['record']*499 + ['totalScore']
        rows = [[]] + [[i, 10**9] for i in range(1, 500)] + [[1, 499]]
        self.assertEqual(o.reference(3709, [operations, rows])[-1], 499*10**9)

    def test_auction_replacement_ties_decrease_removal_and_readdition(self):
        args = [['AuctionSystem', 'addBid', 'addBid', 'getHighestBidder', 'addBid', 'getHighestBidder', 'updateBid', 'getHighestBidder', 'removeBid', 'removeBid', 'getHighestBidder', 'addBid', 'getHighestBidder'],
                [[], [1, 1, 7], [50000, 1, 7], [1], [50000, 1, 1], [1], [1, 1, 1], [1], [1, 1], [50000, 1], [1], [1, 1, 7], [1]]]
        self.assertEqual(o.reference(3815, args), [None, None, None, 50000, None, 1, None, 50000, None, None, -1, None, 1])

    def test_item_namespaces_are_independent(self):
        args = [['AuctionSystem', 'addBid', 'addBid', 'removeBid', 'getHighestBidder', 'getHighestBidder'],
                [[], [1, 1, 10**9], [1, 2, 1], [1, 1], [1], [2]]]
        self.assertEqual(o.reference(3815, args), [None, None, None, None, -1, 1])

    def test_cancellation_and_one_sided_wait_do_not_consume_the_other_queue(self):
        args = [['RideSharingSystem', 'addDriver', 'matchDriverWithRider', 'addRider', 'cancelRider', 'matchDriverWithRider', 'addRider', 'matchDriverWithRider', 'cancelRider', 'matchDriverWithRider'],
                [[], [1000], [], [1000], [1000], [], [1], [], [1000], []]]
        self.assertEqual(o.reference(3829, args), [None, None, [-1, -1], None, None, [-1, -1], None, [1000, 1], None, [-1, -1]])

    def test_invalid_trace_shape_and_unknown_methods(self):
        for pid in o.IDS:
            for args in (None, [], [[], []], [[o.CLASSES[pid]], [()]], [[o.CLASSES[pid]], [[], []]],
                         [[o.CLASSES[pid], '__getattribute__'], [[], []]], [[o.CLASSES[pid], o.CLASSES[pid]], [[], []]]):
                with self.subTest(pid=pid, args=args), self.assertRaises(ValueError): o.validate(pid, args)
        for pid in (True, 3709.0, '3709', 3816):
            with self.assertRaises(ValueError): o.validate(pid, [['ExamTracker'], [[]]])

    def test_exam_chronology_and_exact_types(self):
        invalid = [
            [['ExamTracker', 'totalScore'], [[], [1, 1]]],
            [['ExamTracker', 'record'], [[], [True, 1]]],
            [['ExamTracker', 'record'], [[], [1, 1.0]]],
            [['ExamTracker', 'record', 'record'], [[], [2, 1], [2, 1]]],
            [['ExamTracker', 'record', 'totalScore'], [[], [2, 1], [1, 3]]],
            [['ExamTracker', 'record', 'totalScore'], [[], [2, 1], [2, 1]]],
        ]
        for args in invalid:
            with self.assertRaises(ValueError): o.validate(3709, args)

    def test_auction_missing_update_remove_and_bounds(self):
        for operation, row in [('updateBid', [1, 1, 1]), ('removeBid', [1, 1]),
                               ('addBid', [0, 1, 1]), ('addBid', [1, 1, 10**9+1]),
                               ('getHighestBidder', [True]), ('getHighestBidder', [50001])]:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                o.validate(3815, [['AuctionSystem', operation], [[], row]])

    def test_rider_and_driver_uniqueness_are_separate(self):
        o.validate(3829, [['RideSharingSystem', 'addRider', 'addDriver'], [[], [1], [1]]])
        for method in ('addRider', 'addDriver'):
            with self.assertRaises(ValueError): o.validate(3829, [['RideSharingSystem', method, method], [[], [1], [1]]])
        for row in ([True], [0], [1001]):
            with self.assertRaises(ValueError): o.validate(3829, [['RideSharingSystem', 'cancelRider'], [[], row]])

    def test_full_domain_and_reference_budget_are_distinct(self):
        args = [['ExamTracker'] + ['record']*99999 + ['totalScore'],
                [[]] + [[i, 10**9] for i in range(1, 100000)] + [[1, 99999]]]
        o.validate(3709, args)
        with self.assertRaises(ValueError): o.reference(3709, args)
        args[0].append('totalScore'); args[1].append([1, 99999])
        with self.assertRaises(ValueError): o.validate(3709, args)

    def test_generated_traces_remain_lawful_repeatable_and_input_preserving(self):
        for pid in o.IDS:
            first, second = o.generate_cases(pid), o.generate_cases(pid)
            self.assertEqual(first, second); self.assertEqual(len(first), 48)
            for case in first:
                before = repr(case['args'])
                self.assertEqual(o.reference(pid, case['args']), case['expected'])
                self.assertEqual(repr(case['args']), before)

    def test_wrong_value_type_effect_alias_and_error_are_rejected(self):
        args = [['AuctionSystem', 'getHighestBidder'], [[], [1]]]
        expected = [None, -1]
        good = dict(result=expected, args_before=args, args_after=args, alias_edges=[])
        self.assertIsNone(o.check_observation(3815, args, good, expected))
        for change, reason in [({'result': [None, -1.0]}, 'result_value'),
                               ({'args_after': [[], []]}, 'input_effects'),
                               ({'alias_edges': [['result', 'args.0']]}, 'return_aliases'),
                               ({'error': 'failure'}, 'candidate_error')]:
            self.assertEqual(o.check_observation(3815, args, {**good, **change}, expected), reason)


if __name__ == '__main__': unittest.main()
