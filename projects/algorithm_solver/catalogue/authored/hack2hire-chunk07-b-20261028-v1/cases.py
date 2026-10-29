"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from itertools import product
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h07b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _tree(rng, n, max_depth):
    """Random {"val", "children"} tree with n nodes, unique vals and depth <= max_depth; returns (root, vals)."""
    vals = rng.sample(range(-50, 51), n)
    nodes = [{'val': v, 'children': []} for v in vals]
    depth = [0]
    for i in range(1, n):
        p = rng.choice([j for j in range(i) if depth[j] < max_depth])
        nodes[p]['children'].append(nodes[i]); depth.append(depth[p] + 1)
    return nodes[0], vals


def _caterpillar():
    """Spine vals 0..88 (spine node s at depth s), each with 1100 leaf children valued 1000 + 1100 * s + j."""
    child = None
    for s in range(88, -1, -1):
        kids = [{'val': 1000 + 1100 * s + j, 'children': []} for j in range(1100)]
        if child is not None: kids.insert(550, child)
        child = {'val': s, 'children': kids}
    return child


def _menu(rng, items, entries, only_wanted):
    out = []
    for e in range(entries):
        k = rng.choice([1, 1, 2, 2, 3, 4])
        chosen = rng.sample(items if only_wanted or rng.random() < 0.7 else items + ['zz', 'yy'], min(k, len(items)))
        out.append(['e%d' % e, rng.choice([1, 2, 3, 5, 8, 10, 1000000]), ','.join(chosen)])
    return out


def _monster(rng, uid, name):
    m = {'name': name, 'health': rng.choice([1, 2, 3, 5, 10, 1000]), 'attack': rng.choice([1, 2, 3, 4, 7, 1000])}
    if uid != _o.MTB1: m['defense'] = rng.choice([0, 0, 1, 2, 5, 1000])
    if uid == _o.MTB3: m['speed'] = rng.choice([1, 2, 2, 3, 1000])
    return m


def _hierarchy(rng, n, with_cost, p_hostile):
    names = rng.sample(['m%d' % i for i in range(60)], n)
    kids = {x: [] for x in names}
    for i in range(1, n): kids[names[rng.randrange(i)]].append(names[i])
    rows = []
    for x in names:
        label = x + ('*' if rng.random() < p_hostile else '')
        rows.append([label, rng.choice([1, 2, 3, 5, 10, 1000000]), kids[x]] if with_cost else [label, kids[x]])
    rng.shuffle(rows)
    return [rows, names[0]]


def _nested(rng, depth):
    out = []
    for _ in range(rng.randrange(0, 4)):
        if depth < 4 and rng.random() < 0.4: out.append(_nested(rng, depth + 1))
        else: out.append(rng.choice(['a', 'b', 'c', 'x1']))
    return out


def _shuffled_copy(rng, v):
    if type(v) is str: return v
    out = [_shuffled_copy(rng, x) for x in v]
    if out and rng.random() < 0.3: out.append(rng.choice(out))  # repeated element: same set
    rng.shuffle(out)
    return out


def _random_tree_edges(rng, n):
    fr, to = [], []
    for i in range(1, n):
        p = rng.randrange(i)
        if rng.random() < 0.5: fr.append(p); to.append(i)
        else: fr.append(i); to.append(p)
    perm = list(range(1, n)); rng.shuffle(perm); perm = [0] + perm  # relabel so 0 stays the root
    fr = [perm[x] for x in fr]; to = [perm[x] for x in to]
    order = list(range(n - 1)); rng.shuffle(order)
    return [fr[i] for i in order], [to[i] for i in order]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.CONVEX:
        args = [[[[0, 0]], 0, 0, 1], [[[1, 0]], -5, 5, 1], [[[-1, 0]], -5, 5, 3], [[[1, 0], [-1, 0]], -5, 5, 2], [[[0, 4], [2, -10], [-2, -10]], -20, 20, 1],
                [[[3, 0], [-3, 0]], -7, 7, 100]]
        for _ in range(250):
            lines = [[rng.randrange(-6, 7), rng.randrange(-30, 31)] for _ in range(rng.randrange(1, 6))]
            a = rng.randrange(-40, 20); b = a + rng.randrange(0, 60)
            args.append([lines, a, b, rng.choice([1, 1, 2, 3, 7, 100])])
    elif uid == o.BATT:
        args = [[[5], [0], 12], [[5], [1], 6], [[5], [1], 5], [[3, 4], [4, 3], 20], [[3, 4], [5, 3], 8], [[3, 4], [5, 3], 7], [[1, 1, 1], [2, 2, 2], 100]]
        for _ in range(250):
            n = rng.randrange(1, 6)
            usage = [rng.randrange(1, 8) for _ in range(n)]
            s = sum(usage)
            charge = [max(0, s - u + rng.choice([-2, -1, 0, 0, 1])) for u in usage] if rng.random() < 0.7 else [rng.randrange(0, 20) for _ in range(n)]
            args.append([usage, charge, rng.randrange(1, 80)])
    elif uid in (o.NARY1, o.NARY2):
        single = {'val': 7, 'children': []}
        if uid == o.NARY1: args = [[single, 7, 7], [{'val': 1, 'children': [{'val': 2, 'children': []}]}, 2, 1]]
        else: args = [[single, [7], [7]], [{'val': 1, 'children': [{'val': 2, 'children': []}, {'val': 3, 'children': []}]}, [2], [3, 2]]]
        for _ in range(250):
            n = rng.randrange(1, 30); root, vals = _tree(rng, n, rng.choice([2, 4, 10, 30]))
            if uid == o.NARY1: args.append([root, rng.choice(vals), rng.choice(vals)])
            else: args.append([root, rng.sample(vals, rng.randrange(1, min(n, 4) + 1)), rng.sample(vals, rng.randrange(1, min(n, 4) + 1))])
    elif uid == o.ASSET:
        args = [[1, 0, 0, 0, 0], [1, 1, 0, 10, 5], [2, 1, 0, 10, 5], [3, 5, 1, 2, 1], [1, 0, 1, 2, 0], [2, 2, 5, 5, 3], [4, 1, 0, 3, 2]]
        for _ in range(250):
            a = rng.randrange(0, 20); b = a + rng.randrange(0, 15)
            args.append([rng.randrange(1, 7), rng.randrange(0, 8), a, b, rng.randrange(0, 40)])
    elif uid in (o.MENU1, o.MENU2):
        args = [[[['x', 5, 'a']], ['a']], [[['x', 5, 'a']], ['b']], [[['x', 5, 'a,b'], ['y', 3, 'a'], ['z', 3, 'b']], ['a', 'b']],
                [[['x', 6, 'a,b'], ['y', 3, 'a'], ['z', 3, 'b']], ['a', 'b']], [[['x', 1, 'a,q,r']], ['a']]]
        for _ in range(250):
            items = ['a', 'b', 'c', 'd', 'e', 'f'][:rng.randrange(1, 7)]
            wants = rng.sample(items, rng.randrange(1, len(items) + 1))
            args.append([_menu(rng, items, rng.randrange(1, 10), False), wants])
    elif uid == o.MENU3:
        args = [[[['x', 5, 'a']], ['a']], [[['x', 5, 'a,b']], ['a']], [[['x', 5, 'a,b'], ['y', 2, 'a'], ['z', 3, 'b'], ['w', 5, 'b,a']], ['a', 'b']],
                [[['x', 2, 'a,b'], ['y', 2, 'b,c'], ['z', 2, 'a']], ['a', 'b', 'c']]]
        for _ in range(250):
            items = ['a', 'b', 'c', 'd', 'e', 'f'][:rng.randrange(1, 7)]
            wants = rng.sample(items, rng.randrange(1, len(items) + 1))
            menu = _menu(rng, items, rng.randrange(1, 13), False)
            for e in menu: e[1] = rng.choice([1, 2, 2, 3, 4])
            args.append([menu, wants])
    elif uid == o.SWAPS:
        args = [['R'], ['W'], ['RW'], ['RWR'], ['WRRWWR'], ['RRRR'], ['WWWW'], ['RWWWWR']]
        for _ in range(250): args.append([''.join(rng.choice('RW') for _ in range(rng.randrange(1, 25)))])
    elif uid in o.MTBS:
        for _ in range(255):
            names = rng.sample(['m%d' % i for i in range(30)], rng.randrange(2, 9))
            cut = rng.randrange(1, len(names))
            args.append([[_monster(rng, uid, x) for x in names[:cut]], [_monster(rng, uid, x) for x in names[cut:]]])
    elif uid in (o.MB1, o.MB2):
        cost = uid == o.MB2
        args = [[[['a', 1, []] if cost else ['a', []]], 'a'], [[['a*', 1, []] if cost else ['a*', []]], 'a'],
                [[['r', 4, ['h']] if cost else ['r', ['h']], ['h*', 1, []] if cost else ['h*', []]], 'r']]
        for _ in range(250):
            args.append(_hierarchy(rng, rng.randrange(1, 13), cost, rng.choice([0.0, 0.1, 0.25, 0.5])))
    elif uid == o.MFS:
        args = [['', 1], ['a', 2], ['a', 1], ['abab', 2], ['banana', 2], ['zzzz', 4], ['abc', 1]]
        for _ in range(250):
            s = ''.join(rng.choice('ab' if rng.random() < 0.5 else 'abcz') for _ in range(rng.randrange(0, 30)))
            args.append([s, rng.randrange(1, 6)])
    elif uid == o.MTS:
        args = [[[], 1], [[], 5], [[3], 1], [[3], 4], [[2, 1], 2], [[5, 5, 5], 2], [[-1000000000, 1000000000, 0], 3]]
        for _ in range(250):
            n = rng.randrange(0, 40)
            args.append([[rng.randrange(-20, 21) for _ in range(n)], rng.randrange(1, 12)])
    elif uid == o.NSE:
        args = [[[], []], [['a'], []], [['a'], [['a']]], [['a', 'a'], ['a']], [['a', ['b', 'c']], [['c', 'b'], 'a']], [[[]], []], [[[], []], [[]]],
                [[['a', 'b'], ['a']], [['a'], ['b', 'a'], ['a']]]]
        for _ in range(250):
            a = _nested(rng, 0)
            b = _shuffled_copy(rng, a) if rng.random() < 0.5 else _nested(rng, 0)
            args.append([a, b])
    elif uid == o.NEWS:
        args = [[[['a']], ['LEFT'], 1], [[['ab', 'c']], ['RIGHT'], 4], [[['hello', 'world'], ['x']], ['LEFT', 'RIGHT'], 5],
                [[['one', 'two', 'three']], ['LEFT'], 13]]
        for _ in range(250):
            width = rng.randrange(1, 16)
            paras = [[''.join(rng.choice('ab.-') for _ in range(rng.randrange(1, width + 1))) for _ in range(rng.randrange(1, 8))] for _ in range(rng.randrange(1, 5))]
            args.append([paras, [rng.choice(['LEFT', 'RIGHT']) for _ in paras], width])
    elif uid == o.OFFSET:
        args = [[[0]], [[1]], [[1, 0]], [[2, 0, 1]], [[0, 2, 1]], [[0, 1, 2]], [[5, 3, 0, 1, 2, 4]], [[1000000000, 0]]]
        for _ in range(250):
            n = rng.randrange(1, 15)
            pool = list(range(n + rng.randrange(0, 3))); rng.shuffle(pool)
            args.append([pool[:n]])
    elif uid == o.PAL:
        args = [[['a'], [], [], [0]], [['a', 'b'], [0], [1], [1, 0, 1]], [['a', 'b', 'a'], [1, 2], [0, 1], [2, 1, 0]]]
        for _ in range(250):
            n = rng.randrange(1, 25)
            fr, to = _random_tree_edges(rng, n)
            arr = [rng.choice('ab' if rng.random() < 0.5 else 'abcz') for _ in range(n)]
            args.append([arr, fr, to, [rng.randrange(n) for _ in range(rng.randrange(1, 8))]])
    else:
        args = [['12'], ['00'], ['99'], ['123'], ['3902'], ['0000000'], ['1234567890']]
        for _ in range(250): args.append([''.join(rng.choice('0123456789') for _ in range(rng.randrange(2, 40)))])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction (MTB rows replay the reference)."""
    o = _o; out = []
    if uid == o.CONVEX:
        out.append(([[[1, 0], [-1, 0]], -10**9, 10**9, 3], -1))  # grid is 2 mod 3: -1 and 2 bracket 0
        out.append(([[[2 * k, -k * k] for k in range(-1000, 1000)], -10**9, 10**9, 1], 0))  # tangents of x**2: F(x) = x**2 on [-1000, 999]
        out.append(([[[5, 7]], -10**9, 10**9, 1], -10**9))
        out.append(([[[-10**6, 10**12]], -10**9, 10**9, 7], -10**9 + (2 * 10**9 // 7) * 7))
        out.append(([[[0, 5], [1, -100], [-1, -100]], -10**9, 10**9, 10], -100))  # flat on [-105, 105]; leftmost grid point there is -100
    elif uid == o.BATT:
        n = 100000
        out.append(([[10] * n, [10 * (n - 1)] * n, 10**15], 10**14))
        tight = [10 * (n - 1)] * n; tight[500] += 1
        out.append(([[10] * n, tight, 10 * (n + 500)], n + 500))  # pass two reaches battery 500 exactly at the target
        out.append(([[10] * n, tight, 10 * (n + 500) + 1], -1))
        k = 70000
        out.append(([list(range(1, n + 1)), [0] * n, k * (k + 1) // 2], k))
    elif uid in (o.NARY1, o.NARY2):
        root = _caterpillar()
        deep = 1000 + 1100 * 88
        if uid == o.NARY1:
            out += [([root, deep, 1000], 90), ([root, 0, deep], 89), ([root, deep, deep], 0)]
        else:
            leaves = lambda s: [1000 + 1100 * s + j for j in range(1100)]
            out += [([root, leaves(0), leaves(88)], 90), ([root, leaves(50), [88]], 39), ([root, leaves(3) + [deep], leaves(88)], 0)]
    elif uid == o.ASSET:
        out += [([100, 100, 0, 1000, 1000], '50000.000000'), ([100, 50, 0, 1000, 1000], '50000.000000'), ([100, 100, 0, 1000, 0], '0.000000'),
                ([100, 0, 1, 1000, 1000], '50050.000000'), ([100, 100, 7, 7, 3], '300.000000')]
    elif uid in (o.MENU1, o.MENU2):
        names = ['item' + chr(97 + i) for i in range(12)]
        menu = [['s%d_%d' % (i, j), 100 + j, names[i]] for i in range(12) for j in range(24)]
        menu += [['h1', 500, ','.join(names[:6])], ['h2', 500, ','.join(names[6:])], ['t', 650, ','.join(names[:10])],
                 ['u', 640, ','.join(names[2:])], ['v', 200, ','.join(names[:2])]]
        out.append(([menu, names], 840 if uid == o.MENU1 else [840, 2]))  # u + v (two entries) ties u + s0 + s1 (three)
        out.append(([menu, names[:11] + ['zzz']], -1 if uid == o.MENU1 else [-1, -1]))
    elif uid == o.MENU3:
        names = ['item' + chr(97 + i) for i in range(10)]
        menu = [[c + str(i), 10, names[i]] for i in range(10) for c in 'ab']
        menu += [['p%d' % i, 20, names[2 * i] + ',' + names[2 * i + 1]] for i in range(5)]
        menu += [['x0', 60, ','.join(names[:5])], ['bad', 1, names[0] + ',zz']]
        combos = []
        for pick in product(range(5), repeat=5):
            ids = []
            for i, c in enumerate(pick):
                ids += ['p%d' % i] if c == 4 else ['ab'[c // 2] + str(2 * i), 'ab'[c % 2] + str(2 * i + 1)]
            combos.append(sorted(ids))
        out.append(([menu, names], sorted(combos)))  # 5**5 = 3125 optimal exact covers of cost 100
        out.append(([menu, names[:9] + ['zy']], []))  # zy is on no entry
    elif uid == o.SWAPS:
        r = 100000
        out += [(['RW' * r], r * r // 4), (['R' * 200000], 0), (['W' * r + 'R' * r], 0), (['R' + 'W' * 199998 + 'R'], 199998)]
    elif uid in o.MTBS:
        extra = ({} if uid == o.MTB1 else {'defense': 0}) | ({'speed': 5} if uid == o.MTB3 else {})
        a = [dict({'name': 'A%d' % i, 'health': 1000, 'attack': 1}, **extra) for i in range(100)]
        b = [dict({'name': 'B%d' % i, 'health': 1000, 'attack': 1}, **extra) for i in range(100)]
        out.append(([a, b], o.ref_battle(uid, a, b)))
        c = [dict(m, attack=1000) for m in b[:1]] + b[1:]
        out.append(([a, c], o.ref_battle(uid, a, c)))
    elif uid in (o.MB1, o.MB2):
        cost = uid == o.MB2
        spine = ['m%04d' % i for i in range(1000)]
        rows = []
        for i, s in enumerate(spine):
            leaves = ['l%04d_%02d' % (i, j) for j in range(99)]
            kids = leaves + ([spine[i + 1]] if i < 999 else [])
            rows.append([s, 1000 - i, kids] if cost else [s, kids])
            for leaf in leaves:
                label = leaf + ('*' if i in (500, 700) else '')
                rows.append([label, 1, []] if cost else [label, []])
        rng = random.Random(7); rng.shuffle(rows)
        if cost:
            out.append(([rows, 'm0000'], 500))
            hostile_root = [[r[0] + '*' if r[0] == 'm0000' else r[0]] + r[1:] for r in rows]
            out.append(([hostile_root, 'm0000'], -1))
        else:
            out.append(([rows, 'm0000'], spine[:501]))
            hostile_root = [[r[0] + '*' if r[0] == 'm0000' else r[0]] + r[1:] for r in rows]
            out.append(([hostile_root, 'm0000'], []))
            calm = [[r[0].rstrip('*'), r[1]] for r in rows]
            out.append(([calm, 'm0000'], sorted(r[0] for r in calm)))
    elif uid == o.MFS:
        out += [(['ab' * 50000, 100], 'ab' * 50), (['z' * 100000, 100], 'z' * 100), (['q' * 99, 100], ''),
                ([''.join(chr(97 + i % 26) for i in range(100000)), 1], 'a')]  # a, b, c, d occur 3847 times, the rest 3846
    elif uid == o.MTS:
        n = 100000
        rng = random.Random(11); perm = list(range(-n // 2, n // 2)); rng.shuffle(perm)
        out += [([list(range(n, 0, -1)), 7], list(range(1, n + 1))), ([perm, 1000], list(range(-n // 2, n // 2))),
                ([[3, 1, 2] * 33333 + [0], 1], [0] + [1] * 33333 + [2] * 33333 + [3] * 33333)]
    elif uid == o.NSE:
        def deep(atom):
            v = [atom]
            for _ in range(189): v = [v]
            return v
        out += [([deep('x'), deep('x')], True), ([deep('x'), deep('y')], False), ([[deep('x')[0], deep('x')[0]], deep('x')], True)]
        wide = ['w%d' % (i % 5000) for i in range(50000)]
        out += [([wide, wide[::-1]], True), ([wide, wide[:-5000] + ['w5000'] * 5000], False)]
    elif uid == o.NEWS:
        paras = [['abcd'] * 200 for _ in range(100)]
        aligns = ['LEFT' if i % 2 else 'RIGHT' for i in range(100)]
        out.append(([paras, aligns, 9], ['*' * 11] + ['*abcd abcd*'] * 10000 + ['*' * 11]))
        paras2 = [['abcdefg'] * 200 for _ in range(100)]
        lines = ['*' * 1002]
        for al in aligns:
            l1, l2 = ' '.join(['abcdefg'] * 125), ' '.join(['abcdefg'] * 75)
            for line in (l1, l2):
                pad = ' ' * (1000 - len(line))
                lines.append('*' + (line + pad if al == 'LEFT' else pad + line) + '*')
        lines.append('*' * 1002)
        out.append(([paras2, aligns, 1000], lines))
    elif uid == o.OFFSET:
        n = 200000
        out += [([list(range(n - 1, -1, -1))], [-1] * (n - 1) + [n - 1]), ([list(range(n))], list(range(n))),
                ([[x ^ 1 for x in range(n)]], [-1 if i % 2 == 0 else i for i in range(n)])]
    elif uid == o.PAL:
        n = 100000
        rng = random.Random(5)
        order = list(range(1, n)); rng.shuffle(order); order = [0] + order
        fr, to = [], []
        for i in range(1, n):
            if i % 2: fr.append(order[i - 1]); to.append(order[i])
            else: fr.append(order[i]); to.append(order[i - 1])
        depth = [0] * n
        for d, v in enumerate(order): depth[v] = d
        out.append(([['a'] * n, fr, to, list(range(n))], [depth[v] + 1 for v in range(n)]))
        alt = ['a' if depth[v] % 2 else 'b' for v in range(n)]
        qs = [order[-1], order[n // 2], 0]
        f = lambda d: (d + 2) // 2 + (d + 1) // 4  # segment of length L is palindrome-able iff L is odd or L % 4 == 0
        out.append(([alt, fr, to, qs], [f(n - 1), f(n // 2), 1]))
        star = ['a'] + ['b'] * (n - 1)
        out.append(([star, [0] * (n - 1), list(range(1, n)), list(range(n))], [1] * n))
    else:
        n = 100000
        out += [(['1' * n], str(pow(2, n - 2, 10)) * 2), (['0' * n], '00'), (['1' + '0' * (n - 1)], '10')]
    return out
