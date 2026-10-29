"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h11b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _fbt(rng):
    users = ['a', 'b', 'c', 'd9']; reqs = []; seqs = rng.sample(range(1, 999), 40)
    for i in range(rng.randrange(0, 40)):
        r = rng.random(); u, v = rng.choice(users), rng.choice(users)
        if r < 0.25: s = 'v1/REGISTER/%s/%d' % (u, rng.choice([0, 5, 10, 10**9]))
        elif r < 0.45: s = 'v1/FRIEND_REQUEST/%s/%s' % (u, v)
        elif r < 0.6: s = 'v1/ACCEPT_FRIEND_REQUEST/%d' % (rng.choice([x[0] for x in reqs]) if reqs and rng.random() < 0.8 else rng.randrange(1, 999))
        elif r < 0.85: s = 'v1/TRANSFER/%s/%s/%d' % (u, v, rng.choice([1, 3, 5, 7, 11]))
        else: s = 'v1/BALANCE/%s' % u
        reqs.append((seqs[i], s))
    return [[[str(q), s] for q, s in reqs]]


def _fsq(rng):
    return [[rng.randrange(1, 7) for _ in range(rng.randrange(0, 13))]] + [rng.randrange(0, 21) for _ in range(3)]


def _guu(rng):
    given = ['Al', 'Bo', 'alice', 'Ann', 'Bob']; middle = ['Q', 'Mary', 'x']
    family = ['Smith', 'Smithson', 'Smithsonian', 'Lee', 'Abcdefghij', 'Abcdefgx', 'Bcdefgh', 'Lu']
    out = []
    for _ in range(rng.randrange(0, 40)):
        words = [rng.choice(given)] + rng.sample(middle, rng.randrange(0, 3)) + [rng.choice(family)]
        out.append(' '.join(words))
    return [out]


def _gds(rng):
    iv = []
    for _ in range(rng.randrange(0, 40)):
        s = rng.randrange(9, 17); iv.append([s, rng.randrange(s + 1, min(17, s + 4) + 1)])
    return [iv, rng.randrange(1, 5)]


def _hop(rng):
    n = rng.randrange(1, 31); s = []
    for _ in range(n):
        if rng.random() < 0.2: s.append('X'); continue
        s.append(''.join(rng.choice('LR') + rng.choice(['', '', '1', '2', '3', '4', '5', '9']) for _ in range(rng.randrange(1, 4))))
    return [s, rng.randrange(n)]


def _ip(v): return '.'.join(str(v >> s & 255) for s in (24, 16, 8, 0))


def _ipr(rng):
    bases = [rng.randrange(0, 2**32) for _ in range(3)]
    routes = []
    for _ in range(rng.randrange(0, 15)):
        b = rng.choice(bases) ^ rng.choice([0, 0, 1, 1 << 7, 1 << 20, rng.randrange(2**32)])
        routes.append(['%s/%d' % (_ip(b), rng.choice([0, 1, 8, 12, 16, 20, 24, 25, 31, 32])), rng.choice(['a', 'b.c', 'hop-1', 'x9'])])
    queries = [_ip(rng.choice(bases) ^ rng.choice([0, 1, 255, 1 << 9, 1 << 30, rng.randrange(2**32)])) for _ in range(rng.randrange(0, 15))]
    return [routes, queries]


def _dsj(rng, uid):
    ch = rng.sample(['id', 'region', 'name'], 3) if rng.random() < 0.7 else ['id', 'region']
    ph = rng.sample(['region', 'id', 'amt', 'ok'], rng.randrange(2, 5))
    for need in ('id', 'region'):
        if need not in ph: ph.append(need)
    vals = {'id': ['1', '2', '3', ''], 'region': ['eu', 'us'], 'name': ['ann', 'b.o', ''], 'amt': ['5', '7.5', '-1'], 'ok': ['y', 'n']}
    c = [','.join(ch)] + [','.join(rng.choice(vals[h]) for h in ch) for _ in range(rng.randrange(0, 12))]
    p = [','.join(ph)] + [','.join(rng.choice(vals[h]) for h in ph) for _ in range(rng.randrange(0, 12))]
    key = rng.sample(['id', 'region'], rng.randrange(1, 3)) if uid == _o.DSJ4 else rng.choice(['id', 'region'])
    return [c, p, key]


def _its(rng):
    pool = ['a', 'b', 'c', 'd', 'e', 'f', 'g1']; calls = []
    for _ in range(rng.randrange(0, 30)):
        if rng.random() < 0.7: calls.append(('addTask', rng.choice(pool), rng.sample(pool, rng.choice([0, 0, 1, 1, 2, 3]))))
        else: calls.append(('getExecutionOrder',))
    return _ops('TaskScheduler', [], calls)


def _iwf(rng):
    nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(0, 15))]; name = rng.choice(_o.FILTERS)
    left = sum(1 for v in nums if _o.accepts(name, v)); calls = []
    for _ in range(rng.randrange(0, 25)):
        if left and rng.random() < 0.5: calls.append(('next',)); left -= 1
        else: calls.append(('hasNext',))
    return _ops('FilterIterator', [nums, name], calls)


def _jbh(rng):
    n = rng.randrange(1, 31); return [[rng.randrange(0, 7) for _ in range(n)], rng.randrange(n)]


def _kvp(rng):
    pool = ['a', 'ab', 'abc', 'b', 'ba', 'bab', 'aa']; present = set(); calls = []
    for _ in range(rng.randrange(0, 40)):
        r = rng.random(); k = rng.choice(pool)
        if r < 0.3: calls.append(('update', k, rng.randrange(-9, 10)) if k in present else ('set', k, rng.randrange(-9, 10))); present.add(k)
        elif r < 0.5: calls.append(('get', k))
        elif r < 0.65: calls.append(('deleteKey', k)); present.discard(k)
        else: calls.append(('prefixSearch', rng.choice(['', 'a', 'ab', 'b', 'ba', 'abc', 'c'])))
    return _ops('KVStore', [], calls)


def _klc(rng):
    out = ''
    while len(out) < rng.randrange(0, 11): out += rng.choice('0123456789') * rng.randrange(1, 4)
    return [out[:10]]


def _bst(values):
    """Level-order array of the BST obtained by inserting values in the given order."""
    if not values: return []
    left, right = {}, {}
    root = values[0]
    for v in values[1:]:
        cur = root
        while True:
            side = left if v < cur else right
            if cur in side: cur = side[cur]
            else: side[cur] = v; break
    out, queue, head = [], [root], 0
    while head < len(queue):
        v = queue[head]; head += 1
        out.append(v)
        if v is not None: queue.append(left.get(v)); queue.append(right.get(v))
    while out[-1] is None: out.pop()
    return out


def _lcb(rng):
    return [_bst(rng.sample(range(-20, 21), rng.randrange(1, 20))), _bst(rng.sample(range(-20, 21), rng.randrange(1, 20)))]


def _lgs(rng):
    n = rng.randrange(1, 14); perm = list(range(n)); rng.shuffle(perm); edges = []
    for i in range(1, n):
        if rng.random() < 0.8:
            e = [perm[i], perm[rng.randrange(i)]]; rng.shuffle(e); edges.append(e)
    rng.shuffle(edges)
    return [n, edges]


def _lkw(rng):
    n = rng.randrange(1, 31); w = rng.randrange(1, n + 1)
    return [[rng.randrange(-5, 6) for _ in range(n)], rng.randrange(1, w + 1), w]


def _points(rng, m, top):
    cells = [[x, y] for x in range(top) for y in range(top)]
    pts = rng.sample(cells, min(len(cells), rng.randrange(0, m + 1)))
    scale = rng.choice([1, 1, 7, 6000])
    return [[[x * scale, y * scale] for x, y in pts]]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.FBT:
        args = [[[]], [[['1', 'v1/REGISTER/ann/100'], ['2', 'v1/REGISTER/bo/5'], ['3', 'v1/TRANSFER/ann/bo/10'], ['4', 'v1/FRIEND_REQUEST/ann/bo'],
                        ['5', 'v1/ACCEPT_FRIEND_REQUEST/4'], ['6', 'v1/ACCEPT_FRIEND_REQUEST/4'], ['7', 'v1/TRANSFER/ann/bo/100'], ['8', 'v1/TRANSFER/ann/bo/1'],
                        ['9', 'v1/BALANCE/bo'], ['10', 'v1/BALANCE/cy'], ['11', 'v1/REGISTER/bo/1'], ['12', 'v1/FRIEND_REQUEST/bo/ann']]]]
        args += [_fbt(rng) for _ in range(250)]
    elif uid == o.FSQ:
        args = [[[], 0, 0, 0], [[2, 8, 4, 3, 2], 7, 11, 3], [[5], 4, 4, 4], [[1, 1, 1, 1], 1, 1, 1], [[3, 3, 3], 10, 0, 0]]
        args += [_fsq(rng) for _ in range(250)]
    elif uid == o.GUU:
        args = [[[]], [['John Smith', 'Jane Smith', 'John Q Smith', 'Alexander Montgomery', 'Al Montgomeryx', 'ann lee']]]
        args += [_guu(rng) for _ in range(250)]
    elif uid == o.GDS:
        args = [[[], 1], [[[9, 10], [9, 10], [9, 11]], 1], [[[9, 17]] * 5, 2], [[[16, 17], [15, 17], [9, 17]], 1]]
        args += [_gds(rng) for _ in range(250)]
    elif uid == o.HOP:
        args = [[['R'], 0], [['X'], 0], [['R2', 'X', 'L1R1', 'R'], 0], [['R', 'L', 'R'], 0], [['L3R2', 'R', 'R', 'L2', 'R10', 'L'], 2], [['R', 'R', 'X'], 0]]
        args += [_hop(rng) for _ in range(250)]
    elif uid == o.IPR:
        args = [[[], []], [[['192.168.1.0/24', 'a'], ['192.168.0.0/16', 'b'], ['0.0.0.0/0', 'c'], ['192.168.1.123/32', 'd'], ['192.168.1.0/24', 'e']],
                          ['192.168.1.123', '192.168.1.7', '192.168.2.1', '10.0.0.1', '192.168.1.124']], [[['10.255.0.0/8', 'x']], ['10.0.0.0', '11.0.0.0']]]
        args += [_ipr(rng) for _ in range(250)]
    elif uid in o.DSJ:
        key = ['id'] if uid == o.DSJ4 else 'id'
        args = [[['id,name', '1,ann', '2,bob', '3,cy', '2,dee'], ['pid,id,amt', 'p1,2,5', 'p2,4,7', 'p3,2,9'], key], [['id'], ['id', ''], key],
                [['id,name'], ['amt,id', '1,1'], key]]
        if uid == o.DSJ4: args.append([['a,b,c', '1,x,q', '1,y,r', '2,x,s'], ['b,z,a', 'x,1,1', 'y,2,1', 'x,3,2'], ['a', 'b']])
        args += [_dsj(rng, uid) for _ in range(250)]
    elif uid == o.ITS:
        args = [_ops('TaskScheduler', [], [('getExecutionOrder',), ('addTask', 'c', ['a', 'b']), ('addTask', 'a', []), ('getExecutionOrder',), ('addTask', 'b', ['a']),
                                           ('getExecutionOrder',), ('addTask', 'b', []), ('addTask', 'd', ['d']), ('addTask', 'e', ['f']), ('addTask', 'f', ['c', 'e']),
                                           ('addTask', 'f', ['c']), ('getExecutionOrder',)])]
        args += [_its(rng) for _ in range(250)]
    elif uid == o.IWF:
        args = [_ops('FilterIterator', [[], 'even'], [('hasNext',), ('hasNext',)]),
                _ops('FilterIterator', [[3, -2, 0, 7, 8, -5], 'odd'], [('hasNext',), ('next',), ('next',), ('hasNext',), ('hasNext',), ('next',), ('hasNext',)])]
        args += [_iwf(rng) for _ in range(250)]
    elif uid == o.JBH:
        args = [[[0], 0], [[1], 0], [[2, 1, 3, 5, 1], 2], [[1, 1, 1], 1], [[3, 0, 1, 4, 2, 9], 3]]
        args += [_jbh(rng) for _ in range(250)]
    elif uid == o.KVP:
        args = [_ops('KVStore', [], [('set', 'apple', 3), ('set', 'app', 1), ('set', 'b', 2), ('get', 'apple'), ('get', 'ap'), ('prefixSearch', 'ap'), ('update', 'app', 9),
                                     ('prefixSearch', ''), ('deleteKey', 'apple'), ('deleteKey', 'zz'), ('prefixSearch', 'app'), ('get', 'apple'), ('prefixSearch', 'c')])]
        args += [_kvp(rng) for _ in range(250)]
    elif uid == o.KLC:
        args = [[''], ['2'], ['22'], ['111'], ['7777'], ['0000'], ['12'], ['9919']]
        args += [_klc(rng) for _ in range(250)]
    elif uid == o.LCB:
        args = [[[5, 3, 8, 1, 4, None, 9], [7, 4, 9, None, None, 8]], [[1], [2]], [[-1], [-1, -5]], [[2, 1, 3], [3, 2, None, 1]]]
        args += [_lcb(rng) for _ in range(250)]
    elif uid == o.LGS:
        args = [[1, []], [3, [[0, 1], [1, 2]]], [5, [[0, 1], [0, 2], [0, 3], [0, 4]]], [4, []], [7, [[0, 1], [1, 2], [2, 3], [4, 5]]]]
        args += [_lgs(rng) for _ in range(250)]
    elif uid == o.LKW:
        args = [[[1], 1, 1], [[1, 3, -1, -3, 5, 3, 6, 7], 2, 3], [[4, 4, 4], 2, 2], [[5, 1, 9], 3, 3]]
        args += [_lkw(rng) for _ in range(250)]
    elif uid in (o.LRA1, o.LRA2):
        args = [[[]], [[[1, 1], [1, 3], [3, 1], [3, 3], [2, 2]]], [[[1, 1], [1, 3], [3, 1], [3, 3], [4, 1], [4, 3]]], [[[0, 1], [1, 0], [2, 1], [1, 2], [5, 5]]]]
        args += [_points(rng, 30 if uid == o.LRA1 else 14, 6) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _balanced(lo, hi):
    """Level order of the balanced BST over the integers lo..hi-1 (middle as root)."""
    out, queue, head = [], [(lo, hi)], 0
    while head < len(queue):
        item = queue[head]; head += 1
        if item is None: out.append(None); continue
        a, b = item; m = (a + b) // 2; out.append(m)
        queue.append((a, m) if a < m else None); queue.append((m + 1, b) if m + 1 < b else None)
    while out[-1] is None: out.pop()
    return out


def _compositions(total, letters):
    """All strings over letters where letter j weighs j + 1 and the weights sum to total, sorted (bottom-up lists)."""
    by = [['']]
    for t in range(1, total + 1):
        by.append(sorted(letters[g - 1] + rest for g in range(1, len(letters) + 1) if g <= t for rest in by[t - g]))
    return by[total]


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.FBT:
        m = n - 6
        reqs = [['1', 'v1/REGISTER/a/1000000000'], ['2', 'v1/REGISTER/b/0'], ['3', 'v1/FRIEND_REQUEST/a/b'], ['4', 'v1/ACCEPT_FRIEND_REQUEST/3']]
        reqs += [[str(5 + i), 'v1/TRANSFER/a/b/1'] for i in range(m)] + [[str(5 + m), 'v1/BALANCE/a'], [str(6 + m), 'v1/BALANCE/b']]
        out.append(([reqs], ['OK'] * (4 + m) + [str(10**9 - m), str(m)]))
        reqs = [[str(i), 'v1/REGISTER/u%d/7' % i] for i in range(49999)] + [['49999', 'v1/REGISTER/u0/5']]
        reqs += [[str(50000 + i), 'v1/TRANSFER/u1/u2/1'] for i in range(50000)]
        out.append(([reqs], ['OK'] * 49999 + ['ERROR'] * 50001))
    elif uid == o.FSQ:
        out.append(([[1] * n, 10**9, 10**9, 10**9], (n - 1) // 3))
        out.append(([[10000] * n, 10**9, 0, 0], (n - 1) * 10000))
        out.append(([[5] * (n - 1) + [10**9], 10**9 - 1, 10**9 - 1, 10**9 - 1], -1))
    elif uid == o.GUU:
        m = 10000
        for name, base in (('John Smith', 'jsmith'), ('Alexander Q Montgomery', 'amontgom')):
            out.append(([[name] * m], [base] + [base[:8 - len(str(k))] + str(k) for k in range(1, m)]))
    elif uid == o.GDS:
        out.append(([[[9, 17]] * n, n], n))
        out.append(([[[9, 10]] * n, 3], 3))
        out.append(([[[9 + i % 8, 10 + i % 8] for i in range(n)], 10000], 80000))
    elif uid == o.HOP:
        out.append(([['R'] * n, 0], n - 1))
        out.append(([['R2L1'] * n, 0], 50001))  # +2/-1 moves: 2a - b = 99999 with b odd, minimal at b = 1
        out.append(([['R'] * (n - 1) + ['X'], 0], -1))
        out.append(([['L1R100000'] * (n - 1) + ['L99999'], n - 1], 0))
    elif uid == o.IPR:
        base = 10 << 24
        routes = [['%s/%d' % (_ip(base), k), 'h%d' % k] for k in range(33)]
        routes += [['%s/32' % _ip((172 << 24) | (16 << 16) | i), 'x%d' % i] for i in range(19967)]
        queries = [_ip(base ^ (1 << (j % 32))) for j in range(10000)] + [_ip((172 << 24) | (16 << 16) | i) for i in range(9000)]
        queries += [_ip((172 << 24) | (17 << 16) | i) for i in range(1000)]
        expected = ['h%d' % (31 - j % 32) for j in range(10000)] + ['x%d' % i for i in range(9000)] + ['h0'] * 1000
        out.append(([routes, queries], expected))
    elif uid in o.DSJ:
        m = 20000
        cust = ['id,name'] + ['%d,n%d' % (i, i) for i in range(m)]
        if uid == o.DSJ4:
            proc = ['pid,id,name,amt'] + ['p%d,%d,n%d,%d' % (i, 2 * i, 2 * i if i % 2 == 0 else 0, i) for i in range(m)]
            exp = ['id,name,pid,id,name,amt'] + ['%d,n%d,p%d,%d,n%d,%d' % (i, i, i // 2, i, i, i // 2) for i in range(0, m, 4)]
            out.append(([cust, proc, ['name', 'id']], exp))
        else:
            proc = ['pid,id,amt'] + ['p%d,%d,%d' % (i, 2 * i, i) for i in range(m)]
            head = ['id,name,pid,id,amt']
            if uid == o.DSJ1: exp = head + ['%d,n%d,p%d,%d,%d' % (i, i, i // 2, i, i // 2) for i in range(0, m, 2)]
            else:
                exp = head + [('%d,n%d,p%d,%d,%d' % (i, i, i // 2, i, i // 2)) if i % 2 == 0 else '%d,n%d,,,' % (i, i) for i in range(m)]
                if uid == o.DSJ3: exp += [',,p%d,%d,%d' % (i, 2 * i, i) for i in range(m // 2, m)]
            out.append(([cust, proc, 'id'], exp))
        k = 300
        cust = ['key,c'] + ['k,c%d' % i for i in range(k)]; proc = ['p,key'] + ['p%d,k' % j for j in range(k)]
        out.append(([cust, proc, ['key'] if uid == o.DSJ4 else 'key'], ['key,c,p,key'] + ['k,c%d,p%d,k' % (i, j) for i in range(k) for j in range(k)]))
    elif uid == o.ITS:
        m = 2000; ids = ['t%04d' % i for i in range(m)]
        calls, exp = [], [None]
        for i in range(m):
            calls.append(('addTask', ids[i], [ids[i - 1]] if i else [])); exp.append(True)
            if i % 100 == 99: calls.append(('getExecutionOrder',)); exp.append(ids[:i + 1])
        calls += [('addTask', 't0000', []), ('addTask', 'zz', ['zz']), ('addTask', 'r', ['s']), ('addTask', 's', ['r']), ('getExecutionOrder',)]
        exp += [False, False, True, False, ids]
        out.append((_ops('TaskScheduler', [], calls), exp))
        calls, exp = [], [None]
        for i in range(m - 1, -1, -1):
            calls.append(('addTask', ids[i], [ids[i - 1]] if i else [])); exp.append(True)
            if i % 100 == 0: calls.append(('getExecutionOrder',)); exp.append(ids if i == 0 else [])
        calls += [('addTask', 't0000', ['t1999']), ('addTask', 'q', ['t1999']), ('getExecutionOrder',)]
        exp += [False, True, ids + ['q']]
        out.append((_ops('TaskScheduler', [], calls), exp))
    elif uid == o.IWF:
        nums = [i - 50000 for i in range(n)]
        calls, exp = [], [None]
        for v in range(-50000, 50000, 2): calls += [('hasNext',), ('next',)]; exp += [True, v]
        calls.append(('hasNext',)); exp.append(False)
        out.append((_ops('FilterIterator', [nums, 'even'], calls), exp))
        out.append((_ops('FilterIterator', [nums, 'positive'], [('next',)] * 49999 + [('hasNext',)]), [None] + list(range(1, 50000)) + [False]))
    elif uid == o.JBH:
        out.append(([[1] * n, 0], 0))
        out.append(([[1] * n, 50000], -1))
        out.append(([[0] * n, 777], -1))
        nums, c = [1] * n, 50000
        pos, t = c, 0
        while True:
            target = pos - (t + 1) if t % 2 == 0 else pos + (t + 1)
            if not 0 <= target < n: break
            t += 1; pos = target; nums[pos] = t + 1
        out.append(([nums, c], t))
    elif uid == o.KVP:
        m = 50000; keys = ['k' + _code(i, 4) for i in range(m)]
        calls = [('set', keys[i], i) for i in range(m)]; exp = [None] + [None] * m
        groups = (m + 675) // 676
        for j in range(1000):
            g = j % groups; calls.append(('prefixSearch', 'k' + _code(g, 2))); exp.append(list(range(g * 676, min(m, g * 676 + 676))))
        for i in range(20000):
            calls.append(('get', keys[i] if i % 2 == 0 else 'k' + _code(i, 3))); exp.append(i if i % 2 == 0 else -1)
        for i in range(20000): calls.append(('deleteKey', keys[i])); exp.append(None)
        for j in range(1000):
            g = j % groups; calls.append(('prefixSearch', 'k' + _code(g, 2))); exp.append(list(range(max(20000, g * 676), min(m, g * 676 + 676))))
        calls.append(('prefixSearch', '')); exp.append(list(range(20000, m)))
        out.append((_ops('KVStore', [], calls), exp))
    elif uid == o.KLC:
        out.append((['1' * 20], _compositions(20, 'ABC')))
        out.append((['7' * 25], _compositions(25, 'ST')))
        out.append((['0' * 60], ['Z' * 60]))
        out.append((['1234567890' * 6], [''.join(o.KEYPAD[d][0] for d in '1234567890') * 6]))
    elif uid == o.LCB:
        tree1 = _balanced(0, n)
        chain = [-50000]
        for v in range(-49999, 50000): chain += [None, v]
        out.append(([tree1, chain], 49999))
        left = [199999]
        for v in range(199998, 99999, -1): left += [v, None]
        left.pop()
        out.append(([tree1, left], -1))
        out.append(([_balanced(-10**9, -10**9 + n), _balanced(-10**9 + n - 1, -10**9 + 2 * n - 1)], -10**9 + n - 1))
    elif uid == o.LGS:
        out.append(([n, [[i, i + 1] for i in range(n - 1)]], n // 2))
        out.append(([n, [[0, i] for i in range(1, n)]], n - 1))
        out.append(([n, []], n))
        out.append(([n, [[i, i + 1] for i in range(0, n - 1, 2)]], n // 2))  # disjoint pairs: one per pair
    elif uid == o.LKW:
        m = 20000
        nums = list(range(m))
        out.append(([nums, 19, 10000], [[i + 9999 - j for j in range(19)] for i in range(m - 10000 + 1)]))
        nums = [m - i for i in range(m)]
        out.append(([nums, 1, 2], [[m - i] for i in range(m - 1)]))
        nums = [(i * 7919) % 20011 - 10000 for i in range(m)]
        out.append(([nums, m, m], [sorted(nums, reverse=True)]))
        out.append(([[5] * m, 10, 100], [[5] * 10 for _ in range(m - 99)]))
    elif uid == o.LRA1:
        s = 1904
        out.append(([[[x * s, y * s] for x in range(22) for y in range(22)]], (21 * s) ** 2))
        out.append(([[[7, y * 80] for y in range(500)]], 0))
        out.append(([[[x, y * 160] for x in (0, 40000) for y in range(250)]], 40000 * 249 * 160))
    elif uid == o.LRA2:
        N, c = 48612265, 20000; r = int(N ** 0.5) + 1
        pts = set()
        for a in range(-r, r + 1):
            rest = N - a * a
            if rest < 0: continue
            b = int(rest ** 0.5)
            while b * b > rest: b -= 1
            while (b + 1) ** 2 <= rest: b += 1
            if b * b == rest: pts.add((c + a, c + b)); pts.add((c + a, c - b))
        circle = sorted([list(p) for p in pts])
        out.append(([circle], 2 * N))
        out.append(([[[i * 133, i * 133] for i in range(300)]], 0))
        out.append(([[[x * 2500, y * 2500] for x in range(17) for y in range(17)]], 40000 * 40000))
    return out
