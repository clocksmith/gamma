"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h12a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _tree_from_parents(vals, parent):
    """Canonical level-order list of the tree whose node i has parent[i] (parent[0] == -1, parents precede children)."""
    kids = [[] for _ in vals]
    for i in range(1, len(vals)): kids[parent[i]].append(i)
    order, out_vals, out_kids, index = [0] if vals else [], [], [], {}
    for v in order:
        index[v] = len(out_vals); out_vals.append(vals[v]); order.extend(kids[v])
    for v in order: out_kids.append([index[c] for c in kids[v]])
    return _o.nary_serialize(out_vals, out_kids)


def _tree(rng, n, lo=-20, hi=20):
    vals = [rng.randrange(lo, hi + 1) for _ in range(n)]
    parent = [-1] + [rng.randrange(max(0, i - rng.choice([1, 3, i])), i) for i in range(1, n)]
    return _tree_from_parents(vals, parent)


def _records(rng):
    fields = ['name', 'email', 'company', 'phone'][:rng.randrange(1, 5)]
    header = ['id'] + fields
    rng.shuffle(header)
    pool = {f: ['', 'a', 'b', 'c', 'x@y.z'] for f in fields}
    rows = [header]
    for i in range(rng.randrange(0, 15)):
        rows.append([('u%d' % i) if f == 'id' else rng.choice(pool[f]) for f in header])
    cuts = sorted(rng.randrange(0, 10001) for _ in range(len(fields) - 1))
    parts = [b - a for a, b in zip([0] + cuts, cuts + [10000])]
    weights = []
    for f, u in zip(fields, parts):
        s = '%d.%04d' % (u // 10000, u % 10000)
        weights.append('%s:%s' % (f, s.rstrip('0').rstrip('.') if rng.random() < 0.5 and '.' in s else s))
    rng.shuffle(weights)
    t = rng.choice([0, 1, 0.5, 0.25, 0.3, 0.6, 0.75, 0.1, 1.0, 0.0001, 0.9999, 0.4])
    return [rows, weights, t]


def _lfc(rng):
    n = rng.randrange(1, 9); names = ['s%d' % i for i in range(n)]
    edges = [[names[a], names[b]] for a in range(n) for b in range(a + 1, n) if rng.random() < 0.35]
    rng.shuffle(edges)
    return [edges, rng.choice(names[:max(1, n // 2)])]


def _lvp(rng):
    alphabet = rng.choice(['()', '()[]', '(){}[]', '[]{}', '(){}[]'])
    return [''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 23)))]


def _grid(rng, alphabet, weights, must=None):
    m, n = rng.randrange(1, 11), rng.randrange(1, 11)
    while m * n > 120: n -= 1
    g = [[rng.choices(alphabet, weights)[0] for _ in range(n)] for _ in range(m)]
    if must:
        for row in g:
            for j, ch in enumerate(row):
                if ch == must: row[j] = '.'
        g[rng.randrange(m)][rng.randrange(n)] = must
    return [[''.join(r) for r in g]]


def _mco(rng):
    n = rng.randrange(1, 40)
    p = rng.random()
    return [''.join('1' if rng.random() < p else '0' for _ in range(n)), rng.randrange(0, 5)]


def _mfd(rng):
    n = rng.randrange(1, 15)
    return [[rng.choice([0, 1, 2, 5, 9, 100, 10**9]) for _ in range(n)], rng.randrange(0, 6)]


def _mle(rng):
    n = rng.randrange(1, 30)
    return [[rng.randrange(0, 6) for _ in range(n)], [rng.randrange(0, 8) for _ in range(n)], rng.randrange(0, 25)]


def _mbt(rng):
    m = rng.randrange(1, 6)
    return [m, [rng.randrange(1, 6) for _ in range(rng.randrange(0, 15))]]


def _mio(rng):
    out = []
    for _ in range(rng.randrange(0, 25)):
        s = rng.randrange(-10, 11); out.append([s, s + rng.choice([0, 0, 1, 2, 5, 9])])
    return [out]


def _mmp(rng):
    n = rng.randrange(1, 9)
    edges = [[u, v, rng.randrange(0, 11)] for u in range(n) for v in range(n) if u != v and rng.random() < 0.4]
    rng.shuffle(edges)
    return [n, edges, rng.randrange(n), rng.randrange(n)]


def _mvf(rng):
    m = rng.randrange(1, 8); n = rng.randrange(1, 12)
    return [[[rng.randrange(0, 8) for _ in range(n)] for _ in range(m)]]


def _mmq(rng):
    calls, size = [], 0
    for _ in range(rng.randrange(0, 60)):
        r = rng.random()
        if size == 0 or r < 0.4: calls.append(('enqueue', rng.randrange(-5, 6))); size += 1
        elif r < 0.6: calls.append(('dequeue',)); size -= 1
        elif r < 0.8: calls.append(('getMin',))
        else: calls.append(('getMax',))
    return _ops('MinMaxQueue', [], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid in (o.LMN, o.MRP):
        args = [[[]], [[7]], [[1, None, 3, 2, 4, None, 5, 6]], [[1, None, 2, 3, None, None, 4, None, 5, 6]], [[-5, None, 2, -9, None, None, 1]]]
        args += [[_tree(rng, rng.randrange(1, 60))] for _ in range(250)]
    elif uid in o.LUR:
        sample = [['id', 'name', 'email', 'company'], ['1', 'Ann', 'a@x.io', 'Acme'], ['2', 'Ann', 'a@x.io', 'Bolt'], ['3', 'Bo', 'b@x.io', 'Acme'],
                  ['4', 'Bo', 'a@x.io', ''], ['5', 'Cy', '', '']]
        args = [[[['id', 'name']], ['name:1'], 0.5], [sample, ['name:0.5', 'email:0.3', 'company:0.2'], 0.5], [sample, ['email:0.6', 'name:0.4'], 0.6],
                [sample, ['company:1.0'], 0], [sample, ['name:0.25', 'email:0.75'], 1]]
        args += [_records(rng) for _ in range(250)]
    elif uid == o.LFC:
        args = [[[], 'api'], [[['api', 'auth'], ['api', 'db'], ['auth', 'db'], ['db', 'disk'], ['cache', 'db']], 'api'], [[['a', 'b'], ['b', 'c']], 'b']]
        args += [_lfc(rng) for _ in range(250)]
    elif uid == o.LVP:
        args = [[''], ['()'], ['([])'], ['[()]'], ['{[()]}'], ['(()'], [')()())'], ['{}[]()'], ['[[]]{{}}'], ['(]'], ['{([])}']]
        args += [_lvp(rng) for _ in range(250)]
    elif uid == o.MES:
        args = [[['U']], [['XXX', 'XUX', 'X.X']], [['XXXX', 'XU.X', 'XX.X']], [['P..', '.U.', '...']], [['.....', '.XXX.', '.XUX.', '.X.X.', '.X.XP']],
                [['X.X', 'XUX', 'XPX']]]
        args += [_grid(rng, 'P.X', [1, 6, 3], 'U') for _ in range(250)]
    elif uid == o.MCO:
        args = [['0', 0], ['0', 1], ['1', 0], ['1001101', 1], ['1001101', 2], ['000', 0], ['0101010', 3]]
        args += [_mco(rng) for _ in range(250)]
    elif uid == o.MFD:
        args = [[[5], 0], [[5], 1], [[3, 1, 4, 1, 5], 1], [[3, 1, 4, 1, 5], 2], [[1, 9, 1, 9], 1]]
        args += [_mfd(rng) for _ in range(250)]
    elif uid == o.MLE:
        args = [[[1], [0], 0], [[1], [0], 1], [[2, 1, 3, 1], [1, 0, 2, 0], 6], [[0, 0], [5, 0], 4]]
        args += [_mle(rng) for _ in range(250)]
    elif uid == o.MBT:
        args = [[1, []], [3, [1, 1, 1]], [2, [1, 1, 2, 2, 3]], [2, [5, 5, 5, 6]], [3, [1, 2, 3, 1, 2, 3, 4]]]
        args += [_mbt(rng) for _ in range(250)]
    elif uid == o.MBH:
        args = [[['P']], [['-']], [['P--']], [['P-X-']], [['---', '-P-', '---']], [['P----', 'XXXX-', '-----']], [['X']]]
        args += [_grid(rng, 'P-X', [1, 8, 2]) for _ in range(250)]
    elif uid == o.MIO:
        args = [[[]], [[[1, 3], [3, 5]]], [[[1, 2], [3, 4]]], [[[1, 10], [2, 3], [4, 5], [2, 4]]], [[[0, 0], [0, 0], [-1, 0]]]]
        args += [_mio(rng) for _ in range(250)]
    elif uid == o.MMP:
        args = [[1, [], 0, 0], [2, [], 0, 1], [3, [[0, 1, 2], [1, 2, 3], [0, 2, 5]], 0, 2], [3, [[0, 1, 2], [1, 2, 3], [0, 2, 7]], 0, 2],
                [4, [[0, 1, 0], [1, 3, 10], [0, 2, 1], [2, 3, 1]], 0, 3]]
        args += [_mmp(rng) for _ in range(250)]
    elif uid == o.MVF:
        args = [[[[0]]], [[[1, 1], [2, 2]]], [[[7, 0, 7], [0, 7, 0]]], [[[3, 3], [3, 3]]], [[[0, 5], [5, 0], [5, 5]]]]
        args += [_mvf(rng) for _ in range(250)]
    elif uid == o.MNT:
        args = [[[], []], [[1], []], [[], [2, None, 3]], [[1, None, 2, 3], [10, None, 20, None, 30]], [[1, None, 3, 2, 4, None, 5, 6], [1, None, 1, 1]]]
        args += [[_tree(rng, rng.randrange(0, 40)), _tree(rng, rng.randrange(0, 40))] for _ in range(250)]
    elif uid == o.MMQ:
        args = [_ops('MinMaxQueue', [], []),
                _ops('MinMaxQueue', [], [('enqueue', 3), ('enqueue', 1), ('enqueue', 2), ('getMin',), ('getMax',), ('dequeue',), ('getMax',), ('dequeue',),
                                         ('getMin',), ('enqueue', 2), ('getMax',), ('dequeue',), ('getMin',)])]
        args += [_mmq(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _chain(vals): return _tree_from_parents(vals, [-1] + list(range(len(vals) - 1)))


def _star(vals): return _tree_from_parents(vals, [-1] + [0] * (len(vals) - 1))


def _heap(vals): return _tree_from_parents(vals, [-1] + [(i - 1) // 2 for i in range(1, len(vals))])


def _serpentine(fill, start, end_cell):
    """399 x 500 grid: border X, corridors on odd rows, walls on even rows with gaps alternating right/left."""
    H, W = 399, 500
    g = [['X'] * W for _ in range(H)]
    for r in range(1, H - 1, 2):
        for c in range(1, W - 1): g[r][c] = fill
    for j in range(1, 199): g[2 * j][W - 2 if j % 2 else 1] = fill
    g[start[0]][start[1]] = start[2]
    if end_cell: g[end_cell[0]][end_cell[1]] = end_cell[2]
    return g


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.LMN:
        out.append(([_chain([7] * n)], 1))
        out.append(([_star(list(range(n)))], 2))
        out.append(([_heap([1] * n)], 17))  # levels 1..16 hold 2**(L-1) nodes; level 17 holds 100000 - 65535 = 34465 > 32768
        k = 49999  # root, k children, one grandchild under each child: levels 2 and 3 tie, the smaller wins
        out.append(([_tree_from_parents([5] * (1 + 2 * k), [-1] + [0] * k + list(range(1, k + 1)))], 2))
    elif uid in o.LUR:
        m = 500
        rows = [['id', 'name', 'email', 'company']] + [['u%d' % i, 'Same', 'e%d@x' % i, 'c%d' % i] for i in range(m)]
        ids = ['u%d' % i for i in range(m)]
        w = ['name:0.5', 'email:0.3', 'company:0.2']
        exp = {o.LUR1: [[ids[i], ids[j]] for i in range(m) for j in range(i + 1, m)], o.LUR2: [ids], o.LUR3: [ids[1]] + [ids[0]] * (m - 1)}[uid]
        out.append(([rows, w, 0.5], exp))
        rows = [['email', 'id', 'name']] + [['g%d@x' % (i // 5), 'u%d' % i, 'n%d' % i] for i in range(m)]
        exp = {o.LUR1: [[ids[i], ids[j]] for i in range(m) for j in range(i + 1, m) if i // 5 == j // 5],
               o.LUR2: [ids[g * 5:g * 5 + 5] for g in range(m // 5)],
               o.LUR3: [ids[g * 5 + (1 if i % 5 == 0 else 0)] for i in range(m) for g in [i // 5]]}[uid]
        out.append(([rows, ['name:0.7', 'email:0.3'], 0.3], exp))
        rows = [['id', 'name']] + [['u%d' % i, 'n%d' % i] for i in range(m)]
        out.append(([rows, ['name:1'], 1.0], {o.LUR1: [], o.LUR2: [], o.LUR3: [''] * m}[uid]))
        # chain linking via alternating shared fields: record i shares name with i+1 when i even, email when i odd
        rows = [['id', 'name', 'email']] + [['u%d' % i, 'n%d' % ((i + 1) // 2), 'e%d' % (i // 2)] for i in range(m)]
        exp = {o.LUR1: [[ids[i], ids[i + 1]] for i in range(m - 1)], o.LUR2: [ids],
               o.LUR3: [ids[1]] + [ids[i - 1] for i in range(1, m)]}[uid]
        out.append(([rows, ['name:0.5', 'email:0.5'], 0.5], exp))
    elif uid == o.LFC:
        names = ['v%d' % i for i in range(n)]
        out.append(([[[names[i], names[i + 1]] for i in range(n - 1)], names[0]], sorted([[v, 1] for v in names])))
        layers = 52; edges = [['e', 'a0'], ['e', 'b0']]
        for i in range(layers):
            for x in 'ab':
                for y in 'ab': edges.append(['%s%d' % (x, i), '%s%d' % (y, i + 1)])
        loads = [['e', 1]] + [['%s%d' % (x, i), 2**i] for i in range(layers + 1) for x in 'ab']
        fan = ['f%d' % i for i in range(n - 2 * layers - 3)]
        edges += [['e', f] for f in fan]
        out.append(([edges, 'e'], sorted(loads + [[f, 1] for f in fan])))
        edges = [['x%d' % i, 'y%d' % i] for i in range(50000)] + [['root', 'y0']]
        exp = sorted([['x%d' % i, 0] for i in range(50000)] + [['y%d' % i, 0] for i in range(1, 50000)] + [['y0', 1], ['root', 1]])
        out.append(([edges, 'root'], exp))
    elif uid == o.LVP:
        out.append((['()' * 50000], n))
        out.append((['{[()]}' * 16666], 99996))
        out.append((['([])' * 25000], 2))
        out.append((['(' * 50000 + ')' * 50000], n))
        out.append((['[' * n], 0))
        out.append((['{' * 20000 + '[' * 20000 + '(' * 10000 + ')' * 10000 + ']' * 20000 + '}' * 20000], n))
        out.append((['(' * 25000 + '[' * 25000 + ']' * 25000 + ')' * 25000], 50000))
    elif uid == o.MES:
        g = [['.'] * 500 for _ in range(400)]; g[199][249] = 'U'; g[0][0] = 'P'
        out.append(([[''.join(r) for r in g]], 199))
        out.append(([[''.join(r) for r in _serpentine('.', (1, 1, 'U'), (397, 0, '.'))]], 198 * 499 + 1))
        g = _serpentine('.', (1, 1, 'U'), (397, 0, '.')); g[397][2] = 'P'
        out.append(([[''.join(r) for r in g]], -1))
    elif uid == o.MCO:
        out.append((['01' * 50000, 1000], 2001))
        out.append((['0' * n, 0], 0))
        out.append((['0' * n, 1], n))
        out.append((['1' * n, 0], n))
        out.append((['110' * 33333 + '1', 33334], 99999 + 1))
    elif uid == o.MFD:
        out.append(([[7] * n, 10], 7 * ((n + 10) // 2)))
        out.append(([[1 if i % 2 == 0 else 10**9 for i in range(n)], 1], 50000 * 10**9))
        out.append(([list(range(1000)), 1000], sum(range(1000))))
    elif uid == o.MLE:
        out.append(([[1] * n, [0] * n, 1000], [min(1000, n - i) for i in range(n)]))
        energy = [1001 if j % 1000 == 0 else 0 for j in range(n)]
        out.append(([[0] * n, energy, 1000], [(-i) % 1000 for i in range(n)]))
        out.append(([[10**9] * n, [0] * n, 10**14], [n - i for i in range(n)]))
    elif uid == o.MBT:
        out.append(([n, list(range(1, n + 1))], n))
        out.append(([3, [7] * n], 3))
        out.append(([7, [1 + i % 10000 for i in range(n)]], 70000))
        out.append(([n, [5] * n], n))
    elif uid == o.MBH:
        g = [['-'] * 500 for _ in range(400)]; g[0][0] = 'P'
        out.append(([[''.join(r) for r in g]], 399 + 499))
        out.append(([[''.join(r) for r in _serpentine('-', (1, 1, 'P'), None)]], 198 * 499 + 497))
        g = [['P'] * 500 for _ in range(400)]; g[200][200] = '-'
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)): g[200 + dr][200 + dc] = 'X'
        out.append(([[''.join(r) for r in g]], -1))
    elif uid == o.MIO:
        out.append(([[[0, 10**9]] * n], n))
        out.append(([[[i, i] for i in range(n)]], 1))
        out.append(([[[i, i + 1] for i in range(n)]], 2))
        out.append(([[[-i, i] for i in range(n)]], n))
    elif uid == o.MMP:
        full = [[u, v, 2] for u in range(12) for v in range(12) if u != v]
        out.append(([12, full, 0, 11], 2**11))
        out.append(([12, [[u, v, 10] for u in range(12) for v in range(12) if u != v], 3, 4], 10**11))
        out.append(([12, [[u, v, 2 if v == u + 1 else 1] for u in range(12) for v in range(12) if u != v], 0, 11], 2**11))
        out.append(([12, [[u, v, 10 if (u, v) == (0, 11) else 1] for u in range(12) for v in range(12) if u != v], 0, 11], 10))
        out.append(([12, [[u, v, 9] for u in range(11) for v in range(11) if u != v], 0, 11], -1))
    elif uid == o.MVF:
        m, w = 400, 500
        out.append(([[[0] * w for _ in range(m)]], [0, 0]))
        out.append(([[[7 if c == wk % m else 0 for wk in range(w)] for c in range(m)]], [7 * w, w - 1]))
        out.append(([[[1] * w, [2] * w] + [[0] * w for _ in range(m - 2)]], [2 * w, 1]))
        out.append(([[[7] * w for _ in range(m)]], [7 * w, 0]))
    elif uid == o.MNT:
        out.append(([_chain([1] * n), _chain([2] * n)], _chain([3] * n)))
        a, b = list(range(n)), [10**9] * 50000
        out.append(([_star(a), _star(b)], _star([10**9] + [a[i] + 10**9 for i in range(1, 50000)] + a[50000:])))
        big = _heap([-7] * n)
        out.append(([[], big], big))
        out.append(([_heap(list(range(n))), _heap([-i for i in range(n)])], _heap([0] * n)))
    elif uid == o.MRP:
        out.append(([_chain([10**9] * n)], 10**14))
        out.append(([_star([0] + [i - 50000 for i in range(1, n)])], -49999))
        out.append(([_heap([1] * n)], 16))
        out.append(([_chain([-10**9] * n)], -10**14))
    elif uid == o.MMQ:
        m = 50000; calls = [('enqueue', i) for i in range(m)]; exp = [None] * (m + 1)
        for i in range(m): calls += [('getMin',), ('getMax',), ('dequeue',)]; exp += [i, m - 1, i]
        out.append((_ops('MinMaxQueue', [], calls), exp))
        calls = [('enqueue', -i) for i in range(m)]; exp = [None] * (m + 1)
        for i in range(m): calls += [('getMax',), ('getMin',), ('dequeue',)]; exp += [-i, -(m - 1), -i]
        out.append((_ops('MinMaxQueue', [], calls), exp))
        calls, exp, top = [], [None], None
        for i in range(n // 2):  # nothing is dequeued, so getMax is the running maximum of the enqueued values
            v = (i % 7) * (1 if i % 2 else -1) * 10**8
            top = v if top is None else max(top, v)
            calls += [('enqueue', v), ('getMax',)]; exp += [None, top]
        out.append((_ops('MinMaxQueue', [], calls), exp))
    return out
