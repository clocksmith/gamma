"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h06a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _expr(rng, depth):
    if depth == 0 or rng.random() < 0.3:
        return str(rng.choice([0, 1, 2, 5, 9, 10, 37, 1000000000, -1, -7, -1000000000]))
    sp = rng.choice(['', '', ' '])
    if rng.random() < 0.5:
        return 'sub(' + sp + _expr(rng, depth - 1) + sp + ',' + sp + _expr(rng, depth - 1) + ')'
    return 'add(' + (',' + sp).join(_expr(rng, depth - 1) for _ in range(rng.randrange(2, 5))) + sp + ')'


def _tree_fs(rng):
    dirs, files, edges = ['/r'], [], []
    for i in range(rng.randrange(0, 14)):
        parent = rng.choice(dirs)
        child = parent + '/' + ('d%d' % i if rng.random() < 0.45 else 'f%d.t' % i)
        (dirs if child.split('/')[-1].startswith('d') else files).append(child)
        edges.append([parent, child])
    if rng.random() < 0.2: dirs.append('/other'); files.append('/other/x'); edges.append(['/other', '/other/x'])
    rng.shuffle(edges)  # child order is edge order
    path = rng.choice(dirs + files + ['/missing', '/r'])
    return [dirs, edges, files, path]


def _dir_tree(rng, depth):
    kids = []
    for i in range(rng.randrange(0, 4)):
        if depth < 4 and rng.random() < 0.4: kids.append(_dir_tree(rng, depth + 1))
        else: kids.append({'name': 'f%d' % i, 'size': rng.choice([0, 1, 5, 40, 100, 100000000])})
    return {'name': 'd%d' % depth, 'children': kids}


def _dag(rng, n, p):
    order = list(range(n)); rng.shuffle(order)
    return [[order[i], order[j]] for i in range(n) for j in range(i + 1, n) if rng.random() < p]


def _maze(rng, values):
    m, n = rng.randrange(1, 7), rng.randrange(1, 7)
    return [[rng.choice(values) for _ in range(n)] for _ in range(m)]


def _fsc(rng):
    cols = ['a', 'b', 'c', 'd', 'e']
    files = []
    for i in range(rng.randrange(0, 8)):
        ids = [rng.choice(cols) for _ in range(rng.randrange(0, 4))]
        files.append(','.join(['f%d' % i, str(rng.randrange(1, 20))] + ids))
    calls, parent = [], {}
    for _ in range(rng.randrange(1, 14)):
        op = rng.choice(['getTotalSize', 'getCollectionSize', 'getTopCollections', 'setParent', 'setParent', 'getHierarchySize', 'getHierarchySize'])
        if op == 'getTotalSize': calls.append((op,))
        elif op == 'getTopCollections': calls.append((op, rng.randrange(1, 7)))
        elif op == 'setParent':
            child, par = rng.choice(cols + ['z']), rng.choice(cols + ['y'])
            a = par
            while a is not None and a != child: a = parent.get(a)
            if child == par or child in parent or a == child: continue
            parent[child] = par; calls.append((op, child, par))
        else: calls.append((op, rng.choice(cols + ['q'])))
    return _ops('FileSystemStats', [files], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid in (o.EOD1, o.EOD2):
        args = [[[]], [[['a', 'b', 5]]], [[['a', 'b', 5], ['b', 'a', 5]]], [[['x', 'y', 3], ['y', 'z', 3]]], [[['B', 'a', 1], ['a', 'B', 2]]]]
        for _ in range(250):
            names = rng.sample(['al', 'bo', 'cy', 'di', 'Ed', 'fx_1'], rng.randrange(2, 7))
            rows = []
            for _ in range(rng.randrange(0, 10)):
                a, b = rng.sample(names, 2); rows.append([a, b, rng.choice([1, 2, 3, 5, 10, 1000000000])])
            args.append([rows])
    elif uid == o.EVAL:
        args = [['0'], ['-5'], ['add(1,2)'], ['sub(1,2)'], ['add( 1 , 2 , 3 )'], ['sub(add(1,2),sub(5,-3))'], [' add(1000000000,1000000000) '],
                ['sub(-1000000000,1000000000)']]
        for _ in range(250): args.append([_expr(rng, rng.randrange(0, 5))])
    elif uid in (o.FAC1, o.FAC2, o.FAC3):
        args = [[[[5]]], [[[0], [0]]], [[[1, 2], [1, 2]]], [[[3, 1, 2], [3, 1, 2], [3, 1, 2]]], [[[7], [1, 9], [7]]]]
        for _ in range(250):
            n = rng.randrange(1, 7)
            args.append([[[rng.randrange(0, 10) for _ in range(rng.choice([1, 2, 2, 3, 3, 4]))] for _ in range(n)]])
        if uid == o.FAC3:
            out = []
            for a in args:
                n = len(a[0])
                edges = [[rng.randrange(i), i] if rng.random() < 0.5 else [i, rng.randrange(i)] for i in range(1, n)]
                rng.shuffle(edges); out.append([a[0], edges])
            args = out
    elif uid == o.FSC:
        args = [_ops('FileSystemStats', [[]], [('getTotalSize',), ('getTopCollections', 3), ('getCollectionSize', 'a'), ('getHierarchySize', 'a')]),
                _ops('FileSystemStats', [['x,10,a,a,b', 'y,5', 'z,7,b']], [('getTotalSize',), ('getCollectionSize', 'a'), ('getCollectionSize', 'b'),
                                                                          ('getTopCollections', 1), ('setParent', 'a', 'b'), ('getHierarchySize', 'b'), ('setParent', 'b', 'q'), ('getHierarchySize', 'q')])]
        args += [_fsc(rng) for _ in range(250)]
    elif uid == o.FSD:
        args = [[[], [], [], '/a'], [['/a'], [], [], '/a'], [['/a'], [['/a', '/a/f']], ['/a/f'], '/a/f'],
                [['/a', '/a/b'], [['/a', '/a/x'], ['/a', '/a/b'], ['/a/b', '/a/b/y']], ['/a/x', '/a/b/y'], '/a']]
        args += [_tree_fs(rng) for _ in range(250)]
    elif uid == o.FSDS:
        args = [[{'name': 'r', 'children': []}, 0], [{'name': 'r', 'children': [{'name': 'f', 'size': 3}]}, 2],
                [{'name': 'r', 'children': [{'name': 'f', 'size': 3}, {'name': 's', 'children': [{'name': 'g', 'size': 2}]}]}, 10]]
        for _ in range(250): args.append([_dir_tree(rng, 0), rng.choice([0, 1, 10, 50, 100, 200, 10**8, 10**14])])
    elif uid == o.BOTT:
        args = [[1, []], [2, []], [2, [[0, 1]]], [3, [[0, 1], [0, 2]]], [4, [[0, 1], [0, 2], [1, 3], [2, 3]]], [3, [[2, 1], [1, 0]]]]
        for _ in range(250):
            n = rng.randrange(1, 10); args.append([n, _dag(rng, n, rng.choice([0.1, 0.3, 0.6]))])
    elif uid == o.MID1:
        args = [[[['a', 'b'], ['b', 'c']]], [[['c', 'd'], ['a', 'b'], ['b', 'c'], ['d', 'e']]]]
        for _ in range(250):
            k = 2 * rng.randrange(1, 9); names = rng.sample(['c%d' % i for i in range(40)], k + 1)
            pairs = [[names[i], names[i + 1]] for i in range(k)]; rng.shuffle(pairs); args.append([pairs])
    elif uid == o.MID2:
        args = [[[['a', 'b']]], [[['a', 'b'], ['b', 'c']]], [[['a', 'b'], ['b', 'c'], ['c', 'd']]], [[['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['a', 'd']]],
                [[['x', 'y'], ['p', 'q']]]]
        for _ in range(250):
            n = rng.randrange(2, 10); names = ['n%d' % i for i in range(n)]
            pairs = [[names[u], names[v]] for u, v in _dag(rng, n, rng.choice([0.2, 0.35, 0.5]))]
            if pairs: args.append([pairs])
    elif uid in (o.EXIT1, o.EXIT2):
        args = [[[[1]], [0, 0]], [[[1, 1]], [0, 0]], [[[1, 1, 1], [1, 1, 1], [1, 1, 1]], [1, 1]], [[[0, 0, 0], [0, 1, 0], [0, 0, 0]], [1, 1]],
                [[[1, 0, 1], [0, 1, 0], [1, 0, 1]], [1, 1]]]
        while len(args) < 255:
            g = _maze(rng, [0, 1, 1]); opens = [[r, c] for r in range(len(g)) for c in range(len(g[0])) if g[r][c]]
            if opens: args.append([g, rng.choice(opens)])
    elif uid == o.OFFER:
        offers = [['o1', '0', '10', '1'], ['o2', '5', '20', '2'], ['o3', '15', '30', '0']]
        args = [[[], [], 0], [offers, [], 7], [offers, [['u', '3', 'redeem', 'o1'], ['u', '4', 'redeem', 'o1'], ['v', '6', 'unredeem', 'o2']], 7],
                [offers, [['u', '12', 'redeem', 'o2'], ['u', '8', 'redeem', 'o2'], ['u', '9', 'unredeem', 'o2'], ['u', '11', 'redeem', 'o9']], 10]]
        for _ in range(250):
            offs = []
            for i in range(rng.randrange(0, 5)):
                s = rng.randrange(0, 20); offs.append(['o%d' % i, str(s), str(s + rng.randrange(0, 15)), str(rng.randrange(0, 4))])
            evs = [[rng.choice(['u1', 'u2', 'U3']), str(rng.randrange(0, 40)), rng.choice(['redeem', 'redeem', 'unredeem']), 'o%d' % rng.randrange(0, 6)]
                   for _ in range(rng.randrange(0, 14))]
            args.append([offs, evs, rng.randrange(0, 40)])
    elif uid == o.PREFIX:
        args = [[['a']], [['ab', 'ac']], [['zebra', 'dog', 'duck', 'dove']], [['abc', 'abd', 'b']], [['aaaa', 'aaab', 'aab']]]
        while len(args) < 255:
            al = rng.choice(['ab', 'abc', 'xyz']); words = sorted({''.join(rng.choice(al) for _ in range(rng.randrange(1, 7))) for _ in range(rng.randrange(1, 10))})
            words = [w for w in words if not any(o2 != w and o2.startswith(w) for o2 in words)]
            rng.shuffle(words); args.append([words])
    elif uid == o.HUB:
        args = [[[5], [[]], 5, '0:0'], [[5], [['0:0']], 5, '0:0'], [[4], [[]], 5, '1:2'], [[9, 6, 6], [[], ['3:4'], []], 6, '4:9'], [[7, 7], [[], []], 1, '0:1000000000']]
        for _ in range(250):
            n = rng.randrange(1, 7)
            ivs = []
            for _ in range(n):
                row = []
                for _ in range(rng.randrange(0, 4)):
                    a = rng.randrange(0, 20); row.append('%d:%d' % (a, a + rng.randrange(0, 5)))
                ivs.append(row)
            t = rng.randrange(0, 20)
            args.append([[rng.randrange(1, 10) for _ in range(n)], ivs, rng.randrange(1, 10), '%d:%d' % (t, t + rng.randrange(0, 4))])
    elif uid == o.DNA:
        args = [[[]], [['A']], [['A', 'T']], [['AT', 'AT', 'AT']], [['ACG', 'CGT', 'CGT', 'TGC']], [['GC', 'CG', 'GC']]]
        for _ in range(250):
            args.append([[''.join(rng.choice('ACGT') for _ in range(rng.randrange(1, 4))) for _ in range(rng.randrange(0, 14))]])
    elif uid == o.LOGIN:
        args = [[[], 5], [['a signin 1', 'a signout 6'], 5], [['a signin 1', 'a signout 7'], 5], [['a signout 1', 'a signin 2', 'a signin 9', 'a signout 10'], 1],
                [['b signin 0', 'a signin 0', 'b signout 0', 'a signout 3'], 0]]
        for _ in range(250):
            t, logs = 0, []
            for _ in range(rng.randrange(0, 14)):
                t += rng.choice([0, 1, 2, 5]); logs.append('%s %s %d' % (rng.choice(['al', 'bo', 'Cy']), rng.choice(['signin', 'signout']), t))
            args.append([logs, rng.choice([0, 1, 2, 4, 10])])
    elif uid == o.CITY:
        args = [[['a'], [1], [1], ['a']], [['a', 'b'], [1, 1], [1, 5], ['a', 'b']], [['c', 'b', 'a'], [3, 1, 5], [3, 3, 3], ['c', 'a']],
                [['p', 'q'], [1, 2], [1, 2], ['q']]]
        for _ in range(250):
            n = rng.randrange(1, 9); pts = rng.sample([(x, y) for x in range(1, 6) for y in range(1, 6)], n)
            names = rng.sample(['c%d' % i for i in range(30)] + ['b', 'aa'], n)
            args.append([names, [p[0] for p in pts], [p[1] for p in pts], [rng.choice(names) for _ in range(rng.randrange(1, 5))]])
    elif uid == o.PATH:
        args = [[[[1]]], [[[0]]], [[[1, 0], [0, 1]]], [[[1, 1], [1, 0]]], [[[9, 0, 0], [0, 3, 0], [0, 0, 7]]], [[[1, 0, 1, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 0, 1]]]]
        for _ in range(250): args.append([_maze(rng, [0, 1, 2, 5, 9, 9])])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _revcomp(s): return s.translate(str.maketrans('ACGT', 'TGCA'))[::-1]


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid in (o.EOD1, o.EOD2):
        n = 100000
        ring = [['p%03d' % (i % 1000), 'p%03d' % ((i + 1) % 1000), 1000] for i in range(n)]  # everyone pays and receives 100 x 1000
        star = [['hub', 'm%05d' % i, i + 1] for i in range(n)]  # hub pays m_i exactly i + 1
        if uid == o.EOD1:
            out.append(([ring], [['p%03d' % i, 0] for i in range(1000)]))
            out.append(([star], [['hub', -n * (n + 1) // 2]] + [['m%05d' % i, i + 1] for i in range(n)]))
        else:
            out.append(([ring], []))
            out.append(([star], [['hub', 'm%05d' % i, i + 1] for i in range(n - 1, -1, -1)]))  # largest creditor first
            pairs = [['d%05d' % i, 'c%05d' % i, 7] for i in range(n)]  # 1e5 debtors and creditors all at 7: ties by name pair them in order
            out.append(([pairs], [['d%05d' % i, 'c%05d' % i, 7] for i in range(n)]))
    elif uid == o.EVAL:
        k = 14000
        out.append((['add(' * k + '1' + ',1)' * k], k + 1))
        out.append((['sub(' * k + '5' + ',2)' * k], 5 - 2 * k))
        out.append((['add(' + ','.join(['1000000000'] * 9000) + ')'], 9 * 10**12))
        out.append((['add( ' + ' , '.join(['-7'] * 16000) + ' )'], -7 * 16000))
    elif uid in (o.FAC1, o.FAC2, o.FAC3):
        n = 100000
        alt = [[4] if i % 2 == 0 else [3, 9] for i in range(n)]  # single rows force option 0, so the others must take 9
        same = [[1, 2]] * n  # alternate 0 and 1: n/2 * 1 + n/2 * 2
        path = [[i, i + 1] for i in range(n - 1)]
        if uid == o.FAC1:
            out.append(([alt], (n // 2) * 4 + (n // 2) * 3))
            out.append(([same], n))
        elif uid == o.FAC2:
            out.append(([alt], (n // 2) * 4 + (n // 2) * 9))
            out.append(([same], (n // 2) * 3))
            out.append(([[[0]] * n], -1))
        else:
            rev = [[i + 1, i] for i in range(n - 2, -1, -1)]
            out.append(([alt, rev], (n // 2) * 4 + (n // 2) * 9))
            out.append(([same, path], (n // 2) * 3))
            star = [[1, 100]] + [[1, 50]] * (n - 1)
            edges = [[0, i] if i % 2 else [i, 0] for i in range(1, n)]
            out.append(([star, edges], min(1 + (n - 1) * 50, 100 + (n - 1))))
    elif uid == o.FSC:
        files = ['f%d,%d,c%d' % (i, i % 100 + 1, i % 2000) for i in range(10000)]  # c_j gets 5 files of size j % 100 + 1
        direct = {j: 5 * (j % 100 + 1) for j in range(2000)}
        calls, exp = [], [None]
        calls.append(('getTotalSize',)); exp.append(100 * 5050)
        for j in range(999):
            calls.append(('setParent', 'c%d' % (j + 1), 'c%d' % j)); exp.append(None)
        whole = sum(direct[j] for j in range(1000))
        top = sorted(range(2000), key=lambda j: (-direct[j], 'c%d' % j))[:100]
        for r in range(999):
            calls.append(('getHierarchySize', 'c0')); exp.append(whole)
            calls.append(('getTopCollections', 100)); exp.append(['c%d' % j for j in top])
        calls.append(('getHierarchySize', 'c500')); exp.append(sum(direct[j] for j in range(500, 1000)))
        calls.append(('getCollectionSize', 'c1999')); exp.append(500)
        out.append((_ops('FileSystemStats', [files], calls), exp))
    elif uid == o.FSD:
        n = 99999
        files = ['/r/f%d' % i for i in range(n)]
        out.append(([['/r'], [['/r', f] for f in files], files, '/r'], files + ['/r']))
        chain = ['/d' * (k + 1) for k in range(1000)]
        edges = [[chain[k], chain[k + 1]] for k in range(999)] + [[chain[-1], chain[-1] + '/leaf']]
        out.append(([chain, edges, [chain[-1] + '/leaf'], chain[0]], [chain[-1] + '/leaf'] + chain[::-1]))
        out.append(([chain, edges, [chain[-1] + '/leaf'], chain[500]], [chain[-1] + '/leaf'] + chain[500:][::-1]))
    elif uid == o.FSDS:
        root = {'name': 'root', 'children': [{'name': 'f%d' % i, 'size': 1000} for i in range(99999)]}
        out.append(([root, 10**14], 99999000))
        out.append(([root, 99998999], 0))
        node = {'name': 'd89', 'children': [{'name': 'x', 'size': 10**8}]}
        for k in range(88, -1, -1):  # d_k holds a file of 1e8 and d_{k+1}: total (90 - k) * 1e8
            node = {'name': 'd%d' % k, 'children': [{'name': 'x', 'size': 10**8}, node]}
        node['children'].append({'name': 'w', 'children': [{'name': 'f%d' % i, 'size': 0} for i in range(99000)]})
        out.append(([node, 45 * 10**8], sum(m for m in range(1, 46)) * 10**8))
    elif uid == o.BOTT:
        n = 100000
        out.append(([n, [[i, i + 1] for i in range(n - 1)]], list(range(n))))
        edges, singles = [], []
        k = 33333  # triples s, a, b: s -> a, s -> b, a -> next s, b -> next s
        for t in range(k):
            s, a, b = 3 * t, 3 * t + 1, 3 * t + 2
            edges += [[s, a], [s, b]]; singles.append(s)
            if t + 1 < k: edges += [[a, s + 3], [b, s + 3]]
        out.append(([3 * k, edges[::-1]], singles))
    elif uid == o.MID1:
        n = 100000
        rng = random.Random(6)
        names = ['c%06d' % i for i in range(n + 1)]; rng.shuffle(names)
        pairs = [[names[i], names[i + 1]] for i in range(n)]; rng.shuffle(pairs)
        out.append(([pairs], names[n // 2]))
    elif uid == o.MID2:
        w, layers = 10, 51  # complete layered DAG: every path has 51 courses, middle index 25
        names = [['L%02dn%d' % (i, j) for j in range(w)] for i in range(layers)]
        pairs = [[a, b] for i in range(layers - 1) for a in names[i] for b in names[i + 1]]
        out.append(([pairs], sorted(names[25])))
        chain = ['n%03d' % i for i in range(1000)]
        pairs2 = [[chain[i], chain[i + 1]] for i in range(999)] + [['n000', 'n002'], ['n997', 'n999']]
        out.append(([pairs2], ['n499', 'n500']))
    elif uid in (o.EXIT1, o.EXIT2):
        g = [[1] * 316 for _ in range(316)]
        out.append(([g, [158, 158]], 157 if uid == o.EXIT1 else [158, 315]))
        g2, start, moves, cell = o.serpentine_exit(199, 501)
        out.append(([g2, start], moves if uid == o.EXIT1 else cell))
        g3 = [[0] * 316] + [[0] + [1] * 314 + [0] for _ in range(314)] + [[0] * 316]
        out.append(([g3, [1, 1]], -1 if uid == o.EXIT1 else [-1, -1]))
    elif uid == o.OFFER:
        offers = [['o%03d' % j, '0', '1000000000', str(j % 3)] for j in range(200)]
        events = [['u%03d' % (i % 500), str(i), 'redeem', 'o%03d' % ((i // 500) % 200)] for i in range(100000)]  # every (user, offer) once
        out.append(([offers, events, 10**9], [['u%03d' % u, ['o%03d' % j for j in range(200) if j % 3 == 2]] for u in range(500)]))
        cut = [['u%03d' % u, ['o%03d' % j for j in range(200) if (j % 3 == 2 if j < 100 else j % 3 >= 1)]] for u in range(500)]
        out.append(([offers, events, 49999], cut))
    elif uid == o.PREFIX:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        words = [''.join(letters[(i // 26 ** p) % 26] for p in (3, 2, 1, 0)) for i in range(75000)]  # distinct, equal length, every 3-prefix shared
        rng = random.Random(7); shuffled = list(words); rng.shuffle(shuffled)
        out.append(([shuffled], shuffled))
        w2 = [c + 'q' * 99 for c in letters[1:]] + ['a' * 99 + c for c in letters]
        out.append(([w2], list(letters[1:]) + w2[25:]))
    elif uid == o.HUB:
        n = 10000
        caps = [10**9 - i for i in range(n)]
        ivs = [['%d:%d' % (k * 1000, k * 1000 + 10) for k in range(9)] + (['550:550'] if i % 2 == 0 else ['601:700']) for i in range(n)]
        out.append(([caps, ivs, 1, '500:600'], n - 1))  # odd hubs are free; the last one has the smallest capacity
        out.append(([caps, ivs, 10**9, '500:600'], -1))  # only hub 0 is large enough and it is booked
    elif uid == o.DNA:
        trip = [a + b + c for a in 'ACGT' for b in 'ACGT' for c in 'ACGT']
        seqs = [trip[i % 64] for i in range(100000)]
        cnt = {s: 1562 + (1 if trip.index(s) < 32 else 0) for s in trip}
        out.append(([seqs], sum(cnt[s] * cnt[_revcomp(s)] for s in trip) // 2))  # odd length: never its own reverse complement
        out.append(([['A' * 100] * 3000], 0))
    elif uid == o.LOGIN:
        n = 50000
        logs = ['u%05d signin %d' % (i, i) for i in range(n)] + ['u%05d signout %d' % (i, n + i) for i in range(n)]
        out.append(([logs, n], ['u%05d' % i for i in range(n)]))
        out.append(([logs, n - 1], []))
    elif uid == o.CITY:
        s = 316
        names = ['c%05d' % i for i in range(s * s)]
        xs = [i // s + 1 for i in range(s * s)]; ys = [i % s + 1 for i in range(s * s)]

        def best(i):
            r, c = divmod(i, s)
            near = [(r + dr) * s + c + dc for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= r + dr < s and 0 <= c + dc < s]
            return 'c%05d' % min(near)
        out.append(([names, xs, ys, names], [best(i) for i in range(s * s)]))
        n = 100000
        out.append(([['k%d' % i for i in range(n)], list(range(1, n + 1)), list(range(1, n + 1)), ['k%d' % i for i in range(n)]], ['NONE'] * n))
    elif uid == o.PATH:
        out.append(([[[1] * 316 for _ in range(316)]], 316))
        g, cells = o.serpentine_path(199, 501)
        out.append(([g], cells))
        g2 = [[1] * 316 for _ in range(316)]; g2[315][315] = 0
        out.append(([g2], -1))
    return out
