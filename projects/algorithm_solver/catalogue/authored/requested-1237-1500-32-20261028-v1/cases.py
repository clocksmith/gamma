"""Private case generation from file-local independent references."""
import importlib.util
from pathlib import Path
import random

_spec = importlib.util.spec_from_file_location('gamma_1237_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)
reference, validate_domain, IDS = _o.reference, _o.validate_domain, _o.IDS


def build_cases(pid, include_maximum=False):
    rng = random.Random(2026102800 + pid)
    args = []

    if pid == 1237:
        for fid in range(1, 10):
            for z in (2, 5, 6, 10, 12, 25):
                args.append([fid, z])
    elif pid == 1244:
        args = [
            [
                ['Leaderboard', 'addScore', 'addScore', 'addScore', 'addScore', 'addScore', 'top', 'reset', 'reset', 'addScore', 'top'],
                [[], [1, 73], [2, 56], [3, 39], [4, 51], [5, 4], [1], [1], [2], [2, 51], [3]],
            ],
            [['Leaderboard', 'addScore', 'top', 'reset', 'addScore', 'top'], [[], [1, 10], [1], [1], [1, 20], [1]]],
        ]
    elif pid == 1245:
        args = [
            [[]],
            [[[0, 1], [0, 2]]],
            [[[0, 1], [1, 2], [2, 3], [1, 4], [4, 5]]],
            [[[0, 1], [1, 2], [2, 3], [3, 4]]],
        ]
    elif pid == 1246:
        args = [
            [[1, 2]],
            [[1, 3, 4, 1, 5]],
            [[1, 2, 1]],
            [[1, 4, 1, 1, 2, 3, 2, 1]],
        ]
        for _ in range(8):
            args.append([[rng.randint(1, 5) for _ in range(rng.randint(1, 10))]])
    elif pid == 1261:
        args = [
            [['FindElements', 'find', 'find'], [[[-1, None, -1]], [1], [2]]],
            [['FindElements', 'find', 'find', 'find'], [[[-1, -1, -1, -1, -1]], [1], [3], [5]]],
            [['FindElements', 'find', 'find', 'find', 'find'], [[[-1, None, -1, -1, None, -1]], [2], [3], [4], [5]]],
        ]
    elif pid == 1265:
        args = [
            [[1, 2, 3, 4]],
            [[-2, 0, 6, 4, 4, -6]],
            [[99]],
        ]
    elif pid == 1273:
        args = [
            [7, [-1, 0, 0, 1, 2, 2, 2], [1, -2, 4, 0, -2, -1, -1]],
            [7, [-1, 0, 0, 1, 2, 2, 2], [1, -2, 4, 0, -2, -1, -2]],
            [5, [-1, 0, 1, 0, 0], [-672, 441, 18, 728, 378]],
        ]
    elif pid == 1274:
        args = [
            [[[1, 1], [2, 2], [3, 3], [5, 5]], [4, 4], [0, 0]],
            [[[1, 1], [2, 2], [3, 3]], [1000, 1000], [0, 0]],
            [[], [500, 500], [0, 0]],
        ]
    elif pid == 1278:
        args = [
            ['abc', 2],
            ['aabbc', 3],
            ['leetcode', 8],
            ['ababab', 2],
        ]
    elif pid == 1286:
        args = [
            [['CombinationIterator', 'next', 'hasNext', 'next', 'hasNext', 'next', 'hasNext'], [['abc', 2], [], [], [], [], [], []]],
            [['CombinationIterator', 'hasNext', 'next', 'hasNext'], [['z', 1], [], [], []]],
        ]
    elif pid == 1302:
        args = [
            [[1, 2, 3, 4, 5, None, 6, 7, None, None, None, None, 8]],
            [[6, 7, 8, 2, 7, 1, 3, 9, None, 1, 4, None, None, None, 5]],
            [[42]],
        ]
    elif pid == 1315:
        args = [
            [[6, 7, 8, 2, 7, 1, 3, 9, None, 1, 4, None, None, None, 5]],
            [[1]],
            [[2, 1, 3, 4, 5, 6, 7]],
        ]
    elif pid == 1348:
        args = [
            [
                ['TweetCounts', 'recordTweet', 'recordTweet', 'recordTweet', 'getTweetCountsPerFrequency', 'getTweetCountsPerFrequency', 'recordTweet', 'getTweetCountsPerFrequency'],
                [[], ['tweet3', 0], ['tweet3', 60], ['tweet3', 10], ['minute', 'tweet3', 0, 59], ['minute', 'tweet3', 0, 60], ['tweet3', 120], ['hour', 'tweet3', 0, 210]],
            ],
        ]
    elif pid == 1352:
        args = [
            [
                ['ProductOfNumbers', 'add', 'add', 'add', 'add', 'add', 'getProduct', 'getProduct', 'getProduct', 'add', 'getProduct'],
                [[], [3], [0], [2], [5], [4], [2], [3], [4], [8], [2]],
            ],
        ]
    elif pid == 1357:
        args = [
            [
                ['Cashier', 'getBill', 'getBill', 'getBill', 'getBill', 'getBill', 'getBill', 'getBill'],
                [
                    [3, 50, [1, 2, 3, 4, 5, 6, 7], [100, 200, 300, 400, 300, 200, 100]],
                    [[1, 2], [1, 2]],
                    [[3, 7], [10, 10]],
                    [[1, 2, 3, 4, 5, 6, 7], [1, 1, 1, 1, 1, 1, 1]],
                    [[4], [10]],
                    [[7, 3], [10, 10]],
                    [[7, 5, 3, 1, 6, 4, 2], [10, 10, 10, 9, 9, 9, 7]],
                    [[2, 3, 5], [5, 3, 2]],
                ],
            ],
        ]
    elif pid == 1367:
        args = [
            [[4, 2, 8], [1, 4, 4, None, 2, 2, None, 1, None, 6, 8, None, None, None, None, 1, 3]],
            [[1, 4, 2, 6], [1, 4, 4, None, 2, 2, None, 1, None, 6, 8, None, None, None, None, 1, 3]],
            [[1, 4, 2, 6, 8], [1, 4, 4, None, 2, 2, None, 1, None, 6, 8, None, None, None, None, 1, 3]],
        ]
    elif pid == 1379:
        args = [
            [[7, 4, 3, None, None, 6, 19], 3],
            [[7], 7],
            [[8, None, 6, None, 5, None, 4, None, 3, None, 2, None, 1], 4],
        ]
    elif pid == 1381:
        args = [
            [
                ['CustomStack', 'push', 'push', 'pop', 'push', 'push', 'push', 'increment', 'increment', 'pop', 'pop', 'pop', 'pop'],
                [[3], [1], [2], [], [2], [3], [4], [5, 100], [2, 100], [], [], [], []],
            ],
        ]
    elif pid == 1396:
        args = [
            [
                ['UndergroundSystem', 'checkIn', 'checkIn', 'checkIn', 'checkOut', 'checkOut', 'checkOut', 'getAverageTime', 'getAverageTime', 'checkIn', 'getAverageTime', 'checkOut', 'getAverageTime'],
                [
                    [],
                    [45, 'Leyton', 3],
                    [32, 'Paradise', 8],
                    [27, 'Leyton', 10],
                    [45, 'Waterloo', 15],
                    [27, 'Waterloo', 20],
                    [32, 'Cambridge', 22],
                    ['Paradise', 'Cambridge'],
                    ['Leyton', 'Waterloo'],
                    [10, 'Leyton', 24],
                    ['Leyton', 'Waterloo'],
                    [10, 'Waterloo', 38],
                    ['Leyton', 'Waterloo'],
                ],
            ],
        ]
    elif pid == 1428:
        args = [
            [[[0, 0], [1, 1]]],
            [[[0, 0], [0, 1]]],
            [[[0, 0], [0, 0]]],
            [[[0, 0, 0, 1], [0, 0, 1, 1], [0, 1, 1, 1]]],
        ]
    elif pid == 1429:
        args = [
            [
                ['FirstUnique', 'showFirstUnique', 'add', 'showFirstUnique', 'add', 'showFirstUnique', 'add', 'showFirstUnique'],
                [[[2, 3, 5]], [], [5], [], [2], [], [3], []],
            ],
            [
                ['FirstUnique', 'showFirstUnique', 'add', 'add', 'add', 'add', 'add', 'showFirstUnique'],
                [[[7, 7, 7, 7, 7, 7]], [], [7], [3], [3], [7], [17], []],
            ],
        ]
    elif pid == 1430:
        args = [
            [[0, 1, 0, 0, 1, 0, None, None, 1, 0, 0], [0, 1, 0, 1]],
            [[0, 1, 0, 0, 1, 0, None, None, 1, 0, 0], [0, 0, 1]],
            [[0, 1, 0, 0, 1, 0, None, None, 1, 0, 0], [0, 1, 1]],
        ]
    elif pid == 1448:
        args = [
            [[3, 1, 4, 3, None, 1, 5]],
            [[3, 3, None, 4, 2]],
            [[1]],
        ]
    elif pid == 1457:
        args = [
            [[2, 3, 1, 3, 1, None, 1]],
            [[2, 1, 1, 1, 3, None, None, None, None, None, 1]],
            [[9]],
        ]
    elif pid == 1469:
        args = [
            [[1, 2, 3, None, 4]],
            [[7, 1, 4, 6, None, 5, 3, None, None, None, None, None, 2]],
            [[11, 99, 88, 77, None, None, 66, 55, None, None, 44, 33, None, None, 22]],
        ]
    elif pid == 1472:
        args = [
            [
                ['BrowserHistory', 'visit', 'visit', 'visit', 'back', 'back', 'forward', 'visit', 'forward', 'back', 'back'],
                [['leetcode.com'], ['google.com'], ['facebook.com'], ['youtube.com'], [1], [1], [1], ['linkedin.com'], [2], [2], [7]],
            ],
        ]
    elif pid == 1474:
        args = [
            [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 2, 3],
            [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 1, 3],
            [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 3, 1],
        ]
    elif pid == 1476:
        args = [
            [
                ['SubrectangleQueries', 'getValue', 'updateSubrectangle', 'getValue', 'getValue', 'updateSubrectangle', 'getValue', 'getValue'],
                [[[[1, 2, 1], [4, 3, 4], [3, 2, 1], [1, 1, 1]]], [0, 2], [0, 0, 3, 2, 5], [0, 2], [3, 1], [3, 0, 3, 2, 10], [3, 1], [0, 2]],
            ],
        ]
    elif pid == 1483:
        args = [
            [['TreeAncestor', 'getKthAncestor', 'getKthAncestor', 'getKthAncestor'], [[7, [-1, 0, 0, 1, 1, 2, 2]], [3, 1], [5, 2], [6, 3]]],
            [['TreeAncestor', 'getKthAncestor'], [[1, [-1]], [0, 1]]],
        ]
    elif pid == 1485:
        args = [
            [[[1, None], None, [4, 3], [7, 0]]],
            [[[1, 4], None, [1, 0], None, [1, 5], [1, 5]]],
            [[]],
        ]
    elif pid == 1490:
        args = [
            [[1, None, 3, 2, 4, None, 5, 6]],
            [[1, None, 2, 3, 4, 5, None, None, 6, 7, None, 8, None, 9, 10, None, None, 11, None, 12, None, 13, None, None, 14]],
            [[]],
        ]
    elif pid == 1500:
        args = [
            [
                ['FileSharing', 'join', 'join', 'join', 'request', 'request', 'leave', 'request', 'leave', 'join'],
                [[4], [[1, 2]], [[2, 3]], [[4]], [1, 3], [2, 2], [1], [2, 1], [2], [[]]],
            ],
        ]

    rows = [{'args': a, 'expected': reference(pid, a), 'category': 'independent-bounded-reference'} for a in args]

    if include_maximum:
        extra = []
        if pid == 1237:
            extra = [([1, 100], [[x, 100 - x] for x in range(1, 100)])]
        elif pid == 1244:
            extra = [([['Leaderboard', 'addScore', 'top'], [[], [10000, 100], [1]]], [None, None, 100])]
        elif pid == 1245:
            e = [[i, i + 1] for i in range(10000)]
            extra = [([e], 10000)]
        elif pid == 1246:
            extra = [([[1] * 100], 1)]
        elif pid == 1261:
            extra = [([['FindElements', 'find'], [[[-1] * 10000], [0]]], [None, True])]
        elif pid == 1265:
            seq = list(range(1, 1001))
            extra = [([seq], list(reversed(seq)))]
        elif pid == 1273:
            extra = [([10000, [-1] + [0] * 9999, [1] * 10000], 10000)]
        elif pid == 1274:
            extra = [([[[1000, 1000]], [1000, 1000], [0, 0]], 1)]
        elif pid == 1278:
            extra = [(['a' * 100, 100], 0)]
        elif pid == 1286:
            extra = [([['CombinationIterator', 'hasNext', 'next'], [['abcdefghijklmno', 15], [], []]], [None, True, 'abcdefghijklmno'])]
        elif pid == 1302:
            extra = [([[10000]], 10000)]
        elif pid == 1315:
            extra = [([[2, 2, 2, 100, 100, 100, 100]], 400)]
        elif pid == 1348:
            extra = [([['TweetCounts', 'recordTweet', 'getTweetCountsPerFrequency'], [[], ['max', 10**9], ['day', 'max', 10**9, 10**9]]], [None, None, [1]])]
        elif pid == 1352:
            extra = [([['ProductOfNumbers', 'add', 'getProduct'], [[], [100], [1]]], [None, None, 100])]
        elif pid == 1357:
            extra = [([['Cashier', 'getBill'], [[1, 100, [1], [1000]], [[1], [1000]]]], [None, 0.0])]
        elif pid == 1367:
            extra = [([[100], [100]], True)]
        elif pid == 1379:
            extra = [([[10**5], 10**5], 10**5)]
        elif pid == 1381:
            extra = [([['CustomStack', 'push', 'increment', 'pop'], [[1000], [1000], [1000, 100], []]], [None, None, None, 1100])]
        elif pid == 1396:
            extra = [([['UndergroundSystem', 'checkIn', 'checkOut', 'getAverageTime'], [[], [10**6, 'A', 1], [10**6, 'B', 10**6], ['A', 'B']]], [None, None, None, 999999.0])]
        elif pid == 1428:
            g = [[0] * 99 + [1] for _ in range(100)]
            extra = [([g], 99)]
        elif pid == 1429:
            extra = [([['FirstUnique', 'showFirstUnique'], [[[10**8] * 100000], []]], [None, -1])]
        elif pid == 1430:
            extra = [([[9], [9]], True)]
        elif pid == 1448:
            extra = [([[10**4] * 1000], 1000)]
        elif pid == 1457:
            extra = [([[9] * 1023], 512)]
        elif pid == 1469:
            extra = [([[10000, 9999]], [9999])]
        elif pid == 1472:
            extra = [([['BrowserHistory', 'visit', 'back'], [['a' * 20], ['b' * 20], [100]]], [None, None, 'a' * 20])]
        elif pid == 1474:
            extra = [([[1] * 10000, 1000, 1000], [1] * 5000)]
        elif pid == 1476:
            mat = [[1] * 100 for _ in range(100)]
            extra = [([['SubrectangleQueries', 'updateSubrectangle', 'getValue'], [[mat], [0, 0, 99, 99, 10**9], [99, 99]]], [None, None, 10**9])]
        elif pid == 1483:
            p = [-1] + list(range(49999))
            extra = [([['TreeAncestor', 'getKthAncestor'], [[50000, p], [49999, 49999]]], [None, 0])]
        elif pid == 1485:
            extra = [([[[10**6, 0]]], [[10**6, 0]])]
        elif pid == 1490:
            nary = [10000, None] + [10000] * 9999
            extra = [([nary], nary)]
        elif pid == 1500:
            extra = [([['FileSharing', 'join', 'request'], [[100], [list(range(1, 101))], [1, 100]]], [None, 1, [1]])]

        for a, expected in extra:
            validate_domain(pid, a)
            rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})

    return rows
