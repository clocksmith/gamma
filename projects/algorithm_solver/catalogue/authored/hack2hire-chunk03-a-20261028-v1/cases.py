"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h03a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _ntree(rng, n, depth_cap=6):
    """Random N-ary tree with n nodes and unique shuffled ids; depth capped."""
    ids = rng.sample(range(0, 50), n)
    nodes = [{'id': i, 'children': []} for i in ids]
    depth = [1] * n
    for v in range(1, n):
        p = rng.choice([u for u in range(v) if depth[u] < depth_cap])
        nodes[p]['children'].append(nodes[v]); depth[v] = depth[p] + 1
    return nodes[0], ids


def _level_order(rng, n):
    """Random binary tree with n nodes, serialised LeetCode style (trailing nulls trimmed)."""
    vals = [rng.choice([-5, -1, 0, 1, 2, 3, 7, rng.randrange(-20, 21)]) for _ in range(n)]
    left, right = [-1] * n, [-1] * n
    for v in range(1, n):
        while True:
            p = rng.randrange(v); side = rng.choice((left, right))
            if side[p] < 0: side[p] = v; break
    out, queue, qi = [vals[0]], [0], 0
    while qi < len(queue):
        p = queue[qi]; qi += 1
        for c in (left[p], right[p]):
            if c >= 0: out.append(vals[c]); queue.append(c)
            else: out.append(None)
    while out[-1] is None: out.pop()
    return out


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.ITOA:
        args = [[0], [-1], [1], [7], [-7], [10], [-10], [2**31 - 1], [-2**31], [-2**31 + 1], [1000000000], [-1000000000]]
        args += [[rng.choice([rng.randrange(-2**31, 2**31), rng.randrange(-1000, 1000), -(10 ** rng.randrange(0, 10))])] for _ in range(240)]
    elif uid == o.TOKEN:
        args = [['', ['a']], ['a', ['a']], ['aaaa', ['a', 'aa']], ['aaa', ['a', 'aa', 'aaa']], ['abab', ['a', 'b', 'ab', 'abab', 'ba']],
                ['abc', ['a', 'b', 'c', 'bc', 'ab', 'abc']], ['abc', ['c', 'b', 'a', 'xy']]]
        for _ in range(250):
            chars = rng.sample('abcd', rng.randrange(1, 5))
            text = ''.join(rng.choice(chars) for _ in range(rng.randrange(0, 16)))
            alpha = list(chars) + [c for c in 'abcd' if c not in chars and rng.random() < 0.3]
            for _ in range(rng.randrange(0, 8)):
                if rng.random() < 0.7:
                    a, b = rng.choice(alpha), rng.choice(alpha)
                    if len(a + b) <= 30 and a + b not in alpha: alpha.append(a + b)
                else:
                    w = ''.join(rng.choice(chars) for _ in range(rng.randrange(2, 5)))
                    if w not in alpha: alpha.append(w)
            args.append([text, alpha])
    elif uid == o.ILV:
        args = [_ops('InterleaveIterator', [[], False], [('hasNext',), ('next',)]), _ops('InterleaveIterator', [[], True], [('hasNext',), ('next',)]),
                _ops('InterleaveIterator', [[[], []], True], [('next',), ('hasNext',)]),
                _ops('InterleaveIterator', [[[1, 2, 3], [4], [5, 6]], False], [('next',)] * 7 + [('hasNext',)]),
                _ops('InterleaveIterator', [[[1, 2, 3], [4], [5, 6]], True], [('next',)] * 13 + [('hasNext',)])]
        for _ in range(250):
            arrays = [[rng.randrange(-9, 10) for _ in range(rng.choice([0, 0, 1, 2, 3, 5]))] for _ in range(rng.randrange(0, 5))]
            calls = [(rng.choice(['next', 'next', 'hasNext']),) for _ in range(rng.randrange(1, 25))]
            args.append(_ops('InterleaveIterator', [arrays, rng.random() < 0.5], calls))
    elif uid == o.JUMP:
        args = [[[5]], [[-5]], [[1, -2]], [[1, -100, -100, 7]], [[0] * 14 + [3]]]
        for _ in range(230):
            n = rng.choice([rng.randrange(1, 30), rng.randrange(1, 60), rng.randrange(30, 120)])
            args.append([[rng.choice([rng.randrange(-10, 11), rng.randrange(-10**4, 10**4 + 1)]) for _ in range(n)]])
        for _ in range(20):
            args.append([[rng.randrange(-10**4, 10**4 + 1) for _ in range(rng.randrange(150, 400))]])
    elif uid == o.KTH:
        args = [[[1], 1], [[1, 2], 2], [[2, 1], 1], [[3, 1, 2], 2]]
        for _ in range(250):
            n = rng.randrange(1, 40); arr = list(range(1, n + 1)); rng.shuffle(arr)
            args.append([arr, rng.randrange(1, n + 1)])
    elif uid == o.TEAM:
        args = [[[1]], [[5, 5, 5]], [[1, 3, 5]], [[1, 2, 2, 3, 5]], [[10**9, 10**9 - 1, 1]]]
        for _ in range(250):
            hi = rng.choice([5, 10, 30, 10**9])
            args.append([[rng.randrange(1, hi + 1) for _ in range(rng.randrange(1, 25))]])
    elif uid == o.LEAGUE:
        args = [[['A', 'A'], [1, 1], [0, 0], 'A'], [['A', 'B', 'A'], [10, 99, 20], [1, 5, 2], 'A'],
                [['Serie A', 'Serie A', 'Liga'], [3, 7, 1], [1, 0, 100], 'Serie A']]
        for _ in range(250):
            names = rng.sample(['Premier', 'Liga', 'Serie A', 'Bundesliga 2'], rng.randrange(1, 4))
            n = rng.randrange(2, 12); leagues = [rng.choice(names) for _ in range(n)]
            target = rng.choice(leagues)
            if leagues.count(target) < 2: leagues.append(target)
            n = len(leagues)
            caps = [rng.choice([1, 2, 3, 7, 100000, rng.randrange(1, 100001)]) for _ in range(n)]
            silver = [rng.choice([0, 0, 1, 3, 100, rng.randrange(0, 101)]) for _ in range(n)]
            args.append([leagues, caps, silver, target])
    elif uid in (o.TREE1, o.TREE2):
        args = [[{'id': 0, 'children': []}, [] if uid == o.TREE1 else 1]]
        chain = {'id': 3, 'children': []}
        for i in (2, 1): chain = {'id': i, 'children': [chain]}
        root = {'id': 0, 'children': [chain, {'id': 9, 'children': []}]}
        args += [[root, [1, 2, 3] if uid == o.TREE1 else 1], [root, [3] if uid == o.TREE1 else 2], [root, [9] if uid == o.TREE1 else 4]]
        for _ in range(250):
            n = rng.randrange(1, 13 if uid == o.TREE2 else 25)
            tree, ids = _ntree(rng, n)
            if uid == o.TREE1: args.append([tree, rng.sample(ids[1:], rng.randrange(0, n))])
            else: args.append([tree, rng.randrange(1, 7)])
    elif uid == o.LERP:
        args = [[[[0, 0]], [0, -1, 1]], [[[0, 0], [2, 1]], [1]], [[[0, 5], [0, 1], [3, 9], [3, -3]], [-1, 0, 1, 2, 3, 4]],
                [[[1, 1]], []], [[[-10**6, 10**6], [10**6, -10**6]], [0, 999999, -999999]]]
        for _ in range(250):
            pts = [[rng.randrange(-6, 7), rng.randrange(-10, 11)] for _ in range(rng.randrange(1, 9))]
            args.append([pts, [rng.randrange(-8, 9) for _ in range(rng.randrange(0, 10))]])
    elif uid == o.FILLPTS:
        args = [[1, [[0, 0]]], [1, [[0, 0], [1, 5]]], [2, [[0, 0], [1, 7], [5, 0]]], [3, [[0, 0], [9, 1]]], [5, [[-10, 3], [0, -4], [2, 2]]]]
        for _ in range(250):
            interval = rng.choice([1, 2, 3, 5, 7])
            pts, x = [], rng.randrange(-20, 20)
            for _ in range(rng.randrange(1, 7)):
                pts.append([x, rng.randrange(-20, 21)])
                x += rng.choice([interval * rng.randrange(1, 5), rng.randrange(1, interval + 1)])
            args.append([interval, pts])
    elif uid == o.SHIFT:
        args = [[[1]], [[2, 2, 2]], [[3, 2, 1]], [[1, 3, 2]], [[1, 2, 3]], [[2, 1, 3]], [[1, 1, 2, 1]], [[2, 1, 2, 1]]]
        for _ in range(250):
            n = rng.randrange(1, 12)
            if rng.random() < 0.6:
                base = sorted((rng.randrange(-3, 4) for _ in range(n)), reverse=True); t = rng.randrange(n)
                arr = base[t:] + base[:t]
                if rng.random() < 0.2: arr[rng.randrange(n)] = rng.randrange(-3, 4)
            else: arr = [rng.randrange(-3, 4) for _ in range(n)]
            args.append([arr])
    elif uid == o.TILES:
        args = [[0, 0], [1, 0], [0, 1], [3, 0], [4, 0], [5, 0], [5, 1], [4, 1], [8, 1], [0, 10**9], [10**9, 0], [10**9, 10**9], [6, 2], [7, 2]]
        for _ in range(240):
            args.append([rng.choice([rng.randrange(0, 50), rng.randrange(0, 10**9 + 1)]), rng.choice([rng.randrange(0, 30), rng.randrange(0, 10**9 + 1)])])
    elif uid == o.LEAF:
        args = [[[5]], [[1, 2]], [[1, None, 3]], [[1, 2, 3]], [[-10, 9, 20, None, None, 15, 7]], [[1, 2, None, 3, 4]],
                [[-1, -2, -3]], [[10**9, -10**9, 10**9]]]
        for _ in range(250):
            args.append([_level_order(rng, rng.randrange(1, 30))])
    elif uid == o.DEPLOY:
        args = [[[1, 1, 1]], [[1, 2, 3]], [[5, 1, 9]], [[10**9, 1, 1]], [[4, 4, 1, 1]], [[1, 10**9, 10**9, 1]]]
        for _ in range(250):
            hi = rng.choice([3, 6, 100, 10**9])
            args.append([[rng.randrange(1, hi + 1) for _ in range(rng.randrange(3, 9))]])
    elif uid == o.CALLS:
        D = o.DAY_MS
        args = [[[]], [[[1, 'a', 0, 1]]], [[[1, 'a', 0, 10], [1, 'b', 10, 20]]], [[[1, 'a', 0, 10], [1, 'b', 9, 20], [2, 'c', 5, 6]]],
                [[[7, 'x', D - 1, D + 1], [7, 'y', D, D + 2]]], [[[3, 'long', 5, 5 + 3 * D]]], [[[1, 'z', 10**12, 10**12 + 3 * D]]]]
        for _ in range(250):
            calls = []
            for i in range(rng.randrange(0, 12)):
                s = rng.choice([rng.randrange(0, 50), D - rng.randrange(1, 30), rng.randrange(0, 3 * D)])
                e = s + rng.choice([1, rng.randrange(1, 40), rng.randrange(1, 3 * D + 1)])
                calls.append([rng.choice([1, 2, 3]), 'c' + str(i), s, e])
            args.append([calls])
    elif uid == o.STAB:
        args = [[[0], [0]], [[5], [3]], [[1, 2], [10, 1]], [[3, 3, 3], [1, 1, 1]], [[10**6, 0], [10**4, 10**4]]]
        for _ in range(230):
            n = rng.randrange(1, 12)
            args.append([[rng.randrange(0, 12) for _ in range(n)], [rng.randrange(0, 12) for _ in range(n)]])
        for _ in range(20):
            n = rng.randrange(13, 300)
            args.append([[rng.randrange(0, 10**6 + 1) for _ in range(n)], [rng.randrange(0, 10**4 + 1) for _ in range(n)]])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _frac(num, den):
    from math import gcd
    g = gcd(num, den); num, den = num // g, den // g
    return str(num) if den == 1 else '%d/%d' % (num, den)


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.ITOA:
        out.append(([-2**31], '-2147483648'))
    elif uid == o.TOKEN:
        # 'ab' * 50000: token 'ab' merges every pair, 'abab' merges pairs of those, ... up to 2**k copies.
        text = 'ab' * 50000
        alpha = ['a', 'b'] + ['ab' * (1 << k) for k in range(0, 4)]
        out.append(([text, alpha], [5] * 6250))
        # Long alphabet whose multi-character tokens never occur (no valid adjacent pair): sequence unchanged.
        letters = 'abcdefghijklmnopqrstuvwxyz'
        alpha2 = list(letters) + ['z' + letters[i % 26] + letters[(i // 26) % 26] + letters[(i // 676) % 26] for i in range(4974)]
        text2 = ''.join(letters[i % 25] for i in range(100000))
        out.append(([text2, alpha2], [i % 25 for i in range(100000)]))
    elif uid == o.ILV:
        arrays = [[i] * 10 for i in range(10000)]
        calls = [('next',)] * 100000
        out.append((_ops('InterleaveIterator', [arrays, False], calls), [None] + list(range(10000)) * 10))
        arrays = [list(range(100000))]
        calls = [('next',), ('hasNext',)] * 50000
        expected = [None]
        for i in range(50000): expected += [i, True]
        out.append((_ops('InterleaveIterator', [arrays, True], calls), expected))
        arrays = [[7]] + [[] for _ in range(9999)]
        out.append((_ops('InterleaveIterator', [arrays, True], [('next',)] * 100000), [None] + [7] * 100000))
    elif uid == o.JUMP:
        out.append(([[1] * 5000], 5000))
        n = 4999  # n-1 = 4998 is a multiple of 3: jumps of 3 visit only zero cells.
        out.append(([[0 if i % 3 == 0 else -10**4 for i in range(n)]], 0))
        out.append(([[10**4] + [-10**4] * 4998 + [10**4]], _jump_all_negative()))
    elif uid == o.KTH:
        n = 100000
        out.append(([list(range(1, n + 1)), 1], list(range(1, n + 1))))
        out.append(([list(range(1, n + 1)), 50000], [i - 50000 + 1 for i in range(50000, n + 1)]))
        out.append(([list(range(n, 0, -1)), 777], [n - 777 + 1] * (n - 777 + 1)))
    elif uid == o.TEAM:
        out.append(([list(range(1, 100001))[::-1]], 100000))
        out.append(([[2 * i + 1 for i in range(100000)]], 1))
        out.append(([[5] * 50000 + [6] * 50000], 100000))
    elif uid == o.LEAGUE:
        c = 10000
        out.append(([['Big'] * c + ['Other'] * 90000, [100000] * c + [1] * 90000, [100] * c + [0] * 90000, 'Big'],
                    [c * (c - 1) * 100000 * 200, '20000000.00']))
        # caps 1, silverware 1 for one club and 0 for the rest: total = sum over matches involving the star.
        out.append(([['L'] * c, [1] * c, [1] + [0] * (c - 1), 'L'], [2 * (c - 1), _avg(2 * (c - 1), c * (c - 1))]))
    elif uid in (o.TREE1, o.TREE2):
        # 400 chains of 98 nodes under the root (39201 nodes; depth 99).
        root, nid = {'id': 0, 'children': []}, 1
        for _ in range(400):
            node = None
            for _ in range(98):
                node = {'id': nid, 'children': [node] if node else []}; nid += 1
            root['children'].append(node)
        if uid == o.TREE1:
            out.append(([root, []], 99))
            out.append(([root, list(range(1, nid, 2))], 50))
        else:
            out.append(([root, 99], 0))
            out.append(([root, 10], 400 * (99 - 10)))
        # broom: chain of 97 nodes under the root ending in 60000 leaves (depth 99).
        leaves = [{'id': 1000 + i, 'children': []} for i in range(60000)]
        node = {'id': 97, 'children': leaves}
        for i in range(96, 0, -1): node = {'id': i, 'children': [node]}
        broom = {'id': 0, 'children': [node]}
        if uid == o.TREE1: out.append(([broom, list(range(1, 98))], 2))
        else: out.append(([broom, 5], 99 - 5))
    elif uid == o.LERP:
        pts = []
        for m in range(50000): pts += [[2 * m, 2 * m], [2 * m, 2 * m - 1]]
        qs = list(range(-1, 100000))
        exp = []
        for q in qs:
            if q < 0: exp.append('-1')
            elif q > 99998: exp.append('99998')
            elif q % 2 == 0: exp.append(str(q))
            else: exp.append(_frac(4 * (q // 2) + 1, 2))
        out.append(([pts, qs[:100000]], exp[:100000]))
    elif uid == o.FILLPTS:
        out.append(([1, [[0, 0], [99999, 3 * 99999]]], [[x, str(3 * x)] for x in range(100000)]))
        out.append(([3, [[-999999, 0], [-999999 + 3 * 99999, 33333]]], [[-999999 + 3 * k, _frac(k, 3)] for k in range(100000)]))
    elif uid == o.SHIFT:
        n = 100000; base = list(range(n, 0, -1)); t = 31337
        out.append(([base[n - t:] + base[:n - t]], n - t))  # arr is base shifted by t; shifting by n - t restores it
        out.append(([[4] * n], 0))
        out.append(([list(range(n))], -1))
    elif uid == o.TILES:
        out.append(([10**9, 10**9], 70710))  # isqrt(5e9) = 70710 (even): 1e9 two-by-two tiles cover 4e9, the remaining 999904100 cells take one-by-one tiles.
        out.append(([0, 10**9], 63244))  # largest even s with (s/2)**2 <= 1e9: s/2 = 31622.
    elif uid == o.LEAF:
        # perfect tree with 16 levels of value 1: leaf-to-leaf through the root has 31 nodes.
        out.append(([[1] * 65535], 31))
        # left chain of 50000 nodes (single leaf): the degenerate rule returns the leaf value.
        vals = [1]
        for i in range(49999): vals += [2, None]
        vals[-2] = -3
        out.append(([vals[:-1]], -3))
    elif uid == o.DEPLOY:
        out.append(([list(range(1, 100001))], 2 * 100000 - 3))
        out.append(([[7] * 100000], 0))
    elif uid == o.CALLS:
        D = o.DAY_MS
        out.append(([[[1, 'c' + str(i), 0, 1000] for i in range(100000)]], [[1, 0, 100000]]))
        out.append(([[[i % 50 + 1, 'k' + str(i), (i // 50) * D, (i // 50) * D + 3 * D] for i in range(100000)]],
                    [[c, d, _calls_peak(d)] for c in range(1, 51) for d in range(2002)]))
    elif uid == o.STAB:
        n = 100000
        out.append(([[10**6] * n, [10**4] * n], 10**6 * n * 10**4))
        out.append(([list(range(1, n + 1)), [1] * n], 50000 * 50001))
    return out


def _calls_peak(day):
    """Each customer has one 3-day call starting at each day 0..1999: day d sees calls started on days max(0,d-2)..min(1999,d)."""
    return min(day, 1999) - max(0, day - 2) + 1


def _avg(total, matches):
    cents = (total * 100 * 2 + matches) // (2 * matches)
    return '%d.%02d' % (cents // 100, cents % 100)


def _jump_all_negative():
    """nums[0] = nums[-1] = 1e4, others -1e4: maximise = 2e4 - 1e4 * (minimum interior landings).
    Minimum hops over distance 4998 using steps 1 or primes ending in 3; computed by a BFS over positions."""
    n = 5000
    primes = [p for p in range(2, n) if p % 10 == 3 and _o.is_prime(p)]
    dist = [None] * n; dist[0] = 0; frontier = [0]
    while frontier:
        nxt = []
        for v in frontier:
            for s in [1] + primes:
                w = v + s
                if w < n and dist[w] is None: dist[w] = dist[v] + 1; nxt.append(w)
        frontier = nxt
    return 2 * 10**4 - 10**4 * (dist[n - 1] - 1)
