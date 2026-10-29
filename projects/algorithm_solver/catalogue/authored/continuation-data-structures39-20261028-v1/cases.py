"""Private case generation from file-local independent references."""
import importlib.util
from pathlib import Path
import random

_spec = importlib.util.spec_from_file_location('gamma_ds39_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_o)
reference, validate_domain, IDS = _o.reference, _o.validate_domain, _o.IDS


def build_cases(pid, include_maximum=False):
    rng = random.Random(2026102800 + pid)
    args = []

    if pid == 295:
        args = [
            [['MedianFinder', 'addNum', 'addNum', 'findMedian', 'addNum', 'findMedian'], [[], [1], [2], [], [3], []]],
            [['MedianFinder', 'addNum', 'findMedian', 'addNum', 'findMedian'], [[], [-5], [], [-10], []]],
        ]
        for _ in range(12):
            ops = ['MedianFinder', 'addNum']
            rows = [[], [rng.randint(-100, 100)]]
            for _ in range(15):
                if rng.random() < 0.6:
                    ops.append('addNum')
                    rows.append([rng.randint(-1000, 1000)])
                else:
                    ops.append('findMedian')
                    rows.append([])
            args.append([ops, rows])

    elif pid == 297:
        args = [
            [[]],
            [[1]],
            [[1, 2, 3, None, None, 4, 5]],
            [[-1000, 0, 1000, -500, None, None, 500]],
        ]
        for n in range(2, 12):
            args.append([[rng.randint(-100, 100) for _ in range(n)]])

    elif pid == 303:
        args = [
            [['NumArray', 'sumRange', 'sumRange', 'sumRange'], [[[-2, 0, 3, -5, 2, -1]], [0, 2], [2, 5], [0, 5]]],
            [['NumArray', 'sumRange'], [[[42]], [0, 0]]],
        ]
        for _ in range(12):
            n = rng.randint(1, 20)
            nums = [rng.randint(-100, 100) for _ in range(n)]
            ops = ['NumArray']
            rows = [[nums]]
            for _ in range(10):
                l = rng.randint(0, n - 1)
                r = rng.randint(l, n - 1)
                ops.append('sumRange')
                rows.append([l, r])
            args.append([ops, rows])

    elif pid == 304:
        args = [
            [
                ['NumMatrix', 'sumRegion', 'sumRegion', 'sumRegion'],
                [[[[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]]], [2, 1, 4, 3], [1, 1, 2, 2], [1, 2, 2, 4]],
            ],
            [['NumMatrix', 'sumRegion'], [[[[ -7 ]]], [0, 0, 0, 0]]],
        ]
        for _ in range(10):
            m, n = rng.randint(1, 8), rng.randint(1, 8)
            mat = [[rng.randint(-50, 50) for _ in range(n)] for _ in range(m)]
            ops = ['NumMatrix']
            rows = [[mat]]
            for _ in range(8):
                r1 = rng.randint(0, m - 1)
                r2 = rng.randint(r1, m - 1)
                c1 = rng.randint(0, n - 1)
                c2 = rng.randint(c1, n - 1)
                ops.append('sumRegion')
                rows.append([r1, c1, r2, c2])
            args.append([ops, rows])

    elif pid == 307:
        args = [
            [['NumArray', 'sumRange', 'update', 'sumRange'], [[[1, 3, 5]], [0, 2], [1, 2], [0, 2]]],
            [['NumArray', 'update', 'sumRange'], [[[10]], [0, -10], [0, 0]]],
        ]
        for _ in range(12):
            n = rng.randint(1, 15)
            nums = [rng.randint(-100, 100) for _ in range(n)]
            ops = ['NumArray']
            rows = [[nums]]
            for _ in range(12):
                if rng.random() < 0.5:
                    ops.append('update')
                    rows.append([rng.randint(0, n - 1), rng.randint(-100, 100)])
                else:
                    l = rng.randint(0, n - 1)
                    r = rng.randint(l, n - 1)
                    ops.append('sumRange')
                    rows.append([l, r])
            args.append([ops, rows])

    elif pid == 321:
        args = [
            [[3, 4, 6, 5], [9, 1, 2, 5, 8, 3], 5],
            [[6, 7], [6, 0, 4], 5],
            [[3, 9], [8, 9], 3],
            [[9], [1], 1],
        ]
        for _ in range(12):
            m, n = rng.randint(1, 6), rng.randint(1, 6)
            a = [rng.randint(0, 9) for _ in range(m)]
            b = [rng.randint(0, 9) for _ in range(n)]
            k = rng.randint(1, m + n)
            args.append([a, b, k])

    elif pid == 328:
        args = [
            [[]],
            [[1]],
            [[1, 2, 3, 4, 5]],
            [[2, 1, 3, 5, 6, 4, 7]],
        ]
        for n in range(2, 15):
            args.append([[rng.randint(-100, 100) for _ in range(n)]])

    elif pid == 341:
        samples = [
            [[1, 1], 2, [1, 1]],
            [1, [4, [6]]],
            [[], [1], [], [[2, 3], []]],
            [[]],
        ]
        for nl in samples:
            flat = []
            def collect(items):
                for x in items:
                    if type(x) is int:
                        flat.append(x)
                    else:
                        collect(x)
            collect(nl)
            ops = ['NestedIterator']
            rows = [[nl]]
            for _ in flat:
                ops.extend(['hasNext', 'next'])
                rows.extend([[], []])
            ops.append('hasNext')
            rows.append([])
            args.append([ops, rows])

    elif pid == 352:
        args = [
            [
                ['SummaryRanges', 'addNum', 'getIntervals', 'addNum', 'getIntervals', 'addNum', 'getIntervals', 'addNum', 'getIntervals', 'addNum', 'getIntervals'],
                [[], [1], [], [3], [], [7], [], [2], [], [6], []],
            ],
        ]
        for _ in range(12):
            ops = ['SummaryRanges']
            rows = [[]]
            for _ in range(15):
                if rng.random() < 0.7:
                    ops.append('addNum')
                    rows.append([rng.randint(0, 25)])
                else:
                    ops.append('getIntervals')
                    rows.append([])
            ops.append('getIntervals')
            rows.append([])
            args.append([ops, rows])

    elif pid == 355:
        args = [
            [
                ['Twitter', 'postTweet', 'getNewsFeed', 'follow', 'postTweet', 'getNewsFeed', 'unfollow', 'getNewsFeed'],
                [[], [1, 5], [1], [1, 2], [2, 6], [1], [1, 2], [1]],
            ],
        ]
        for trial in range(10):
            ops = ['Twitter']
            rows = [[]]
            tid = 1 + trial * 50
            for _ in range(20):
                r = rng.random()
                u = rng.randint(1, 5)
                if r < 0.45:
                    ops.append('postTweet')
                    rows.append([u, tid])
                    tid += 1
                elif r < 0.7:
                    ops.append('getNewsFeed')
                    rows.append([u])
                elif r < 0.85:
                    v = rng.randint(1, 5)
                    if v != u:
                        ops.append('follow')
                        rows.append([u, v])
                else:
                    v = rng.randint(1, 5)
                    if v != u:
                        ops.append('unfollow')
                        rows.append([u, v])
            args.append([ops, rows])

    elif pid == 374:
        args = [
            [10, 6],
            [1, 1],
            [2, 1],
            [2, 2],
            [100, 1],
            [100, 100],
            [1000, 731],
        ]
        for _ in range(12):
            n = rng.randint(1, 10**6)
            args.append([n, rng.randint(1, n)])

    elif pid == 380:
        args = [
            [
                ['RandomizedSet', 'insert', 'remove', 'insert', 'getRandom', 'remove', 'insert', 'getRandom'],
                [[], [1], [2], [2], [], [1], [2], []],
            ],
            [
                ['RandomizedSet', 'insert', 'getRandom', 'remove', 'insert', 'getRandom'],
                [[], [42], [], [42], [99], []],
            ],
        ]
        for _ in range(10):
            ops = ['RandomizedSet']
            rows = [[]]
            present = set()
            for _ in range(15):
                if not present or rng.random() < 0.5:
                    v = rng.randint(-5, 5)
                    ops.append('insert')
                    rows.append([v])
                    present.add(v)
                elif rng.random() < 0.5:
                    v = rng.randint(-5, 5)
                    ops.append('remove')
                    rows.append([v])
                    present.discard(v)
                else:
                    ops.append('getRandom')
                    rows.append([])
            args.append([ops, rows])

    elif pid == 381:
        args = [
            [
                ['RandomizedCollection', 'insert', 'insert', 'insert', 'getRandom', 'remove', 'getRandom'],
                [[], [1], [1], [2], [], [1], []],
            ],
            [
                ['RandomizedCollection', 'insert', 'insert', 'remove', 'getRandom'],
                [[], [7], [7], [7], []],
            ],
        ]
        for _ in range(10):
            ops = ['RandomizedCollection']
            rows = [[]]
            total = 0
            counts = {}
            for _ in range(15):
                if total == 0 or rng.random() < 0.5:
                    v = rng.randint(1, 4)
                    ops.append('insert')
                    rows.append([v])
                    counts[v] = counts.get(v, 0) + 1
                    total += 1
                elif rng.random() < 0.5:
                    v = rng.randint(1, 4)
                    ops.append('remove')
                    rows.append([v])
                    if counts.get(v, 0) > 0:
                        counts[v] -= 1
                        total -= 1
                else:
                    ops.append('getRandom')
                    rows.append([])
            args.append([ops, rows])

    elif pid == 382:
        args = [
            [['Solution', 'getRandom', 'getRandom', 'getRandom'], [[[10]], [], [], []]],
            [['Solution', 'getRandom', 'getRandom', 'getRandom', 'getRandom'], [[[1, 2, 3]], [], [], [], []]],
        ]
        for n in range(1, 10):
            vals = [rng.randint(-50, 50) for _ in range(n)]
            args.append([['Solution'] + ['getRandom'] * 5, [[vals]] + [[]] * 5])

    elif pid == 384:
        args = [
            [['Solution', 'shuffle', 'reset', 'shuffle'], [[[1, 2, 3]], [], [], []]],
            [['Solution', 'shuffle', 'reset'], [[[42]], [], []]],
        ]
        for n in range(2, 10):
            vals = list(range(1, n + 1))
            args.append([['Solution', 'shuffle', 'reset', 'shuffle'], [[vals], [], [], []]])

    elif pid == 385:
        args = [
            ['324'],
            ['-1000000'],
            ['[123,[456,[789]]]'],
            ['[]'],
            ['[[],[1,[-2,3]],[]]'],
            ['[0,[-1,[2,[-3,4]]]]'],
        ]

    elif pid == 398:
        args = [
            [['Solution', 'pick', 'pick', 'pick'], [[[1, 2, 3, 3, 3]], [3], [1], [3]]],
            [['Solution', 'pick'], [[[99]], [99]]],
        ]
        for _ in range(10):
            vals = [rng.randint(1, 5) for _ in range(12)]
            ops = ['Solution']
            rows = [[vals]]
            for _ in range(6):
                ops.append('pick')
                rows.append([rng.choice(vals)])
            args.append([ops, rows])

    elif pid == 420:
        args = [
            ['a'],
            ['aA1'],
            ['1337C0d3'],
            ['aaa111'],
            ['aaaaaaaaaaaaaaaaaaaaa'],
            ['ABABABABABABABABABAB1'],
            ['bbaaaaaaaaaaaaaaacccccc'],
            ['..................!!!'],
            ['1111111111'],
            ['aaaaabbbb1234567890123456'],
        ]

    elif pid == 427:
        args = [
            [[[0]]],
            [[[1]]],
            [[[0, 1], [1, 0]]],
            [[[1, 1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0]]],
        ]
        for size in (2, 4, 8):
            for _ in range(4):
                args.append([[[rng.randint(0, 1) for _ in range(size)] for _ in range(size)]])

    elif pid == 429:
        args = [
            [[]],
            [[1]],
            [[1, None, 3, 2, 4, None, 5, 6]],
            [[1, None, 2, 3, 4, 5, None, None, 6, 7, None, 8, None, 9, 10, None, None, 11, None, 12, None, 13, None, None, 14]],
        ]

    elif pid == 430:
        args = [
            [[]],
            [[1, 2, 3]],
            [[1, 2, None, 3]],
            [[1, 2, 3, 4, 5, 6, None, None, None, 7, 8, 9, 10, None, None, 11, 12]],
        ]

    elif pid == 432:
        args = [
            [
                ['AllOne', 'inc', 'inc', 'getMaxKey', 'getMinKey', 'inc', 'getMaxKey', 'getMinKey'],
                [[], ['hello'], ['hello'], [], [], ['leet'], [], []],
            ],
            [
                ['AllOne', 'inc', 'inc', 'inc', 'dec', 'getMaxKey', 'getMinKey', 'dec', 'dec', 'getMaxKey', 'getMinKey'],
                [[], ['a'], ['b'], ['b'], ['a'], [], [], ['b'], ['b'], [], []],
            ],
        ]
        for _ in range(10):
            ops = ['AllOne']
            rows = [[]]
            counts = {}
            for _ in range(16):
                if not counts or rng.random() < 0.5:
                    k = rng.choice(['alpha', 'beta', 'gamma', 'delta'])
                    ops.append('inc')
                    rows.append([k])
                    counts[k] = counts.get(k, 0) + 1
                elif rng.random() < 0.4:
                    k = rng.choice(list(counts.keys()))
                    ops.append('dec')
                    rows.append([k])
                    counts[k] -= 1
                    if counts[k] == 0:
                        del counts[k]
                else:
                    ops.append(rng.choice(['getMaxKey', 'getMinKey']))
                    rows.append([])
            args.append([ops, rows])

    elif pid == 449:
        args = [
            [[]],
            [[2, 1, 3]],
            [[5, 3, 8, 1, 4, 7, 10]],
            [[10, 5, 15, 2, 7, None, 20]],
        ]

    elif pid == 460:
        args = [
            [
                ['LFUCache', 'put', 'put', 'get', 'put', 'get', 'get', 'put', 'get', 'get', 'get'],
                [[2], [1, 1], [2, 2], [1], [3, 3], [2], [3], [4, 4], [1], [3], [4]],
            ],
            [
                ['LFUCache', 'put', 'get', 'put', 'get', 'get'],
                [[1], [1, 10], [1], [2, 20], [1], [2]],
            ],
        ]
        for _ in range(10):
            cap = rng.randint(1, 4)
            ops = ['LFUCache']
            rows = [[cap]]
            for _ in range(20):
                if rng.random() < 0.55:
                    ops.append('put')
                    rows.append([rng.randint(1, 6), rng.randint(1, 100)])
                else:
                    ops.append('get')
                    rows.append([rng.randint(1, 6)])
            args.append([ops, rows])

    elif pid == 466:
        args = [
            ['acb', 4, 'ab', 2],
            ['acb', 1, 'acb', 1],
            ['abc', 5, 'xyz', 1],
            ['abaacdbac', 100, 'adcbd', 4],
            ['aaa', 10, 'aa', 2],
        ]

    elif pid == 470:
        args = [
            [[1, 1]],
            [[7, 7, 7, 6, 1, 2]],
            [[6, 5, 2, 3]],
        ]
        for a in range(1, 8):
            for b in range(1, 8):
                if (a - 1) * 7 + b <= 40:
                    args.append([[a, b]])

    elif pid == 478:
        args = [
            [['Solution', 'randPoint', 'randPoint', 'randPoint'], [[1.0, 0.0, 0.0], [], [], []]],
            [['Solution', 'randPoint', 'randPoint'], [[10.0, 5.0, -7.5], [], []]],
        ]
        for _ in range(8):
            r = float(rng.randint(1, 100))
            xc = float(rng.randint(-50, 50))
            yc = float(rng.randint(-50, 50))
            args.append([['Solution', 'randPoint', 'randPoint'], [[r, xc, yc], [], []]])

    elif pid == 479:
        args = [[n] for n in range(1, 6)]

    elif pid == 480:
        args = [
            [[1, 3, -1, -3, 5, 3, 6, 7], 3],
            [[1, 2, 3, 4, 2, 3, 1, 4, 2], 3],
            [[1, 4, 2, 3], 4],
            [[5], 1],
        ]
        for _ in range(10):
            n = rng.randint(2, 20)
            k = rng.randint(1, n)
            args.append([[rng.randint(-50, 50) for _ in range(n)], k])

    elif pid == 483:
        args = [
            ['3'],
            ['7'],
            ['13'],
            ['15'],
            ['4681'],
            ['100000'],
        ]
        for v in range(3, 40):
            args.append([str(v)])

    elif pid == 488:
        args = [
            ['WRRBBW', 'RB'],
            ['WWRRBBWW', 'WRBRW'],
            ['G', 'GGGGG'],
            ['RRWWRRBBRR', 'WB'],
            ['RBYYBBRRB', 'YRBGB'],
        ]

    elif pid == 497:
        args = [
            [['Solution', 'pick', 'pick', 'pick', 'pick', 'pick'], [[[[-2, -2, 1, 1], [2, 2, 4, 6]]], [], [], [], [], []]],
            [['Solution', 'pick', 'pick'], [[[[0, 0, 0, 0]]], [], []]],
        ]

    elif pid == 519:
        args = [
            [['Solution', 'flip', 'flip', 'flip', 'reset', 'flip'], [[3, 1], [], [], [], [], []]],
            [['Solution', 'flip', 'reset', 'flip'], [[1, 1], [], [], []]],
        ]
        for m, n in [(2, 2), (2, 3), (3, 2)]:
            args.append([['Solution'] + ['flip'] * (m * n) + ['reset', 'flip'], [[m, n]] + [[]] * (m * n + 2)])

    elif pid == 528:
        args = [
            [['Solution', 'pickIndex'], [[[1]], []]],
            [['Solution', 'pickIndex', 'pickIndex', 'pickIndex', 'pickIndex', 'pickIndex'], [[[1, 3]], [], [], [], [], []]],
        ]
        for _ in range(8):
            w = [rng.randint(1, 20) for _ in range(rng.randint(1, 8))]
            args.append([['Solution'] + ['pickIndex'] * 6, [[w]] + [[]] * 6])

    elif pid == 535:
        args = [
            ['https://leetcode.com/problems/design-tinyurl'],
            ['http://example.com/a/b/c?x=1&y=2'],
            ['https://gamma.local/single'],
        ]

    elif pid == 558:
        args = [
            [[[1, 0]], [[1, 1]]],
            [[[0, 1], [1, 1], [1, 1], [1, 0], [1, 0]], [[0, 1], [1, 1], [0, 1], [1, 1], [1, 0], None, None, None, None, [1, 0], [1, 0], [1, 0], [1, 1]]],
            [[[1, 1]], [[0, 1], [1, 0], [1, 1], [1, 0], [1, 1]]],
        ]

    elif pid == 559:
        args = [
            [[]],
            [[1]],
            [[1, None, 3, 2, 4, None, 5, 6]],
            [[1, None, 2, 3, 4, 5, None, None, 6, 7, None, 8, None, 9, 10, None, None, 11, None, 12, None, 13, None, None, 14]],
        ]

    elif pid == 572:
        args = [
            [[3, 4, 5, 1, 2], [4, 1, 2]],
            [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]],
            [[1, 1], [1]],
            [[1, 2, 3], [2]],
        ]

    elif pid == 587:
        args = [
            [[[1, 1], [2, 2], [2, 0], [2, 4], [3, 3], [4, 2]]],
            [[[1, 2], [2, 2], [4, 2]]],
            [[[0, 0]]],
            [[[0, 0], [0, 5], [5, 0], [5, 5], [2, 2]]],
        ]

    rows = [{'args': a, 'expected': reference(pid, a), 'category': 'independent-bounded-reference'} for a in args]

    if include_maximum:
        extra = []
        if pid == 295:
            extra = [([['MedianFinder', 'addNum', 'addNum', 'findMedian'], [[], [-10**5], [10**5], []]], [None, None, None, 0.0])]
        elif pid == 297:
            big = [1000] * 10000
            extra = [([big], big)]
        elif pid == 303:
            extra = [([['NumArray', 'sumRange'], [[[10**5] * 10000], [0, 9999]]], [None, 10**9])]
        elif pid == 304:
            mat = [[10**4] * 200 for _ in range(200)]
            extra = [([['NumMatrix', 'sumRegion'], [[mat], [0, 0, 199, 199]]], [None, 400000000])]
        elif pid == 307:
            extra = [([['NumArray', 'update', 'sumRange'], [[[100] * 30000], [29999, -100], [0, 29999]]], [None, None, 2999800])]
        elif pid == 321:
            extra = [([[9] * 500, [9] * 500, 1000], [9] * 1000)]
        elif pid == 328:
            seq = list(range(1, 10001))
            extra = [([seq], list(range(1, 10001, 2)) + list(range(2, 10001, 2)))]
        elif pid == 341:
            nl = [[10**6]] * 500
            extra = [([['NestedIterator', 'hasNext', 'next'], [[nl], [], []]], [None, True, 10**6])]
        elif pid == 352:
            extra = [([['SummaryRanges', 'addNum', 'addNum', 'getIntervals'], [[], [0], [10**4], []]], [None, None, None, [[0, 0], [10**4, 10**4]]])]
        elif pid == 355:
            extra = [([['Twitter', 'postTweet', 'getNewsFeed'], [[], [500, 10**4], [500]]], [None, None, [10**4]])]
        elif pid == 374:
            extra = [([2**31 - 1, 2**31 - 1], 2**31 - 1), ([2**31 - 1, 1], 1)]
        elif pid == 380:
            extra = [([['RandomizedSet', 'insert', 'getRandom'], [[], [2**31 - 1], []]], [None, True, 2**31 - 1])]
        elif pid == 381:
            extra = [([['RandomizedCollection', 'insert', 'getRandom'], [[], [-2**31], []]], [None, True, -2**31])]
        elif pid == 382:
            extra = [([['Solution', 'getRandom'], [[[10**4] * 10000], []]], [None, 10**4])]
        elif pid == 384:
            seq50 = list(range(1, 51))
            extra = [([['Solution', 'reset'], [[seq50], []]], [None, seq50])]
        elif pid == 385:
            extra = [(['[1000000,-1000000]'], [1000000, -1000000])]
        elif pid == 398:
            extra = [([['Solution', 'pick'], [[[2**31 - 1] * 20000], [2**31 - 1]]], [None, reference(398, [['Solution', 'pick'], [[[2**31 - 1] * 20000], [2**31 - 1]]])[1]])]
        elif pid == 420:
            extra = [(['a' * 50], 36)]
        elif pid == 427:
            g64 = [[1] * 64 for _ in range(64)]
            extra = [([g64], [[1, 1]])]
        elif pid == 429:
            nary = [10000, None] + [10000] * 9999
            extra = [([nary], [[10000], [10000] * 9999])]
        elif pid == 430:
            ml = [10**5] * 1000
            extra = [([ml], [10**5] * 1000)]
        elif pid == 432:
            extra = [([['AllOne', 'inc', 'getMaxKey', 'getMinKey'], [[], ['z' * 10], [], []]], [None, None, 'z' * 10, 'z' * 10])]
        elif pid == 449:
            extra = [([[10000]], [10000])]
        elif pid == 460:
            extra = [([['LFUCache', 'put', 'get'], [[10**4], [10**5, 10**9], [10**5]]], [None, None, 10**9])]
        elif pid == 466:
            extra = [(['a' * 100, 10**6, 'a' * 100, 10**6], 1)]
        elif pid == 470:
            stream = [7, 7] * 49999 + [1, 1]
            extra = [([stream], 1)]
        elif pid == 478:
            a = [['Solution', 'randPoint'], [[float(10**8), float(10**7), float(-10**7)], []]]
            extra = [(a, reference(478, a))]
        elif pid == 479:
            extra = [([8], 475)]
        elif pid == 480:
            extra = [([[2**31 - 1] * 100000, 100000], [float(2**31 - 1)])]
        elif pid == 483:
            extra = [(['1000000000000000000'], '999999999999999999')]
        elif pid == 488:
            extra = [(['R' * 16, 'R' * 5], 0)]
        elif pid == 497:
            extra = [([['Solution', 'pick'], [[[[10**9, 10**9, 10**9, 10**9]]], []]], [None, [10**9, 10**9]])]
        elif pid == 519:
            a = [['Solution', 'flip', 'reset'], [[10**4, 10**4], [], []]]
            extra = [(a, reference(519, a))]
        elif pid == 528:
            a = [['Solution', 'pickIndex'], [[[10**5] * 10000], []]]
            extra = [(a, reference(528, a))]
        elif pid == 535:
            u = 'https://leetcode.com/' + 'a' * 9979
            extra = [([u], u)]
        elif pid == 558:
            extra = [([[[1, 1]], [[1, 0]]], [[1, 1]])]
        elif pid == 559:
            nary = [10000, None] + [10000] * 9999
            extra = [([nary], 2)]
        elif pid == 572:
            extra = [([[10**4] * 2000, [10**4] * 1000], False)]
        elif pid == 587:
            box = [[0, 0], [0, 100], [100, 0], [100, 100]]
            extra = [([box], box)]

        for a, expected in extra:
            validate_domain(pid, a)
            rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})

    return rows
