"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h16a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _gwc(rng, uid):
    words = ['err', 'Err', 'error', 'ok', 'warn', 'xerrx', '', 'e r r']
    lines = [' '.join(rng.choice(words) for _ in range(rng.randrange(0, 3))) for _ in range(rng.randrange(0, 25))]
    target = rng.choice(['err', 'Err', 'r', 'warn', 'e r', 'zzz'])
    if uid == _o.GWC1: return [lines, target, rng.randrange(0, 5)]
    return [lines, target, rng.randrange(0, 4), rng.randrange(0, 4)]


def _ges(rng):
    n = rng.randrange(0, 25); ids = rng.sample(range(0, 60), n)
    return [[[i] + [rng.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'][:rng.randrange(2, 9)]) + str(p) for p in range(3)] for i in ids]]


def _hee(rng):
    n = rng.randrange(1, 40); names = ['a', 'b', 'ab', 'c1', 'z']; ops, exps, ds = [], [], []
    for _ in range(n):
        if rng.random() < 0.6: ops.append('U'); exps.append(rng.choice(names)); ds.append(rng.randrange(-6, 7))
        else: ops.append('Q'); exps.append(rng.choice(['', 'a', 'q9'])); ds.append(rng.choice([0, 0, 5, -3]))
    return [ops, exps, ds]


def _jbs(rng):
    vocab = ['Joe', 'joe', 'Pizza', 'Inc.', '&', 'Co', 'pizza', "Joe's"]
    def name(): return ' '.join(rng.choice(vocab[:rng.randrange(1, 9)]) for _ in range(rng.randrange(0, 7)))
    return [name(), name()]


def _lot(rng):
    n = rng.randrange(0, 12); tasks = rng.sample(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'ab', 'ba'], n)
    order = list(tasks); rng.shuffle(order); deps = set()
    for _ in range(rng.randrange(0, 2 * n + 1)):
        i, j = rng.randrange(n), rng.randrange(n)
        if i == j: continue
        if rng.random() < 0.9 and i > j: i, j = j, i
        deps.add((order[i], order[j]))
    deps = sorted(deps); rng.shuffle(deps)
    return [tasks, [list(d) for d in deps]]


def _lps(rng):
    alpha = 'ab' if rng.random() < 0.7 else 'abc'; unit = ''.join(rng.choice(alpha) for _ in range(rng.randrange(1, 5)))
    s = (unit * rng.randrange(1, 8))[:rng.randrange(1, 30)] if rng.random() < 0.6 else ''.join(rng.choice(alpha) for _ in range(rng.randrange(1, 30)))
    return [s or 'a']


def _mes(rng):
    n = rng.randrange(1, 7); pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
    edges = rng.sample(pairs, rng.randrange(0, len(pairs) + 1))
    return [n, [[b, a] if rng.random() < 0.5 else [a, b] for a, b in edges]]


def _mnk(rng):
    s = str(rng.randrange(1, 10)) + ''.join(rng.choice('0123456789555') for _ in range(rng.randrange(0, 10)))
    return [s, rng.randrange(0, 6)]


def _mst(rng):
    return [[rng.randrange(1, 12) for _ in range(rng.randrange(0, 10))]]


def _mpq(rng):
    n = rng.randrange(1, 10)
    return [[rng.randrange(1, 15) for _ in range(n)], [rng.randrange(1, 20) for _ in range(n)], rng.randrange(0, 40)]


def _mss(rng):
    n = rng.randrange(1, 9); names = ['lodge'] + ['c%d' % i for i in range(1, n)]
    routes = []
    for _ in range(rng.randrange(0, min(14, n * (n - 1) // 2 + 1) + 1)):
        if n < 2: break
        i, j = sorted(rng.sample(range(n), 2))
        routes.append([names[i], rng.randrange(0, 8), names[j]])
    cps = [[x, rng.randrange(0, 10)] for x in names if rng.random() < 0.8]
    rng.shuffle(cps)
    return [routes, cps]


def _msp(rng):
    days = [rng.randrange(1, 8) for _ in range(rng.randrange(1, 8))]
    return [days, rng.randrange(1, sum(days) + 1)]


def _mcs(rng):
    alpha = 'ab' if rng.random() < 0.7 else 'abc'
    base = ''.join(rng.choice(alpha) for _ in range(rng.randrange(1, 20)))
    a = base[:rng.randrange(1, len(base) + 1)]
    b = base[rng.randrange(0, len(base)):] + ''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 5)))
    if rng.random() < 0.5: a, b = b or 'a', a
    return [a or 'b', b or 'a']


def _mje(rng):
    logs = {}
    for sid in rng.sample(['a', 'b', 'srv1', 's10', 's2', 'zz'], rng.randrange(1, 5)):
        t, ev = rng.randrange(0, 3), []
        for _ in range(rng.randrange(0, 6)):
            t += rng.choice([0, 0, 1, 2]); e = {'time': t, 'type': rng.choice(['send', 'receive', 'idle'])}
            if e['type'] != 'idle' and rng.random() < 0.8: e['target'] = rng.choice(['a', 'b', 'srv1', 'q'])
            ev.append(e)
        logs[sid] = ev
    return [logs]


def _ivs(rng):
    out, x = [], rng.randrange(-20, 5)
    for _ in range(rng.randrange(0, 7)):
        s = x + rng.randrange(0, 4); e = s + rng.randrange(0, 5); out.append([s, e]); x = e + 1
    return out


def _mti(rng): return [_ivs(rng), _ivs(rng)]


def _mua(rng):
    def arr(): return sorted(rng.randrange(-8, 9) for _ in range(rng.randrange(0, 12)))
    return [arr(), arr()]


GEN = {}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.GWC1:
        doc = ['alpha', 'Alexandra', 'beta', 'gamma', 'alex', 'delta', 'ALEX', 'Alex']
        args = [[[], 'x', 3], [doc, 'Alex', 0], [doc, 'Alex', 1], [doc, 'Alex', 100], [doc, 'zeta', 2], [['a', 'a', 'a'], 'a', 1], [['xy'], 'xyz', 0]]
        args += [_gwc(rng, uid) for _ in range(250)]
    elif uid == o.GWC2:
        doc = ['m1', 'a', 'b', 'c', 'd', 'm2', 'e', 'f', 'g', 'h', 'i', 'm3']
        args = [[[], 'x', 1, 1], [doc, 'm', 0, 0], [doc, 'm', 1, 1], [doc, 'm', 2, 2], [doc, 'm', 0, 4], [doc, 'q', 5, 5], [['m', 'x', 'm'], 'm', 0, 0]]
        args += [_gwc(rng, uid) for _ in range(250)]
    elif uid == o.GES:
        args = [[[]], [[[1, 'a', 'b', 'c']]], [[[3, 'a', 'x', 'y'], [1, 'b', 'x', 'z'], [2, 'c', 'w', 'z'], [9, 'd', 'e', 'f']]],
                [[[5, 'a', 'b', 'c'], [4, 'b', 'c', 'a']]], [[[7, 'p', 'q', 'r'], [8, 'p', 'q', 'r'], [6, 's', 't', 'u']]]]
        args += [_ges(rng) for _ in range(250)]
    elif uid == o.HEE:
        args = [[['Q'], [''], [0]], [['U', 'U', 'Q', 'U', 'Q', 'U', 'Q'], ['b', 'a', '', 'b', '', 'a', ''], [5, 5, 0, -1, 0, -10, 0]],
                [['U', 'Q', 'U', 'Q'], ['x', '', 'x', 'zz'], [-3, 7, 3, -1]]]
        args += [_hee(rng) for _ in range(250)]
    elif uid == o.JBS:
        args = [['', ''], ['a', ''], ['', 'b'], ['Joe Pizza', 'Joe Pizza'], ['Joe Pizza Co', 'Pizza Co Inc'], ['a b c', 'A B C'], ['a a a', 'a'],
                ['a b c d e f g h', 'a'], ['a b c', 'a d e f g h i j']]
        args += [_jbs(rng) for _ in range(250)]
    elif uid == o.LOT:
        args = [[[], []], [['a'], []], [['b', 'a', 'c'], [['a', 'c'], ['b', 'c']]], [['x', 'y'], [['x', 'y'], ['y', 'x']]],
                [['d', 'c', 'b', 'a'], [['a', 'b'], ['b', 'c'], ['a', 'c'], ['a', 'd']]]]
        args += [_lot(rng) for _ in range(250)]
    elif uid == o.LPS:
        args = [['a'], ['aa'], ['ab'], ['aaaa'], ['abcab'], ['aabcdaabc'], ['abab'], ['abcd']]
        args += [_lps(rng) for _ in range(250)]
    elif uid == o.MES:
        args = [[1, []], [2, [[0, 1]]], [3, [[0, 1], [1, 2]]], [4, [[0, 1], [0, 2], [0, 3]]], [5, []], [3, [[2, 0]]]]
        args += [_mes(rng) for _ in range(250)]
    elif uid == o.MNK:
        args = [['1', 0], ['1', 1], ['5', 3], ['9', 1], ['1234', 2], ['6142', 1], ['555', 2], ['105', 5], ['99', 2]]
        args += [_mnk(rng) for _ in range(250)]
    elif uid == o.MST:
        args = [[[]], [[4, 2]], [[1, 2, 3]], [[1, 2, 3, 4, 5, 6]], [[5, 5, 5, 5, 5]], [[9, 1, 8, 2, 7, 3, 6, 4, 5]]]
        args += [_mst(rng) for _ in range(250)]
    elif uid == o.MPQ:
        args = [[[5], [3], 4], [[5], [3], 5], [[2, 3], [3, 4], 6], [[2, 3], [4, 6], 6], [[1, 2], [1, 3], 7], [[7, 8], [1, 1], 0]]
        args += [_mpq(rng) for _ in range(250)]
    elif uid == o.MSS:
        args = [[[], []], [[], [['lodge', 5]]], [[['lodge', 2, 'a'], ['a', 1, 'b'], ['lodge', 0, 'b']], [['a', 4], ['b', 3]]],
                [[['lodge', 9, 'a']], [['a', 1]]], [[['lodge', 0, 'a'], ['lodge', 5, 'a'], ['x', 0, 'lodge']], [['a', 2], ['x', 100]]],
                [[['lodge', 1, 'a'], ['a', 1, 'b'], ['a', 1, 'c'], ['c', 1, 'd']], [['a', 1], ['b', 1], ['c', 2], ['d', 0]]]]
        args += [_mss(rng) for _ in range(250)]
    elif uid == o.MSP:
        args = [[[1], 1], [[3], 2], [[3], 3], [[1, 3, 1], 2], [[2, 3, 1], 3], [[3, 3, 3], 5], [[4, 1], 5]]
        args += [_msp(rng) for _ in range(250)]
    elif uid == o.MCS:
        args = [['abc', 'cde'], ['abc', 'def'], ['abab', 'abab'], ['a', 'a'], ['abcab', 'ab'], ['xab', 'abab'], ['aaa', 'aaaa']]
        args += [_mcs(rng) for _ in range(250)]
    elif uid == o.MJE:
        args = [[{'a': []}], [{'s1': [{'time': 1, 'type': 'send', 'target': 's2'}, {'time': 5, 'type': 'idle'}],
                               's2': [{'time': 1, 'type': 'receive', 'target': 's1'}, {'time': 3, 'type': 'idle'}]}],
                [{'b': [{'time': 2, 'type': 'idle'}], 'a': [{'time': 2, 'type': 'send', 'target': 'b'}, {'time': 2, 'type': 'idle'}]}]]
        args += [_mje(rng) for _ in range(250)]
    elif uid == o.MTI:
        args = [[[], []], [[[1, 3]], []], [[[1, 3], [6, 9]], [[2, 5]]], [[[1, 3]], [[3, 5]]], [[[1, 2]], [[3, 4]]], [[[0, 10]], [[2, 3], [5, 6], [11, 12]]],
                [[[1, 1], [3, 3]], [[2, 2]]]]
        args += [_mti(rng) for _ in range(250)]
    elif uid == o.MUA:
        args = [[[], []], [[1, 1, 2], []], [[], [-1, -1]], [[1, 3, 5], [2, 3, 4]], [[1, 2, 2, 3], [2, 2, 2]]]
        args += [_mua(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid in o.GWC:
        lines = ['ERROR %d' % i if i % 1000 == 0 else 'line %d' % i for i in range(n)]
        if uid == o.GWC1:
            out.append(([lines, 'ERROR', 2], [lines[i] for i in range(n) if i % 1000 <= 2 or (i % 1000 >= 998 and i < 99000)]))
            out.append(([lines, 'ERROR 5', 100000], list(lines)))
            out.append(([lines, 'line', 0], [lines[i] for i in range(n) if i % 1000]))
            out.append(([lines, 'nothing', 100000], []))
        else:
            out.append(([lines, 'ERROR', 3, 1], [lines[max(0, j - 3):j + 2] for j in range(0, n, 1000)]))
            out.append(([lines, 'ERROR', 999, 0], [lines[:99001]]))
            out.append(([lines, 'ERROR 99000', 0, 100000], [lines[99000:]]))
            out.append(([lines, 'nothing', 5, 5], []))
    elif uid == o.GES:
        chain = [[(n - 1 - i) * 3, 'a' + _code(i // 2, 4), 'b' + _code((i + 1) // 2, 4), 'c' + _code(i, 4)] for i in range(n)]
        out.append(([chain], [[3 * i for i in range(n)]]))
        alone = [[i, 'a' + _code(i, 4), 'b' + _code(i, 4), 'c' + _code(i, 4)] for i in range(n)]
        out.append(([alone], [[i] for i in range(n)]))
        quads = [[i, 'a' + _code(i // 2, 4), 'b' + _code(i // 4, 4), 'c' + _code(i, 4)] for i in range(n // 2)]
        out.append(([quads], [[4 * g, 4 * g + 1, 4 * g + 2, 4 * g + 3] for g in range(n // 8)]))
    elif uid == o.HEE:
        names = ['e' + _code(j, 3) for j in range(1000)]
        ops, exps, ds, want = [], [], [], []
        for j in range(1000): ops.append('U'); exps.append(names[j]); ds.append(j)
        for t in range(999):
            ops += ['U', 'Q']; exps += [names[999 - t], '']; ds += [-10**6, 0]; want.append(names[998 - t])
        out.append(([ops, exps, ds], want))
        ops, exps, ds, want = [], [], [], []
        for j in range(1000): ops.append('U'); exps.append(names[j]); ds.append(5)
        for t in range(24500):
            x = names[(t * 37) % 1000]
            ops += ['U', 'Q', 'U', 'Q']; exps += [x, '', x, '']; ds += [1, 0, -1, 0]; want += [x, names[0]]
        out.append(([ops, exps, ds], want))
        out.append(([['U'] * (n - 1) + ['Q'], ['big'] * (n - 1) + [''], [10**9] * (n - 1) + [0]], ['big']))
    elif uid == o.JBS:
        a = ' '.join(_code(i, 4) for i in range(20000)); b = ' '.join(_code(i, 4) for i in range(10000, 30000))
        out.append(([a, b], 0.33))
        out.append(([a, a], 1.0))
        out.append(([' '.join(['x'] * 50000), 'x'], 1.0))
        out.append(([a, ''], 0.0))
    elif uid == o.LOT:
        names = [_code(i, 4) for i in range(n)]
        out.append(([names, [[names[i], names[i + 1]] for i in range(n - 1)]], [[x] for x in names]))
        rev = names[::-1]
        out.append(([rev, [[names[2 * i + 1], names[2 * i]] for i in range(n // 2)]], [sorted(names[1::2]), sorted(names[0::2])]))
        out.append(([names, [[names[i], names[i + 1]] for i in range(n - 1)] + [[names[-1], names[0]]]], []))
        out.append(([rev, []], [list(names)]))
    elif uid == o.LPS:
        out.append((['a' * n], n - 1))
        out.append((['ab' * (n // 2)], n - 2))
        out.append((['a' * (n - 1) + 'b'], 0))
        out.append((['abc' * 33333 + 'a'], 99997))
    elif uid == o.MES:
        out.append(([n, [[0, i] for i in range(1, n)]], n * (n - 1) + (n - 1) * n // 2))
        out.append(([n, [[i, i + 1] for i in range(n - 1)]], 3 + 2 * (n * (n + 1) // 2 - 3)))
        out.append(([n, []], 0))
    elif uid == o.MNK:
        out.append((['1' * n, n // 2], '5' * (n // 2) + '1' * (n // 2)))
        out.append((['9' * n, n], '9' * n))
        out.append((['4' + '6' * (n - 1), 1], '5' + '6' * (n - 1)))
        out.append((['3' * n, n], '5' * n))
    elif uid == o.MST:
        c = 33333
        out.append(([list(range(1, n))], c * 99999 - c * c))
        out.append(([[10**9] * n], c * 10**9))
        out.append(([list(range(n, 0, -1))], sum(n - 1 - 2 * i for i in range(c))))
    elif uid == o.MPQ:
        out.append(([list(range(1, n + 1)), [10**4] * n, 10**9], [10**13, 0]))
        out.append(([[10**9] * n, [10**4] * n, 10**9 - 1], [0, -1]))
        out.append(([[2] * n, [1] * (n - 1) + [10**4], 10**9], [5 * 10**12, n - 1]))
    elif uid == o.MSS:
        L = n - 1; names = ['lodge'] + ['c' + _code(i, 4) for i in range(1, L + 1)]
        routes = [[names[i], 1, names[i + 1]] for i in range(L)]
        out.append(([routes, [[x, 3] for x in names[1:]]], 2 * L))
        layers = 24999; routes, cps = [], [['lodge', 7]]
        prev = ['lodge']
        for k in range(layers):
            cur = ['a' + _code(k, 4), 'b' + _code(k, 4)]
            for p in prev:
                for q in cur: routes.append([p, 0, q])
            cps += [[cur[0], 10], [cur[1], 1]]; prev = cur
        out.append(([routes, cps], 10 * layers))
        out.append(([[[names[i], 10**6, names[i + 1]] for i in range(L)], []], -10**6 * L))
    elif uid == o.MSP:
        big = n * (n + 1) // 2
        out.append(([[n] * n, n], big))
        out.append(([[1, n] * (n // 2), n + 1], big + 1))
        days = [i % 7 + 1 for i in range(n)]
        out.append(([days, sum(days)], sum(d * (d + 1) // 2 for d in days)))
        out.append(([[n] * n, 1], n))
    elif uid == o.MCS:
        out.append((['a' * n, 'a' * n], 'a' * n))
        out.append((['ab' * (n // 2), 'b' + 'a' * (n - 1)], 'ab' * (n // 2) + 'a' * (n - 1)))
        out.append((['z' * n, 'a' * n], 'z' * n + 'a' * n))
        out.append((['b' + 'a' * (n - 1), 'a' * (n - 1) + 'c'], 'b' + 'a' * (n - 1) + 'c'))
    elif uid == o.MJE:
        sids = ['s' + _code(i, 3) for i in range(1000)]
        logs = {sid: [{'time': j, 'type': 'send', 'target': sids[(i + 1) % 1000]} for j in range(100)] for i, sid in enumerate(reversed(sids))}
        want = [{'serverId': sid, 'time': j, 'type': 'send', 'target': sids[(i + 1) % 1000]} for j in range(100) for i, sid in sorted(enumerate(reversed(sids)), key=lambda p: p[1])]
        out.append(([logs], want))
        one = [{'time': i, 'type': 'idle'} for i in range(n)]
        out.append(([{'solo': one}], [{'serverId': 'solo', 'time': i, 'type': 'idle'} for i in range(n)]))
    elif uid == o.MTI:
        out.append(([[[4 * i, 4 * i + 1] for i in range(n)], [[4 * i + 1, 4 * i + 2] for i in range(n)]], [[4 * i, 4 * i + 2] for i in range(n)]))
        out.append(([[[4 * i, 4 * i + 1] for i in range(n)], [[4 * i + 2, 4 * i + 3] for i in range(n)]], [[2 * i, 2 * i + 1] for i in range(2 * n)]))
        out.append(([[[4 * i, 4 * i + 1] for i in range(n)], [[-10**9, 10**9]]], [[-10**9, 10**9]]))
    elif uid == o.MUA:
        a = list(range(0, 2 * n, 2)); b = list(range(0, 3 * n, 3))
        out.append(([a, b], sorted(set(a) | set(b))))
        out.append(([[5] * n, [5] * n], [5]))
        out.append(([list(range(-10**9, -10**9 + n)), list(range(10**9 - n + 1, 10**9 + 1))], list(range(-10**9, -10**9 + n)) + list(range(10**9 - n + 1, 10**9 + 1))))
    return out
