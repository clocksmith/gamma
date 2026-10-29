"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from itertools import permutations, product
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h13b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _upper(i, width): return _code(i, width).upper()


def _rcf(rng):
    n, m = rng.randrange(0, 8), rng.randrange(0, 8)
    pairs = [(i, j) for i in range(n) for j in range(m) if rng.random() < 0.45]
    c2f = [['F%d' % j for i2, j in pairs if i2 == i] for i in range(n)]
    f2c = [['C%d' % i for i, j2 in pairs if j2 == j] for j in range(m)]
    for lst in c2f + f2c: rng.shuffle(lst)
    return [c2f, f2c, rng.randrange(-1, n + 1)]


def _rcp(rng):
    cuts = sorted(rng.sample(range(-30, 31), rng.randrange(0, 14)))
    iv = [[a, b] for a, b in zip(cuts, cuts[1:]) if rng.random() < 0.6]
    rng.shuffle(iv)
    total = sum(b - a for a, b in iv)
    return [iv, rng.randrange(0, total + 3)]


def _rmv(rng):
    out = []
    for _ in range(rng.randrange(0, 12)):
        w = ''.join(rng.choice('aeiouAEIOUbcdxyzY') for _ in range(rng.randrange(1, 8)))
        out.append(w)
    return [out]


def _rps(rng):
    n = rng.randrange(1, 9); names = ['r%d' % i for i in range(n)]; perm = list(range(n)); rng.shuffle(perm)
    parents = [[] for _ in range(n)]
    for k in range(1, n):
        child = perm[k]
        parents[child] = [names[p] for p in rng.sample(perm[:k], rng.randrange(0, min(k, 3) + 1))]
    pool = ['read', 'write', 'exec', 'admin', 'audit', 'del_x']
    allowed = [rng.sample(pool, rng.randrange(0, 4)) for _ in range(n)]
    disallowed = [rng.sample(pool, rng.randrange(0, 3)) for _ in range(n)]
    return [names, parents, allowed, disallowed]


_STEPS = [(1, 0), (0, 1), (-1, 0), (0, -1), (3, 4), (4, 3), (-3, 4), (4, -3), (-4, -3), (5, 12), (-12, 5), (6, 8), (2, 0), (0, -2), (8, -6)]


def _rnc(rng):
    pts = [[rng.randrange(100, 900), rng.randrange(100, 900)]]
    for _ in range(rng.randrange(0, 10)):
        dx, dy = rng.choice(_STEPS); pts.append([pts[-1][0] + dx, pts[-1][1] + dy])
    total = sum(_o.isqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) for a, b in zip(pts, pts[1:]))
    return [pts, [rng.randrange(0, total + 6) for _ in range(rng.randrange(0, 10))]]


def _build_tree(rng, texts):
    """Random grouping of texts (in order) into a flat node list with shuffled non-root indices."""
    nested = []

    def group(items, depth):
        if len(items) == 1 and (depth > 0 and rng.random() < 0.7 or rng.random() < 0.3): return items[0]
        cuts = sorted(rng.sample(range(1, len(items)), min(len(items) - 1, rng.randrange(0, 3)))) if len(items) > 1 else []
        bounds = [0] + cuts + [len(items)]
        return [group(items[a:b], depth + 1) for a, b in zip(bounds, bounds[1:])]
    nested = group(texts, 0)
    order = []

    def flat(node):
        k = len(order); order.append(None)
        if isinstance(node, str): order[k] = [node, []]
        else: order[k] = ['', [flat(c) for c in node]]
        return k
    flat(nested)
    n = len(order); perm = [0] + rng.sample(range(1, n), n - 1)
    out = [None] * n
    for k, (t, kids) in enumerate(order): out[perm[k]] = [t, [perm[c] for c in kids]]
    return out


def _split(rng, word):
    cuts = sorted(rng.sample(range(1, len(word)), rng.randrange(0, min(len(word) - 1, 5) + 1))) if len(word) > 1 else []
    bounds = [0] + cuts + [len(word)]
    parts = [word[a:b] for a, b in zip(bounds, bounds[1:])]
    out = []
    for p in parts:
        while len(p) > 10: out.append(p[:10]); p = p[10:]
        out.append(p)
    return out


def _swh(rng):
    word = ''.join(rng.choice('ab') for _ in range(rng.randrange(1, 12)))
    other = word
    r = rng.random()
    if r < 0.2: other = word + rng.choice('ab')
    elif r < 0.4:
        i = rng.randrange(len(word)); other = word[:i] + ('b' if word[i] == 'a' else 'a') + word[i + 1:]
    elif r < 0.45 and len(word) > 1: other = word[:-1]
    return [_build_tree(rng, _split(rng, word)), _build_tree(rng, _split(rng, other))]


def _sop(rng):
    planes = [[d, rng.randrange(0, 9)] for d in rng.sample(range(0, 20), rng.randrange(0, 7))]
    orders = [[rng.randrange(0, 20), [rng.randrange(1, 7) for _ in range(rng.randrange(1, 4))]] for _ in range(rng.randrange(0, 9))]
    return [planes, orders]


def _shs(rng):
    pool = ['a', 'b', 'c', 'd', 'e', 'f']; calls = []
    for _ in range(rng.randrange(0, 30)):
        calls.append(('add', rng.choice(pool)) if rng.random() < 0.65 else ('getTopK', rng.randrange(0, 8)))
    return _ops('SearchHistory', [rng.randrange(1, 6)], calls)


def _ssr(rng, uid):
    ids = rng.sample([_code(i, 2) for i in range(60)] + ['x1', 'y22', 'z9'], 40); nodes = iter(ids); segs = []
    chain_count = 1 if uid == _o.SSR1 else rng.randrange(0 if uid == _o.SSR3 else 1, 4)
    for _ in range(chain_count):
        path = [next(nodes) for _ in range(rng.randrange(2, 7))]
        cyclic = uid == _o.SSR2 and rng.random() < 0.3
        if cyclic and rng.random() < 0.3: path = path[:1] + path[:1]
        elif cyclic: path.append(path[0])
        segs += [[a, b, ''.join(rng.choice('pqr') for _ in range(rng.randrange(0, 4)))] for a, b in zip(path, path[1:])]
    rng.shuffle(segs)
    return [segs]


def _sva(rng):
    bases = ['ab', 'abc', 'aab', 'xyz', 'rst']; word_set = set()
    for b in bases:
        for p in permutations(b):
            if rng.random() < 0.5: word_set.add(''.join(p))
    word_set |= set(rng.sample(['q', 'qq', 'mn', 'nm', 'pq'], rng.randrange(0, 4)))
    word_set = sorted(word_set); rng.shuffle(word_set)
    vocab = ['ab', 'ba', 'abc', 'cab', 'aba', 'zyx', 'tsr', 'mn', 'q', 'hello', 'xyz']
    sentences = [' '.join(rng.choice(vocab) for _ in range(rng.randrange(1, 5))) for _ in range(rng.randrange(0, 5))]
    return [word_set, sentences]


def _shr(rng):
    out = []
    for i in rng.sample(range(100), rng.randrange(0, 9)):
        a = rng.randrange(0, 40); out.append('%s:%d:%d' % (_code(i, 2) if i % 3 else 'id%d' % i, a, a + rng.randrange(0, 16)))
    return [rng.randrange(1, 4), out]


def _sup(rng):
    n = rng.randrange(1, 13)
    return [[rng.randrange(0, 21) for _ in range(n)], ''.join(rng.choice('0111') for _ in range(n))]


def _src(rng, uid):
    pool = ['AA', 'BB', 'CC', 'DD', 'EEE']; methods = ['Air', 'Sea', 'UPS', 'x']; seen = set(); routes = []
    for _ in range(rng.randrange(1, 26)):
        a, b = rng.sample(pool, 2); m = rng.choice(methods)
        if (a, b, m) in seen: continue
        seen.add((a, b, m)); routes.append('%s:%s:%s:%d' % (a, b, m, rng.randrange(1, 12)))
    s, t = rng.sample(pool, 2) if uid != _o.SRC3 or rng.random() < 0.85 else [rng.choice(pool)] * 2
    if uid == _o.SRC3 and rng.random() < 0.1: t = 'ZZZ'
    return [routes, s, t]


def _spg(rng):
    m, n = rng.randrange(1, 8), rng.randrange(1, 8)
    if m * n < 2: n = 2
    cells = [[rng.choice('....#G') for _ in range(n)] for _ in range(m)]
    a, b = rng.sample(range(m * n), 2)
    cells[a // n][a % n] = 'S'; cells[b // n][b % n] = 'D'
    return [[''.join(r) for r in cells], rng.randrange(0, 7)]


def _dense(rng, r, c):
    return [[rng.choice([0, 0, 0, 1, -2, 3, 7]) for _ in range(c)] for _ in range(r)]


def _smo(rng):
    r, c = rng.randrange(1, 5), rng.randrange(1, 5); calls = []
    for _ in range(rng.randrange(0, 12)):
        x = rng.random()
        if x < 0.3: calls.append(('get', rng.randrange(r), rng.randrange(c)))
        elif x < 0.55: calls.append(('set', rng.randrange(r), rng.randrange(c), rng.choice([0, 0, 4, -5, 1000])))
        elif x < 0.75: calls.append(('add', _dense(rng, r, c)))
        else: calls.append(('multiply', _dense(rng, c, rng.randrange(1, 5))))
    return _ops('SparseMatrix', [_dense(rng, r, c)], calls)


def _sae(rng):
    if rng.random() < 0.5:
        left = [rng.randrange(1, 6) for _ in range(rng.randrange(1, 6))]; target = sum(left); right = []
        while sum(right) < target: right.append(rng.randrange(1, min(6, target - sum(right)) + 1))
        return [left + right]
    return [[rng.randrange(1, 6) for _ in range(rng.randrange(1, 11))]]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid in o.RCF:
        args = [[[], [], 0], [[['F0', 'F1'], ['F1'], ['F2'], []], [['C0'], ['C1', 'C0'], ['C2']], 0], [[['F0'], ['F0', 'F1'], ['F1']], [['C0', 'C1'], ['C1', 'C2']], 0],
                [[['F0'], []], [['C0']], 1], [[['F0'], ['F0']], [['C1', 'C0']], -1], [[['F0'], ['F0']], [['C1', 'C0']], 2]]
        args += [_rcf(rng) for _ in range(250)]
    elif uid == o.RCP:
        args = [[[], 0], [[[10, 13]], 0], [[[10, 13]], 1], [[[10, 13]], 2], [[[10, 13]], 3], [[[5, 7], [-3, -1], [20, 21]], 2], [[[5, 7], [-3, -1], [20, 21]], 4]]
        args += [_rcp(rng) for _ in range(250)]
    elif uid == o.RMV:
        args = [[[]], [['apple', 'Area', 'education', 'a', 'io', 'sky', 'OboE', 'banana']]]
        args += [_rmv(rng) for _ in range(250)]
    elif uid == o.RPS:
        args = [[['viewer'], [[]], [['read']], [[]]],
                [['admin', 'editor', 'viewer', 'guest'], [['editor'], ['viewer'], [], ['viewer']], [['delete'], ['write'], ['read', 'list'], []], [[], [], [], ['list']]],
                [['a', 'b', 'c', 'd'], [[], ['a'], ['a'], ['b', 'c']], [['x', 'y'], [], ['z'], ['y']], [[], ['x'], [], []]]]
        args += [_rps(rng) for _ in range(250)]
    elif uid == o.RNC:
        args = [[[[0, 0]], [0, 5]], [[[0, 0], [10, 0]], [0, 4, 5, 6, 10, 99]], [[[0, 0], [3, 4], [3, 0]], [0, 2, 3, 5, 7, 8, 9, 100]], [[[0, 0], [6, 0], [0, 0]], [3, 6, 9, 12]]]
        args += [_rnc(rng) for _ in range(250)]
    elif uid == o.SWH:
        args = [[[['abc', []]], [['', [1, 2]], ['ab', []], ['c', []]]], [[['', [1]], ['', [2]], ['x', []]], [['y', []]]],
                [[['', [2, 1]], ['c', []], ['ab', []]], [['abc', []]]], [[['', [1, 2]], ['', [3]], ['d', []], ['ab', []]], [['', [1, 2]], ['a', []], ['bd', []]]]]
        args += [_swh(rng) for _ in range(250)]
    elif uid == o.SOP:
        args = [[[], []], [[[10, 5]], [[3, [2, 2]], [3, [2]], [10, [1]]]], [[[4, 3], [2, 5], [9, 4]], [[1, [3, 3, 2]], [1, [5, 1]], [3, [4]], [0, [4, 9]]]],
                [[[5, 0], [6, 2]], [[4, [1, 1, 1]], [4, [2]]]]]
        args += [_sop(rng) for _ in range(250)]
    elif uid == o.SHS:
        args = [_ops('SearchHistory', [2], [('getTopK', 3), ('add', 'cat'), ('add', 'dog'), ('add', 'cat'), ('getTopK', 5), ('add', 'emu'), ('getTopK', 2), ('getTopK', 0)]),
                _ops('SearchHistory', [1], [('add', 'a'), ('add', 'a'), ('getTopK', 1), ('add', 'b'), ('getTopK', 9)])]
        args += [_shs(rng) for _ in range(250)]
    elif uid in o.SSR:
        args = [[[['b', 'c', 'lo'], ['a', 'b', 'hel'], ['c', 'd', '']]], [[['x', 'y', 'abc']]]]
        if uid == o.SSR2: args += [[[['a', 'b', 'x'], ['b', 'a', 'y']]], [[['a', 'a', 'x']]], [[['a', 'b', 'x'], ['c', 'd', 'y']]], [[['a', 'b', 'x'], ['c', 'd', 'y'], ['d', 'c', 'z']]]]
        if uid == o.SSR3: args += [[[]], [[['m', 'n', 'x'], ['c', 'd', 'y'], ['d', 'e', 'z'], ['b', 'q', '']]]]
        args += [_ssr(rng, uid) for _ in range(250)]
    elif uid == o.SVA:
        args = [[[], []], [['listen', 'silent', 'enlist', 'google', 'act', 'cat'], ['tac listen', 'dog', 'google act']], [['ab'], ['ba ba']]]
        args += [_sva(rng) for _ in range(250)]
    elif uid == o.SHR:
        args = [[1, []], [1, ['a:0:10', 'b:5:15', 'c:20:30']], [2, ['a:0:10', 'b:5:15', 'c:3:8', 'd:12:12']], [1, ['z:0:5', 'a:0:5']], [3, ['x:7:7']],
                [1, ['a:0:10', 'b:2:5', 'c:3:20', 'd:4:30']]]
        args += [_shr(rng) for _ in range(250)]
    elif uid == o.SUP:
        args = [[[5], '1'], [[5], '0'], [[10, 5, 8, 1], '0101'], [[3, 9, 4], '011'], [[7, 2, 6, 4], '1011']]
        args += [_sup(rng) for _ in range(250)]
    elif uid in o.SRC:
        routes = ['US:UK:UPS:5', 'US:UK:DHL:3', 'US:CA:FedEx:3', 'CA:UK:DHL:7', 'CA:UK:UPS:1', 'UK:FR:DHL:2', 'US:FR:UPS:20']
        args = [[routes, 'US', 'UK'], [routes, 'US', 'FR'], [routes, 'UK', 'US'], [['AB:CD:x:1'], 'AB', 'CD']]
        if uid == o.SRC3: args += [[routes, 'US', 'US'], [routes, 'CA', 'FR']]
        args += [_src(rng, uid) for _ in range(250)]
    elif uid == o.SPG:
        args = [[['SD'], 0], [['SD'], 1], [['S.D'], 1], [['S.G.D'], 2], [['S#D'], 5], [['S..', '##.', 'D..'], 6], [['SG..D'], 1], [['S.G', '#.#', 'D..'], 2]]
        args += [_spg(rng) for _ in range(250)]
    elif uid == o.SMO:
        args = [_ops('SparseMatrix', [[[1, 0, 0], [-1, 0, 3]]], [('get', 1, 2), ('multiply', [[7, 0, 0], [0, 0, 0], [0, 0, 1]]), ('add', [[-1, 0, 0], [0, 2, 0]]),
                                                                ('set', 1, 2, 0), ('get', 1, 2), ('multiply', [[1], [1], [1]])]),
                _ops('SparseMatrix', [[[0]]], [('get', 0, 0), ('add', [[0]]), ('multiply', [[5, 0]])])]
        args += [_smo(rng) for _ in range(250)]
    elif uid == o.SAE:
        args = [[[1]], [[2, 2]], [[1, 2, 3, 3, 2, 1]], [[1, 1, 1]], [[10, 3, 7]], [[3, 7, 10]]]
        args += [_sae(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    if uid in o.RCF:
        m = 19999
        c2f = [['F%d' % j for j in range(m)]] + [['F%d' % j] for j in range(m)]
        f2c = [['C0', 'C%d' % (j + 1)] for j in range(m)]
        out.append(([c2f, f2c, 0], ['C%d' % i for i in range(1, m + 1)]))
        out.append(([c2f, f2c, 5], ['C0'] if uid == o.RCF1 else ['C%d' % i for i in range(m + 1) if i != 5]))
        out.append(([c2f, f2c, m + 1], []))
        chain_c = [['F0']] + [['F%d' % (i - 1), 'F%d' % i] for i in range(1, m)] + [['F%d' % (m - 1)]]
        chain_f = [['C%d' % j, 'C%d' % (j + 1)] for j in range(m)]
        out.append(([chain_c, chain_f, 10000], ['C9999', 'C10001'] if uid == o.RCF1 else ['C%d' % i for i in range(m + 1) if i != 10000]))
    elif uid == o.RCP:
        n = 100000
        iv = [[3 * i, 3 * i + 2] for i in range(n - 1, -1, -1)]
        for k in (0, 31337, n - 1):
            i = n - 1 - k
            out.append(([iv, 2 * k + 1], iv[:k] + [[3 * i, 3 * i + 1]] + iv[k + 1:]))
        out.append(([iv, 2 * n], iv))
        out.append(([[[-10**9, 10**9]], 10**9], [[-10**9, 0], [1, 10**9]]))
        out.append(([[[-10**9, 10**9]], 4 * 10**9], [[-10**9, 10**9]]))
    elif uid == o.RMV:
        n = 100000
        words = ['Abcdefghijklmnopqrsu', 'xyz', 'Ou', 'eXYZWi'] * (n // 4)
        out.append(([words], ['Asrqponmlkjihgfedcbu', 'xyz', 'Ou', 'eWZYXi'] * (n // 4)))
    elif uid == o.RPS:
        n = 2000; names = ['r%d' % k for k in range(n)]; priv = ['p_' + _code(k, 2) for k in range(50)]
        order = list(range(n - 1, -1, -1))
        parents = [[names[k - 1]] if k else [] for k in order]
        allowed = [[priv[k % 50]] for k in order]
        out.append(([[names[k] for k in order], parents, allowed, [[] for _ in order]], [priv[:min(k, 49) + 1] for k in order]))
        disallowed = [[priv[(k + 1) % 50]] for k in order]
        final, cur = {}, set()  # chain recurrence: final(k) = (final(k - 1) | {p_k}) - {p_(k+1)}
        for k in range(n):
            cur = (cur | {priv[k % 50]}) - {priv[(k + 1) % 50]}; final[k] = sorted(cur)
        out.append(([[names[k] for k in order], parents, allowed, disallowed], [final[k] for k in order]))
        root = priv[:10]
        out.append(([['root'] + names[1:], [[]] + [['root']] * (n - 1), [root] + [[] for _ in range(n - 1)], [[]] + [[root[k % 10]] for k in range(1, n)]],
                    [root] + [[p for p in root if p != root[k % 10]] for k in range(1, n)]))
    elif uid == o.RNC:
        pts = [[2 * i, 0] for i in range(500)]
        ds = [2 * k + (k % 2) for k in range(497)] + [998, 999, 10**7]
        out.append(([pts, ds], list(range(497)) + [499, 499, 499]))
        pts = [[3 * i, 4 * i] for i in range(200)]
        out.append(([pts, list(range(500))], [d // 5 + (1 if d % 5 > 2 else 0) for d in range(500)]))
    elif uid == o.SWH:
        n = 100000
        chain = [['', [k + 1]] for k in range(n - 1)] + [['abcde', []]]
        flat = [['', list(range(1, 6))]] + [[c, []] for c in 'abcde']
        out.append(([chain, flat], True))
        many = [['', list(range(1, n))]] + [['ab', []] for _ in range(n - 1)]
        three = [['', list(range(1, 66667))]] + [['aba' if k % 2 == 0 else 'bab', []] for k in range(66666)]
        out.append(([many, three], True))
        three_bad = three[:-1] + [['baa', []]]
        out.append(([many, three_bad], False))
        out.append(([chain, many], False))
    elif uid == o.SOP:
        planes = [[i + 1, 1] for i in range(19999, -1, -1)]
        orders = [[0, [1, 1]] for _ in range(10000)] + [[0, [1]]]
        out.append(([planes, orders], [[2 * k + 1, 2 * k + 2] for k in range(10000)] + [[]]))
        big = [[2 * i, 10**9] for i in range(20000)]
        out.append(([big, [[2 * k, [10**9]] for k in range(20000)]], [[2 * k + 2] for k in range(19999)] + [[]]))
        out.append(([planes, [[0, [1, 2]] for _ in range(20000)]], [[] for _ in range(20000)]))
    elif uid == o.SHS:
        n = 99999; calls, expected, added = [], [None], 0
        for i in range(n):
            if i % 100 == 99:
                calls.append(('getTopK', 100)); expected.append([_code(added - 1 - t, 4) for t in range(min(100, added))])
            else: calls.append(('add', _code(added, 4))); expected.append(None); added += 1
        out.append((_ops('SearchHistory', [500], calls), expected))
        calls, expected, added = [], [None], 0
        for i in range(n):
            if i % 50 == 49:
                calls.append(('getTopK', 100)); expected.append([_code((added - 1 - t) % 150, 3) for t in range(min(100, added))])
            else: calls.append(('add', _code(added % 150, 3))); expected.append(None); added += 1
        out.append((_ops('SearchHistory', [100], calls), expected))
    elif uid in o.SSR:
        n = 100000; ids = [_code(i, 4) for i in range(n + 1)]
        segs = [[ids[i], ids[i + 1], 'ab' if i % 2 else 'c'] for i in range(n)]
        shuffled = [segs[(i * 7919) % n] for i in range(n)]
        word = ''.join(s[2] for s in segs)
        if uid == o.SSR3:
            out.append(([shuffled], [word]))
            chains = [[ids[100 * c + j], ids[100 * c + j + 1] if j < 99 else 'z' + ids[c], 'q' * (j % 3)] for c in range(1000) for j in range(100)]
            per = ''.join('q' * (j % 3) for j in range(100))
            out.append(([chains[::-1]], [per] * 1000))
            out.append(([[[ids[i], 'e' + ids[i], ids[i][-1]] for i in range(n - 1, -1, -1)]], [ids[i][-1] for i in range(n)]))
        else:
            out.append(([shuffled], word))
            if uid == o.SSR2:
                cycle = [[s[0], ids[0], s[2]] if s[1] == ids[n] else s for s in shuffled]
                out.append(([cycle], ''))
                out.append(([[s for s in shuffled if s[0] != ids[50000]]], ''))
    elif uid == o.SVA:
        a = sorted(''.join(p) for p in permutations('abc')); d = sorted(''.join(p) for p in permutations('defg'))
        letters = 'hijklmnopqrstuvwxyz'
        noise = [''.join(letters[i // 19 ** p % 19] for p in range(3, -1, -1)) for i in range(9970)]
        word_set = noise[:5000] + a + d + noise[5000:]
        variations = [x + ' ' + y for x in a for y in d]
        sentences = ['abc defg', 'cab gfed'] * 170
        out.append(([word_set, sentences], [variations] * 340))
        out.append(([word_set, ['hello world ' + ' '.join(['abc'] * 3)] * 30], [['hello world ' + ' '.join(t) for t in product(a, a, a)]] * 30))
    elif uid == o.SHR:
        n = 20000; big = 10**9; ids = ['s' + _code(i, 4) for i in range(n)]
        out.append(([5, ['%s:%d:%d' % (ids[k], k, big) for k in range(n - 1, -1, -1)]], ['%s:%d:%d' % (ids[k], k, big) for k in range(5)]))
        out.append(([1, ['%s:%d:%d' % (ids[i], 20 * i, 20 * i + 9) for i in range(n)]],
                    ['%s:%d:%d' % (ids[0], 0, 9)] + ['%s:%d:%d' % (ids[i], 20 * i - 10, 20 * i + 9) for i in range(1, n)]))
        out.append(([1, ['%s:%d:%d' % (ids[i], 10 * i, 10 * i + 9) for i in range(n - 1, -1, -1)]], ['%s:%d:%d' % (ids[i], 10 * i, 10 * i + 9) for i in range(n)]))
        out.append(([10, ['%s:0:%d' % (ids[i], big) for i in range(n)]], ['%s:0:%d' % (ids[i], big) for i in range(10)]))
    elif uid == o.SUP:
        n = 100000
        pop = [10**9 - (i % 7) for i in range(n)]
        out.append(([pop, '1' * n], sum(pop)))
        pop2 = [i + 1 for i in range(n)]
        out.append(([pop2, '0' + '1' * (n - 1)], n * (n + 1) // 2 - 1))
        pop3 = [(i * 7) % 1000 for i in range(n)]
        out.append(([pop3, '01' * (n // 2)], sum(max(pop3[2 * k], pop3[2 * k + 1]) for k in range(n // 2))))
        out.append(([pop2, '0' * n], 0))
    elif uid in o.SRC:
        if uid == o.SRC1:
            routes = ['AAA:BBB:m%s:%d' % (_code(i, 3), 10**6 - i // 2) for i in range(2000)]
            out.append(([routes, 'AAA', 'BBB'], [['m' + _code(i, 3), 10**6 - i // 2] for i in sorted(range(2000), key=lambda i: (10**6 - i // 2, i))]))
            out.append(([routes, 'BBB', 'AAA'], []))
        elif uid == o.SRC2:
            mids = [_upper(i, 3) for i in range(999)]
            routes = ['AA:BB:Direct:5'] + ['AA:%s:Air:%d' % (x, i + 1) for i, x in enumerate(mids)] + ['%s:BB:Sea:%d' % (x, 1000 - i) for i, x in enumerate(mids)]
            out.append(([routes, 'AA', 'BB'], [['AA:Direct:BB', 5]] + [['AA:Air:%s:Sea:BB' % x, 1001] for x in sorted(mids)]))
            out.append(([routes, 'BB', 'AA'], []))
        else:
            names = [_upper(i, 3) for i in range(1000)]
            routes = ['%s:%s:Rail:1' % (names[i], names[i + 1]) for i in range(999)] + ['%s:%s:Air:3' % (names[i], names[i + 2]) for i in range(998)]
            out.append(([routes, names[0], names[999]], 999))
            out.append(([routes, names[999], names[0]], -1))
            out.append(([routes, names[500], names[500]], 0))
    elif uid == o.SPG:
        out.append(([['S' + '.' * 49] + ['.' * 50] * 48 + ['.' * 49 + 'D'], 100], 98))
        rows = []
        for r in range(49):
            if r % 2 == 0: rows.append('.' * 50)
            elif (r // 2) % 2 == 0: rows.append('#' * 49 + 'G')
            else: rows.append('G' + '#' * 49)
        rows[0] = 'S' + rows[0][1:]; rows[48] = rows[48][:49] + 'D'
        out.append(([rows, 100], 1273)); out.append(([rows, 51], 1273)); out.append(([rows, 50], -1))
        out.append(([['S' + '.' * 49] + ['.' * 50] * 48 + ['.' * 49 + 'D'], 97], -1))
    elif uid == o.SMO:
        n = 60
        ident = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        b = [[(i * 7 + j * 3) % 2001 - 1000 if (i + j) % 5 else 0 for j in range(n)] for i in range(n)]
        bt = [[i, j, v] for i in range(n) for j in range(n) for v in [b[i][j]] if v]
        it = [[i, j, b[i][j] + (1 if i == j else 0)] for i in range(n) for j in range(n) if b[i][j] + (1 if i == j else 0)]
        calls, expected = [], [None]
        for k in range(20): calls += [('multiply', b), ('add', b)]; expected += [bt, it]
        out.append((_ops('SparseMatrix', [ident], calls), expected))
        calls, expected = [], [None]
        for k in range(150):
            r, c, v = k % n, (k * 7) % n, (k % 1999) - 999 or 5
            calls += [('set', r, c, v), ('get', r, c)]; expected += [None, v]
        out.append((_ops('SparseMatrix', [[[0] * n for _ in range(n)]], calls), expected))
    elif uid == o.SAE:
        n = 100000
        out.append(([[1] * n], n // 2 - 1))
        out.append(([[10**9] * (n - 1)], -1))
        out.append(([[1] * (n - 2) + [n - 2]], n - 3))
    return out
