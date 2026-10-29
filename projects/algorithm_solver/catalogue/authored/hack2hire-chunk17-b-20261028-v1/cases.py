"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h17b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width, base=97):
    s = ''
    for _ in range(width): s = chr(base + i % 26) + s; i //= 26
    return s


def _urd(rng):
    def path(wild):
        segs = [('*' if wild and rng.random() < 0.4 else rng.choice(['a', 'b', 'c1'])) for _ in range(rng.randrange(0, 4))]
        return '/' + '/'.join(segs)
    calls = []
    for _ in range(rng.randrange(0, 30)):
        if rng.random() < 0.45: calls.append(('addRoute', path(True), 'h' + str(rng.randrange(10))))
        else: calls.append(('callRoute', path(False)))
    return _ops('Router', [], calls)


def _une(rng):
    n = rng.randrange(1, 13)
    return [[rng.randrange(1, 4) for _ in range(n)], rng.randrange(0, min(n, 4) + 1)]


def _wcm(rng):
    s = ''.join(rng.choice('ab') for _ in range(rng.randrange(0, 11)))
    if rng.random() < 0.5 and s:
        p = list(s)
        for _ in range(rng.randrange(1, 4)):
            i = rng.randrange(len(p) + 1); j = rng.randrange(i, min(len(p), i + 3) + 1); p[i:j] = ['*']
        if rng.random() < 0.3 and p: p[rng.randrange(len(p))] = rng.choice('ab*')
        p = ''.join(p)
    else:
        p = ''.join(rng.choice('ab**') for _ in range(rng.randrange(0, 8)))
    return [s, p]


def _wpm(rng):
    pattern = ''.join(rng.choice('abc') for _ in range(rng.randrange(1, 7)))
    words = [''.join(rng.choice('xyz') for _ in range(max(0, len(pattern) + rng.choice([-1, 0, 0, 0, 1])))) for _ in range(rng.randrange(0, 9))]
    return [pattern, words]


def _wdb(rng):
    return _ops('DiskBlockManager', [rng.randrange(1, 6), rng.randrange(1, 5)], [('write',)] * rng.randrange(0, 26))


def _aba(rng):
    n = rng.randrange(1, 7); calls = []
    for _ in range(rng.randrange(0, 25)):
        if rng.random() < 0.6: calls.append(('attack', rng.randrange(-2, n + 2)))
        else: calls.append(('isDestroyed',))
    return _ops('AlienBaseAttack', [n], calls)


def _ags(rng):
    n = rng.randrange(1, 9)
    state = [rng.choice('001') for _ in range(n)]
    if '1' not in state: state[rng.randrange(n)] = '1'
    return [[rng.randrange(1, 20) for _ in range(n)], ''.join(state), rng.randrange(1, 11)]


def _bsd(rng):
    n = rng.randrange(1, 9)
    return [[rng.randrange(1, 11) for _ in range(n)], [rng.randrange(1, 21) for _ in range(n)], rng.randrange(1, 7)]


def _crt(rng):
    return [[rng.randrange(-3, 4) for _ in range(rng.randrange(0, 13))]]


def _cdt(rng):
    def day(d):
        return [['2024-01-%02d' % d, rng.choice(['u0', 'u1', 'u2', 'u_3', 'u4']), rng.choice(['buy', 'sell', 'gift']), str(rng.randrange(1, 500))]
                for _ in range(rng.randrange(0, 9))]
    return _ops('PurchaseAnalyzer', [day(1), day(2)], [('crossDayDiverseUsers',)] * rng.randrange(0, 4))


def _expr(rng, depth):
    if depth == 0 or rng.random() < 0.35: return str(rng.randrange(-9, 10))
    parts = [rng.choice(['add', 'mul'])] + [_expr(rng, depth - 1) for _ in range(rng.randrange(2, 4))]
    left = rng.choice(['(', '( ']); right = rng.choice([')', ' )'])
    return left + rng.choice([' ', '  ']).join(parts) + right


def _ese(rng):
    return [_expr(rng, rng.randrange(0, 4))]


def _ffe(rng):
    logs = [[rng.choice(['u0', 'u1', 'u2']), rng.randrange(0, 200001), rng.choice(['a', 'b', 'c_d'])] for _ in range(rng.randrange(0, 13))]
    if logs and rng.random() < 0.4:
        u, t, e = rng.choice(logs); logs.append([u, t + rng.choice([0, 1, 86399, 86400]), e])
    return [logs, rng.randrange(1, 4)]


def _lpd(rng):
    pool = rng.sample(['A', 'B', 'AB', 'C', 'BA', 'D', 'E', 'Z'], rng.randrange(2, 8))
    edges = [[pool[i], pool[j]] for i in range(len(pool)) for j in range(i + 1, len(pool)) if rng.random() < 0.35]
    rng.shuffle(edges)
    return [edges[:20]]


def _fpe(rng):
    out = []
    for _ in range(rng.randrange(1, 11)):
        e = rng.randrange(0, 21); out.append([e, e + rng.randrange(1, 11)])
    return [out]


def _frs(rng):
    return [''.join(rng.choice('abez') for _ in range(rng.randrange(1, 16))), rng.randrange(-3, 4), rng.randrange(-3, 4)]


def _got(rng):
    n = rng.randrange(1, 13); t = []
    for _ in range(rng.randrange(0, 9)):
        e = rng.randrange(n); t.append([e, rng.randrange(e, n)])
    return [n, t]


GEN = {_o.URD: _urd, _o.UNE: _une, _o.WCM: _wcm, _o.WPM: _wpm, _o.WDB: _wdb, _o.ABA: _aba, _o.AGS: _ags, _o.BSD: _bsd, _o.CRT: _crt, _o.CDT: _cdt,
       _o.ESE: _ese, _o.FFE: _ffe, _o.LPD: _lpd, _o.FPE: _fpe, _o.FRS: _frs, _o.GOT: _got}

HAND = {
    _o.URD: [_ops('Router', [], [('addRoute', '/users/*', 'anyUser'), ('addRoute', '/users/me', 'me'), ('addRoute', '/*/*', 'pair'), ('callRoute', '/users/me'),
                                 ('callRoute', '/users/42'), ('callRoute', '/posts/7'), ('callRoute', '/users'), ('addRoute', '/', 'root'), ('callRoute', '/'),
                                 ('addRoute', '/*/me', 'anyMe'), ('addRoute', '/users/me', 'me2'), ('callRoute', '/users/me'), ('callRoute', '/x/me')]),
             _ops('Router', [], [('addRoute', '/*/b/*', 'x'), ('addRoute', '/a/*/*', 'y'), ('callRoute', '/a/b/c'), ('callRoute', '/q/b/c')])],
    _o.UNE: [[[1, 2, 1, 1, 3], 2], [[1, 2, 3, 4, 5, 1], 0], [[7], 0], [[1, 2, 1, 2, 1], 1], [[5, 5, 5], 3]],
    _o.WCM: [['', ''], ['', '*'], ['a', ''], ['aa', 'a'], ['aa', '*'], ['abcd', 'a*d'], ['abcd', 'a*c'], ['abab', '*ab'], ['aab', '*a*b*'], ['ab', 'ab*b']],
    _o.WPM: [['abba', ['dogg', 'xyyx', 'xyzx', 'xxxx', 'xyy']], ['a', ['', 'z', 'zz']], ['abc', ['xyz', 'xyx', 'cab']]],
    _o.WDB: [_ops('DiskBlockManager', [3, 2], [('write',)] * 8), _ops('DiskBlockManager', [1, 1], [('write',), ('write',)])],
    _o.ABA: [_ops('AlienBaseAttack', [3], [('isDestroyed',), ('attack', 0), ('attack', 2), ('isDestroyed',), ('attack', 3), ('attack', -1), ('isDestroyed',),
                                          ('attack', 1), ('isDestroyed',), ('attack', 1), ('isDestroyed',)])],
    _o.AGS: [[[5, 1, 9, 2], '1000', 4], [[5, 1, 9, 2], '0010', 3], [[3, 8], '01', 2], [[4], '1', 1]],
    _o.BSD: [[[3, 1], [2, 2], 1], [[1], [5], 2], [[1, 2, 3], [3, 3, 3], 3], [[2, 5], [4, 1], 2]],
    _o.CRT: [[[]], [[3, 2, 1]], [[5, 4, 4, 3]], [[1, 2, 3]], [[4, 3, 2, 1]]],
    _o.CDT: [_ops('PurchaseAnalyzer', [[['2024-03-01', 'ann', 'buy', '10'], ['2024-03-01', 'bob', 'buy', '5'], ['2024-03-01', 'cy', 'buy', '1']],
                                       [['2024-03-02', 'bob', 'sell', '7.5'], ['2024-03-02', 'ann', 'buy', '3'], ['2024-03-02', 'dee', 'gift', '2']]],
                  [('crossDayDiverseUsers',), ('crossDayDiverseUsers',)])],
    _o.ESE: [['7'], ['-12'], ['(add 1 2)'], ['(mul 2 (add 1 2) 4)'], ['( add  (mul -3 4)(add 1 1) )'], ['(mul 0 -5)']],
    _o.FFE: [[[['u1', 0, 'login'], ['u1', 86399, 'login'], ['u2', 5, 'pay'], ['u3', 6, 'pay'], ['u1', 86400, 'pay'], ['u1', 1, 'pay']], 2], [[], 1]],
    _o.LPD: [[[]], [[['A', 'B'], ['B', 'C'], ['A', 'C']]], [[['X', 'Y'], ['A', 'B']]], [[['B', 'C'], ['A', 'C'], ['C', 'D']]]],
    _o.FPE: [[[[1, 4], [2, 5], [4, 6]]], [[[0, 1], [1, 2]]], [[[5, 9], [0, 3], [6, 7], [2, 4]]]],
    _o.FRS: [['abc', 1, 1], ['ab', 2, 0], ['aeb', 2, 0], ['zz', 0, 1]],
    _o.GOT: [[5, [[0, 2], [1, 1], [4, 4]]], [3, []], [1, [[0, 0], [0, 0]]]],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = list(HAND[uid]) + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.URD:
        lit = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        calls, want = [], [None]
        for mask in range(256):
            calls.append(('addRoute', '/' + '/'.join('*' if mask >> i & 1 else lit[i] for i in range(8)), 'h%d' % mask)); want.append(None)
        for q in range(9700):
            mask = (q * 37) % 256
            calls.append(('callRoute', '/' + '/'.join('z' if mask >> i & 1 else lit[i] for i in range(8)))); want.append('h%d' % mask)
        out.append((_ops('Router', [], calls), want))
        # every 7-segment prefix pattern ends in a segment that never matches, so each query reaches the all-wildcard route last
        calls, want = [], [None]
        for mask in range(128):
            calls.append(('addRoute', '/' + '/'.join('*' if mask >> i & 1 else lit[i] for i in range(7)) + '/q', 'p%d' % mask)); want.append(None)
        calls.append(('addRoute', '/*/*/*/*/*/*/*/*', 'last')); want.append(None)
        for _ in range(9800): calls.append(('callRoute', '/a/b/c/d/e/f/g/h')); want.append('last')
        out.append((_ops('Router', [], calls), want))
        calls, want = [('addRoute', '/', 'root')], [None, None]
        for i in range(4999): calls.append(('addRoute', '/v1/' + _code(i, 3) + '/x', 'r' + _code(i, 3))); want.append(None)
        for i in range(4999): calls.append(('callRoute', '/v1/' + _code(4998 - i, 3) + '/x')); want.append('r' + _code(4998 - i, 3))
        calls.append(('callRoute', '/')); want.append('root')
        out.append((_ops('Router', [], calls), want))
    elif uid == o.UNE:
        out.append(([[7] * 5000, 50], 5000))
        out.append(([[1] * 2500 + [2] * 2500, 0], 2500))
        out.append(([[1] * 2500 + [2] * 2500, 1], 5000))
        out.append(([[v for v in range(1, 101) for _ in range(50)], 50], 2550))
        out.append(([[10**9 - i for i in range(5000)], 50], 51))
        out.append(([[10**9 - i for i in range(5000)], 0], 1))
    elif uid == o.WCM:
        out.append((['a' * 2000, '*' * 2000], True))
        out.append((['a' * 2000, '*' + 'a' * 999 + 'b'], False))
        out.append((['ab' * 1000, '*' + '*'.join(['ab'] * 666) + '*'], True))
        out.append((['a' * 1999 + 'b', '*' + 'a' * 998 + 'b'], True))
        out.append((['a' * 2000, 'a' * 2000], True))
        out.append((['a' * 2000, 'a' * 1999 + 'b'], False))
        out.append((['a' * 2000, ('a' * 99 + 'b*') * 19 + 'a'], False))
        out.append((['ab' * 1000, 'a*' * 1000], True))
        out.append((['ab' * 1000, '*a' * 998 + '*aa'], False))
        out.append((['ab' * 1000, 'a*' * 999 + 'b'], True))
    elif uid == o.WPM:
        out.append((['ab' * 500, ['cd' * 500] * 100 + ['cc' * 500] * 50 + ['cd' * 499 + 'ce'] * 50], [True] * 100 + [False] * 100))
        pat = 'abcdefghijklmnopqrst'
        words = [''.join(chr(97 + (ord(c) - 97 + s) % 26) for c in pat) for s in range(10000)]
        out.append(([pat, words], [True] * 10000))
        out.append(([pat, [w[:-1] + w[0] for w in words]], [False] * 10000))
    elif uid == o.WDB:
        out.append((_ops('DiskBlockManager', [n, 10**9], [('write',)] * n), [None] + [0] * n))
        out.append((_ops('DiskBlockManager', [n, 1], [('write',)] * n), [None] + list(range(n))))
        out.append((_ops('DiskBlockManager', [1, 50000], [('write',)] * n), [None] + [0] * 50000 + [-1] * 50000))
        out.append((_ops('DiskBlockManager', [3, 1], [('write',)] * n), [None, 0, 1, 2] + [-1] * (n - 3)))
    elif uid == o.ABA:
        calls, want = [], [None]
        for i in range(n - 1): calls.append(('attack', i - 50000)); want.append(None)
        calls.append(('isDestroyed',)); want.append(False)
        out.append((_ops('AlienBaseAttack', [10**9], calls), want))
        m = 49000; calls, want = [], [None]
        for i in range(m):
            calls.append(('attack', m - 1 - i)); want.append(None)
            if i % 1000 == 999: calls.append(('isDestroyed',)); want.append(i == m - 1)
        for i in range(1000): calls += [('attack', 10**9 - i), ('isDestroyed',)]; want += [None, True]
        out.append((_ops('AlienBaseAttack', [m], calls), want))
        calls, want = [], [None]
        for i in range(50000): calls += [('attack', 1), ('isDestroyed',)]; want += [None, False]
        out.append((_ops('AlienBaseAttack', [2], calls), want))
    elif uid == o.AGS:
        out.append(([list(range(1, n + 1)), '1' + '0' * (n - 1), n], list(range(1, n + 1))))
        arr = [(i * 7919) % 1000003 + 1 for i in range(n)]
        out.append(([arr, '1' * n, n], [max(arr)] * n))
        out.append(([[10**9] * (n - 1) + [1], '0' * (n - 1) + '1', n], [1] * n))
        out.append(([[10**9 - i for i in range(n)], '0' * (n // 2) + '1' + '0' * (n - n // 2 - 1), 5], [10**9 - n // 2] * 5))
    elif uid == o.BSD:
        m = 50000
        out.append(([[1] * m, [10**4] * m, 1], 10**4 * m * (m + 1) // 2))
        out.append(([[100] * m, [10**4] * m, 1], 100 * 10**4 * m * (m + 1) // 2))
        req = [i % 100 + 1 for i in range(m)]
        desc = sorted(req, reverse=True)
        out.append(([req, [10**4] * m, 10**4], sum(r * (j + 1) for j, r in enumerate(desc))))
        # two job kinds with equal ratio (t / r = 100): any order gives the same total
        req = [1 if i % 2 else 100 for i in range(m)]; health = [100 if i % 2 else 10**4 for i in range(m)]
        out.append(([req, health, 1], None))
    elif uid == o.CRT:
        out.append(([list(range(n, 0, -1))], n * (n - 1) * (n - 2) // 6))
        out.append(([list(range(n))], 0))
        out.append(([[5] * n], 0))
        m = n // 2
        out.append(([[10**9 - i // 2 for i in range(n)]], m * (m - 1) * (m - 2) // 6 * 8))
    elif uid == o.CDT:
        d1 = [['2024-05-01', 'u' + str(i), 'a', '1.5'] for i in range(n)]
        d2 = [['2024-05-02', 'u' + str(i), 'b' if i % 2 == 0 else 'a', '2'] for i in range(n)]
        users = sorted('u' + str(i) for i in range(0, n, 2))
        out.append((_ops('PurchaseAnalyzer', [d1, d2], [('crossDayDiverseUsers',)] * 3), [None, users, users, users]))
        d2 = [['2024-05-02', 'v' + str(i), 'b', '2'] for i in range(n)]
        out.append((_ops('PurchaseAnalyzer', [d1, d2], [('crossDayDiverseUsers',)] * 100), [None] + [[]] * 100))
    elif uid == o.ESE:
        d = 14000
        out.append((['(add 1' * d + ' 1' + ')' * d], d + 1))
        out.append((['(add ' + ' '.join(['1000000000'] * 9000) + ')'], 9 * 10**12))
        out.append((['(mul' + ' 2' * 52 + ')'], 2**52))
        # 12000 calls: the innermost gives 5 and each of the other 11999 multiplies by -1
        out.append((['(mul -1(mul -1' * 6000 + ' 5 -1' + ')' * 12000], -5))
        out.append((['(mul 1 (add 0 ' * 5000 + ' 3 4' + ')' * 10000], 7))
    elif uid == o.FFE:
        logs = [['u1', 2 * i, 'aa'] for i in range(33333)] + [['u1', 3 * i, 'bb'] for i in range(33333)] + [['u2', 3 * i, 'cc'] for i in range(33333)]
        out.append(([logs[::-1], 28801], ['aa']))
        types = ['t' + _code(i, 2) for i in range(10)]
        out.append(([[['x' + str(i), i, types[i % 10]] for i in range(n)], 1], sorted(types)))
        logs = []
        for i in range(50000): logs += [['p' + str(i), 10 * i, 'e'], ['p' + str(i), 10 * i + 86400, 'e']]
        out.append(([logs, 2], []))
        logs = [list(r) for r in logs]
        logs[-1] = ['p49999', 499990 + 86399, 'f']; logs[-3] = ['p49998', 499980 + 86399, 'e']
        out.append(([logs, 2], ['e']))
    elif uid == o.LPD:
        names = [_code(i, 4, 65) for i in range(10001)]
        out.append(([[[names[i], names[i + 1]] for i in range(10000)][::-1]], names))
        b = ['B' + _code(i, 4, 65) for i in range(5001)]; a = ['A' + _code(i, 4, 65) for i in range(5001)]
        # both longest paths have 5000 edges; 'A' sorts before 'BAAAA'
        edges = [[b[i], b[i + 1]] for i in range(5000)] + [[a[i], a[i + 1]] for i in range(4999)] + [['A', a[0]]]
        out.append(([edges], ['A'] + a[:5000]))
        edges = [[b[i], b[i + 1]] for i in range(5000)] + [[a[i], a[i + 1]] for i in range(5000)]
        out.append(([edges], a))
        out.append(([[['ROOT', names[9999 - i]] for i in range(10000)]], ['ROOT', names[0]]))
    elif uid == o.FPE:
        out.append(([[[0, 10**9]] * n], 0))
        out.append(([[[i, 200000 - i] for i in range(n)]], n - 1))
        out.append(([[[i, i + 1] for i in range(n)]], 0))
        out.append(([[[2 * i, 2 * i + 2] for i in range(n - 1)] + [[500, 501]]], 500))
    elif uid == o.FRS:
        out.append((['a' * n, 1, 0], n * (n + 1) // 2))
        out.append((['ab' * (n // 2), 2, 0], 2500000000))
        out.append((['b' * n, 0, 0], 0))
        out.append((['z' * n, 10**5, 10**5], 0))
    elif uid == o.GOT:
        out.append(([n, [[0, n - 1]] * n], [n] * n))
        out.append(([n, [[i, i] for i in range(n)]], [1] * n))
        out.append(([n, [[i, n - 1] for i in range(n)]], list(range(1, n + 1))))
    if uid == o.BSD:
        # fill the equal-ratio total: jobs (t=1e4, r=100) and (t=100, r=1); every order gives the same total, take kinds in input order
        a, w = out[-1]; total = elapsed = 0
        for r, h in zip(a[0], a[1]): elapsed += h; total += r * elapsed
        out[-1] = (a, total)
    return out
