"""Host-only trace construction. Generated packets and expected outputs stay private."""
from copy import deepcopy
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('native_trace_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)

EXAMPLES = {
    3709: [
        ([['ExamTracker', 'record', 'totalScore', 'record', 'totalScore', 'totalScore', 'totalScore', 'totalScore'],
          [[], [1, 98], [1, 1], [5, 99], [1, 3], [1, 5], [3, 4], [2, 5]]],
         [None, None, 98, None, 98, 197, 0, 99]),
    ],
    3815: [
        ([['AuctionSystem', 'addBid', 'addBid', 'getHighestBidder', 'updateBid', 'getHighestBidder', 'removeBid', 'getHighestBidder', 'getHighestBidder'],
          [[], [1, 7, 5], [2, 7, 6], [7], [1, 7, 8], [7], [2, 7], [7], [3]]],
         [None, None, None, 2, None, 1, None, 1, -1]),
    ],
    3829: [
        ([['RideSharingSystem', 'addRider', 'addDriver', 'addRider', 'matchDriverWithRider', 'addDriver', 'cancelRider', 'matchDriverWithRider', 'matchDriverWithRider'],
          [[], [3], [2], [1], [], [5], [3], [], []]],
         [None, None, None, None, [2, 3], None, None, [5, 1], [-1, -1]]),
        ([['RideSharingSystem', 'addRider', 'addDriver', 'addDriver', 'matchDriverWithRider', 'addRider', 'cancelRider', 'matchDriverWithRider'],
          [[], [8], [8], [6], [], [2], [2], []]],
         [None, None, None, None, [8, 8], None, None, [-1, -1]]),
    ],
}

TARGETED = {
    3709: [
        [['ExamTracker'], [[]]],
        [['ExamTracker', 'record', 'record', 'totalScore', 'totalScore', 'totalScore'],
         [[], [1, 10**9], [10**9, 10**9], [1, 10**9], [2, 10**9-1], [10**9, 10**9]]],
        [['ExamTracker'] + ['record']*499 + ['totalScore'],
         [[]] + [[i, 10**9] for i in range(1, 500)] + [[1, 499]]],
    ],
    3815: [
        [['AuctionSystem'], [[]]],
        [['AuctionSystem', 'addBid', 'addBid', 'getHighestBidder', 'addBid', 'getHighestBidder', 'updateBid', 'getHighestBidder', 'removeBid', 'removeBid', 'getHighestBidder', 'addBid', 'getHighestBidder'],
         [[], [1, 1, 7], [50000, 1, 7], [1], [50000, 1, 1], [1], [1, 1, 1], [1], [1, 1], [50000, 1], [1], [1, 1, 7], [1]]],
        [['AuctionSystem', 'addBid', 'addBid', 'removeBid', 'getHighestBidder', 'getHighestBidder'],
         [[], [1, 1, 10**9], [1, 2, 1], [1, 1], [1], [2]]],
        [['AuctionSystem'] + ['addBid']*100 + ['getHighestBidder', 'removeBid', 'getHighestBidder'],
         [[]] + [[50000, 50000, 10**9-i] for i in range(100)] + [[50000], [50000, 50000], [50000]]],
    ],
    3829: [
        [['RideSharingSystem'], [[]]],
        [['RideSharingSystem', 'addDriver', 'matchDriverWithRider', 'addRider', 'cancelRider', 'matchDriverWithRider', 'addRider', 'matchDriverWithRider', 'cancelRider', 'matchDriverWithRider'],
         [[], [1000], [], [1000], [1000], [], [1], [], [1000], []]],
        [['RideSharingSystem'] + ['addRider']*100 + ['cancelRider']*100 + ['addDriver', 'matchDriverWithRider', 'addRider', 'matchDriverWithRider'],
         [[]] + [[i] for i in range(1, 101)] + [[i] for i in range(1, 101)] + [[1000], [], [1000], []]],
    ],
}


def maximum_case(pid):
    """Analytic operation-count witnesses; no claim an existing runner admits them.

    The caller must freeze packet/output byte sizes and preserve unchanged
    runtime limits before dispatch. An oversized witness is a retained transport
    gap, never permission to shrink the official input domain or raise caps.
    """
    if pid == 3709:
        args = [['ExamTracker'] + ['record'] * 99999 + ['totalScore'],
                [[]] + [[i, 10**9] for i in range(1, 100000)] + [[1, 99999]]]
        expected = [None] * 100000 + [99999 * 10**9]
    elif pid == 3815:
        args = [['AuctionSystem'] + ['addBid'] * 49999 + ['getHighestBidder'],
                [[]] + [[i, 50000, 10**9] for i in range(1, 50000)] + [[50000]]]
        expected = [None] * 50000 + [49999]
    elif pid == 3829:
        names = ['RideSharingSystem'] + ['addRider'] * 250 + ['addDriver'] * 250 + ['matchDriverWithRider'] * 500
        rows = [[]] + [[i] for i in range(751, 1001)] + [[i] for i in range(751, 1001)] + [[] for _ in range(500)]
        args = [names, rows]
        expected = [None] * 501 + [[i, i] for i in range(751, 1001)] + [[-1, -1] for _ in range(250)]
    else:
        raise ValueError('unsupported exact native identity')
    oracle.validate(pid, args)
    return {'args': args, 'expected': expected, 'compare': 'return', 'category': 'analytic-maximum-method-count'}


def build_cases(pid, *, include_maximum=False):
    if type(pid) is not int or pid not in oracle.IDS:
        raise ValueError('exact native identity required')
    cases = []
    for args, expected in EXAMPLES[pid]:
        if not oracle.exact(oracle.reference(pid, args), expected):
            raise ValueError('independent model disagrees with official example')
        cases.append({'args': deepcopy(args), 'expected': deepcopy(expected), 'compare': 'return', 'category': 'official-public-example'})
    for args in TARGETED[pid]:
        cases.append({'args': deepcopy(args), 'expected': oracle.reference(pid, args), 'compare': 'return', 'category': 'targeted-state-boundary'})
    cases.extend({**case, 'category': 'seeded-small-state-transitions'} for case in oracle.generate_cases(pid))
    if include_maximum: cases.append(maximum_case(pid))
    return cases
