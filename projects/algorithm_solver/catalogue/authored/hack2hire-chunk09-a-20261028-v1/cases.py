"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h09a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _vps(rng):
    n = rng.randrange(1, 7)
    if rng.random() < 0.5:  # a genuine shuffle window, sometimes perturbed
        seq = []
        for _ in range(rng.randrange(1, 5)):
            cyc = list(range(1, n + 1)); rng.shuffle(cyc); seq += cyc
        a = rng.randrange(0, len(seq)); seq = seq[a:a + rng.randrange(0, 3 * n + 1)]
        if seq and rng.random() < 0.4: seq[rng.randrange(len(seq))] = rng.randrange(1, n + 1)
    else:
        seq = [rng.randrange(1, n + 1) for _ in range(rng.randrange(0, 12))]
    return [n, seq]


def _wak(rng):
    n = rng.randrange(1, 14); w = rng.randrange(1, n + 1)
    vals = rng.choice([[-3, -1, 0, 2, 5], [1, 1, 2], [-10**9, 10**9, 7, -7], list(range(-20, 21))])
    return [[rng.choice(vals) for _ in range(n)], w, rng.randrange(0, w)]


def _tok(rng, uid):
    plans = ['basic', 'Pro', 'T_1'][:rng.randrange(1, 4)]
    pricing = []
    for p in plans:
        f = [p, str(rng.choice([0, 1, 2, 5, 1000])), str(rng.choice([0, 1, 3, 1000]))]
        if uid != _o.TOK1: f += [str(rng.choice([0, 9, 1000000])), str(rng.choice([0, 1, 50, 300, 1000000000]))]
        if uid == _o.TOK3: f.append(str(rng.choice([0, 100, 999, 5000, 10**12])))
        pricing.append(','.join(f))
    rng.shuffle(pricing)
    sessions = ['%s,%d,%d,%s' % (rng.choice(['a', 'b', 'u_1', 'zz9']), rng.choice([0, 1, 40, 100, 1000000]), rng.choice([0, 7, 60, 250]), rng.choice(plans))
                for _ in range(rng.randrange(0, 10))]
    return [sessions, pricing]


def _api(rng):
    segs = ['a', 'b', 'v1', 'x9']; calls = []
    for _ in range(rng.randrange(1, 20)):
        d = rng.randrange(0, 4)
        path = '/' if d == 0 else ''.join('/' + rng.choice(segs) for _ in range(d))
        if rng.random() < 0.45: calls.append(('registerPath', path, rng.choice(['h1', 'h2', 'H_3', 'root'])))
        else: calls.append(('matchPath', path))
    return _ops('APIMatchingSystem', [], calls)


def _ard(rng, uid):
    n = rng.randrange(0, 10)
    if uid == _o.ARD1:
        emails = [rng.choice(['a@x.com', 'b@x.com', 'A@x.com', 'a.b@y.org', 'c+1@x.com']) for _ in range(n)]
        phones = [rng.choice(['555', '5 55', '(1)2', '0']) for _ in range(n)]
    else:
        emails = [rng.choice(['ab@x.com', 'A.B@x.com', 'a.b+q@X.com', 'ab+@x.com', 'ab@y.com', '+z@x.com', 'b.a@x.com']) for _ in range(n)]
        phones = [rng.choice(['555-12', '(555) 12', '+55512', '1 2', '12', '9']) for _ in range(n)]
    return [[rng.choice(['Ann', 'Bo Li', 'x']) for _ in range(n)], emails, phones]


def _drl(rng):
    calls = [('allowRequest', rng.choice(['a.com', 'b.org', 'c'])) for _ in range(rng.randrange(1, 25))]
    return _ops('DomainRateLimiter', [rng.randrange(1, 4), rng.choice([1, 2, 3, 5, 10, 10**9])], calls)


def _ast(rng):
    n = rng.randrange(0, 12)
    return [[rng.choice([1, 2, 3, 4, 6, 10**6]) for _ in range(n)], [rng.choice([1, 2, 3, -1, -2, -3, 10**6, -10**6]) for _ in range(n)]]


def _acp(rng):
    pool = ['ab', 'ba', 'abc', 'cab', 'bca', 'aab', 'aba', 'a', 'z', 'zz']
    return [[rng.choice(pool) for _ in range(rng.randrange(0, 10))], [rng.choice(pool + ['q']) for _ in range(rng.randrange(0, 6))]]


def _bmd(rng):
    dates = ['2026-01-02', '2026-01-10', '2025-12-31', '2026-02-01']
    return [[[rng.choice(['Ann', 'Bob', 'Cy', 'Di']), rng.choice(['US', 'Peru', 'New Zealand']), [rng.choice(dates) for _ in range(rng.randrange(0, 4))]]
             for _ in range(rng.randrange(0, 9))]]


def _bub(rng):
    m, n = rng.randrange(1, 7), rng.randrange(1, 7); colors = rng.randrange(1, 4)
    return [[[rng.randrange(1, colors + 1) for _ in range(n)] for _ in range(m)]]


def _cpu(rng):
    logs, stack, t = [], [], 0
    for _ in range(rng.randrange(0, 8)):
        t += rng.choice([0, 1, 2, 5])
        if stack and rng.random() < 0.5: logs.append([stack.pop(), 'exit', str(t)])
        else:
            name = rng.choice(['a', 'b', 'Main', 'gc_1']); stack.append(name); logs.append([name, 'enter', str(t)])
    while stack:
        t += rng.choice([0, 1, 3]); logs.append([stack.pop(), 'exit', str(t)])
    return [logs]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.ZBP:
        args = [[[]], [[0]], [[1]], [[-1]], [[1, 0]], [[0, 0]], [[2, 0, 1]], [[3, 0, 1]], [[1, 2, 0, 2]], [[10**9, -10**9]]]
        for _ in range(250):
            n = rng.randrange(0, 10); a = list(range(n)); rng.shuffle(a)
            if a and rng.random() < 0.5: a[rng.randrange(n)] = rng.choice([-1, n, rng.randrange(n), 10**9])
            args.append([a])
    elif uid == o.VPS:
        args = [[1, []], [1, [1, 1, 1]], [2, [1, 1]], [2, [1, 2, 2, 1]], [2, [1, 1, 1]], [3, [1, 2, 1, 3]], [3, [2, 3, 1, 2, 3, 1, 2]], [3, [1, 2, 3, 1, 3]]]
        args += [_vps(rng) for _ in range(250)]
    elif uid == o.WAK:
        args = [[[5], 1, 0], [[1, 2, 3, 4], 2, 1], [[4, 4, 1], 3, 2], [[-3, -2], 2, 1], [[-1, -2, 0], 3, 0], [[7, 7, 7, 1], 4, 3]]
        args += [_wak(rng) for _ in range(250)]
    elif uid in (o.TOK1, o.TOK2, o.TOK3):
        if uid == o.TOK1: pr = ['basic,1,2', 'pro,3,4']
        elif uid == o.TOK2: pr = ['basic,1,2,10,150', 'pro,3,4,0,0']
        else: pr = ['basic,1,2,10,150,250', 'pro,3,4,0,0,1000000']
        args = [[[], pr], [['u,100,200,basic'], pr], [['u,100,200,basic', 'u,0,50,pro', 'a,1,1,basic', 'u,30,0,basic'], pr]]
        args += [_tok(rng, uid) for _ in range(250)]
    elif uid == o.API:
        args = [_ops('APIMatchingSystem', [], [('matchPath', '/')]),
                _ops('APIMatchingSystem', [], [('registerPath', '/a', 'A'), ('registerPath', '/a/b/c', 'C'), ('matchPath', '/a/b'), ('matchPath', '/a/b/c/d'), ('matchPath', '/ab'),
                                               ('registerPath', '/', 'R'), ('matchPath', '/ab'), ('registerPath', '/a', 'A2'), ('matchPath', '/a/x')])]
        args += [_api(rng) for _ in range(250)]
    elif uid in (o.ARD1, o.ARD2):
        args = [[[], [], []], [['A', 'B', 'C'], ['a@x.com', 'b@x.com', 'a@x.com'], ['1', '1', '2']], [['A', 'B', 'C'], ['a@x.com', 'b@x.com', 'c@x.com'], ['1', '2', '1']]]
        if uid == o.ARD2: args.append([['A', 'B', 'C', 'D'], ['A.b+1@x.com', 'ab@X.com', 'c@x.com', 'c@y.com'], ['(555) 1', '7', '5551', '8']])
        args += [_ard(rng, uid) for _ in range(250)]
    elif uid == o.DRL:
        args = [_ops('DomainRateLimiter', [1, 1], [('allowRequest', 'a')] * 3),
                _ops('DomainRateLimiter', [2, 3], [('allowRequest', 'a'), ('allowRequest', 'a'), ('allowRequest', 'a'), ('allowRequest', 'b'), ('allowRequest', 'a'), ('allowRequest', 'a')])]
        args += [_drl(rng) for _ in range(250)]
    elif uid == o.AST:
        args = [[[], []], [[5], [-1]], [[2, 3], [3, -2]], [[2, 3], [3, -3]], [[1, 1], [-1, 1]], [[4, 1, 5], [1, 2, -1]], [[1, 1, 10], [5, 5, -1]]]
        args += [_ast(rng) for _ in range(250)]
    elif uid == o.ACP:
        args = [[[], []], [['abc'], []], [[], ['a']], [['eat', 'tea', 'tan', 'ate', 'nat', 'bat'], ['ate', 'nat', 'cab']], [['aa', 'a', 'aa'], ['aa']]]
        args += [_acp(rng) for _ in range(250)]
    elif uid == o.BPG:
        args = [[[]], [[5]], [[-5]], [[1, 2]], [[1, -1]], [[3, -10, 4]], [[1, 5, 233, 7]], [[-1, -2, -3, -4]], [[10, -1, -1, 10]]]
        for _ in range(250):
            args.append([[rng.choice([-10**4, -5, -1, 0, 1, 2, 3, 7, 10**4]) for _ in range(rng.randrange(0, 13))]])
        args.append([[rng.randrange(-10**4, 10**4 + 1) for _ in range(300)]])
    elif uid == o.BMD:
        args = [[[]], [[['Ann', 'US', []]]],
                [[['Ann', 'US', ['2026-01-02', '2026-01-01']], ['Bob', 'US', ['2026-01-02']], ['Cy', 'Peru', ['2026-03-01', '2026-02-01']], ['Di', 'US', ['2026-01-01']]]]]
        args += [_bmd(rng) for _ in range(250)]
    elif uid == o.BUB:
        args = [[[[1]]], [[[1, 1, 1]]], [[[1, 1], [1, 2]]], [[[2, 1, 2], [1, 1, 1], [2, 1, 2]]], [[[1, 2], [2, 1]]], [[[3, 1], [2, 1], [2, 1], [2, 3]]]]
        args += [_bub(rng) for _ in range(250)]
    elif uid in (o.BSN1, o.BSN2):
        if uid == o.BSN1:
            args = [[[0]], [[0, 0]], [[5]], [[3, 0, 1]], [[0, 0, 2, 1]], [[9, 9, 0]]]
            for _ in range(250): args.append([[rng.choice([0, 0, 1, 2, 5, 9]) for _ in range(rng.randrange(1, 8))]])
        else:
            args = [[[0]], [[0, 0]], [[10, 2]], [[0, 10, 2]], [[0, 2, 21]], [[3, 30, 34, 5, 9]], [[0, 1, 10]], [[1000000000, 0, 7]]]
            for _ in range(250):
                args.append([[rng.choice([0, 0, 1, 2, 10, 12, 21, 100, 101, 210, 1000000000]) for _ in range(rng.randrange(1, 7))]])
    elif uid == o.SPK:
        args = [[[]], [[1]], [[1, 1]], [[1, 2]], [[4, 5, 7, 6, 3, 2]], [[1, 1, 5, 4, 3]], [[2, 2, 2, 1, 1, 1]], [[-1, -1, 0]]]
        for _ in range(250): args.append([[rng.choice([-10**9, -2, 0, 1, 1, 3, 4, 10**9]) for _ in range(rng.randrange(0, 12))]])
    elif uid == o.CPU:
        args = [[[]], [[['a', 'enter', '0'], ['a', 'exit', '5']]], [[['a', 'enter', '0'], ['b', 'enter', '2'], ['b', 'exit', '5'], ['a', 'exit', '6']]],
                [[['a', 'enter', '1'], ['a', 'enter', '3'], ['a', 'exit', '4'], ['a', 'exit', '4'], ['b', 'enter', '7'], ['b', 'exit', '7']]]]
        args += [_cpu(rng) for _ in range(250)]
    elif uid == o.CAE:
        args = [['', 3], ['abc', 0], ['xyz', 3], ['Hello, World!', 13], ['Zebra-123', -1], ['aA', 26], ['aA', -27], ['a', 10**9], ['~ z', -10**9]]
        for _ in range(250):
            args.append([''.join(rng.choice('aZmz Az09!~') for _ in range(rng.randrange(0, 15))), rng.choice([0, 1, 25, 26, -1, -26, 52, 10**9, -10**9, rng.randrange(-100, 100)])])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _game_line(value, n):
    """Score difference for a line of n equal values; four moves collapse to taking 1 or 2 (closed recurrence)."""
    d = [0] * (n + 1)
    for i in range(1, n + 1):
        d[i] = value - d[i - 1]
        if i >= 2: d[i] = max(d[i], 2 * value - d[i - 2])
    return (n * value + d[n]) // 2


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.ZBP:
        out.append(([list(range(n - 1, -1, -1))], True))
        out.append(([list(range(n - 1)) + [0]], False))
        out.append(([list(range(1, n + 1))], False))
    elif uid == o.VPS:
        out.append(([n, list(range(1, n + 1))], True))
        out.append(([n // 2, list(range(1, n // 2 + 1)) * 2], True))
        out.append(([3, [1, 2, 3] * 33333 + [1]], True))
        out.append(([2, [1] * n], False))
        out.append(([n, list(range(1, n)) + [1]], True))
        out.append(([n, [1, 2, 1] + list(range(3, n - 2))], True))
        out.append(([n, [5, 5] + list(range(6, n)) + [6]], False))  # 5,5 forces the cut at 1; 6 ... 6 lie inside one piece
    elif uid == o.WAK:
        w, k = 10000, 5000
        out.append(([list(range(n)), w, k], [i + (w - k - 1) // 2 for i in range(n - w + 1)]))
        out.append(([[-i for i in range(n)], w, k], [-i - 7500 for i in range(n - w + 1)]))
        out.append(([[10**9] * n, n, n - 1], [10**9]))
        out.append(([[(-1) ** i * i for i in range(n)], 1, 0], [(-1) ** i * i for i in range(n)]))
    elif uid in (o.TOK1, o.TOK2, o.TOK3):
        tail = {o.TOK1: '', o.TOK2: ',7,150', o.TOK3: ',7,150,40000'}[uid]
        sessions = ['u%03d,100,200,A' % (i % 1000) for i in range(n)]
        per = {o.TOK1: 100 * 500, o.TOK2: 300 + 99 * 500 + 7, o.TOK3: 40000 + 7}[uid]
        out.append(([sessions, ['A,1,2' + tail]], [['u%03d' % u, per] for u in range(1000)]))
        tail = {o.TOK1: '', o.TOK2: ',1000000,0', o.TOK3: ',1000000,0,1000000000000'}[uid]
        big = {o.TOK1: 2 * 10**14, o.TOK2: 2 * 10**14 + 10**6, o.TOK3: 10**12 + 10**6}[uid]
        out.append(([['whale,1000000,1000000,Max'] * n, ['Max,1000,1000' + tail, 'Min,0,0' + tail]], [['whale', big]]))
    elif uid == o.API:
        calls = [('registerPath', '/', 'root')] + [('registerPath', '/x%d' % i, 'h%d' % i) for i in range(50000)]
        calls += [('matchPath', '/x%d/y/z' % i) for i in range(49999)]
        out.append((_ops('APIMatchingSystem', [], calls), [None] * 50002 + ['h%d' % i for i in range(49999)]))
        deep = '/a' * 20; calls = [('registerPath', '/a' * 10, 'mid')] + [('matchPath', deep)] * 99999
        out.append((_ops('APIMatchingSystem', [], calls), [None, None] + ['mid'] * 99999))
    elif uid in (o.ARD1, o.ARD2):
        names = ['n'] * n; phones = ['1%d' % i for i in range(n)]
        if uid == o.ARD1: emails = ['a%d@x.com' % (i // 2) for i in range(n)]
        else: emails = [('U.%d@x.com' if i % 2 == 0 else 'u%d+z@X.com') % (i // 2) for i in range(n)]
        out.append(([names, emails, phones], list(range(1, n, 2))))
        out.append(([names, ['e%d@x.com' % i for i in range(n)], ['5'] * n], list(range(1, n))))
    elif uid == o.DRL:
        out.append((_ops('DomainRateLimiter', [3, 10], [('allowRequest', 'a.com')] * n), [None] + [t % 10 in (1, 2, 3) for t in range(1, n + 1)]))
        out.append((_ops('DomainRateLimiter', [1, 10**9], [('allowRequest', 'd%d' % i) for i in range(n)]), [None] + [True] * n))
        out.append((_ops('DomainRateLimiter', [100000, 10**9], [('allowRequest', 'x')] * n), [None] + [True] * n))
    elif uid == o.AST:
        out.append(([[1] * (n - 1) + [10**6], [1] * (n - 1) + [-10**6]], [[10**6, -10**6]]))
        out.append(([[2, 1] * (n // 2), [1, -2] * (n // 2)], []))
        out.append(([[3] * n, [-1] * (n // 2) + [1] * (n // 2)], [[3, -1]] * (n // 2) + [[3, 1]] * (n // 2)))
        out.append(([[10**6] * (n // 2) + [1] * (n // 2), [10**6] * (n // 2) + [-1] * (n // 2)], [[10**6, 10**6]] * (n // 2)))
    elif uid == o.ACP:
        words = ['ab' * 50 if i % 2 else 'ba' * 50 for i in range(1000)]
        out.append(([words, ['ab' * 50] * 100], [words] * 100))
        words = ['%s%s%s' % (chr(97 + i // 676), chr(97 + i // 26 % 26), chr(97 + i % 26)) for i in range(1000)]
        sig = [''.join(sorted(w)) for w in words]  # each code's anagrams are the codes with the same sorted letters
        out.append(([words, [w[::-1] for w in words]], [[x for x, t in zip(words, sig) if t == s] for s in sig]))
    elif uid == o.BPG:
        out.append(([[1] * 500], _game_line(1, 500)))
        out.append(([[-1] * 500], _game_line(-1, 500)))
        out.append(([[10**4] * 499], _game_line(10**4, 499)))
    elif uid == o.BMD:
        countries = ['K' + chr(65 + i // 26) + chr(97 + i % 26) for i in range(100)]
        ppl = [['p' + chr(97 + i % 26) * (1 + i // 26 % 19), countries[i % 100], ['2026-01-05', '2026-01-03'] + ['2026-02-%02d' % (1 + (i + j) % 28) for j in range(8)]] for i in range(10000)]
        out.append(([ppl], [[c, '2026-01-03', [p[0] for p in ppl if p[1] == c]] for c in sorted(countries)]))
        ppl = [['a', 'Solo', ['2030-12-%02d' % (31 - j % 31) for j in range(100)]] for _ in range(1000)]
        out.append(([ppl], [['Solo', '2030-12-01', ['a'] * 1000]]))
    elif uid == o.BUB:
        out.append(([[[1 + (r + c) % 2 for c in range(50)] for r in range(50)]], [[1 + (r + c) % 2 for c in range(50)] for r in range(50)]))
        out.append(([[[7] * 50 for _ in range(50)]], [[0] * 50 for _ in range(50)]))
        out.append(([[[1 + c % 2 for c in range(50)] for _ in range(50)]], [[0] * 50 for _ in range(50)]))
    elif uid == o.BSN1:
        out.append(([[0] * 50000 + [9] * 50000], '9' + '0' * 50000 + '9' * 49999))
        out.append(([[0] * n], '0'))
        digits = [(i * 7) % 10 for i in range(n)]
        out.append(([digits], '1' + '0' * 10000 + '1' * 9999 + ''.join(str(d) * 10000 for d in range(2, 10))))
    elif uid == o.BSN2:
        out.append(([[0] * 500 + [10] * 500], '10' + '0' * 500 + '10' * 499))
        out.append(([[0] * 100 + list(range(1899, 999, -1))], '1000' + '0' * 100 + ''.join(str(x) for x in range(1001, 1900))))
        out.append(([[1000000000] * 1000], '1000000000' * 1000))
    elif uid == o.SPK:
        out.append(([[i // 2 for i in range(n)]], 99999))
        out.append(([[5] * n], 1))
        out.append(([list(range(-n // 2, n // 2))], n))
    elif uid == o.CPU:
        m = 50000
        logs = [['t%d' % i, 'enter', str(i)] for i in range(m)] + [['t%d' % (m - 1 - j), 'exit', str(m + j)] for j in range(m)]
        out.append(([logs], [[name, 1 if name == 't%d' % (m - 1) else 2] for name in sorted('t%d' % i for i in range(m))]))
        logs = []
        for i in range(m): logs += [['job', 'enter', str(i * 20000)], ['job', 'exit', str(i * 20000 + 3)]]
        out.append(([logs], [['job', 3 * m]]))
    elif uid == o.CAE:
        msg = ''.join(chr(32 + i % 95) for i in range(n))

        def rot(ch, s):
            if 'a' <= ch <= 'z': return chr(97 + (ord(ch) - 97 + s) % 26)
            if 'A' <= ch <= 'Z': return chr(65 + (ord(ch) - 65 + s) % 26)
            return ch
        for s in (10**9, -10**9, 13):
            out.append(([msg, s], ''.join(rot(ch, s) for ch in msg)))
    return out
