"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import textwrap
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h11a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _gt(rng):
    return [[rng.choice([0, 0, 1, 5, 9, rng.randrange(10)]) for _ in range(rng.randrange(3, 12))]]


def _lcm(rng):
    n = rng.randrange(1, 25); names = ['e%d' % i for i in range(n)]; rng.shuffle(names)
    reports = {x: [] for x in names}
    for i in range(1, n): reports[names[rng.randrange(max(0, i - 3) if rng.random() < 0.5 else 0, i)]].append(names[i])
    order = [names[0]] + rng.sample(names[1:], n - 1)
    return [[[x, reports[x]] for x in order], rng.choice(names), rng.choice(names)]


def _fms(rng):
    n = rng.randrange(1, 7); word = ''.join(rng.choice('aab') for _ in range(n)); sk = []
    for _ in range(rng.randrange(0, 12)):
        s = list(word)
        for i in range(n):
            r = rng.random()
            if r < 0.4: s[i] = '-'
            elif r < 0.5: s[i] = rng.choice('abc')
        sk.append(''.join(s))
    return [word, sk]


def _med(rng):
    return [[rng.choice([rng.randrange(-5, 6), rng.randrange(-10**9, 10**9 + 1)]) for _ in range(rng.randrange(1, 14))]]


def _fmo(rng):
    return [''.join(rng.choice('01') for _ in range(rng.randrange(1, 9)))]


def _mst(rng):
    games = [[str(rng.choice([0, 1, 2, 5, 9, 10, 100, 10**9])), rng.choice(['win', 'lose'])] for _ in range(rng.randrange(0, 15))]
    return [games, rng.choice([0, 0.0, 1, 1.0, 0.5, 0.25, 0.3, 2 / 3, 0.75, 0.1])]


def _fom(rng):
    return [[rng.choice([0, 1, 2, 3, 10**9]) for _ in range(rng.randrange(1, 12))]]


def _fpt(rng):
    n = rng.randrange(1, 12); s = _o.fib_size(n)
    return [n, rng.randrange(s), rng.randrange(s)]


def _mbn(rng):
    n = rng.randrange(2, 9); edges = []
    for _ in range(rng.randrange(0, 14)):
        u, v = rng.sample(range(1, n + 1), 2); edges.append([u, v, rng.choice([1, 2, 3, 5, 8, 10**9])])
    return [n, edges, rng.randrange(1, n + 2)]


def _pmw(rng):
    words = sorted({''.join(rng.choice('ab') for _ in range(rng.randrange(1, 6))) for _ in range(rng.randrange(1, 12))})
    rng.shuffle(words)
    return [words, ''.join(rng.choice('ab?..') for _ in range(rng.randrange(1, 6)))]


def _lss(rng):
    return [[rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 12, 10**9]) for _ in range(rng.randrange(1, 10))]]


def _fwp(rng):
    return [''.join(rng.choice('aezuyjtpk') for _ in range(rng.randrange(1, 10)))]


def _f2d(rng):
    vec = [[rng.randrange(-5, 6) for _ in range(rng.choice([0, 0, 1, 2, 3]))] for _ in range(rng.randrange(0, 5))]
    total = sum(map(len, vec)); left = total; calls = []
    for _ in range(rng.randrange(1, 25)):
        r = rng.random()
        if r < 0.4 and left: calls.append(('next',)); left -= 1
        elif r < 0.6: calls.append(('hasNext',))
        elif r < 0.85: calls.append(('remove',))
        else: calls.append(('getVector',))
    return _ops('Vector2D', [vec], calls)


def _fds(rng, uid):
    rs = [['r%d' % i, rng.randrange(-5, 6), rng.randrange(-5, 6)] for i in range(rng.randrange(1, 5))]
    menu = [[r[0], it, rng.choice([1, 2, 5, 10**6])] for r in rs for it in ['a', 'b', 'c'] if rng.random() < 0.6]
    rng.shuffle(menu); calls = []
    for _ in range(rng.randrange(1, 10)):
        x, y = rng.randrange(-6, 7), rng.randrange(-6, 7)
        if uid == _o.FDS2 and rng.random() < 0.5: calls.append(('getBestOrder', rng.sample(['a', 'b', 'c', 'd'], rng.randrange(1, 4)), x, y))
        else: calls.append(('getBestOption', rng.choice(['a', 'b', 'c', 'd']), x, y))
    return _ops('FoodDeliverySystem', [rs, menu], calls)


def _faw(rng):
    width = rng.randrange(1, 12)
    arts = [' '.join(rng.choice(['a', 'bb', 'ccc', 'dddd', 'x!y', '12345'])[:width] for _ in range(rng.randrange(1, 9))) for _ in range(rng.randrange(1, 4))]
    return [arts, width]


def _mov1(rng):
    n = rng.randrange(1, 9); k = rng.randrange(1, 4)
    return [['c%d' % i for i in range(n)], [[rng.choice('xyz') for _ in range(rng.randrange(0, 6))] for _ in range(n)], k]


def _mov2(rng):
    calls = []
    for _ in range(rng.randrange(1, 30)):
        c = rng.choice(['a', 'b', 'c', 'd'])
        calls.append(('watch', c, rng.choice('xyz')) if rng.random() < 0.7 else ('getFriends', c))
    return _ops('MovieFriends', [rng.randrange(1, 4)], calls)


GEN = {_o.GT: _gt, _o.LCM: _lcm, _o.FMS: _fms, _o.MED: _med, _o.FMO: _fmo, _o.MST: _mst, _o.FOM: _fom, _o.FPT: _fpt, _o.MBN: _mbn,
       _o.PMW: _pmw, _o.LSS: _lss, _o.FWP: _fwp, _o.F2D: _f2d, _o.FAW: _faw, _o.MOV1: _mov1, _o.MOV2: _mov2}

HAND = {
    _o.GT: [[[1, 2, 3]], [[0, 0, 7]], [[9, 0, 0, 0]], [[3, 9, 1, 9, 2, 9]], [[5, 4, 3, 2, 1]]],
    _o.LCM: [[[['ceo', ['a', 'b']], ['a', ['c', 'd']], ['b', []], ['c', []], ['d', ['e']], ['e', []]], 'e', 'c'],
             [[['ceo', ['a', 'b']], ['a', ['c', 'd']], ['b', []], ['c', []], ['d', ['e']], ['e', []]], 'e', 'b'],
             [[['ceo', ['a']], ['a', []]], 'a', 'a'], [[['solo', []]], 'solo', 'solo']],
    _o.FMS: [['hello', ['he--o', 'he-lo', '-ello', 'h-l-o', 'hello', 'hell-', '-----', 'hexlo']], ['a', ['-', 'a', 'b']], ['ab', []]],
    _o.MED: [[[3, 1, 2]], [[4, 1, 3, 2]], [[1, 2]], [[-3, -4]], [[7]], [[5, 5, 5, 5]], [[10**9, -10**9]]],
    _o.FMO: [['0'], ['01'], ['0011'], ['0110'], ['10110'], ['00101101']],
    _o.MST: [[[['10', 'lose'], ['20', 'win'], ['30', 'lose'], ['5', 'win']], 0.5], [[], 0.5], [[['1', 'win']], 0.0], [[['1', 'win']], 0.01],
             [[['3', 'lose'], ['3', 'win'], ['1', 'win']], 0.5]],
    _o.FOM: [[[1, 2, 3, 2, 1]], [[3, 1, 3]], [[0]], [[0, 0, 4, 0, 4]]],
    _o.FPT: [[1, 0, 0], [3, 1, 3], [3, 3, 1], [4, 2, 6], [5, 0, 11]],
    _o.MBN: [[3, [[1, 2, 5], [2, 3, 1], [1, 3, 10]], 2], [3, [[1, 2, 5], [2, 3, 1], [1, 3, 10]], 1], [4, [[1, 2, 1]], 3], [2, [[1, 2, 7], [2, 1, 3]], 1]],
    _o.PMW: [[['cat', 'cart', 'ct', 'coat', 'cats'], 'c.t'], [['ab', 'a', 'abc'], '??'], [['abc', 'aXc'.lower()], 'a?c'], [['aa', 'aaa'], '..']],
    _o.LSS: [[[16, 17, 71, 62, 12, 24, 14]], [[8, 8]], [[1, 2, 4]], [[7]]],
    _o.FWP: [['leet'], ['code'], ['zdz'], ['a'], ['zz'], ['uz']],
    _o.FAW: [[['the quick brown fox', 'jumps over'], 10], [['a b c d'], 1], [['hello'], 5], [['aa bb cc', 'dd'], 5]],
    _o.MOV1: [[['u1', 'u2', 'u3', 'u4'], [['a', 'b', 'c'], ['x', 'c', 'b'], ['c', 'b'], ['b', 'b']], 2], [['u1', 'u2'], [['a'], ['a']], 2],
              [['p', 'q', 'r'], [['a', 'a', 'b'], ['b', 'a'], ['a', 'b', 'b']], 3]],
}
HAND_TRACE = {
    _o.F2D: [_ops('Vector2D', [[[1, 2], [3], [], [4]]], [('remove',), ('next',), ('next',), ('remove',), ('remove',), ('getVector',), ('next',), ('next',), ('remove',),
                                                         ('hasNext',), ('getVector',)]),
             _ops('Vector2D', [[]], [('hasNext',), ('getVector',), ('remove',)])],
    _o.FDS1: [_ops('FoodDeliverySystem', [[['r1', 0, 0], ['r2', 10, 10]], [['r1', 'pizza', 12], ['r2', 'pizza', 8], ['r2', 'soup', 5]]],
                   [('getBestOption', 'pizza', 1, 1), ('getBestOption', 'soup', 0, 0), ('getBestOption', 'tea', 0, 0)])],
    _o.FDS2: [_ops('FoodDeliverySystem', [[['r1', 0, 0], ['r2', 10, 10]], [['r1', 'pizza', 12], ['r2', 'pizza', 8], ['r2', 'soup', 5]]],
                   [('getBestOption', 'pizza', 1, 1), ('getBestOrder', ['pizza', 'soup'], 0, 0), ('getBestOrder', ['pizza'], 9, 9), ('getBestOrder', ['tea'], 0, 0)])],
    _o.MOV2: [_ops('MovieFriends', [2], [('watch', 'a', 'x'), ('getFriends', 'a'), ('watch', 'a', 'y'), ('watch', 'b', 'y'), ('watch', 'b', 'x'), ('getFriends', 'a'),
                                         ('watch', 'c', 'x'), ('watch', 'c', 'x'), ('watch', 'a', 'x'), ('getFriends', 'b'), ('getFriends', 'z')])],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o
    args = list(HAND.get(uid, [])) + list(HAND_TRACE.get(uid, []))
    if uid in (o.FDS1, o.FDS2): args += [_fds(rng, uid) for _ in range(250)]
    else: args += [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.GT:
        out += [([[9] * 50], 999), ([[0] * 49 + [7]], 7), ([list(range(10)) * 5], 999), ([[i % 9 for i in range(50, 0, -1)]], 888)]
    elif uid == o.LCM:
        chain = [['e%d' % i, ['e%d' % (i + 1)] if i + 1 < n else []] for i in range(n)]
        out.append(([chain, 'e99999', 'e50000'], 'e50000'))
        out.append(([chain, 'e99999', 'e99999'], 'e99999'))
        star = [['boss', ['w%d' % i for i in range(n - 1)]]] + [['w%d' % i, []] for i in range(n - 1)]
        out.append(([star, 'w5', 'w99997'], 'boss'))
    elif uid == o.FMS:
        word = ('abcde' * 20)
        sk = []
        for i in range(10000):
            s = list(word)
            if i % 3 == 0:
                for j in range(i % 5, 100, 5): s[j] = '-'      # hides one letter everywhere: match
            elif i % 3 == 1:
                s[i % 100] = '-'; s[(i + 1) % 100] = '-'          # hides two different letters: no match
            else:
                s[i % 100] = 'z'                                  # mismatch
            sk.append(''.join(s))
        out.append(([word, sk], [s for i, s in enumerate(sk) if i % 3 == 0]))
    elif uid == o.MED:
        vals = list(range(-100000, 100000)); random.Random(3).shuffle(vals)
        out.append(([vals], -0.5))
        vals = [5] * 99999 + [-10**9] * 50000 + [10**9] * 50000; random.Random(4).shuffle(vals)
        out.append(([vals], 5))
        out.append(([[10**9 - (i % 2) for i in range(200000)]], 999999999.5))
        out.append(([list(range(199999, 0, -1))], 100000))
    elif uid == o.FMO:
        out += [(['0' * n + '1' * n], n), (['0110' * 50000], 0), (['1' + '0' * (2 * n - 1)], 1)]
    elif uid == o.MST:
        games = [[str(i), 'lose' if i >= 50000 else 'win'] for i in range(n)]
        out += [([games, 0.75], 33334), ([games, 0.5], 0), ([games, 1], 50000), ([[[str(10**9), 'win']] * n, 0.5], -1)]
    elif uid == o.FOM:
        out += [([[10**9] * n], 10**9), ([[0 if i % 2 else 10**9 for i in range(n)]], 50000 * 10**9), ([list(range(n))], n - 1)]
    elif uid == o.FPT:
        s = o.fib_size(75)
        out += [([75, s - 1, 0], 'U' * 74), ([75, 1, s - 1], 'U' + 'R' * 74), ([75, 0, 0], ''), ([75, s - 1, s - 2], 'U')]
    elif uid == o.MBN:
        m = 20000
        edges = [[i, i + 1, i] for i in range(1, m)] + [[1, m, 10**9]]
        noise = random.Random(5)
        edges += [[a, b, 10**9] for a, b in (noise.sample(range(1, m + 1), 2) for _ in range(29999))]
        out += [([m, edges, m - 1], m - 1), ([m, edges, m - 2], 10**9), ([m, [[i, i + 1, 7] for i in range(1, m)], m - 2], -1)]
    elif uid == o.PMW:
        words = [format(i * 1000003 % (1 << 30), '030b').replace('0', 'a').replace('1', 'b') for i in range(1000)]
        assert len(set(words)) == 1000
        pat = 'a' + '.?' * 14 + 'b'
        out.append(([words, pat], [w for w in words if w[0] == 'a' and w[-1] == 'b']))
        out.append(([words, '.' * 30], words))
        out.append(([words, '.' * 15 + 'a' * 14], [w for w in words if w.endswith('a' * 14)]))
    elif uid == o.LSS:
        out += [([[1 << (i % 30) for i in range(n)]], 3334), ([[10**9] * n], n), ([[(1 << 29) - 1] * 3 + [1 << 29] * (n - 3)], n - 3)]
    elif uid == o.FWP:
        word = 'ze' * 10000
        out.append(([word], 'DDDDD!' + 'UUUUURRRR!LLLLDDDDD!' * 9999 + 'UUUUURRRR!'))
        out.append(([('y' * 20000)], 'DDDDRRRR!' + '!' * 19999))
    elif uid == o.FAW:
        arts = [' '.join(['word%d' % (j % 10) for j in range(40)]) for _ in range(800)]
        exp = []
        for i, a in enumerate(arts):
            if i: exp.append('')
            exp += textwrap.wrap(a, 23, break_long_words=False, break_on_hyphens=False)
        out.append(([arts, 23], exp))
        out.append(([[' '.join('x' * 1000 for _ in range(190))], 1000], ['x' * 1000] * 190))
    elif uid == o.MOV1:
        ids = ['c%d' % i for i in range(10000)]
        movies = [[] if i % 7 == 0 else ['m%d' % ((i % 50) + j) for j in range(20)] for i in range(10000)]
        groups = {}
        for i in range(10000):
            if i % 7: groups.setdefault(i % 50, []).append(ids[i])
        out.append(([ids, movies, 10], list(groups.values())))
    elif uid == o.F2D:
        vec = [[r * 100 + c for c in range(100)] for r in range(1000)]
        calls = []
        for i in range(49998): calls += [('next',), ('remove',) if i % 2 == 0 else ('hasNext',)]
        calls += [('getVector',), ('hasNext',)]
        exp = [None]
        for i in range(49998): exp += [i, True]
        snap = [[v for v in row if not (v < 49998 and v % 2 == 0)] for row in vec]
        out.append((_ops('Vector2D', [vec], calls), exp + [snap, True]))
        vec = [[] if r % 100 else list(range(r * 10, r * 10 + 1000)) for r in range(10000)]
        flat = [v for row in vec for v in row]
        calls = [('next',)] * 99979 + [('remove',)] + [('getVector',)] * 19
        out.append((_ops('Vector2D', [vec], calls), [None] + flat[:99979] + [True] + [[[v for v in row if v != flat[99978]] for row in vec]] * 19))
    elif uid in (o.FDS1, o.FDS2):
        rs = [['r%d' % i, i, -i] for i in range(200)]
        menu = [['r%d' % i, 'it%d' % j, (7 * i + j) % 1000 + 1] for j in range(100) for i in range(200)]
        best = [min((7 * i + j) % 1000 + 1 for i in range(200)) for j in range(100)]
        fixed = min(sum((7 * i + d) % 1000 + 1 for d in range(10)) for i in range(200))
        calls, exp = [], [None]
        for t in range(20000):
            j = t * 37 % 101
            if uid == o.FDS2 and t % 2:
                items = ['it%d' % ((t + d) % 100) for d in range(10)]
                if t < 200: tot = min(sum((7 * i + (t + d) % 100) % 1000 + 1 for d in range(10)) for i in range(200))
                else: items = ['it%d' % d for d in range(10)]; tot = fixed
                calls.append(('getBestOrder', items, 0, 0)); exp.append([tot, 0])
            else:
                calls.append(('getBestOption', 'it%d' % j, 300, -300)); exp.append([best[j], 2 * (300 - 199)] if j < 100 else [-1, -1])
        out.append((_ops('FoodDeliverySystem', [rs, menu], calls), exp))
    elif uid == o.MOV2:
        calls = [('watch', 'c%04d' % c, 'm%d' % (j + c % 3)) for j in range(49) for c in range(1000)]
        calls += [('getFriends', 'c%04d' % c) for c in range(1000)]
        exp = [None] * 49001 + [['c%04d' % d for d in range(1000) if d % 3 == c % 3 and d != c] for c in range(1000)]
        out.append((_ops('MovieFriends', [40], calls), exp))
    return out
