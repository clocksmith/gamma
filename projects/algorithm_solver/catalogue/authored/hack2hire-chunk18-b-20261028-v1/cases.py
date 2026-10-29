"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h18b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _nct(rng):
    return [''.join(rng.choice('abcdeiouhmnstxyz') for _ in range(rng.randrange(1, 21)))]


def _ohe(rng):
    return [[rng.randrange(-3, 4) for _ in range(rng.randrange(1, 11))]]


def _prefix(rng, depth):
    if depth == 0 or rng.random() < 0.3: return rng.choice('ABCxyz019')
    return rng.choice('+-*/^') + _prefix(rng, depth - 1) + _prefix(rng, depth - 1)


def _ptp(rng):
    return [_prefix(rng, rng.randrange(0, 6))]


def _unit(rng):
    if rng.random() < 0.35: body = '(' + ''.join(rng.choice('ab.') for _ in range(rng.randrange(1, 4))) + ')'
    else: body = rng.choice('aab.')
    return body + ('*' if rng.random() < 0.5 else '')


def _sample(rng, unit):
    star = unit.endswith('*'); body = unit.rstrip('*').strip('()')
    reps = rng.randrange(0, 3) if star else 1
    return ''.join(''.join(rng.choice('ab') if ch == '.' else ch for ch in body) for _ in range(reps))


def _rpm(rng):
    while True:
        units = [_unit(rng) for _ in range(rng.randrange(1, 6))]
        pattern = ''.join(units)
        if len(pattern) <= 24: break
    if rng.random() < 0.5:
        s = ''.join(_sample(rng, u) for u in units)
        if rng.random() < 0.3 and s:
            i = rng.randrange(len(s)); s = s[:i] + rng.choice('abc') + s[i + 1:]
    else:
        s = ''.join(rng.choice('ab') for _ in range(rng.randrange(0, 9)))
    return [s[:14], pattern]


def _sim(rng):
    m, n = rng.randrange(1, 7), rng.randrange(1, 7)
    return [[[0 if rng.random() < 0.45 else rng.randrange(1, 10) for _ in range(n)] for _ in range(m)]]


def _dls(rng):
    m, h = rng.randrange(1, 6), rng.randrange(1, 6)
    k = rng.randrange(1, min(m, h) + 1) if rng.random() < 0.85 else rng.randrange(1, 7)
    return [rng.randrange(1, 7), m, h, k]


def _dlv(rng):
    t, m, h = rng.randrange(1, 6), rng.randrange(1, 6), rng.randrange(1, 6)
    k = rng.randrange(1, min(m, h) + 1)
    sched = []
    for i in range(t):
        hs = rng.sample(range(1, h + 1), k); ms = rng.sample(range(1, m + 1), k)
        sched += [['t%d' % (i + 1), 'm%d' % a, 'h%d' % b] for a, b in zip(ms, hs)]
    rng.shuffle(sched)
    r = rng.random()
    if r < 0.12 and sched: sched.pop(rng.randrange(len(sched)))
    elif r < 0.24 and sched: sched.append(list(rng.choice(sched)))
    elif r < 0.36 and sched:
        e = rng.choice(sched); e[rng.randrange(3)] = rng.choice(['t0', 'm0', 'h0', 't01', 'm%d' % (m + 1), 'h%d' % (h + 1), 'x1', 'h1', 'm1', 't1'])
    elif r < 0.48 and sched:
        e = rng.choice(sched); e[1], e[2] = e[2], e[1]
    elif r < 0.6 and sched:
        e = rng.choice(sched); e[rng.choice([1, 2])] = rng.choice(['m1', 'm2', 'h1', 'h2'])
    if rng.random() < 0.15: k = rng.randrange(1, 4)
    return [t, m, h, k, sched]


POOL = [0, 1, True, False, None, '1', 'a b', [], [1, 2], [2, 1], [True], {}, {'a': 1, 'b': [1]}, {'b': [1], 'a': 1}, {'a': True}, [{'x': None}]]


def _kwargs(rng):
    keys = rng.sample(['a', 'b', 'c_d'], rng.randrange(0, 3))
    return {k: rng.choice(POOL) for k in keys}


def _fcc(rng):
    calls = []
    for _ in range(rng.randrange(0, 26)):
        if calls and rng.random() < 0.35:
            _, name, args, kw = rng.choice(calls)
            calls.append(('call', name, list(args), dict(reversed(list(kw.items())))))
        else: calls.append(('call', rng.choice(['f', 'g']), [rng.choice(POOL) for _ in range(rng.randrange(0, 3))], _kwargs(rng)))
    return _ops('FunctionCallCache', [rng.randrange(1, 5)], calls)


SIGS = {'f': [['a'], ['b', 0]], 'g': [['x', None], ['y', [1]]], 'h': [], 'k_2': [['p'], ['q'], ['r', {'z': True}]]}


def _fcs_call(rng, name):
    params = SIGS[name]; pos = rng.randrange(0, len(params) + 1); args, kw = [], {}
    for i, p in enumerate(params):
        if i < pos: args.append(rng.choice(POOL[:8]) if rng.random() < 0.8 or len(p) == 1 else p[1])
        elif len(p) == 1 or rng.random() < 0.5: kw[p[0]] = rng.choice(POOL[:8]) if rng.random() < 0.8 or len(p) == 1 else p[1]
    return ('call', name, args, kw)


def _respell(rng, call):
    """The same call written with a random split between positional, keyword and omitted default arguments."""
    _, name, args, kw = call; params = SIGS[name]
    bound = [args[i] if i < len(args) else kw[p[0]] if p[0] in kw else p[1] for i, p in enumerate(params)]
    pos = rng.randrange(0, len(params) + 1); new_kw = {}
    for i in range(len(params) - 1, pos - 1, -1):
        p = params[i]
        if len(p) == 1 or not _o.same(bound[i], p[1]) or rng.random() < 0.5: new_kw[p[0]] = bound[i]
    return ('call', name, bound[:pos], new_kw)


def _fcs(rng):
    names = rng.sample(list(SIGS), rng.randrange(1, 5)); sig = {n: SIGS[n] for n in names}
    calls = []
    for _ in range(rng.randrange(0, 26)):
        calls.append(_respell(rng, rng.choice(calls)) if calls and rng.random() < 0.4 else _fcs_call(rng, rng.choice(names)))
    return _ops('FunctionCallCache', [rng.randrange(1, 5), sig], calls)


def _grid(rng):
    m, n = rng.randrange(1, 8), rng.randrange(1, 8); p = rng.choice([0.15, 0.3, 0.45])
    return [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(m)]


def _cells(rng):
    return [_grid(rng), rng.choice([1, 1, 1, 2, 2, 2, 3, 3, 4, 5, 8])]


def _cgd(rng):
    return _cells(rng) + [rng.choice([0, 1, 2, 3, 5, 10**9])]


def _ote(rng):
    return [rng.randrange(1, 16), rng.randrange(1, 6), rng.randrange(1, 6), rng.randrange(1, 6), rng.randrange(1, 60)]


def _pae(rng):
    nums = [rng.randrange(0, 7) for _ in range(rng.randrange(1, 11))]
    return [nums, [[rng.randrange(0, 9), rng.randrange(0, 9)] for _ in range(rng.randrange(0, 7))]]


GEN = {_o.NCT: _nct, _o.OHE: _ohe, _o.PTP: _ptp, _o.RPM: _rpm, _o.SIM: _sim, _o.DLS: _dls, _o.DLV: _dlv, _o.FCC: _fcc, _o.FCS: _fcs,
       _o.CSD: _cells, _o.CIA: _cells, _o.CFG: _cells, _o.CGD: _cgd, _o.CID: _cells, _o.OTE: _ote, _o.PAE: _pae}

G1 = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
G2 = [[1, 0, 1], [0, 0, 0], [1, 0, 1]]
G3 = [[0, 0], [0, 0]]
HAND_CELLS = [[G1, 1], [G1, 2], [G2, 2], [G2, 4], [G3, 1], [[[1]], 8], [[[1, 1, 0, 0, 0]], 1], [[[1, 0, 1, 0, 0, 0, 1]], 2]]
HAND = {
    _o.NCT: [['a'], ['b'], ['z'], ['hello'], ['xyz'], ['aeiou'], ['abcdefghijklmnopqrstuvwxyz']],
    _o.OHE: [[[3]], [[2, 1, 2]], [[5, -5, 0, 5]], [[7, 7, 7]]],
    _o.PTP: [['A'], ['+AB'], ['*+AB-CD'], ['-a*bc'], ['^2^34'], ['/+ab+cd']],
    _o.RPM: [['', 'a*'], ['', 'a'], ['aab', 'a*b'], ['ab', '.b'], ['ababc', '(ab)*c'], ['abac', '(ab)*c'], ['', '(ab)*'], ['xyz', '(x.)*z'],
             ['aaa', 'a*a'], ['ab', '(.)*'], ['abab', '(a.)(b)*a.'], ['b', 'a*(ab)*b']],
    _o.SIM: [[[[0]]], [[[5]]], [[[1, 2, 0], [0, 3, 0], [4, 0, 9]]], [[[1, 0, 1], [0, 1, 0], [1, 0, 1]]], [[[2, 2], [2, 2]]]],
    _o.DLS: [[2, 3, 3, 2], [3, 2, 4, 2], [1, 1, 1, 1], [2, 1, 5, 2], [4, 5, 2, 2]],
    _o.DLV: [[2, 3, 3, 2, [['t1', 'm1', 'h1'], ['t1', 'm2', 'h2'], ['t2', 'm3', 'h3'], ['t2', 'm1', 'h1']]],
             [2, 3, 3, 2, [['t1', 'm1', 'h1'], ['t1', 'm2', 'h1'], ['t2', 'm3', 'h3'], ['t2', 'm1', 'h1']]],
             [2, 3, 3, 2, [['t1', 'm1', 'h1'], ['t1', 'm2', 'h2'], ['t2', 'm3', 'h3']]],
             [1, 2, 2, 1, [['t1', 'h1', 'm1']]], [1, 2, 2, 1, [['t1', 'm01', 'h1']]], [1, 1, 1, 1, []], [1, 1, 1, 1, [['t1', 'm1', 'h1']]]],
    _o.FCC: [_ops('FunctionCallCache', [2], [('call', 'f', [1], {}), ('call', 'f', [True], {}), ('call', 'f', [1], {}), ('call', 'f', ['1'], {}),
                                             ('call', 'f', [True], {}), ('call', 'g', [], {'a': 1, 'b': 2}), ('call', 'g', [], {'b': 2, 'a': 1}),
                                             ('call', 'g', [{'x': [1, 2], 'y': None}], {}), ('call', 'g', [{'y': None, 'x': [1, 2]}], {}),
                                             ('call', 'g', [{'x': [2, 1], 'y': None}], {})])],
    _o.FCS: [_ops('FunctionCallCache', [3, {'f': [['a'], ['b', 0]], 'g': [['a'], ['b', 0]]}],
                  [('call', 'f', [1], {}), ('call', 'f', [], {'a': 1}), ('call', 'f', [1, 0], {}), ('call', 'f', [], {'b': 0, 'a': 1}),
                   ('call', 'g', [1], {}), ('call', 'f', [1], {'b': False}), ('call', 'f', [1, 1], {}), ('call', 'f', [1], {'b': 1}), ('call', 'g', [], {'a': 1})])],
    _o.CSD: HAND_CELLS, _o.CIA: HAND_CELLS, _o.CFG: HAND_CELLS, _o.CID: HAND_CELLS,
    _o.CGD: [r + [d] for r in HAND_CELLS for d in (0, 1, 10**9)],
    _o.OTE: [[1, 1, 1, 1, 1], [3, 1, 1, 1, 10], [3, 2, 5, 1, 7], [5, 1, 10, 3, 100], [2, 5, 1, 9, 9]],
    _o.PAE: [[[1, 2, 3, 4], [[1, 3]]], [[5, 5, 6], []], [[1, 9], [[1, 5], [5, 9]]], [[4, 2, 4, 3, 2], [[2, 3], [3, 3]]]],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = list(HAND[uid]) + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a)
            category = 'independent-reference-at-scale' if expected is SCALE else 'analytic-maximum'
            if expected is SCALE: expected = _o.ref_ote(*a)
            rows.append({'args': a, 'expected': expected, 'category': category, 'isolate': True})
    return rows


SCALE = object()  # expected value computed by the unbudgeted independent reference (only Optimize Transition)
TABLE = dict(zip('abcdefghijklmnopqrstuvwxyz', 'acdfeghjiklmnpoqrstvuwxyzb'))  # worked by hand


def checker(n):
    """Checkerboard (i + j even infected), threshold 4: infection days worked by hand (see test_oracles)."""
    grid = [[1 if (i + j) % 2 == 0 else 0 for j in range(n)] for i in range(n)]
    day = []
    for i in range(n):
        row = []
        for j in range(n):
            edge = i in (0, n - 1) or j in (0, n - 1)
            corner = i in (0, n - 1) and j in (0, n - 1)
            row.append(0 if (i + j) % 2 == 0 else -1 if corner else 2 if edge else 1)
        day.append(row)
    return grid, day


def cell_rows(n):
    """(grid, threshold, infection-day matrix) constructions for the cellular variants."""
    corner = [[1 if (i, j) == (0, 0) else 0 for j in range(n)] for i in range(n)]
    top = [[1 if i == 0 else 0 for j in range(n)] for i in range(n)]
    board, board_day = checker(n)
    return [(corner, 1, [[max(i, j) for j in range(n)] for i in range(n)]), (top, 2, [[i for j in range(n)] for i in range(n)]),
            (board, 4, board_day), ([[0] * n for _ in range(n)], 1, [[-1] * n for _ in range(n)]),
            (top, 4, [[0 if i == 0 else -1 for j in range(n)] for i in range(n)])]


def cellular_expected(uid, day, days=None):
    last = max(0, max(max(r) for r in day))
    if uid == _o.CSD: return last
    if uid == _o.CIA: return -1 if any(-1 in r for r in day) else last
    if uid == _o.CFG: return [[1 if v >= 0 else 0 for v in r] for r in day]
    if uid == _o.CGD: return [[1 if 0 <= v <= days else 0 for v in r] for r in day]
    return day


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.NCT:
        out.append((['z' * n], 'b' * n))
        s = ('abcdefghijklmnopqrstuvwxyz' * 3847)[:n]
        out.append(([s], ''.join(TABLE[c] for c in s)))
        out.append((['aeiou' * 20000], 'aeiou' * 20000))
    elif uid == o.OHE:
        out.append(([[10**9 - i for i in range(1000)]], [[1 if j == 999 - i else 0 for j in range(1000)] for i in range(1000)]))
        out.append(([[5] * 1000], [[1] for _ in range(1000)]))
        out.append(([[-10**9 if i % 2 else 10**9 for i in range(1000)]], [[1, 0] if i % 2 else [0, 1] for i in range(1000)]))
        out.append(([[i // 2 for i in range(1000)]], [[1 if j == i // 2 else 0 for j in range(500)] for i in range(1000)]))
    elif uid == o.PTP:
        m = 49999
        out.append((['+' * m + 'A' * (m + 1)], 'AA' + '+A' * (m - 1) + '+'))
        out.append((['-A' * m + 'B'], 'A' * m + 'B' + '-' * m))
        pre, post = 'x', 'x'
        for d in range(15):
            op = '+-*/^'[d % 5]; pre = op + pre + pre; post = post + post + op
        out.append(([pre], post))
    elif uid == o.RPM:
        out += [(['a' * 1000, 'a*' * 100], True), (['a' * 1000, '(aa)*'], True), (['a' * 999, '(aa)*'], False), (['ab' * 500, '(a.)*'], True),
                (['a' * 1000, 'a*' * 99 + 'b'], False), (['a' * 990, '(aaaaaaaaaa)*'], True), (['abcde' * 200, '(.....)*'], True),
                (['abcde' * 199 + 'abcd', '(.....)*'], False), (['a' * 1000, '.*' * 100], True), (['a' * 1000, '(a)*' * 49 + 'b'], False),
                (['ab' * 500, '(ab)*' + 'c*' * 97], True), (['a' * 1000, '(' + 'a' * 198 + ')'], False), (['a' * 198, '(' + 'a' * 198 + ')'], True),
                (['a' * 999 + 'b', '(a)*' * 49 + 'b'], True)]
    elif uid == o.SIM:
        out.append(([[[10**6] * 200 for _ in range(200)]], 4 * 10**10))
        g = [[7 if (i + j) % 2 == 0 else 0 for j in range(200)] for i in range(200)]; g[100][100] = 10**6
        out.append(([g], 10**6))
        out.append(([[[0] * 200 for _ in range(200)]], 0))
        snake = [[3] * 200 if i % 2 == 0 else [3 if j == (199 if i % 4 == 1 else 0) else 0 for j in range(200)] for i in range(200)]
        out.append(([snake], 3 * (100 * 200 + 100)))
        out.append(([[[i + 1] * 200 if i % 2 == 0 else [0] * 200 for i in range(200)]], 199 * 200))
    elif uid in (o.DLS, o.DLV):
        def canon(t, m, h, k):
            return [['t%d' % (q // k + 1), 'm%d' % (q % m + 1), 'h%d' % (q % h + 1)] for q in range(t * k)]
        big = [(10**4, 10**4, 10**4, 10), (2000, 50, 50, 50), (n, 1, 1, 1), (10**4, 7, 9999, 7)]
        if uid == o.DLS:
            out += [(list(a), canon(*a)) for a in big]
            out.append(([10, 3, 5, 4], []))
        else:
            for a in big: out.append((list(a) + [canon(*a)], True))
            s = canon(*big[0]); s[-1] = [s[-1][0], s[-1][1], s[-2][2]]
            out.append((list(big[0]) + [s], False))
            s = canon(*big[1]); out.append((list(big[1]) + [s[:-1]], False))
            s = canon(*big[1]); s[0] = ['t01', s[0][1], s[0][2]]; out.append((list(big[1]) + [s], False))
            s = canon(*big[3]); s[5] = [s[5][0], 'm8', s[5][2]]; out.append((list(big[3]) + [s], False))
            s = canon(*big[2]); s[-1] = list(s[-2]); out.append((list(big[2]) + [s], False))
    elif uid == o.FCC:
        calls = [('call', 'f', [i], {}) for i in range(10**4)] * 2
        out.append((_ops('FunctionCallCache', [10**4], calls), [None] + [False] * 10**4 + [True] * 10**4))
        calls = [('call', 'x', [1 if i % 2 else True], {}) for i in range(20000)]
        out.append((_ops('FunctionCallCache', [1], calls), [None] + [False] * 20000))
        calls = [('call', 'f', [i % 6000], {}) for i in range(20000)]
        out.append((_ops('FunctionCallCache', [5000], calls), [None] + [False] * 20000))
        first = [('call', 'nested_fn', [i, {'k': [i, {'z': 'abc', 'a': None}]}], {'b': True, 'a': i}) for i in range(10**4)]
        second = [('call', 'nested_fn', [i, {'k': [i, {'a': None, 'z': 'abc'}]}], {'a': i, 'b': True}) for i in range(10**4)]
        out.append((_ops('FunctionCallCache', [10**4], first + second), [None] + [False] * 10**4 + [True] * 10**4))
    elif uid == o.FCS:
        sig = {'f': [['a'], ['b', 0], ['c', [1, {'x': None}]]], 'g': [['a']]}
        calls = [('call', 'f', [i], {}) for i in range(10**4)]
        calls += [('call', 'f', [], {'c': [1, {'x': None}], 'a': i}) if i % 2 else ('call', 'f', [i, 0], {}) for i in range(10**4)]
        out.append((_ops('FunctionCallCache', [10**4, sig], calls), [None] + [False] * 10**4 + [True] * 10**4))
        calls = [('call', 'f', [1] if i % 2 else [1, 1], {}) for i in range(20000)]
        out.append((_ops('FunctionCallCache', [1, sig], calls), [None] + [False] * 20000))
        calls = [('call', 'g' if i % 2 else 'f', [i // 2], {}) for i in range(20000)]
        out.append((_ops('FunctionCallCache', [3, sig], calls), [None] + [False] * 20000))
    elif uid in o.CELLULAR:
        for grid, threshold, day in cell_rows(200):
            if uid == o.CGD:
                for days in (0, 50, 10**9): out.append(([grid, threshold, days], cellular_expected(uid, day, days)))
            else: out.append(([grid, threshold], cellular_expected(uid, day)))
    elif uid == o.OTE:
        out += [([1000, 1, 1, 1, 1], 1000), ([1000, 1, 2, 1, 1], 1500), ([1000, 1, 5, 10**6, 10**9], 5000)]
        out += [([1000, 10**6, 1, 1, 10**9], SCALE), ([1000, 1000, 1, 999, 10**9], SCALE), ([1000, 7, 3, 5, 123456789], SCALE), ([997, 3, 1, 2, 10**9], SCALE)]
    elif uid == o.PAE:
        out.append(([list(range(n)), [[i, i + 1] for i in range(n - 1)]], [list(range(n))]))
        out.append(([list(range(n)), []], [[i] for i in range(n)]))
        out.append(([list(range(n)), [[i + 2, i] for i in range(n - 2)]], [list(range(0, n, 2)), list(range(1, n, 2))]))
        out.append(([[10**9 - (i % 3) for i in range(n)], [[10**9, -10**9], [-10**9, 10**9 - 2]]],
                    [[10**9 - (i % 3) for i in range(n) if i % 3 != 1], [10**9 - 1] * (n // 3)]))
    return out
