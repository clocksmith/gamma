"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h09b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _board(rng):
    R, C = rng.randrange(1, 7), rng.randrange(1, 7); letters = rng.choice(['A', 'AB', 'ABC', 'ABCD'])
    return [[rng.choice(letters) + str(rng.choice([0, 0, 1, 2, 9])) for _ in range(C)] for _ in range(R)]


def _tree(rng):
    n = rng.randrange(1, 14); vals = rng.sample(range(0, 40), n)
    children = {v: [] for v in vals}
    for i in range(1, n): children[vals[rng.randrange(0, i)]].append(vals[i])
    for v in vals: rng.shuffle(children[v])
    rows, stack = [], [vals[0]]
    while stack:
        v = stack.pop(); rows.append([v, children[v]]); stack.extend(reversed(children[v]))
    comp = [rng.choice(vals + [41, 42]) for _ in range(rng.randrange(0, n + 2))]
    return [rows, comp]


def _cpm(rng):
    calls, pts = [], []
    span = rng.choice([2, 3, 5])
    for _ in range(rng.randrange(1, 30)):
        x = rng.random()
        if x < 0.45 or not pts:
            p = [rng.randrange(-span, span), rng.randrange(-span, span)]; pts.append(p); calls.append(('addPoint', p[0], p[1]))
        else:
            a = list(rng.choice(pts)) if rng.random() < 0.85 else [9, 9]
            b = list(rng.choice(pts)) if rng.random() < 0.85 else [rng.randrange(-span, span), rng.randrange(-span, span)]
            calls.append(('isConnected' if x < 0.7 else 'getMinSteps', a, b))
    return _ops('PointMatrix', [], calls)


def _crc(rng):
    singers, roles = ['s1', 's2', 'S3'][:rng.randrange(1, 4)], ['A', 'B', 'C', 'a', 'D_1'][:rng.randrange(1, 6)]
    perf = [[rng.choice(singers), rng.choice(roles), str(rng.choice([1999, 2000, 2001, 2003, 2010, 0, 9999]))] for _ in range(rng.randrange(0, 12))]
    return [perf, rng.choice([0, 1, 2, 5, 10000])]


def _requests(rng, n):
    ids = rng.sample(range(100), n)
    return [','.join([str(rng.choice([0, 1, 2, 5, 9])), 'id%d' % ids[i], str(rng.choice([0, 5, 100, 999, 1000000000])),
                      rng.choice(['4111', '4222', '5555000011112222']), rng.choice(['shop', 'cafe', 'm_1'])]) for i in range(n)]


def _ccf(rng, uid):
    reqs = _requests(rng, rng.randrange(0, 10))
    args = [reqs]
    if uid != _o.CCF1:
        pool = ['card_number,4111', 'card_number,9999', 'merchant,cafe', 'merchant,zzz', 'max_amount,100', 'max_amount,0', 'max_amount,1000000000']
        args.append([rng.choice(pool) for _ in range(rng.randrange(0, 4))])
    if uid == _o.CCF3:
        reps = []
        for _ in range(rng.randrange(0, 4)):
            if not reqs: break
            r = rng.choice(reqs).split(','); reps.append('%d,%s' % (int(r[0]) + rng.choice([0, 0, 1, 3]), r[1]))
        args.append(reps)
    return args


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.CBS:
        args = [[[['A0']]], [[['B9']]], [[['A1', 'A2'], ['B3', 'A0']]], [[['A1', 'B1', 'A1'], ['A1', 'A1', 'A1']]], [[['C1'], ['C1'], ['D9']]]]
        args += [[_board(rng)] for _ in range(250)]
    elif uid == o.CPS:
        args = [[[]], [[5]], [[3, 1, 2]], [[1, 2, 3]], [[2, 2, 2]], [[5, 1, 9, 0, 7]], [[-1000000000, 1000000000, -1000000000]]]
        args += [[[rng.choice([-3, 0, 1, 2, 5, 1000000000]) for _ in range(rng.randrange(0, 12))]] for _ in range(250)]
    elif uid == o.CDG:
        args = [[[]], [[[0, 5]]], [[[9, 1], [10, 2]]], [[[13, 4], [11, 7], [19, 2], [15, 9]]], [[[25, 3], [2, 8], [21, 1], [8, 6]]]]
        for _ in range(250):
            ts = rng.sample(range(0, rng.choice([15, 40, 100])), rng.randrange(0, 12))
            args.append([[[t, rng.choice([1, 2, 5, 9, 1000000000])] for t in ts]])
    elif uid == o.CLL:
        args = [[[], 1], [[[]], 3], [[[1, 2], [3], [], [4, 5, 6]], 2], [[[1, 2, 3]], 3], [[[7], [8]], 5], [[[-1000000000, 1000000000]], 1]]
        args += [[[[rng.randrange(-5, 6) for _ in range(rng.randrange(0, 5))] for _ in range(rng.randrange(0, 6))], rng.randrange(1, 6)] for _ in range(250)]
    elif uid == o.CRA:
        args = [[[], []], [[], [['c', 'p', 'R'], ['c', 'p', 'R'], ['c', 'q', 'R'], ['c', 'q', 'S']]],
                [[['c', 'p', 'R'], ['c', 'q', 'R']], [['c', 'q', 'R'], ['d', 'q', 'R'], ['c', 'r', 'R']]]]
        for _ in range(250):
            def row(): return [rng.choice(['c1', 'c2', 'C']), rng.choice(['p1', 'p2', 'p3']), rng.choice(['R', 'S', 'A_B'])]
            args.append([[row() for _ in range(rng.randrange(0, 5))], [row() for _ in range(rng.randrange(0, 9))]])
    elif uid == o.CNT:
        args = [[[[1, []]], []], [[[1, []]], [1]], [[[1, [2, 3]], [2, [4, 5]], [4, []], [5, []], [3, []]], [2]],
                [[[1, [2, 3]], [2, [4, 5]], [4, []], [5, []], [3, []]], [2, 4, 99, 1]], [[[0, [1]], [1, [2]], [2, [3]], [3, []]], [1, 2]]]
        args += [_tree(rng) for _ in range(250)]
    elif uid == o.CPM:
        args = [_ops('PointMatrix', [], [('getMinSteps', [0, 0], [0, 0])]),
                _ops('PointMatrix', [], [('addPoint', 0, 0), ('addPoint', 0, 5), ('addPoint', 3, 5), ('addPoint', 7, 7), ('isConnected', [0, 0], [3, 5]),
                                         ('getMinSteps', [0, 0], [3, 5]), ('isConnected', [0, 0], [7, 7]), ('getMinSteps', [0, 0], [7, 7]), ('getMinSteps', [3, 5], [3, 5]),
                                         ('addPoint', 3, 7), ('getMinSteps', [0, 0], [7, 7]), ('isConnected', [0, 0], [1, 1]), ('addPoint', 0, 0), ('getMinSteps', [0, 5], [0, 0])])]
        args += [_cpm(rng) for _ in range(250)]
    elif uid == o.CAT:
        args = [[[], 0, 1, 50], [[5], 4, 1, 100], [[5], 5, 1, 1], [[1, 9, 9, 1, 9], 5, 3, 60], [[1, 9, 9, 1, 9], 5, 3, 67], [[1, 2], 0, 3, 0], [[0, 0], 0, 2, 0]]
        for _ in range(250):
            e = [rng.choice([0, 1, 3, 5, 7, 1000000000]) for _ in range(rng.randrange(0, 15))]
            args.append([e, rng.choice([0, 2, 4, 6]), rng.randrange(1, 8), rng.choice([0, 1, 33, 34, 50, 66, 67, 99, 100])])
    elif uid == o.CDE:
        args = [[[1], 1], [[1, 2, 1, 3, 4, 2, 3], 4], [[-1, -1, 0], 2], [[5, 5, 5], 3], [[-1000000000, 1000000000], 1]]
        for _ in range(250):
            nums = [rng.randrange(-3, 4) for _ in range(rng.randrange(1, 15))]
            args.append([nums, rng.randrange(1, len(nums) + 1)])
    elif uid == o.CDR:
        args = [[[]], [[1, 1, 1, 1, 1]], [[1, 1, 1, 2, 2, 2, 2]], [[i // 2 + 1 for i in range(25)]], [[1] * 3 + [2] * 3 + [3] * 3]]
        for _ in range(250):
            t, times = rng.randrange(1, 5), []
            for _ in range(rng.choice([5, 30, 80, 150])):
                t += rng.choice([0, 0, 0, 1, 1, 2, 7]); times.append(t)
            args.append([times])
    elif uid == o.CIP:
        args = [[['a'], [1], [], []], [['a', 'b'], [2, 3.5], ['a', 'b', 'b', 'a'], [2.0, 3.5, 3, 2]], [['x'], [0.1], ['x'], [0.1]], [['x'], [1000000000], ['x'], [999999999.5]]]
        for _ in range(250):
            names = rng.sample(['a', 'b', 'C', 'd1', 'Ee', 'f'], rng.randrange(1, 7)); prices = [rng.choice([0, 1, 2.5, 10, 9.99]) for _ in names]
            sold = [rng.choice(names) for _ in range(rng.randrange(0, 10))]
            args.append([names, prices, sold, [rng.choice([prices[names.index(s)], prices[names.index(s)], 2.5, 0, 9.99]) for s in sold]])
    elif uid == o.CBD:
        args = [[[], []], [[5], [9]], [[0, 9], [9, 0]], [[0, 0], [1, 1]], [[100, 0, 6], [5, 6, 100]], [[10, 1, 0], [1, 1, 10]], [[0, 5, 6], [10, 1, 2]]]
        for _ in range(250):
            n = rng.randrange(0, 9)
            vals = rng.choice([[0, 1, 2, 3], [0, 5, 10, 1000000000], list(range(10))])
            args.append([[rng.choice(vals) for _ in range(n)], [rng.choice(vals) for _ in range(n)]])
    elif uid == o.COP:
        args = [[['_'], [[0]]], [['*'], [[7]]], [['**', '**'], [[1, 1], [1, 2]]], [['*_*', '***'], [[1, 0, 1], [1, 1, 1]]], [['**', '**'], [[1, 2], [2, 1]]]]
        for _ in range(250):
            R, C = rng.randrange(1, 7), rng.randrange(1, 7)
            g = [''.join(rng.choice('**_') for _ in range(C)) for _ in range(R)]
            args.append([g, [[rng.choice([1, 1, 2, 1000000000]) if g[r][c] == '*' else 0 for c in range(C)] for r in range(R)]])
    elif uid == o.CRC:
        args = [[[], 0], [[['s', 'A', '2000'], ['s', 'B', '2001']], 1], [[['s', 'A', '2000'], ['s', 'B', '2002']], 1],
                [[['s', 'A', '2000'], ['t', 'B', '2000'], ['t', 'A', '2000'], ['s', 'B', '2000'], ['s', 'B', '1990']], 0], [[['s', 'A', '1'], ['s', 'A', '1']], 5]]
        args += [_crc(rng) for _ in range(250)]
    elif uid == o.CWT:
        args = [['', 1], ['   ', 2], ['a', 1], ['The cat the CAT dog', 1], ['b a c b a d', 2], ['x  y Y', 5], ['Hello hello HELLO world', 1]]
        for _ in range(250):
            words = [rng.choice(['a', 'A', 'b', 'Bb', 'bB', 'c', 'dog', 'Dog']) for _ in range(rng.randrange(0, 14))]
            args.append([''.join(w + ' ' * rng.randrange(1, 3) for w in words).strip() if rng.random() < 0.7 else ' '.join(words), rng.randrange(1, 4)])
    elif uid in (o.CCF1, o.CCF2, o.CCF3):
        base = ['5,a,100,4111,shop', '3,b,5,4222,cafe', '5,c,1000,4111,cafe', '1,d,0,5555000011112222,shop']
        args = [[[]] + ([[]] if uid != o.CCF1 else []) + ([[]] if uid == o.CCF3 else [])]
        args.append([base] + ([['merchant,cafe', 'max_amount,999']] if uid != o.CCF1 else []) + ([['3,d', '5,b']] if uid == o.CCF3 else []))
        args += [_ccf(rng, uid) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.CBS:
        out.append(([[['A1'] * 316 for _ in range(316)]], 99856 * 99856))
        out.append(([[['A1' if (r + c) % 2 == 0 else 'B2' for c in range(316)] for r in range(316)]], 49928 * 1 + 49928 * 2))
        out.append(([[['C9' if (c // 10) % 2 == 0 else 'D0' for c in range(n)]]], 5000 * 10 * 90))
        out.append(([[['Z9'] for _ in range(n)]], n * 9 * n))
        snake = [['E1' if r % 2 == 0 or (r % 4 == 1 and c == 315) or (r % 4 == 3 and c == 0) else 'F0' for c in range(316)] for r in range(316)]
        e_tiles = 158 * 316 + 158  # a single winding E region; F tiles form separate zero-crown regions
        out.append(([snake], e_tiles * e_tiles))
    elif uid == o.CPS:
        out.append(([list(range(1, n + 1))], [0] * n))
        out.append(([list(range(n, 0, -1))], [n - 1 - i for i in range(n)]))
        out.append(([[2 if i % 2 == 0 else 1 for i in range(n)]], [n - 1 - i if i % 2 == 0 else 0 for i in range(n)]))
        out.append(([[7] * n], [0] * n))
    elif uid == o.CDG:
        out.append(([[[t, t % 1000 + 1] for t in range(n - 1, -1, -1)]], [[s, s % 1000 + 10, s % 1000 + 1, s % 1000 + 1, s % 1000 + 10] for s in range(0, n, 10)]))
        sparse = [[i * 1000 + 7, (i * 7919) % 1000000000 + 1] for i in range(n)]
        out.append(([sparse[::2] + sparse[1::2]], [[t - 7, p, p, p, p] for t, p in sparse]))
    elif uid == o.CLL:
        vals = [i - 50000 for i in range(n)]
        out.append(([[[v] for v in vals], 7], [vals[i:i + 7] for i in range(0, n, 7)]))
        out.append(([[vals], n], [vals]))
        out.append(([[[] for _ in range(n - 1)] + [vals], 3], [vals[i:i + 3] for i in range(0, n, 3)]))
    elif uid == o.CRA:
        existing = [['c%d' % i, 'p%d' % i, 'R'] for i in range(n // 2)]
        new, exp = [], []
        for i in range(33333):
            new += [['c%d' % i, 'p%d' % i, 'R'], ['c%d' % i, 'q%d' % i, 'R'], ['c%d' % i, 'q%d' % i, 'S']]; exp += ['ALREADY_EXISTS', 'ROLE_TAKEN', 'VALID']
        new.append(['c0', 'q0', 'S']); exp.append('ALREADY_EXISTS')
        out.append(([existing, new], exp))
    elif uid == o.CNT:
        path = [[i, [i + 1] if i + 1 < n else []] for i in range(n)]
        out.append(([path, list(range(1, n, 2))], [[i, [i + 2] if i + 2 < n else []] for i in range(0, n, 2)]))
        out.append(([path, [0, n + 5, 10**9]], path))
        star, grand = [], []
        star.append([0, list(range(1, 301))])
        for m in range(1, 301):
            kids = [1000000 + m * 1000 + j for j in range(332)]
            star.append([m, kids]); star += [[g, []] for g in kids]; grand += kids
        out.append(([star, list(range(1, 301))], [[0, grand]] + [[g, []] for g in grand]))
    elif uid == o.CPM:
        calls, exp = [], [None]
        for i in range(1000):
            calls += [('addPoint', i, i), ('addPoint', i, i + 1)]; exp += [None, None]
        calls += [('addPoint', 10**9, 10**9), ('addPoint', 10**9, -10**9)]; exp += [None, None]
        for k in range(0, 990):
            calls.append(('getMinSteps', [0, 0], [k, k])); exp.append(2 * k)
        calls.append(('getMinSteps', [0, 0], [10**9, 10**9])); exp.append(-1)
        for k in range(48000):
            j = k % 1000
            calls += [('isConnected', [0, 0], [j, j + 1]), ('isConnected', [10**9, -10**9], [j, j])]; exp += [True, False]
        out.append((_ops('PointMatrix', [], calls), exp))
        calls, exp = [], [None]
        for j in range(50000):
            calls.append(('addPoint', 0, j * 20000 - 10**9)); exp.append(None)
        for j in range(49999):
            calls.append(('isConnected', [0, -10**9], [0, j * 20000 - 10**9])); exp.append(True)
        calls.append(('getMinSteps', [0, -10**9], [0, 49999 * 20000 - 10**9])); exp.append(1)
        out.append((_ops('PointMatrix', [], calls), exp))
    elif uid == o.CAT:
        e = [h % 10 for h in range(n)]
        out.append(([e, 4, 10, 50], n - 9))
        out.append(([e, 4, 10, 51], 0))
        out.append(([[10**9] * n, 0, n, 100], 1))
        out.append(([e, 10**9, n - 1, 0], 2))
        out.append(([e, 4, 1, 100], n // 2))
    elif uid == o.CDE:
        out.append(([[i % 1000 for i in range(n)], 5000], [1000] * (n - 5000 + 1)))
        out.append(([list(range(-50000, 50000)), 1], [1] * n))
        out.append(([list(range(-50000, 50000)), n], [n]))
        out.append(([[i // 2 for i in range(n)], 3], [2] * (n - 2)))
    elif uid == o.CDR:
        out.append(([list(range(1, n + 1))], 0))
        out.append(([[5] * n], n - 3))
        two = [1 + i // 2 for i in range(n)]
        out.append(([two], sum(1 for i, t in enumerate(two) if i - max(0, 2 * (t - 60)) >= 60)))
    elif uid == o.CIP:
        names = ['p%d' % i for i in range(n)]
        sold_price = [i if i % 3 == 2 else (float(i) if i % 3 == 1 else i + 0.5) for i in range(n)]
        out.append(([names, list(range(n)), names[::-1][::-1], sold_price], len(range(0, n, 3))))
    elif uid == o.CBD:
        out.append(([[10] * 16, [10] * 16], 16))
        out.append(([[0] * 16, [1] * 16], 1))
        perm = [(i * 5) % 16 for i in range(16)]
        out.append(([[perm[i] for i in range(16)], [perm[i] + 1 for i in range(16)]], 16))
        out.append(([[0] * 15 + [50], [50] * 15 + [0]], 3))
        out.append(([[1000000000] * 8 + [0] * 8, [0] * 8 + [1000000000] * 8], 16))
    elif uid == o.COP:
        out.append(([['*' * 316] * 316, [[r + 1] * 316 for r in range(316)]], 316))
        out.append(([['*' * 316] * 316, [[5] * 316 for _ in range(316)]], 1))
        cb = [''.join('*' if (r + c) % 2 == 0 else '_' for c in range(316)) for r in range(316)]
        out.append(([cb, [[1 if (r + c) % 2 == 0 else 0 for c in range(316)] for r in range(316)]], 49928))
        out.append(([['*' * n], [[i // 7 + 1 for i in range(n)]]], (n + 6) // 7))
    elif uid == o.CRC:
        perf = [['singer', 'r%03d' % r, '2000'] for r in range(200) for _ in range(50)]
        out.append(([perf, 0], [['r%03d' % a, 'r%03d' % b, '1'] for a in range(200) for b in range(200) if a != b]))
        perf = [['s%02d' % s, 'R%d' % r, str(1000 + 10 * r + j)] for s in range(100) for r in range(10) for j in range(10)]
        exp = sorted([['R%d' % r, 'R%d' % (r + 1), '100'] for r in range(9)] + [['R%d' % (r + 1), 'R%d' % r, '100'] for r in range(9)])
        out.append(([perf, 1], exp))
    elif uid == o.CWT:
        words = (['Apple', 'APPLE'] * 2500) + ['banana'] * 4000 + ['Cherry', 'cherry'] * 2000 + ['date'] * 2000
        out.append(([' '.join(words), 2], [['apple', 5000], ['banana', 4000], ['cherry', 4000]]))
        pairs = [a + b for a in 'abcdefghijklmnopqrstuvwxyz' for b in 'abcdefghijklmnopqrstuvwxyz']
        out.append(([' '.join(pairs * 49), 1], [[w, 49] for w in pairs]))
        out.append((['Q' * n, 3], [['q' * n, 1]]))
        out.append(([' ' * n, 1], []))
    elif uid in (o.CCF1, o.CCF2, o.CCF3):
        ts = [(n - i) // 2 for i in range(n)]
        reqs = ['%d,id%d,%d,4000%04d,m%d' % (ts[i], i, i % 1000, i % 500, i % 50) for i in range(n)]
        order = sorted(range(n), key=lambda i: (ts[i], i))
        rules = ['card_number,40000007', 'merchant,m3', 'max_amount,900', 'max_amount,950']
        reports = ['25000,id60000'] + ['%d,id%d' % (ts[i] + 30000, i) for i in range(70000, n, 500)]

        def bad(i):
            if uid == o.CCF1: return False
            ruled = i % 500 == 7 or i % 50 == 3 or i % 1000 > 900
            if uid == o.CCF2: return ruled
            return ruled or (i % 500 == 0 and ts[i] > 25000)
        args = [reqs] + ([rules] if uid != o.CCF1 else []) + ([reports] if uid == o.CCF3 else [])
        out.append((args, [['id%d' % i, 'DECLINE' if bad(i) else 'APPROVE'] for i in order]))
    return out
