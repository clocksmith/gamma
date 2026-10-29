"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from itertools import combinations
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h13a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _ncp(rng):
    n = rng.randrange(1, 13)
    edges = []
    if n > 1:
        for _ in range(rng.randrange(0, 16)):
            a, b = rng.sample(range(n), 2); edges.append([a, b])
    return [n, edges]


def _opb(rng):
    ops = []
    for _ in range(rng.randrange(0, 26)):
        if rng.random() < 0.5: ops.append([1, rng.randrange(0, 16)])
        else:
            x = rng.randrange(1, 17); ops.append([2, x, rng.randrange(1, x + 1)])
    return [ops]


def _oov(rng):
    pool = ['ann', 'bo', 'cy', 'dee', 'ed', 'fay'][:rng.randrange(1, 7)]
    calls = []
    for _ in range(rng.randrange(0, 40)):
        calls.append(('login', rng.choice(pool)) if rng.random() < 0.6 else ('getOldestOneTimeVisitor',))
    return _ops('VisitorTracker', [], calls)


def _osp(rng):
    n = rng.randrange(1, 11)
    span = rng.choice([3, 10, 10**9])
    return [[rng.randrange(-span, span + 1) for _ in range(n)]]


def _ots(rng):
    n = rng.randrange(1, 11)
    return [[rng.randrange(0, n + 1) for _ in range(n)], [rng.randrange(0, n + 1) for _ in range(n)]]


def _obs(rng):
    s = rng.randrange(1, 9)
    return [s, [rng.randrange(1, s + 1) for _ in range(rng.randrange(0, 21))]]


def _pci(rng):
    alphabet = rng.choice(['ab', 'ab#', 'aB#c ', 'xy!'])
    half = [rng.choice(alphabet) for _ in range(rng.randrange(0, 8))]
    if rng.random() < 0.5: chars = half + ([rng.choice(alphabet)] if rng.random() < 0.5 else []) + half[::-1]
    else: chars = [rng.choice(alphabet) for _ in range(rng.randrange(0, 15))]
    if rng.random() < 0.6:  # sprinkle characters that are likely ignored
        for _ in range(rng.randrange(0, 4)): chars.insert(rng.randrange(len(chars) + 1), rng.choice('#!'))
    ignore = rng.sample(list('ab#!xc '), rng.randrange(0, 4))
    if rng.random() < 0.2: ignore = ignore + ignore[:1]
    return [ignore, chars]


def _pst(rng):
    calls, sizes = [], [0]
    for _ in range(rng.randrange(0, 40)):
        v = rng.randrange(len(sizes)); r = rng.random()
        if r < 0.4: calls.append(('push', v, rng.randrange(-9, 10))); sizes.append(sizes[v] + 1)
        elif r < 0.6 and sizes[v]: calls.append(('pop', v))
        elif r < 0.8 and sizes[v]: calls.append(('peek', v))
        else: calls.append(('size', v))
    return _ops('PStack', [], calls)


def _pbc(rng):
    boards = [rng.sample(range(1, 11), rng.randrange(1, 4)) for _ in range(rng.randrange(0, 9))]
    p, q = rng.sample(range(1, 12), 2)
    return [boards, p, q]


def _peo(rng):
    n = rng.randrange(1, 16)
    ids = rng.sample(['e%d' % i for i in range(40)], n)
    names = ['Ann', 'Bo', 'Cy Lee', 'Dee', 'Ed', 'Fay Fox']
    emps = [[ids[0], ids[0], rng.choice(names)]]
    for i in range(1, n): emps.append([ids[i], ids[rng.randrange(max(0, i - rng.choice([1, 2, i])), i)], rng.choice(names)])
    rng.shuffle(emps)
    return [emps]


def _rpw(rng):
    pool = ['Ana', 'Bea', 'Cid', 'Dax', 'Eli', 'Fox', 'Gus', 'ana'][:rng.randrange(2, 9)]
    return [[rng.sample(pool, rng.randrange(1, min(6, len(pool)) + 1)) for _ in range(rng.randrange(1, 7))]]


def _rsp(rng):
    m = rng.randrange(1, 7)
    out = []
    for _ in range(rng.randrange(1, 6)):
        p = list(range(m)); rng.shuffle(p); out.append(p)
    return [out]


def _rvc(rng):
    pool = ['v1', 'v2', 'car-9', 'B_7', 'v10', 'a']
    events = []
    for _ in range(rng.randrange(0, 11)):
        src = rng.choice(pool + ['server'])
        dst = rng.choice([v for v in pool if v != src])
        events.append([src, ' '.join(rng.choice(['c1', 'c2', 'x9', 'ab']) for _ in range(rng.randrange(1, 4))), dst])
    return [events]


def _rhn(rng):
    rows = []
    for _ in range(rng.randrange(1, 6)):
        if sum(map(len, rows)) >= 10: break
        rows.append([rng.randrange(1, 5) for _ in range(rng.randrange(1, 4))])
    return [rows]


def _rmk(rng):
    n = rng.randrange(1, 11)
    big = rng.random() < 0.3
    return [[rng.randrange(0, 10**9 + 1 if big else 21) for _ in range(n)], rng.randrange(0, 31), rng.choice([1, 2, 7, 1000, 10**9 + 7])]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.NCP:
        args = [[1, []], [2, []], [2, [[0, 1]]], [5, [[0, 1], [1, 2], [3, 4]]], [4, [[0, 1], [1, 0], [0, 1]]], [6, [[0, 5]]]]
        args += [_ncp(rng) for _ in range(250)]
    elif uid == o.OPB:
        args = [[[]], [[[1, 2]]], [[[2, 3, 3]]], [[[1, 2], [2, 3, 1], [2, 3, 2], [2, 2, 2], [2, 5, 2]]], [[[1, 0], [2, 1, 1], [1, 0], [2, 4, 3]]]]
        args += [_opb(rng) for _ in range(250)]
    elif uid == o.OOV:
        args = [_ops('VisitorTracker', [], []), _ops('VisitorTracker', [], [('getOldestOneTimeVisitor',)]),
                _ops('VisitorTracker', [], [('login', 'ann'), ('login', 'bo'), ('getOldestOneTimeVisitor',), ('login', 'ann'),
                                             ('getOldestOneTimeVisitor',), ('login', 'bo'), ('getOldestOneTimeVisitor',), ('login', 'cy'),
                                             ('getOldestOneTimeVisitor',)])]
        args += [_oov(rng) for _ in range(250)]
    elif uid == o.OSP:
        args = [[[5]], [[-3]], [[3, 3, 5, 6]], [[5, -1, -3, 8]], [[-2, -1]], [[10, 1, 1, 1]], [[1, 0, 0, 0]]]
        args += [_osp(rng) for _ in range(250)]
    elif uid == o.OTS:
        args = [[[0], [0]], [[1, 1, 1], [1, 1, 1]], [[0, 0, 0], [5, 5, 5]], [[0, 1, 2], [2, 1, 0]], [[2, 0, 1, 0], [0, 1, 0, 3]]]
        args += [_ots(rng) for _ in range(250)]
    elif uid == o.OBS:
        args = [[1, []], [1, [1, 1]], [3, [3, 3, 3, 3]], [3, [1, 2, 3, 3, 2, 1]], [4, [4, 1, 2, 4, 4, 4]]]
        args += [_obs(rng) for _ in range(250)]
    elif uid == o.PCI:
        args = [[[], []], [[], ['a']], [[], list('abba')], [[], list('ab')], [['#'], list('a#b#a')], [['b'], list('ab')], [[' '], list('A a')],
                [['x'], list('xxxx')], [[], list('aA')]]
        args += [_pci(rng) for _ in range(250)]
    elif uid == o.PST:
        args = [_ops('PStack', [], []), _ops('PStack', [], [('size', 0)]),
                _ops('PStack', [], [('push', 0, 5), ('push', 1, 7), ('peek', 2), ('pop', 2), ('peek', 1), ('push', 1, 9), ('size', 3), ('pop', 3),
                                    ('push', 0, -1), ('size', 4), ('peek', 4), ('size', 2)])]
        args += [_pst(rng) for _ in range(250)]
    elif uid in o.PBC:
        args = [[[], 1, 2], [[[1, 2]], 1, 2], [[[1, 2], [2, 3]], 1, 3], [[[1, 2], [3, 4]], 1, 4], [[[1, 2, 3], [3, 4], [4, 5], [1, 5]], 2, 5],
                [[[7]], 7, 8]]
        args += [_pbc(rng) for _ in range(250)]
    elif uid == o.PSS:
        args = [[['A', '2', '3', '4', '5']], [['10', 'J', 'Q', 'K', 'A']], [['J', 'Q', 'K', 'A', '2']], [['2', '3', '4', '5', '7']], [['9', '7', '8', '6', '10']]]
        for hand in combinations(_o.CARDS, 5):
            h = list(hand); rng.shuffle(h); args.append([h])
    elif uid == o.PEO:
        args = [[[['1', '1', 'Ceo']]], [[['2', '1', 'Bo'], ['1', '1', 'Ann'], ['3', '1', 'Cy'], ['4', '2', 'Dee Lane']]],
                [[['a', 'b', 'Ann'], ['b', 'c', 'Bo'], ['c', 'c', 'Cy']]]]
        args += [_peo(rng) for _ in range(250)]
    elif uid in o.RPW:
        args = [[[['Ann']]], [[['Bo', 'Ann'], ['Ann', 'Bo']]], [[['Ann', 'Cy'], ['Ann', 'Cy'], ['Bo', 'Dee', 'Cy'], ['Bo', 'Dee', 'Cy'], ['Bo', 'Dee', 'Cy']]],
                [[['Zed', 'Amy', 'Bob', 'Cat', 'Dan']]], [[['b', 'B', 'a', 'A']]]]
        args += [_rpw(rng) for _ in range(250)]
    elif uid == o.RSP:
        args = [[[[0]]], [[[0, 1], [1, 0]]], [[[0, 1, 2], [1, 0, 2], [1, 2, 0]]], [[[2, 1, 0], [2, 0, 1], [0, 1, 2]]]]
        args += [_rsp(rng) for _ in range(250)]
    elif uid == o.RVC:
        args = [[[]], [[['server', 'c1 c2', 'v1']]], [[['server', 'c1 c2', 'v1'], ['v1', 'c1', 'v2'], ['v2', 'c1', 'v3'], ['v1', 'c2', 'v3']]],
                [[['b', 'x', 'a'], ['a', 'y', 'b']]], [[['v1', 'c1 c1 c1', 'v2'], ['v2', 'c1', 'v1'], ['v3', 'a b', 'v1']]]]
        args += [_rvc(rng) for _ in range(250)]
    elif uid == o.RHN:
        args = [[[[1]]], [[[1, 1]]], [[[1, 1], [2, 2]]], [[[3, 1, 2]]], [[[5], [5], [5]]], [[[1, 1, 1], [2], [2]]], [[[4, 4, 4], [4, 3], [3, 3]]]]
        args += [_rhn(rng) for _ in range(250)]
    elif uid == o.RMK:
        args = [[[0], 0, 1], [[7], 1, 100], [[5, 9, 3], 2, 1000], [[8, 8], 3, 1000], [[1, 2, 3], 10, 7], [[10**9], 3, 10**9 + 7]]
        args += [_rmk(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def pairs(n): return n * (n - 1) // 2


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000; rng = random.Random(13)
    if uid == o.NCP:
        out.append(([n, []], pairs(n)))
        out.append(([n, [[i, i + 1] for i in range(n - 1)]], 0))
        out.append(([n, [[2 * i + 1, 2 * i] for i in range(n // 2)]], pairs(n) - n // 2))
        out.append(([n, [[10 * b, 10 * b + j] for b in range(n // 10) for j in range(1, 10)]], pairs(n) - (n // 10) * 45))
        e = [[i, i + 2] for i in range(n - 2)]; rng.shuffle(e)
        out.append(([n, e], (n // 2) * (n // 2)))
    elif uid == o.OPB:
        m = n // 2
        out.append(([[op for i in range(m) for op in ([1, 1000 * i], [2, 1000 * i + 500, 499])]], '1' * m))
        out.append(([[op for i in range(m) for op in ([1, 1000 * i], [2, 1000 * i + 1, 1])]], '0' * m))
        out.append(([[op for i in range(m) for op in ([2, 10**9, 10**9], [1, 10**9 - 1 - i])]], '1' + '0' * (m - 1)))
        out.append(([[[1, 10**9 - 2 * i] for i in range(m)] + [[2, 10**9 - 2 * i, 1] for i in range(m)]], '1' * m))
    elif uid == o.OOV:
        V = 'VisitorTracker'; G = ('getOldestOneTimeVisitor',)
        m = 66666; calls = [('login', 'u0'), G]; exp = [None, None, 'u0']
        for i in range(1, m): calls += [('login', 'u%d' % i), ('login', 'u%d' % (i - 1)), G]; exp += [None, None, 'u%d' % i]
        out.append((_ops(V, [], calls), exp))
        calls = [('login', 'u%d' % i) for i in range(n)] + [G] * (n - 1)
        out.append((_ops(V, [], calls), [None] * (n + 1) + ['u0'] * (n - 1)))
        calls = [c for i in range(m) for c in (('login', 'u%d' % i), ('login', 'u%d' % i), G)]
        out.append((_ops(V, [], calls), [None] + [None, None, ''] * m))
        h = n // 2; calls = [('login', 'u%d' % i) for i in range(h)]; exp = [None] * (h + 1)
        for i in range(h): calls += [('login', 'u%d' % i), G]; exp += [None, 'u%d' % (i + 1) if i + 1 < h else '']
        out.append((_ops(V, [], calls), exp))
    elif uid == o.OSP:
        out.append(([list(range(n))], pairs(n)))
        out.append(([[10**9 - i for i in range(n)]], 10**9 * n - pairs(n)))
        out.append(([[10**9 - 2 * i for i in range(n)]], 10**9))
        out.append(([[-10**9] * n], -10**9))
        out.append(([[10**9 if i % 2 == 0 else -10**9 for i in range(n)]], (n // 2) * 10**9))
    elif uid == o.OTS:
        out.append(([[n - 1] * n, [n - 1] * n], n))
        out.append(([[0] * n, [0] * n], 1))
        out.append(([list(range(n)), [n - 1 - i for i in range(n)]], n))
        k = 50000
        out.append(([[k - 1] * n, [k - 1] * n], k))
        out.append(([[10**9] * n, [0] * n], 1))
    elif uid == o.OBS:
        out.append(([n, [n] * n], list(range(n))))
        out.append(([n, [1] * n], [0] * n))
        out.append(([3, [3] * n], [i % 3 for i in range(n)]))
        h = n // 2
        out.append(([h, [h] * h + [h - j for j in range(h // 2)]], list(range(h)) + list(range(h // 2))))
    elif uid == o.PCI:
        half = [chr(97 + i % 26) for i in range(n)]
        out.append(([[], half + half[::-1]], True))
        letters = [chr(65 + i % 26) for i in range(40000)]
        arr = [x for c in letters for x in (c, '#')] + [x for c in reversed(letters) for x in ('!', '!', c)]
        out.append(([['#', '!'], arr], True))
        out.append(([['#'], arr], False))
        arr = ['a'] * (2 * n); arr[n] = 'b'
        out.append(([[], arr], False))
        out.append(([['b'], arr], True))
    elif uid == o.PST:
        S = 'PStack'
        calls = [('push', i, i) for i in range(n)]; exp = [None] + list(range(1, n + 1))
        for j in range(33333):
            v = n - j; calls += [('peek', v), ('size', v), ('pop', v)]; exp += [v - 1, v, v - 1]
        out.append((_ops(S, [], calls), exp))
        calls = [('push', 0, i) for i in range(n)] + [('pop', v) for v in range(1, n + 1)]
        out.append((_ops(S, [], calls), [None] + list(range(1, n + 1)) + [0] * n))
        calls, exp = [], [None]
        for k in range(1, n + 1): calls += [('push', 0, 10**9), ('pop', k)]; exp += [k, 0]
        out.append((_ops(S, [], calls), exp))
        calls = [('push', 0, -10**9)] + [('push', 1, i) for i in range(n - 1)] + [('size', v) for v in range(1, n + 1)]
        out.append((_ops(S, [], calls), [None] + list(range(1, n + 1)) + [1] + [2] * (n - 1)))
    elif uid in o.PBC:
        one = uid == o.PBC1
        chain = [[i, i + 1] for i in range(1, n)]
        out.append(([chain, 1, n], True if one else n - 1))
        out.append(([chain, n // 2 + 1, 1], True if one else n // 2))
        out.append(([[list(range(2 * n, 0, -1))], 1, 2 * n], True if one else 1))
        split = [[i, i + 1] for i in range(1, n // 2)] + [[i, i + 1] for i in range(n // 2 + 1, n)]
        out.append(([split, 1, n - 1], False if one else -1))
        out.append(([chain, 1, 10**9], False if one else -1))
        out.append(([[[1, i + 2] for i in range(n)], 2, n + 1], True if one else 2))
    elif uid == o.PSS:
        out.append(([['10', 'J', 'Q', 'K', 'A']], True))
        out.append(([['5', '4', '3', '2', 'A']], True))
        out.append(([['Q', 'K', 'A', '2', '3']], False))
    elif uid == o.PEO:
        emps = [['c', 'c', 'Boss']] + [['e%d' % i, 'c', 'Worker'] for i in range(n - 1)]
        out.append(([emps], '\n'.join(['Boss'] + ['----Worker'] * (n - 1))))
        chain = [['c0', 'c0', 'Chain']] + [['c%d' % i, 'c%d' % (i - 1), 'Chain'] for i in range(1, 1000)]
        out.append(([chain[::-1]], '\n'.join('-' * (4 * d) + 'Chain' for d in range(1000))))
        emps = [['e%d' % i, 'c0', 'Emp'] for i in range(n - 1000)] + chain[::-1]
        out.append(([emps], '\n'.join(['Chain'] + ['----Emp'] * (n - 1000) + ['-' * (4 * d) + 'Chain' for d in range(1, 1000)])))
    elif uid in o.RPW:
        one = uid == o.RPW1
        names = ['R' + a + b for a in 'abcdefghij' for b in 'ab'][:20]
        races = [[names[(r + j) % 20] for j in range(20)] for r in range(10000)]
        out.append(([races], names[0] if one else sorted(names)))
        order = names[::-1]
        out.append(([[order] * 10000], order[0] if one else order[:3] + sorted(order[3:])))
        pad = ['Z' + a + b for a in 'abcdefghi' for b in 'ab'][:17]
        races = [(['Aa', 'Bb', 'Cc'] if r % 2 == 0 else ['Bb', 'Cc', 'Aa']) + pad for r in range(10000)]
        out.append(([races], 'Bb' if one else ['Bb', 'Aa', 'Cc'] + sorted(pad)))
    elif uid == o.RSP:
        m = 200
        out.append(([[list(range(m - 1, -1, -1))] * 1000], list(range(m - 1, -1, -1))))
        out.append(([[[(s + i) % m for s in range(m)] for i in range(1000)]], list(range(m))))
        out.append(([[list(range(m))] * 500 + [list(range(m - 1, -1, -1))] * 500], [x for s in range(m // 2) for x in (s, m - 1 - s)]))
    elif uid == o.RVC:
        ev = [['server', 'a', 'v0']] + [['v%d' % i, 'a b', 'v%d' % (i + 1)] for i in range(n - 1)]
        out.append(([ev], sorted('v%d' % i for i in range(n - 1)) + ['v%d' % (n - 1)]))
        h = n // 2
        ev = [['server', 'z', 'w%d' % i] for i in range(h)] + [['hub', 'x y z', 'w%d' % i] for i in range(h)]
        out.append(([ev], ['hub'] + sorted('w%d' % i for i in range(h))))
        out.append(([[['v1', ' '.join('c%d' % (i % 1000) for i in range(2 * n)), 'v2']]], ['v1', 'v2']))
    elif uid == o.RHN:
        h = n // 2
        out.append(([[[i + 1, i + 1] for i in range(n)]], [[2 * (r % h) + 1, 2 * (r % h) + 2] for r in range(n)]))
        out.append(([[[5, 5]] * n], []))
        out.append(([[list(range(2 * n, 0, -1))]], [list(range(1, 2 * n + 1))]))
        out.append(([[list(range(n, 0, -1)), list(range(1, n + 1))]], [list(range(1, n + 1))] * 2))
        out.append(([[[7]] * n], [[7]] * n))
    elif uid == o.RMK:
        M = 10**9 + 7
        out.append(([[10**9] * n, n, M], (5 * 10**8 * n) % M))
        out.append(([[10**9] * n, 0, M], (10**9 * n) % M))
        out.append(([[1] * n, n, M], 0))
        big = [2**29] * 1000 + [0] * (n - 1000)
        out.append(([big, 10000, M], 1000 * 2**19))
        out.append(([big, 10500, M], 500 * 2**19 + 500 * 2**18))
        out.append(([big, n, M], 0))
        out.append(([[10**9] * n, n, 1], 0))
    return out
