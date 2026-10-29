"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h14b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _node(rng, depth, generic=True):
    r = rng.random()
    if depth >= 3 or r < 0.55:
        pool = ['int', 'char', 'float'] + (['T1', 'T2', 'T3'] if generic else [])
        return rng.choice(pool)
    return [_node(rng, depth + 1, generic) for _ in range(rng.randrange(1, 4))]


def _concrete(rng, node, binding):
    if type(node) is str:
        if node[0] != 'T': return node
        if node not in binding: binding[node] = _node(rng, 1, False)
        return binding[node]
    return [_concrete(rng, x, binding) for x in node]


def _tlg(rng, uid):
    params = [_node(rng, 0) for _ in range(rng.randrange(0, 5))]
    ret = _node(rng, 0)
    if uid == _o.TLG1: return [params, ret]
    binding = {}
    args = [_concrete(rng, p, binding) for p in params]
    r = rng.random()
    if r < 0.15 and args: args[rng.randrange(len(args))] = _node(rng, 1, False)
    elif r < 0.2: args = args + [_node(rng, 1, False)]
    elif r < 0.25 and args: args = args[:-1]
    return [params, ret, args]


def _date(d): return '2024-%02d-%02d' % (1 + d // 28, 1 + d % 28)


def _vla(rng):
    days = sorted(rng.randrange(0, 40) for _ in range(rng.randrange(0, 30)))
    logs = [['p%d' % rng.randrange(4), rng.choice(['spam', 'privacy', 'child', 'hate']), _date(d)] for d in days]
    calls = []
    for _ in range(rng.randrange(0, 15)):
        a, b = sorted(rng.randrange(-2, 42) for _ in range(2))
        if rng.random() < 0.1: a, b = b, a
        lo, hi = _date(max(a, 0)), _date(min(max(b, 0), 41))
        k = rng.randrange(3)
        if k == 0: calls.append(('countPolicies', 'p%d' % rng.randrange(5), lo, hi))
        elif k == 1: calls.append(('countPosts', rng.choice(['spam', 'privacy', 'child', 'hate', 'fraud']), lo, hi))
        else: calls.append(('countViolations', lo, hi))
    return _ops('ViolationLogAnalyzer', [logs], calls)


def _vss(rng):
    alphabet = rng.choice(['aeiou', 'aeiouaeioub', 'aeiouxyz'])
    return [''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 60)))]


def _wpa(rng):
    n = rng.randrange(1, 7); caps = [rng.randrange(1, 5) for _ in range(n)]
    log, open_ = [], list(range(n))
    for _ in range(rng.randrange(0, 40)):
        if rng.random() < 0.15 and len(open_) > 1:
            i = rng.choice(open_); open_.remove(i); log.append('CLOSURE %d' % i)
        else: log.append('PACKAGE')
    return [caps, log]


def _wca(rng):
    keys = ['a', 'b', 'c', 'd', 'e', 'k1']
    calls = []
    for _ in range(rng.randrange(0, 40)):
        if rng.random() < 0.55: calls.append(('put', rng.choice(keys), rng.randrange(0, 100), rng.randrange(1, 12)))
        else: calls.append(('get', rng.choice(keys)))
    return _ops('WeightedCache', [rng.randrange(1, 30)], calls)


def _wse(rng):
    s = ''.join(rng.choice('ab') for _ in range(rng.randrange(0, 16)))
    if rng.random() < 0.4 and s:
        i = rng.randrange(len(s)); j = rng.randrange(i, len(s) + 1); p = list(s[i:j])
        for _ in range(rng.randrange(0, 3)): p.insert(rng.randrange(len(p) + 1), '*')
        return [''.join(p), s]
    return [''.join(rng.choice('ab*') for _ in range(rng.randrange(0, 7))), s]


_EDGES = [[r, c, r, c + 1] for r in range(9) for c in range(8)] + [[r, c, r + 1, c] for r in range(8) for c in range(9)]


def _wdg(rng):
    moves = [list(e) for e in rng.sample(_EDGES, rng.randrange(0, 145))]
    for m in moves:
        if rng.random() < 0.5: m[:] = m[2:] + m[:2]
    return [moves]


def _wsl(rng):
    m, n = rng.randrange(1, 7), rng.randrange(1, 7)
    board = [[rng.choice('abA') for _ in range(n)] for _ in range(m)]
    if rng.random() < 0.5:
        r, c = rng.randrange(m), rng.randrange(n); dr, dc = rng.choice([(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)])
        word = ''
        while 0 <= r < m and 0 <= c < n and len(word) < rng.randrange(1, 7): word += board[r][c]; r += dr; c += dc
        if word: return [board, word]
    return [board, ''.join(rng.choice('abA') for _ in range(rng.randrange(1, 5)))]


def _wtm(rng, uid):
    names = rng.sample(['ann', 'bob', 'cy', 'dee', 'eve', 'fay', 'al', 'b'], rng.randrange(1, 7))
    tasks = [[i * 3 + rng.randrange(3), rng.randrange(1, 6)] for i in range(rng.randrange(0, 30))]
    if uid == _o.WTM1: return [names, tasks]
    spec = [rng.sample(['x', 'y', 'z'], rng.randrange(0, 3)) for _ in names]
    types = [rng.choice(['x', 'y', 'z', 'w']) for _ in tasks]
    if uid == _o.WTM2: return [names, spec, tasks, types]
    return [names, spec, [rng.randrange(0, 6) for _ in names], tasks, types]


def _aba(rng):
    n = rng.randrange(1, 10); arr = [rng.randrange(2) for _ in range(n)]
    return [arr, [rng.choice(['1', '2 %d' % rng.randrange(n)]) for _ in range(rng.randrange(0, 20))]]


def _aeg(rng):
    pool = ['scam', 'cheat', 'bot', 'spam', 'hack', 'troll']
    cats = [[k, rng.choice(['Fraud', 'Gameplay', 'Abuse', 'abuse'])] for k in rng.sample(pool, rng.randrange(0, 6))]
    return [[rng.choice(pool) for _ in range(rng.randrange(0, 15))], cats, rng.choice(['Sam', 'player1', 'X'])]


def _bsm(rng):
    return [rng.randrange(0, 8), [rng.choice([-1, 1]) * rng.randrange(1, 8) for _ in range(rng.randrange(0, 30))]]


def _expr(rng, depth):
    r = rng.random()
    if depth > 3 or r < 0.3: return str(rng.randrange(0, 20))
    if r < 0.4: return '-' + _expr(rng, depth + 1)
    if r < 0.55: return '(' + _expr(rng, depth + 1) + ')'
    return _expr(rng, depth + 1) + rng.choice('+-*/') + _expr(rng, depth + 1)


def _bca(rng):
    while True:
        s = _expr(rng, 0)
        try: validate_domain(_o.BCA, [s]); return [s]
        except ValueError: pass


def _bsd(rng, uid):
    t, v = rng.randrange(1, 6), rng.randrange(1, 6)
    scores = [[rng.randrange(-3, 4) for _ in range(v)] for _ in range(t)]
    return [scores] if uid == _o.BSD1 else [scores, rng.randrange(1, 8)]


def _bcb(rng):
    m, n = rng.randrange(2, 8), rng.randrange(2, 8)
    cells = rng.sample([(x, y) for x in range(m) for y in range(n)], rng.randrange(0, min(m * n, 15) + 1))
    return [m, n, [list(c) for c in cells]]


def _bsa(rng):
    blocks = [rng.sample('abcde', rng.randrange(1, 4)) for _ in range(rng.randrange(0, 9))]
    return [blocks, ''.join(rng.choice('abcdef' if rng.random() < 0.2 else 'abcd') for _ in range(rng.randrange(0, 8)))]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.TLG1:
        args = [[[], 'int'], [['int', 'T1'], ['T1', 'char']], [[['int', ['char', 'T2']], 'float'], [['T2']]]]
        args += [_tlg(rng, uid) for _ in range(250)]
    elif uid == o.TLG2:
        args = [[[], 'int', []], [['T1', 'int'], ['T1', 'T1'], [['char', 'float'], 'int']], [['T1', 'T1'], 'T1', ['int', 'char']], [['T1'], 'T2', ['int']],
                [[['T1', 'char']], 'T1', [['int', 'char']]], [[['T1', 'char']], 'T1', [['int', 'char', 'int']]], [['int'], 'int', ['char']], [['int'], 'int', []]]
        args += [_tlg(rng, uid) for _ in range(250)]
    elif uid == o.VLA:
        logs = [['p1', 'spam', '2024-01-01'], ['p2', 'spam', '2024-01-01'], ['p1', 'spam', '2024-01-02'], ['p1', 'hate', '2024-01-03'], ['p1', 'hate', '2024-01-03']]
        args = [_ops('ViolationLogAnalyzer', [logs], [('countPolicies', 'p1', '2024-01-01', '2024-01-03'), ('countPolicies', 'p1', '2024-01-01', '2024-01-02'),
                                                      ('countPosts', 'spam', '2024-01-01', '2024-01-05'), ('countViolations', '2024-01-01', '2024-01-03'),
                                                      ('countViolations', '2024-01-03', '2024-01-01'), ('countPolicies', 'p9', '2024-01-01', '2024-01-09')]),
                _ops('ViolationLogAnalyzer', [[]], [('countViolations', '2024-01-01', '2024-12-28')])]
        args += [_vla(rng) for _ in range(250)]
    elif uid == o.VSS:
        args = [[''], ['aeiou'], ['aaeiouu'], ['aeioxaeiou'], ['uoiea'], ['aeio'], ['aeiouaeiou']]
        args += [_vss(rng) for _ in range(250)]
    elif uid == o.WPA:
        args = [[[1], []], [[2, 1], ['PACKAGE'] * 4], [[1, 1, 1], ['PACKAGE', 'CLOSURE 1', 'PACKAGE', 'PACKAGE']], [[3, 2], ['PACKAGE', 'CLOSURE 0', 'PACKAGE']]]
        args += [_wpa(rng) for _ in range(250)]
    elif uid == o.WCA:
        args = [_ops('WeightedCache', [10], [('put', 'a', 1, 5), ('put', 'b', 2, 8), ('get', 'a'), ('get', 'b'), ('put', 'c', 3, 5), ('get', 'a'), ('get', 'c')]),
                _ops('WeightedCache', [5], [('put', 'a', 1, 6), ('get', 'a'), ('put', 'b', 2, 3), ('put', 'b', 7, 2), ('get', 'b')])]
        args += [_wca(rng) for _ in range(250)]
    elif uid == o.WSE:
        args = [['', ''], ['', 'abc'], ['*', ''], ['a*c', 'xxabzcx'], ['b*', 'aab'], ['abc', 'ab'], ['a*a', 'a'], ['*b', 'aab'], ['ba*ab', 'abab']]
        args += [_wse(rng) for _ in range(250)]
    elif uid == o.WDG:
        box = [[0, 0, 0, 1], [0, 0, 1, 0], [1, 0, 1, 1], [0, 1, 1, 1]]
        args = [[[]], [box], [box[:3] + [[5, 5, 5, 6]] + box[3:]], [[[0, 1, 0, 0]]]]
        args += [_wdg(rng) for _ in range(250)]
    elif uid == o.WSL:
        args = [[[['a']], 'a'], [[['a']], 'b'], [[['a', 'b'], ['c', 'd']], 'ad'], [[['a', 'b'], ['c', 'd']], 'abd'], [[['a', 'b', 'c']], 'cba'], [[['a', 'B']], 'ab']]
        args += [_wsl(rng) for _ in range(250)]
    elif uid in o.WTM:
        t = [[1, 5], [2, 3], [3, 1], [4, 2], [5, 4]]
        if uid == o.WTM1: args = [[['bob', 'alice'], []], [['bob', 'alice'], t], [['c', 'b', 'a'], t]]
        elif uid == o.WTM2: args = [[['bob', 'alice'], [['x'], ['x', 'y']], t, ['x', 'y', 'x', 'z', 'x']], [['a'], [[]], t[:1], ['x']]]
        else: args = [[['bob', 'alice'], [['x'], ['x', 'y']], [2, 1], t, ['x', 'y', 'x', 'x', 'x']], [['a'], [['x']], [0], t[:1], ['x']]]
        args += [_wtm(rng, uid) for _ in range(250)]
    elif uid == o.ABA:
        args = [[[0], []], [[1, 0, 1, 0], ['1', '1', '1']], [[1, 1], ['2 1', '2 0', '1']], [[0, 0], ['2 0', '1']]]
        args += [_aba(rng) for _ in range(250)]
    elif uid == o.AEG:
        args = [[[], [], 'Sam'], [['scam', 'cheat', 'bot', 'cheat'], [['scam', 'Fraud'], ['cheat', 'Gameplay'], ['bot', 'Gameplay']], 'Kim'], [['zzz'], [['scam', 'Fraud']], 'a1']]
        args += [_aeg(rng) for _ in range(250)]
    elif uid == o.BSM:
        args = [[0, []], [1, [-2]], [1, [-1, 5, -3, -4, 2]], [0, [3, -2, -2, 4, -4, -1]], [10, [-3, -3, -3, -3]]]
        args += [_bsm(rng) for _ in range(250)]
    elif uid == o.BCA:
        args = [['5/2'], ['-7/3'], ['2*(-3)'], ['-4/2'], ['-(3+2)'], ['1+2*3-4/2'], ['2*-3'], ['--5'], ['(1+(4+5+2)-3)+(6+8)'], ['7-3-2'], ['0'], ['8/3/2']]
        args += [_bca(rng) for _ in range(250)]
    elif uid in o.BSD:
        sc = [[1, 3, 3], [5, 2, 0], [0, 0, 0]]
        args = [[sc], [[[7]]], [[[-1, -2], [-5, -5]]]] if uid == o.BSD1 else [[sc, 1], [sc, 4], [sc, 20], [[[7]], 3], [[[1, 2], [3, 3]], 2]]
        args += [_bsd(rng, uid) for _ in range(250)]
    elif uid == o.BCB:
        args = [[2, 2, []], [3, 3, [[0, 0]]], [3, 3, [[0, 0], [1, 1], [0, 2]]], [2, 3, [[0, 0], [0, 1], [1, 0], [1, 1], [1, 2], [0, 2]]]]
        args += [_bcb(rng) for _ in range(250)]
    elif uid == o.BSA:
        args = [[[], ''], [[], 'a'], [[['a', 'b'], ['b']], 'ab'], [[['a', 'b'], ['a']], 'ba'], [[['a'], ['a']], 'aa'], [[['a', 'b']], 'ab'], [[['a', 'b'], ['b', 'c'], ['a']], 'abc']]
        args += [_bsa(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    if uid in o.TLG:
        deep = 'int'
        for _ in range(20): deep = [deep]
        deep_s = '[' * 20 + 'int' + ']' * 20
        if uid == o.TLG1:
            out.append(([['int'] * 10000, deep], '(' + ', '.join(['int'] * 10000) + ') -> ' + deep_s))
            out.append(([[['char'] * 9999], 'T1'], '([' + ', '.join(['char'] * 9999) + ']) -> T1'))
        else:
            out.append(([['T1'] * 5000, ['T1', 'T3'], [['int', 'char']] * 5000], '[[int, char], T3]'))
            out.append(([['T1'] * 5000, ['T1', 'T3'], [['int', 'char']] * 4999 + [['int', 'float']]], None))
            gdeep = 'T5'
            for _ in range(19): gdeep = [gdeep]
            arg = ['float', 'int']
            for _ in range(19): arg = [arg]
            out.append(([[gdeep] * 800, ['T5', 'T5'], [arg] * 800], '[[float, int], [float, int]]'))
            out.append(([['int'] * 10000, 'char', ['int'] * 10000], 'char'))
    elif uid == o.VLA:
        pols = ['spam', 'privacy', 'child', 'hate', 'fraud', 'abuse', 'scam']
        logs = [['p%d' % (k % 100), pols[k % 7], _date(k // 400)] for k in range(10000)]
        lo, hi = _date(0), _date(24)
        calls, expected = [], [None]
        for q in range(33):
            calls += [('countPolicies', 'p%d' % (q * 3), lo, hi), ('countPosts', pols[q % 7], lo, hi), ('countViolations', lo, hi)]
            expected += [7, 100, 700]
        calls += [('countViolations', hi, lo)]; expected += [0]
        out.append((_ops('ViolationLogAnalyzer', [logs], calls), expected))
        calls = [('countViolations', _date(30), _date(40))] * 50 + [('countPosts', 'none', lo, hi)] * 50
        out.append((_ops('ViolationLogAnalyzer', [logs], calls), [None] + [0] * 100))
    elif uid == o.VSS:
        n = 100000
        out.append((['aeiou' * (n // 5)], (n - 4) * (n - 3) // 2))
        out.append((['b' * n], 0))
        out.append((['aeioub' * (n // 6)], n // 6))
        out.append((['a' * (n - 4) + 'eiou'], n - 4))
    elif uid == o.WPA:
        out.append(([[1] * 10000, ['PACKAGE'] * 100000], 9999))
        closures = 4999; opened = list(range(closures, 10000)); packages = 100000 - closures
        q, r = divmod(packages, len(opened))
        out.append(([[1] * 10000, ['CLOSURE %d' % i for i in range(closures)] + ['PACKAGE'] * packages], opened[r - 1] if r else opened[-1]))
        out.append(([[10**9] * 10000, ['PACKAGE'] * 100000], 0))
        log = []
        for i in range(9999): log += ['PACKAGE', 'CLOSURE %d' % i]
        out.append(([[2] * 10000, log + ['PACKAGE'] * (100000 - len(log))], 9999))
    elif uid == o.WCA:
        calls = [('put', 'k%d' % i, i, 1000) for i in range(60000)]; expected = [None] * 60001
        for j in range(39999):
            idx = (j * 3) % 60000; calls.append(('get', 'k%d' % idx)); expected.append(idx if idx >= 59000 else -1)
        out.append((_ops('WeightedCache', [10**6], calls), expected))
        calls = [('put', 'k%d' % i, i, i + 1) for i in range(50000)]; expected = [None] * 50001
        for j in range(49999): calls.append(('get', 'k%d' % j)); expected.append(j if j <= 998 else -1)
        out.append((_ops('WeightedCache', [500000], calls), expected))
    elif uid == o.WSE:
        n = 100000
        out.append((['a' * 500 + '*b', 'a' * (n - 1) + 'b'], 0))
        out.append((['a' * 1000 + 'b', 'a' * (n - 1) + 'b'], n - 1001))
        out.append((['*' * n, ''], 0))
        out.append((['b*a', 'a' * (n - 1) + 'b'], -1))
        out.append((['ab*ba', 'ab' * (n // 2)], 0))
        out.append((['a*' * 50000, 'b' * (n - 1) + 'a'], -1))
        out.append((['a*', 'b' * (n - 1) + 'a'], n - 1))
    elif uid == o.WDG:
        horizontal = [[r, c, r, c + 1] for r in range(9) for c in range(8)]
        vertical = [[r, c, r + 1, c] for c in range(9) for r in range(8)]
        out.append(([horizontal + vertical], 0))
        column0, filler = vertical[:8], []
        for r in range(8): filler += [[r, 1, r + 1, 1], [r, 8, r + 1, 8]]
        out.append(([horizontal + column0 + filler], 1))
    elif uid == o.WSL:
        board = [['a'] * 50 for _ in range(50)]; board[49][49] = 'b'
        for word, want in [('a' * 49 + 'b', True), ('a' * 50, True), ('b' + 'a' * 49, True), ('aba', False), ('a' * 48 + 'bb', False), ('a' * 49 + 'c', False)]:
            out.append(([board, word], want))
    elif uid in o.WTM:
        names = [_code(i, 3) for i in range(1000)][::-1]
        tasks = [[t, 1] for t in range(100000)]
        if uid == o.WTM1:
            lists = [[] for _ in names]
            for t in range(100000): lists[999 - t % 1000].append(t)
            out.append(([names, tasks], lists))
        else:
            spec = [['x'] if (999 - i) % 2 == 0 else ['y'] for i in range(1000)]
            types = [['x', 'y', 'z'][t % 3] for t in range(100000)]
            limits = [10 if (999 - i) % 2 == 0 else 100000 for i in range(1000)]
            lists = [[] for _ in names]; left = []; xs = ys = 0
            for t in range(100000):
                if t % 3 == 0:
                    rank = 2 * (xs % 500)
                    if uid == o.WTM3 and xs >= 5000: left.append(t)
                    else: lists[999 - rank].append(t)
                    xs += 1
                elif t % 3 == 1: lists[999 - (2 * (ys % 500) + 1)].append(t); ys += 1
                else: left.append(t)
            out.append(([names, spec, tasks, types] if uid == o.WTM2 else [names, spec, limits, tasks, types], lists + [left]))
    elif uid == o.ABA:
        n = 100000
        out.append(([[0] * n, ['1'] * n], [1] * n))
        out.append(([[1] * n, ['2 %d' % i for i in range(50000)] + ['1'] * 25000], [1] * 25000 + [0] * 25000 + [1] * 50000))
        out.append(([[0] * n, ['1', '2 0'] * 50000], [0] + [0] * (n - 1)))
    elif uid == o.AEG:
        kws = ['w' + _code(i, 3) for i in range(1000)]
        cats = ['C' + _code(i, 2).upper() for i in range(10)]
        categories = [[kws[i], cats[(i * 3) % 10]] for i in range(1000)]
        words = [kws[(j * 7) % 100] for j in range(10000)]
        lines = ['Dear Moderated42,']
        for c in sorted(cats):
            seen = []
            for j in range(100):
                w = kws[(j * 7) % 100]
                if categories[(j * 7) % 100][1] == c and w not in seen: seen.append(w)
            lines.append(c + ': ' + ', '.join(w + ' (100)' for w in seen))
        out.append(([words, categories, 'Moderated42'], '\n'.join(lines)))
        out.append(([['zz'] * 10000, categories, 'u'], 'Dear u,\nNo violations found.'))
    elif uid == o.BSM:
        n = 100000
        out.append(([0, [1] * n], n))
        out.append(([0, [5, -5] * (n // 2)], n))
        out.append(([50000, [-1] * n], 50000))
        out.append(([0, [-1] + [1, -1] * 49999 + [-1]], 99998))
        out.append(([10**9, [-10**9] * n], 1))
    elif uid == o.BCA:
        out.append((['1+' * 49999 + '1'], 50000))
        out.append((['(' * 30000 + '1' + ')' * 30000], 1))
        out.append((['-' * 99999 + '7'], -7))
        out.append((['-(' * 25000 + '3' + ')' * 25000], 3))
        out.append((['2*' * 49 + '1'], 2 ** 49))
        out.append((['999999999*999999-' + '1-' * 40000 + '1'], 999999999 * 999999 - 40001))
        out.append((['-1000000000/' + '3/' * 10 + '1'], -(10**9 // 3 ** 10)))
    elif uid in o.BSD:
        if uid == o.BSD1:
            scores = []
            for i in range(200):
                row = [0] * 1000; j = (i * 7) % 999; row[j] = row[j + 1] = 5; scores.append(row)
            out.append(([scores], [(i * 7) % 999 for i in range(200)]))
            out.append(([[[-10**6] * 1000 for _ in range(200)]], [0] * 200))
        else:
            out.append(([[[0] * 100 for _ in range(200)], 20], [[0] * 199 + [k] for k in range(20)]))
            row = [10, 9] + [-1] * 98
            out.append(([[row[:] for _ in range(200)], 20], [[0] * 200] + [[0] * p + [1] + [0] * (199 - p) for p in range(199, 180, -1)]))
    elif uid == o.BCB:
        m = n = 100000; R, C = 50000, 70000
        cells = [[R + i, C + j] for i in range(100) for j in range(100)]
        lists = [[], [], [], []]
        for a in range(R - 1, R + 100):
            for b in range(C - 1, C + 100):
                k = (1 if a in (R - 1, R + 99) else 2) * (1 if b in (C - 1, C + 99) else 2)
                lists[k - 1].append([a, b])
        out.append(([m, n, cells], lists))
        out.append(([m, n, []], [[], [], [], []]))
        out.append(([m, n, [[0, 0], [99999, 99999], [0, 99999], [99999, 0]]], [[[0, 0], [0, 99998], [99998, 0], [99998, 99998]], [], [], []]))
    elif uid == o.BSA:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        out.append(([[list(letters)] * 100, 'z' * 100], True))
        blocks = [[letters[i % 26]] for i in range(100)]
        target = ''.join(letters[i % 26] for i in range(100))
        out.append(([blocks, target], True))
        out.append(([blocks, target[:-1] + 'a'], False))
        chain = [[letters[i % 26], letters[(i + 1) % 26]] for i in range(100)]
        out.append(([chain, ''.join(letters[(i + 1) % 26] for i in range(99)) + letters[0]], True))
    return out
