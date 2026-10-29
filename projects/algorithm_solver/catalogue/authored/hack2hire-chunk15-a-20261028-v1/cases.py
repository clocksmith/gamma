"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
import math
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h15a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _blp(rng):
    L = rng.randrange(1, 4); alphabet = rng.choice(['ab', 'abc', 'a'])
    return [[''.join(rng.choice(alphabet) for _ in range(L)) for _ in range(rng.randrange(1, 7))]]


def _bfo(rng):
    fruits = ['apple', 'pear', 'kiwi'][:rng.randrange(1, 4)]
    orders = [[rng.choice(fruits), str(rng.randrange(1, 30)), str(rng.choice([0, 1, 2, 3]) * rng.choice([300000, 600000, 600001]) + rng.randrange(0, 3))]
              for _ in range(rng.randrange(0, 12))]
    prices = [[f, rng.randrange(1, 50)] for f in fruits]
    tiers, lo = [], 1
    for _ in range(rng.randrange(0, 4)):
        lo += rng.randrange(1, 25); tiers.append([lo, rng.randrange(0, 101)])
    return [orders, prices, tiers]


def _ccp(rng):
    m = rng.randrange(2, 12)
    names = ['L%d' % i for i in range(m)]
    roads = []
    for i in range(m):
        to = rng.choice(names[i + 1:] + [_o.CAMP]) if rng.random() < 0.8 else _o.CAMP
        roads.append([names[i], to, rng.randrange(1, 4)])
    s1, s2 = rng.sample(names, 2)
    nxt = {a: b for a, b, _ in roads}
    on = []
    for s in (s1, s2):
        cur = s
        while cur != _o.CAMP:
            if cur not in on: on.append(cur)
            cur = nxt[cur]
    friends = [['F%d' % i, rng.choice(on)] for i in range(rng.randrange(0, 8))]
    rng.shuffle(roads)
    return [roads, friends, s1, s2]


def _cfs(rng, uid):
    leases = []
    for _ in range(rng.randrange(0, 15)):
        s = rng.randrange(0, 20); leases.append([s, s + rng.randrange(1, 8)])
    return [leases] if uid == _o.CFS1 else [leases, rng.randrange(1, 4)]


def _cpp(rng):
    p = list(range(1, rng.randrange(1, 13) + 1)); rng.shuffle(p)
    if rng.random() < 0.3: p.sort(key=lambda v: abs(v - 0.5 - len(p) / 2))
    return [p]


def _cpd(rng):
    r = rng.choice([3, 20, 10**7])
    pts = set()
    while len(pts) < rng.randrange(2, 40): pts.add((rng.randrange(-r, r + 1), rng.randrange(-r, r + 1)))
    return [[list(p) for p in sorted(pts, key=lambda q: rng.random())]]


def _tree_list(rng, size):
    """Random binary tree of about size nodes as a canonical level-order list."""
    if size == 0: return []
    nodes = [[rng.randrange(-20, 21), None, None]]
    while len(nodes) < size:
        parent = rng.choice(nodes); side = rng.randrange(1, 3)
        if parent[side] is None:
            parent[side] = [rng.randrange(-20, 21), None, None]; nodes.append(parent[side])
    out, queue, head = [nodes[0][0]], [nodes[0]], 0
    while head < len(queue):
        n = queue[head]; head += 1
        for child in (n[1], n[2]):
            out.append(None if child is None else child[0])
            if child is not None: queue.append(child)
    while out[-1] is None: out.pop()
    return out


def _cns(rng):
    return [[_tree_list(rng, rng.randrange(0, 9)) for _ in range(rng.randrange(1, 5))]]


def _cds(rng):
    return [[rng.randrange(1, 9) for _ in range(rng.randrange(1, 6))], rng.randrange(1, 60)]


def _cic(rng):
    intervals = []
    for _ in range(rng.randrange(0, 12)):
        lo = rng.randrange(-10, 10); intervals.append([lo, lo + rng.randrange(0, 8)])
    return _ops('IntervalCounter', [intervals], [('count', rng.randrange(-12, 20)) for _ in range(rng.randrange(0, 12))])


def _cvb(rng):
    pattern = ''.join(rng.choice('01??') for _ in range(rng.randrange(1, 15)))
    if pattern.count('?') > 12: pattern = pattern.replace('?', '0', 1)
    arr = [rng.randrange(1, 4) for _ in range(rng.randrange(0, 4))]
    return [arr, pattern]


def _com(rng):
    p = lambda: rng.randrange(1, 12)
    return [[p() for _ in range(rng.randrange(0, 6))], [p() for _ in range(rng.randrange(0, 6))],
            [[rng.choice(['buy', 'sell']), p()] for _ in range(rng.randrange(0, 15))]]


def _dws(rng, uid):
    t, pts = rng.randrange(0, 3), []
    for _ in range(rng.randrange(0, 20)):
        t += rng.randrange(1, 4)
        pts.append({'tags': rng.sample(['web', 'db', 'prod'], rng.randrange(0, 4)), 'timestamp': t, 'value': rng.randrange(-9, 10)})
    return [pts, rng.choice(['web', 'db', 'prod', 'x']), rng.randrange(1, 8)]


def _dkb(rng):
    n = rng.randrange(1, 12)
    nums = [rng.randrange(-3, 4) for _ in range(n)]
    return [nums, rng.randrange(1, n + 1)]


def _dvc(rng, uid):
    keys = set()
    while len(keys) < rng.randrange(0, 12): keys.add((rng.randrange(0, 12), rng.randrange(0, 3), rng.randrange(0, 3)))
    keys = sorted(keys); cut = rng.randrange(0, len(keys) + 1)
    rows = [('%d.%d.%d' % k, i >= cut) for i, k in enumerate(keys)]
    if uid == _o.DVC2: rng.shuffle(rows)
    return [[r[0] for r in rows], [r[1] for r in rows]]


def _das(rng):
    calls, articles = [], 0
    for _ in range(rng.randrange(0, 50)):
        r = rng.random()
        if articles == 0 or r < 0.15: calls.append(('addArticle', rng.choice(['news', 'tech', 'art', 'sport']))); articles += 1
        elif r < 0.75: calls.append((rng.choice(['upvoteArticle', 'downvoteArticle']), rng.randrange(1, articles + 1), rng.randrange(1, 4)))
        elif r < 0.88: calls.append(('getRecentFlips', rng.randrange(1, 4), rng.randrange(1, 4)))
        else: calls.append(('getTopArticles', rng.randrange(1, 5)))
    return _ops('ArticleSystem', [], calls)


def _dcf(rng, uid):
    rows, cols = rng.randrange(1, 7), rng.randrange(1, 7)
    colors = rng.choice(['RY', 'RYB', 'R'])
    calls = []
    for _ in range(rng.randrange(0, 40)):
        if uid == _o.DCF2 and rng.random() < 0.3: calls.append(('getWinner',))
        else: calls.append(('drop', rng.choice(colors), rng.randrange(cols)))
    return _ops('ConnectFourBoard', [rows, cols], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.BLP:
        args = [[['ab', 'ba']], [['ab', 'ab']], [['aa', 'aa', 'aa']], [['abc', 'cba', 'bab', 'xyx']], [['a']], [['ab', 'cd']], [['lc', 'cl', 'gg']]]
        args += [_blp(rng) for _ in range(250)]
    elif uid == o.BFO:
        P = [['apple', 10], ['pear', 7]]
        args = [[[], P, []], [[['apple', '3', '0'], ['apple', '2', '600000']], P, [[5, 20]]], [[['apple', '3', '0'], ['apple', '2', '600001']], P, [[5, 20]]],
                [[['apple', '1', '0'], ['pear', '9', '1'], ['apple', '1', '1200000'], ['apple', '1', '600000']], P, [[2, 10], [3, 50]]],
                [[['pear', '7', '5']], P, [[2, 100]]], [[['pear', '1', '5'], ['pear', '2', '5']], P, [[2, 33]]]]
        args += [_bfo(rng) for _ in range(250)]
    elif uid == o.CCP:
        roads = [['A', 'B', 5], ['B', 'C', 5], ['X', 'C', 3], ['C', 'Campground', 4]]
        args = [[roads, [], 'A', 'X'], [roads, [['amy', 'B'], ['bo', 'C'], ['cy', 'X'], ['di', 'A']], 'A', 'X'],
                [roads, [['amy', 'C']], 'B', 'X'], [roads, [['amy', 'C'], ['zed', 'C']], 'X', 'B'], [[['P', 'Campground', 1], ['Q', 'P', 1]], [['f', 'P']], 'P', 'Q']]
        args += [_ccp(rng) for _ in range(250)]
    elif uid in o.CFS:
        base = [[[0, 30], [5, 10], [10, 20], [15, 25]], [], [[1, 2], [1, 2], [2, 3]], [[5, 6], [0, 10], [0, 5]]]
        args = [[b] for b in base] if uid == o.CFS1 else [[b, c] for b in base for c in (1, 2)]
        args += [_cfs(rng, uid) for _ in range(250)]
    elif uid == o.CPP:
        args = [[[1]], [[2, 1]], [[1, 3, 2]], [[4, 1, 3, 2]], [[2, 4, 1, 3, 5]], [[3, 1, 2]]]
        args += [_cpp(rng) for _ in range(250)]
    elif uid == o.CPD:
        args = [[[[0, 0], [3, 4]]], [[[0, 0], [1, 1], [5, 5], [-1, 2]]], [[[1, 1], [1, 2], [1, 3]]], [[[-10**7, -10**7], [10**7, 10**7]]]]
        args += [_cpd(rng) for _ in range(250)]
    elif uid == o.CNS:
        args = [[[[1, 2, 3], [4]]], [[[1, None, 2], []]], [[[]]], [[[], []]], [[[5, 1], [1, 2], [0, None, 3]]], [[[1, 2, 3, 4], [10]]]]
        args += [_cns(rng) for _ in range(250)]
    elif uid == o.CDS:
        args = [[[1], 1], [[1], 5], [[2, 3], 5], [[2], 3], [[5, 5], 4], [[3, 1, 2], 10]]
        args += [_cds(rng) for _ in range(250)]
    elif uid == o.CIC:
        args = [_ops('IntervalCounter', [[[1, 4], [2, 6], [8, 9], [2, 2]]], [('count', x) for x in (0, 1, 2, 3, 6, 7, 8, 10)]), _ops('IntervalCounter', [[]], [('count', 0)]),
                _ops('IntervalCounter', [[[-5, -5], [-5, -5]]], [('count', -5), ('count', -4)])]
        args += [_cic(rng) for _ in range(250)]
    elif uid == o.CVB:
        args = [[[1, 1, 3], '???0111'], [[1], '?'], [[], '0?0'], [[], '1'], [[2], '??'], [[1, 1], '?????'], [[3, 2, 1], '?###????????'.replace('#', '1')]]
        args += [_cvb(rng) for _ in range(250)]
    elif uid == o.COM:
        args = [[[], [], []], [[5], [10], [['buy', 10], ['sell', 4], ['buy', 9]]], [[3, 8], [9, 12], [['sell', 2], ['buy', 15], ['buy', 15], ['buy', 15]]],
                [[], [7, 7], [['buy', 7], ['buy', 6], ['sell', 6]]]]
        args += [_com(rng) for _ in range(250)]
    elif uid in o.DWS:
        d = [{'tags': ['web'], 'timestamp': 1, 'value': 5}, {'tags': ['db'], 'timestamp': 2, 'value': 7}, {'tags': ['web', 'db'], 'timestamp': 4, 'value': -2},
             {'tags': ['web'], 'timestamp': 6, 'value': 10}]
        args = [[[], 'web', 3], [d, 'web', 3], [d, 'db', 1], [d, 'web', 100], [d, 'x', 2]]
        args += [_dws(rng, uid) for _ in range(250)]
    elif uid == o.DKB:
        args = [[[2, 1, 6, 4], 1], [[1, 1, 1], 1], [[1, 2, 3], 3], [[5], 1], [[1, 2], 1], [[3, 1, 2, 2, 1], 2]]
        args += [_dkb(rng) for _ in range(250)]
    elif uid in o.DVC:
        v = ['1.0.0', '1.2.0', '1.10.0', '2.0.1', '10.0.0']
        args = [[[], []], [v, [False, False, True, True, True]], [v, [False] * 5], [v, [True] * 5], [['103.3.2'], [True]]]
        if uid == o.DVC2: args += [[v[::-1], [True, True, True, False, False]], [['9.0.0', '10.0.0', '1.0.0'], [True, True, False]]]
        args += [_dvc(rng, uid) for _ in range(250)]
    elif uid == o.DAS:
        args = [_ops('ArticleSystem', [], [('addArticle', 'alpha'), ('addArticle', 'beta'), ('upvoteArticle', 1, 7), ('downvoteArticle', 2, 7), ('getTopArticles', 2),
                                          ('downvoteArticle', 1, 7), ('upvoteArticle', 2, 7), ('getRecentFlips', 7, 5), ('getTopArticles', 5), ('upvoteArticle', 2, 7),
                                          ('upvoteArticle', 1, 7), ('getRecentFlips', 7, 1), ('getRecentFlips', 8, 3)]),
                _ops('ArticleSystem', [], [('getTopArticles', 3)])]
        args += [_das(rng) for _ in range(250)]
    elif uid in o.DCF:
        calls = [('drop', 'R', 0), ('drop', 'Y', 0), ('drop', 'R', 0), ('drop', 'B', 1)]
        if uid == o.DCF2: calls = [('getWinner',)] + calls + [('getWinner',)]
        args = [_ops('ConnectFourBoard', [2, 2], calls), _ops('ConnectFourBoard', [1, 1], [('drop', 'R', 0), ('drop', 'Y', 0)])]
        if uid == o.DCF2:
            row = [('drop', 'R', c) for c in range(4)] + [('getWinner',)]
            args.append(_ops('ConnectFourBoard', [1, 5], [('drop', 'Y', 4), ('getWinner',)] + row))
            diag = [('drop', 'Y', 1), ('drop', 'Y', 2), ('drop', 'Y', 2), ('drop', 'Y', 3), ('drop', 'Y', 3), ('drop', 'Y', 3)] + [('drop', 'R', c) for c in range(4)] + [('getWinner',)]
            args.append(_ops('ConnectFourBoard', [4, 4], diag))
            args.append(_ops('ConnectFourBoard', [4, 1], [('drop', 'B', 0)] * 4 + [('getWinner',), ('drop', 'R', 0), ('getWinner',)]))
        args += [_dcf(rng, uid) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _floor_sum_count(prefix, d):
    """Completions by day d from prefix counts of interval multiplicities, one block per distinct quotient (a third method)."""
    total, x, lo, top = 0, d - 1, 1, len(prefix) - 1
    while lo <= top:
        q = x // lo; hi = top if q == 0 else min(top, x // q)
        total += (q + 1) * (prefix[hi] - prefix[lo - 1]); lo = hi + 1
    return total


def _days_by_blocks(intervals, goal):
    prefix = [0] * (max(intervals) + 1)
    for iv in intervals: prefix[iv] += 1
    for i in range(1, len(prefix)): prefix[i] += prefix[i - 1]
    lo, hi = 1, 1 + (goal - 1) * min(intervals)
    while lo < hi:
        mid = (lo + hi) // 2
        if _floor_sum_count(prefix, mid) >= goal: hi = mid
        else: lo = mid + 1
    return lo


def _board(rows, cols, cells):
    return [[cells.get((r, c), '0') for c in range(cols)] for r in range(rows)]


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    if uid == o.BLP:
        out.append(([['ab'] * 50000 + ['ba'] * 50000], 200000))
        out.append(([['aaaaaaaaaa'] * 100000], 1000000))
        out.append(([['abc'] * 99999 + ['aba']], 3))
        out.append(([['a' + _code(i, 4) + 'b' for i in range(100000)]], 0))
        out.append(([['q' + _code(i, 4) + 'z' for i in range(50000)] + ['z' + _code(i, 4)[::-1] + 'q' for i in range(50000)]], 600000))
    elif uid == o.BFO:
        out.append(([[['apple', '1000', str(i * 600000)] for i in range(100000)], [['apple', 10000]], [[2, 10], [100000000, 50]]], 10**8 * 10**4 * 50 // 100))
        out.append(([[['pear', '1000', str(i * 600001)] for i in range(100000)], [['pear', 7]], [[2, 90]]], 10**5 * 1000 * 7))
        orders = [[_code(f, 4), '1', str(10**13 - i * 1000)] for f in range(1000) for i in range(100)]
        out.append(([orders, [[_code(f, 4), 3] for f in range(1000)], [[50, 20], [101, 99]]], 1000 * (100 * 3 * 80 // 100)))
    elif uid == o.CCP:
        n = 100000
        roads = [['L%d' % i, 'L%d' % (i + 1) if i + 1 < n else o.CAMP, 1] for i in range(n)][::-1]
        friends = [['F%d' % i, 'L%d' % i] for i in range(n)]
        out.append(([roads, friends, 'L0', 'L50000'], [['F%d' % i for i in range(50000)], ['F%d' % i for i in range(50000, n)]]))
        roads = [['A%d' % i, 'A%d' % (i + 1) if i + 1 < 50000 else o.CAMP, 2] for i in range(50000)]
        roads += [['B%d' % i, 'B%d' % (i + 1) if i + 1 < 49999 else 'A25000', 1] for i in range(49999)]
        friends = [['a%d' % i, 'A%d' % i] for i in range(0, 50000, 100)] + [['b%d' % i, 'B%d' % i] for i in range(0, 49999, 100)]
        exp1 = ['a%d' % i for i in range(0, 25000, 100)]
        exp2 = ['b%d' % i for i in range(0, 49999, 100)] + ['a%d' % i for i in range(25000, 50000, 100)]
        out.append(([roads, friends, 'A0', 'B0'], [exp1, exp2]))
        # driver 2 reaches A25000 at 49999 * 1 + 1 = 50000, the same time as driver 1: tie goes to driver 1
        roads2 = [r[:] for r in roads]; roads2[50000 + 49998][2] = 2
        out.append(([roads2, friends, 'A0', 'B0'], [['a%d' % i for i in range(0, 50000, 100)], ['b%d' % i for i in range(0, 49999, 100)]]))
    elif uid == o.CFS1:
        n = 100000
        out.append(([[[0, 10**9]] * n], list(range(1, n + 1))))
        out.append(([[[i, i + 1] for i in range(n)]], [1] * n))
        out.append(([[[i, i + 2] for i in range(n)]], [1 + i % 2 for i in range(n)]))
        out.append(([[[n - 1 - i, 10**9] for i in range(n)]], [n - i for i in range(n)]))
    elif uid == o.CFS2:
        n = 100000
        out.append(([[[0, 10**9]] * n, 50000], list(range(1, 50001)) + [-1] * 50000))
        out.append(([[[i, i + 2] for i in range(n)], 1], [1 if i % 2 == 0 else -1 for i in range(n)]))
        out.append(([[[0, 10**9]] * n, n], list(range(1, n + 1))))
        out.append(([[[n - 1 - i, 10**9] for i in range(n)], 100000], [n - i for i in range(n)]))
    elif uid == o.CPP:
        n = 200000
        out.append(([list(range(1, n + 1))], [True] * n))
        out.append(([list(range(n, 0, -1))], [True] * n))
        out.append(([[1] + list(range(n, 1, -1))], [True] + [False] * (n - 2) + [True]))
        split = list(range(1, n, 2)) + list(range(2, n + 1, 2))  # odds then evens: 1 at 0, 2 at n // 2; 1..n - 1 fill all but the last slot
        out.append(([split], [k in (1, n - 1, n) for k in range(1, n + 1)]))
    elif uid == o.CPD:
        pts = [[3 * i, 3 * j] for i in range(223) for j in range(223)]
        out.append(([pts], 3.0))
        out.append(([[[7 * i, 0] for i in range(49999)] + [[3, 1]]], math.sqrt(10)))
        pts = [[i * 200 - 10**7, (i * i * 37) % (2 * 10**7) - 10**7] for i in range(49999)] + [[-10**7 + 1, 1 - 10**7]]
        out.append(([pts], math.sqrt(2)))
        pts = [[i * 300 - 10**7, (i % 2) * 400] for i in range(50000)]
        out.append(([pts], 500.0))
    elif uid == o.CNS:
        n = 10000
        kids = [sum(1 for c in (2 * i + 1, 2 * i + 2) if c < n) for i in range(n)]
        out.append(([[[1] * n for _ in range(10)]], [1 + 9 * (1 + kids[i]) for i in range(n)]))
        chain = [1]
        for _ in range(4999): chain += [None, 1]
        out.append(([[chain, []]], [2 if v is not None else None for v in chain[:-1]] + [1]))
        big = [((i * 37) % 20001) - 10000 for i in range(n)]
        out.append(([[big]], big))
    elif uid == o.CDS:
        out.append(([[100000] * 100000, 10**9], 999900001))
        out.append(([[100000], 10**9], 1 + (10**9 - 1) * 100000))
        out.append(([[1] * 100000, 10**9], 10000))
        iv = list(range(1, 100001))
        out.append(([iv, 10**9], _days_by_blocks(iv, 10**9)))
        iv = [100000 - (i * 7) % 1000 for i in range(100000)]
        out.append(([iv, 10**9], _days_by_blocks(iv, 10**9)))
    elif uid == o.CIC:
        n = 100000
        xs = [2 * j - 1 for j in range(n)]
        cover = lambda x: max(0, min(x, n - 1) - max(0, x - (n - 1)) + 1) if x >= 0 else 0
        out.append((_ops('IntervalCounter', [[[i, i + n - 1] for i in range(n)]], [('count', x) for x in xs]), [None] + [cover(x) for x in xs]))
        q = [(-10**9 + j * 20000) for j in range(n)]
        out.append((_ops('IntervalCounter', [[[-10**9, 10**9]] * n], [('count', x) for x in q]), [None] + [n] * n))
        out.append((_ops('IntervalCounter', [[[i, i] for i in range(n)]], [('count', x) for x in range(-1, n - 1)]), [None, 0] + [1] * (n - 1)))
    elif uid == o.CVB:
        out.append(([[], '?' * 50], 1))
        out.append(([[1], '?' * 50], 50))
        out.append(([[1, 1], '?' * 50], 49 * 48 // 2))
        out.append(([[50], '?' * 50], 1))
        out.append(([[1] * 25, '?' * 49], 1))
        out.append(([[1] * 25, '?' * 50], 26))
        out.append(([[1] * 12, '?' * 50], _binom(39, 12)))
        out.append(([[2] * 10, '1' + '?' * 49], _binom(30, 9)))
    elif uid == o.COM:
        n = 100000
        out.append(([[], list(range(1, n + 1)), [['buy', 10**9]] * n], list(range(1, n + 1))))
        out.append(([list(range(1, n + 1)), [], [['sell', 1]] * n], list(range(n, 0, -1))))
        out.append(([[], [], [['buy', 10], ['sell', 20]] * (n // 2)], [-1] * n))
        out.append(([list(range(1, n + 1)), list(range(n + 1, 2 * n + 1)), [['buy', n + 1 + i] if i % 2 == 0 else ['sell', n - i] for i in range(n)]],
                    [n + 1 + i // 2 if i % 2 == 0 else n - i // 2 for i in range(n)]))
    elif uid in o.DWS:
        n = 100000
        pts = [{'tags': ['a', 'b'] if j % 2 else ['a'], 'timestamp': j, 'value': j} for j in range(n)]
        tri = lambda a, b: (a + b) * (b - a + 1) // 2 if b >= a else 0
        if uid == o.DWS1:
            out.append(([pts, 'a', 1000], [tri(max(0, j - 999), j) for j in range(n)]))
            odd = list(range(1, n, 2))
            out.append(([pts, 'b', 10], [sum(x for x in range(max(1, j - 9), j + 1) if x % 2) for j in odd]))
            out.append(([pts, 'a', 10**9], [tri(0, j) for j in range(n)]))
            big = [{'tags': ['m'], 'timestamp': j * 10000, 'value': -10**9} for j in range(n)]
            out.append(([big, 'm', 10**9], [-10**9 * (j + 1) for j in range(n)]))
        else:
            out.append(([pts, 'a', 1000], [tri(max(0, j - 999), j) for j in range(n)]))
            odd = list(range(1, n, 2))
            out.append(([pts, 'b', 10], [sum(odd[max(0, i - 9):i + 1]) for i in range(len(odd))]))
            out.append(([pts, 'a', 100000], [tri(0, j) for j in range(n)]))
            big = [{'tags': ['m'], 'timestamp': j * 10000, 'value': -10**9} for j in range(n)]
            out.append(([big, 'm', 100000], [-10**9 * (j + 1) for j in range(n)]))
    elif uid == o.DKB:
        n = 100000
        out.append(([[10**9] * n, 2], 0))
        out.append(([[10**9] * n, 1], -1))
        z = [0] * n; z[-1] = 7
        out.append(([z, 1], n - 1))
        out.append(([[-10**9] * n, n], 0))
        w = [(-1) ** i * 10**9 for i in range(n)]  # even sum 5e13, odd sum -5e13
        out.append(([w, 3], -1))
    elif uid in o.DVC:
        n = 100000
        vs = ['%d.%d.%d' % (i // 10000, (i // 100) % 100, i % 100) for i in range(n)]
        perm = list(range(n)) if uid == o.DVC1 else [(i * 7919) % n for i in range(n)]
        for cut in (77777, n, 0, n - 1):
            out.append(([[vs[p] for p in perm], [p >= cut for p in perm]], vs[cut] if cut < n else None))
        wide = ['%d.%d.%d' % (10**6 - i, 999999, 0) for i in range(n)][::-1]
        out.append(([wide, [i >= 1 for i in range(n)]] if uid == o.DVC1 else [wide[::-1], [i <= n - 2 for i in range(n)]], wide[1]))
    elif uid == o.DAS:
        A = 10000
        name = lambda a: 'n' + _code(a, 4)
        calls = [('addArticle', name(a)) for a in range(1, A + 1)]
        calls += [('upvoteArticle', a, 1) for a in range(1, A + 1)] + [('downvoteArticle', a, 2) for a in range(1, A + 1)]
        calls += [('upvoteArticle', a, 2) for a in range(1, A + 1)] + [('upvoteArticle', a, 2) for a in range(1, 2001)]
        calls += [('downvoteArticle', a, 1) for a in range(2, A + 1, 2)]
        queries = [('getTopArticles', 100), ('getRecentFlips', 2, 100), ('getRecentFlips', 1, 100), ('getRecentFlips', 3, 5)] * 750
        expected = [None] + list(range(1, A + 1)) + [None] * (3 * A + 2000 + A // 2)
        answers = {'getTopArticles': [name(a) for a in range(1, 200, 2)], 2: [name(a) for a in range(A, A - 100, -1)],
                   1: [name(a) for a in range(A, A - 200, -2)], 3: []}
        expected += [answers['getTopArticles'] if q[0] == 'getTopArticles' else answers[q[1]] for q in queries]
        out.append((_ops('ArticleSystem', [], calls + queries), expected))
    elif uid in o.DCF:
        R = C = 50
        calls, expected, cells = [], [None], {}
        for i in range(400):
            col, color = i % C, 'R' if i % 2 == 0 else 'Y'
            cells[(R - 1 - i // C, col)] = color
            calls.append(('drop', color, col)); expected.append(_board(R, C, cells))
            if uid == o.DCF2: calls.append(('getWinner',)); expected.append('R' if i >= 150 else '0')
        out.append((_ops('ConnectFourBoard', [R, C], calls), expected))
        calls, expected, cells = [], [None], {}
        for i in range(20000):
            color = 'BG'[i % 2] if i < 5 else 'Q'
            if i < 5: cells[(4 - i, 0)] = color
            calls.append(('drop', color, 0)); expected.append(_board(5, 2, cells))
            if uid == o.DCF2 and i % 4 == 3: calls.append(('getWinner',)); expected.append('0')
        out.append((_ops('ConnectFourBoard', [5, 2], calls), expected))
    return out


def _binom(n, k):
    r = 1
    for i in range(k): r = r * (n - i) // (i + 1)
    return r
