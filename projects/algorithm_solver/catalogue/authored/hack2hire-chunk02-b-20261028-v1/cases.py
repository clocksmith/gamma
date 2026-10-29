"""Private case generation from file-local independent references over INFERRED domains; no source examples."""
import importlib.util
from pathlib import Path
import itertools
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h02b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _org(rng, n):
    """Random tree over n employees; rows in shuffled order, children in random order."""
    names = ['E' + str(i) for i in range(n)]
    rng.shuffle(names)
    kids = {}
    for i in range(1, n): kids.setdefault(names[rng.randrange(0, i)], []).append(names[i])
    rows = [[m] + k for m, k in kids.items()]
    if not rows: rows = [[names[0]]]
    rng.shuffle(rows)
    return rows, names


def _parent_tree(rng, n):
    perm = list(range(1, n)); rng.shuffle(perm); order = [0] + perm
    parent = [-1] * n
    for i in range(1, n): parent[order[i]] = order[rng.randrange(0, i)]
    return parent


def _nary(rng, n, keys):
    nodes = [[rng.choice(keys), rng.randrange(-50, 51)] for _ in range(n)]
    order = list(range(1, n)); rng.shuffle(order); placed = [0]
    for c in order:
        p = rng.choice(placed)
        used = {nodes[x][0] for x in nodes[p][2:]}
        free = [k for k in keys if k not in used]
        if not free: p = 0 if p != 0 else p; used = {nodes[x][0] for x in nodes[p][2:]}; free = [k for k in keys if k not in used]
        if not free: continue
        nodes[c][0] = rng.choice(free); nodes[p].append(c); placed.append(c)
    # renumber to drop rows that could not be placed
    keep = sorted(placed); index = {old: i for i, old in enumerate(keep)}
    return [[nodes[o][0], nodes[o][1]] + [index[c] for c in nodes[o][2:]] for o in keep]


def _item(rng):
    good = '|'.join([rng.choice(['s1', 's2', 's3', 'x']), rng.choice(['apple', 'pear', 'kiwi']), str(rng.randrange(0, 20)), str(rng.randrange(0, 999))])
    bad = rng.choice(['s1|apple|3', 's1|apple|3|4|5', '|apple|1|1', 's2||1|1', 's1|pear|-1|5', 's1|pear|2|-5', 's3|kiwi|1.5|2',
                      's3|kiwi|2|x', 's3|kiwi| 2|3', 's1|apple|007|010', '', '|||', 's1|apple|+2|3'])
    return good if rng.random() < 0.7 else bad


def _maze(rng, n, with_headers):
    urls = ['/'] + ['/p' + str(i) for i in range(1, n)]
    maze = {}
    for u in urls:
        if rng.random() < 0.1: continue
        entry = {'message': rng.choice(['ok', 'ok', 'ok', 'Congrats', 'nope']), 'next': [rng.choice(urls + ['/zz']) for _ in range(rng.randrange(0, 4))]}
        if with_headers:
            if rng.random() < 0.4: entry['headers'] = {'Token': rng.choice(['a1', 'b2'])}
            if rng.random() < 0.3: entry['requiredHeaders'] = {'Token': rng.choice(['a1', 'b2'])}
        maze[u] = entry
    return maze


def _snapshot(rng, n):
    calls, live, iters = [], [], []
    for _ in range(n):
        op = rng.choice(['add', 'add', 'remove', 'contains', 'getIterator', 'hasNext', 'next', 'next'])
        if op in ('add', 'remove', 'contains'): calls.append((op, rng.randrange(-3, 6)))
        elif op == 'getIterator' or not iters: calls.append(('getIterator',)); iters.append(list(live))
        else:
            i = rng.randrange(len(iters))
            if op == 'next' and iters[i]: calls.append(('next', i)); iters[i].pop(0)
            else: calls.append(('hasNext', i))
        if calls[-1][0] == 'add' and calls[-1][1] not in live: live.append(calls[-1][1])
        if calls[-1][0] == 'remove' and calls[-1][1] in live: live.remove(calls[-1][1])
    return _ops('SnapshotSet', [], calls)


def _todo(rng, n, level):
    ids = ['t' + str(i) for i in range(6)]
    calls = []
    for _ in range(n):
        op = rng.choice(['add', 'add', 'get', 'updateStatus', 'addDependency', 'addDependency', 'getDependencies'] + (['getExecutionOrder'] if level == 2 else []))
        if op == 'add': calls.append((op, rng.choice(ids), rng.choice(['train model', 'eval', '']), rng.choice(['TODO', 'DONE', 'IN_PROGRESS'])))
        elif op == 'updateStatus': calls.append((op, rng.choice(ids), rng.choice(['TODO', 'DONE'])))
        elif op == 'addDependency': calls.append((op, rng.choice(ids), rng.choice(ids)))
        elif op == 'getExecutionOrder': calls.append((op,))
        else: calls.append((op, rng.choice(ids)))
    return _ops('ToDoList', [], calls)


def _variadic(rng, n):
    types = ['int', 'str', 'bool']
    calls, k = [], 0
    for _ in range(n):
        if rng.random() < 0.4:
            variadic = rng.random() < 0.5
            params = [rng.choice(types) for _ in range(rng.randrange(1 if variadic else 0, 4))]
            calls.append(('register', 'f' + str(k), params, variadic)); k += 1
        else: calls.append(('findMatches', [rng.choice(types[:2]) for _ in range(rng.randrange(0, 6))]))
    return _ops('FunctionLibrary', [], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid in (o.ORG1, o.ORG2, o.ORG3, o.ORG4):
        args = [[[['Solo']]] + ['Solo'] * {o.ORG3: 1, o.ORG4: 2}.get(uid, 0)]
        for _ in range(250):
            rows, names = _org(rng, rng.randrange(1, 25))
            extra = [rng.choice(names) for _ in range({o.ORG3: 1, o.ORG4: 2}.get(uid, 0))]
            args.append([rows] + extra)
    elif uid == o.PIVOT:
        for _ in range(150):
            header = ['order_id', 'cost', 'sell_price', 'product', 'date'] + (['state'] if rng.random() < 0.5 else [])
            rng.shuffle(header); rows = [header]
            for i in range(rng.randrange(0, 15)):
                v = {'order_id': 'o' + str(i), 'cost': rng.choice(['0', '1', '2.5', '10.05', '3.99', '0.01']),
                     'sell_price': rng.choice(['0', '1.5', '2', '9.99', '12.30', '0.1']), 'product': rng.choice(['milk', 'eggs', 'Bread']),
                     'date': '2024-' + rng.choice(['01', '02', '11']) + '-' + rng.choice(['01', '15', '31']), 'state': rng.choice(['CA', 'NY', ''])}
                rows.append([v[h] for h in header])
            args.append([rows])
    elif uid == o.PCT:
        args = [[['0,1'], 1], [['0,1'], 100], [['5,2', '3,2'], 50], [['5,2', '3,2'], 51]]
        for _ in range(200):
            recs = [f'{rng.choice([0, 1, 5, 99, 100, 250, 999999999])},{rng.randrange(1, 6)}' for _ in range(rng.randrange(1, 10))]
            args.append([recs, rng.randrange(1, 101)])
    elif uid == o.PYTH:
        args = [[1, [], [], 0, 0, 0]]
        for _ in range(200):
            n = rng.randrange(2, 40); parent = _parent_tree(rng, n)
            edges = [(i, parent[i]) if rng.random() < 0.5 else (parent[i], i) for i in range(1, n)]; rng.shuffle(edges)
            args.append([n, [a for a, _ in edges], [b for _, b in edges], rng.randrange(n), rng.randrange(n), rng.randrange(n)])
    elif uid == o.QLOG:
        args = [[[]], [['L: a b']], [['Q: a a', 'L: a']]]
        for _ in range(200):
            ev = []
            for _ in range(rng.randrange(1, 20)):
                k = 'Q' if rng.random() < 0.4 else 'L'
                ev.append(k + ': ' + ' '.join(rng.choice(['a', 'b', 'c', 'd', 'x1']) for _ in range(rng.randrange(1, 5 if k == 'Q' else 7))))
            args.append([ev])
    elif uid == o.NEGATE:
        args = [[[0], []], [[5], [[1, 1]]], [[-3, 0, 4], [[1, 3], [2, 2], [1, 3]]]]
        for _ in range(200):
            n = rng.randrange(1, 20); data = [rng.randrange(-9, 10) for _ in range(n)]
            ups = []
            for _ in range(rng.randrange(0, 15)):
                l = rng.randrange(1, n + 1); ups.append([l, rng.randrange(l, n + 1)])
            args.append([data, ups])
    elif uid == o.PREFIX:
        args = [[[]], [['a']], [['a', 'ab', 'abc']], [['abc', 'ab', 'b']]]
        for _ in range(200):
            words = list({''.join(rng.choice('ab') for _ in range(rng.randrange(1, 5))) for _ in range(rng.randrange(0, 12))})
            rng.shuffle(words); args.append([words])
    elif uid == o.RCS:
        seen = set()
        for _ in range(400):
            s = ''.join(rng.choice('0123') * rng.randrange(1, 13) for _ in range(rng.randrange(1, 5)))
            e = _o.encode_count_say(s)
            if len(e) <= 20 and e not in seen: seen.add(e); args.append([e])
        for e in ['1', '11', '0', '10', '111', '1111', '01', '100', '1011', '2122', '112233', '11111111111111111111', '99999999999999999999',
                  '10101010101010101010', '12121212121212121212', '1213', '113', '9', '91']:
            if e not in seen: seen.add(e); args.append([e])
    elif uid == o.REVERSI:
        args = [[[['.']], 0, 0, 'B'], [[['B']], 0, 0, 'W']]
        for _ in range(250):
            n = rng.randrange(2, 9)
            board = [[rng.choice('BW..BW') for _ in range(n)] for _ in range(n)]
            r, c = rng.randrange(n), rng.randrange(n)
            if rng.random() < 0.8: board[r][c] = '.'
            args.append([board, r, c, rng.choice('BW')])
    elif uid in (o.CART1, o.CART2, o.CART3):
        args = [[[]], [['s|n|0|0']], [['a|b|c|d']]]
        for _ in range(200): args.append([[_item(rng) for _ in range(rng.randrange(0, 12))]])
        if uid == o.CART3: args = [a + [rng.randrange(1, 5)] for a in args]
    elif uid == o.DFA:
        args = [['', [[0, 0]], 0, []], ['', [[0, 0]], 0, [0]]]
        for _ in range(250):
            m = rng.randrange(1, 6)
            table = [[rng.randrange(m), rng.randrange(m)] for _ in range(m)]
            acc = rng.sample(range(m), rng.randrange(0, m + 1))
            args.append([''.join(rng.choice('ab') for _ in range(rng.randrange(0, 15))), table, rng.randrange(m), acc])
    elif uid == o.DRAIN:
        args = [[[-1, 0], [0, 0]], [[-1, 0], [7, 3]]]
        for _ in range(200):
            n = rng.randrange(2, 40); args.append([_parent_tree(rng, n), [rng.randrange(0, 20) for _ in range(n)]])
    elif uid == o.NARY1:
        args = [[[['a', 5]]]]
        for _ in range(200): args.append([_nary(rng, rng.randrange(1, 30), ['a', 'b', 'c', 'd', 'e'])])
    elif uid == o.NARY2:
        args = [[[['r', 1]], [['r', -1]]]]
        for _ in range(200):
            a = _nary(rng, rng.randrange(1, 20), ['a', 'b', 'c']); b = _nary(rng, rng.randrange(1, 20), ['a', 'b', 'c'])
            b[0][0] = a[0][0]; args.append([a, b])
    elif uid in (o.MAZE1, o.MAZE2):
        args = [[{}], [{'/': {'message': 'Congrats', 'next': []}}]]
        for _ in range(250): args.append([_maze(rng, rng.randrange(1, 15), uid == o.MAZE2)])
    elif uid == o.JOURNEY:
        args = [[[]]]
        for _ in range(200):
            logs, used = [], set()
            for _ in range(rng.randrange(0, 25)):
                u = rng.choice(['u1', 'u2', 'u3', 'u4']); t = str(rng.choice([0, 1, 2, 9, 10, 11, 100, 99]))
                if (u, t) in used: continue
                used.add((u, t)); logs.append([u, t, rng.choice(['view', 'cart', 'buy', 'search'])])
            args.append([logs])
    elif uid == o.SNAP:
        args = [_ops('SnapshotSet', [], [])]
        for _ in range(200): args.append(_snapshot(rng, rng.randrange(1, 40)))
    elif uid in (o.TODO1, o.TODO2):
        args = [_ops('ToDoList', [], [])]
        for _ in range(200): args.append(_todo(rng, rng.randrange(1, 40), 2 if uid == o.TODO2 else 1))
    elif uid == o.VARIADIC:
        args = [_ops('FunctionLibrary', [], [('findMatches', [])]), _ops('FunctionLibrary', [], [('register', 'f', [], False), ('findMatches', [])])]
        for _ in range(200): args.append(_variadic(rng, rng.randrange(1, 30)))
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum(uid):
    """Large inferred-domain rows whose expected values follow from their construction."""
    o = _o; out = []
    if uid in (o.ORG1, o.ORG2):
        star = [['Boss'] + ['E' + str(i) for i in range(19999)]]
        suffix = (lambda k: ' (' + str(k) + ')') if uid == o.ORG2 else (lambda k: '')
        out.append(([star], ['Boss' + suffix(19999)] + ['  E' + str(i) + suffix(0) for i in range(19999)]))
        chain = [['C' + str(i), 'C' + str(i + 1)] for i in range(1999)][::-1]
        out.append(([chain], ['  ' * i + 'C' + str(i) + suffix(1999 - i) for i in range(2000)]))
    if uid in (o.ORG3, o.ORG4):
        chain = [['C' + str(i), 'C' + str(i + 1)] for i in range(19999)][::-1]
        if uid == o.ORG3: out.append(([chain, 'C19999'], ['C' + str(i) for i in range(20000)]))
        else: out.append(([chain, 'C19999', 'C19998'], 'C19998'))
        star = [['Boss'] + ['E' + str(i) for i in range(19999)]]
        if uid == o.ORG3: out.append(([star, 'E19998'], ['Boss', 'E19998']))
        else: out.append(([star, 'E0', 'E19998'], 'Boss'))
    if uid == o.PIVOT:
        rows = [['order_id', 'cost', 'sell_price', 'product', 'date', 'state']]
        cells = {}
        for i in range(10000):
            p, m = 'p' + str(i % 50).zfill(2), (i // 50) % 12 + 1
            rows.append(['o' + str(i), '1.25', '9999999.99', p, f'2024-{m:02d}-28', 'CA'])
            cells[(p, m)] = cells.get((p, m), 0) + 999999874
        months = ['2024-' + str(m).zfill(2) for m in range(1, 13)]
        table = [['product'] + months] + [[p] + ['%d.%02d' % divmod(cells[(p, m)], 100) for m in range(1, 13)] for p in sorted({p for p, _ in cells})]
        out.append(([rows], table))
    if uid == o.PCT:
        out.append(([[f'{i},1' for i in range(100000)], 50], 49999))
        out.append(([[f'{99999 - i},1000000' for i in range(100000)], 100], 99999))
        out.append(([[f'{99999 - i},1000000' for i in range(100000)], 1], 999))  # rank 1e9 -> (p+1)*1e6 >= 1e9
    if uid == o.PYTH:
        n = 100000
        out.append(([n, list(range(n - 1)), list(range(1, n)), 0, 0, 0], 1))
        # path: dist to 0 is u, to 0 again u, to n-1 is n-1-u; sorted (u,u,n-1-u) or (n-1-u,u,u)
        expected = sum(1 for u in range(n) if (lambda p, q, r: p * p + q * q == r * r)(*sorted((u, u, n - 1 - u))))
        out.append(([n, list(range(1, n)), list(range(n - 1)), 0, 0, n - 1], expected))
    if uid == o.QLOG:
        ev = ['Q: w' + str(i) + ' g' + str(i % 50) for i in range(2500)] + ['L: g' + str(i % 50) + ' w' + str(i) for i in range(2500)]
        exp = ['ACK: w' + str(i) + ' g' + str(i % 50) + '; ID=' + str(i + 1) for i in range(2500)] + ['M: g' + str(i % 50) + ' w' + str(i) + '; Q=' + str(i + 1) for i in range(2500)]
        out.append(([ev], exp))
    if uid == o.NEGATE:
        data = [i - 50000 for i in range(100000)]
        out.append(([data, [[1, 100000]] * 100000], data))
        out.append(([data, [[1, 100000]] * 99999], [-v for v in data]))
    if uid == o.PREFIX:
        chain = ['a' * k for k in range(1, 51)]
        others = [''.join('bcdefghijk'[int(ch)] for ch in str(i).zfill(4)) for i in range(9950)]
        out.append(([chain + others], ['a' * 50] + others))
    if uid == o.REVERSI:
        n = 60
        board = [['W'] * n for _ in range(n)]; board[0][0] = '.'; board[0][n - 1] = 'B'
        expected = [list(r) for r in board]; expected[0] = ['B'] * n
        out.append(([board, 0, 0, 'B'], expected))
        out.append(([board, 0, 0, 'W'], [list(r) for r in board]))
    if uid in (o.CART1, o.CART2, o.CART3):
        items = ['s' + str(i % 100).zfill(3) + '|name' + str(i % 100) + '|999999|999999' for i in range(1000)]
        if uid == o.CART1: out.append(([items], [999999000, 1000 * 999999 * 999999]))
        else:
            fmt = ['s' + str(i).zfill(3) + '|name' + str(i) + '|9999990|' + str(10 * 999999 * 999999) for i in range(100)]
            out.append(([items] + ([1000] if uid == o.CART3 else []), fmt))
    if uid == o.DFA:
        out.append((['ab' * 50000, [[1, 0], [0, 1]], 0, [0]], True))
        out.append((['a' * 99999, [[1, 0], [0, 1]], 0, [0]], False))
    if uid == o.DRAIN:
        n = 100000
        out.append(([[-1] + list(range(n - 1)), [1] * n], 0))
        out.append(([[-1] + [0] * (n - 1), [10000] * n], 10000 * (n - 2)))
    if uid == o.NARY1:
        n = 20000
        out.append(([[['k', i, i + 1] for i in range(n - 1)] + [['k', n - 1]]], [['k', i] for i in range(n)]))
    if uid == o.NARY2:
        n = 10000
        a = [['k', i, i + 1] for i in range(n - 1)] + [['k', n - 1]]
        b = [['k', 1, i + 1] for i in range(n - 1)] + [['k', 1]]
        out.append(([a, b], [['k', i + 1, i + 1] for i in range(n - 1)] + [['k', n]]))
    if uid in (o.MAZE1, o.MAZE2):
        n = 5000
        maze = {('/' if i == 0 else '/u' + str(i)): {'message': 'ok', 'next': ['/u' + str(i + 1), '/'] + ['/dead' + str(i)]} for i in range(n - 1)}
        maze['/u' + str(n - 1)] = {'message': 'Congrats', 'next': []}
        if uid == o.MAZE2:
            maze['/u' + str(n - 2)]['headers'] = {'Token': 'k1'}
            maze['/u' + str(n - 1)]['requiredHeaders'] = {'Token': 'k1'}
        out.append(([maze], '/u' + str(n - 1)))
        if uid == o.MAZE2:
            locked = {k: dict(v) for k, v in maze.items()}
            locked['/u' + str(n - 2)] = {'message': 'ok', 'next': ['/u' + str(n - 1)]}
            out.append(([locked], ''))
    if uid == o.JOURNEY:
        acts = ['a' + chr(97 + j) for j in range(10)]
        logs = [['u' + str(u), str(10**12 - j * 7), acts[j]] for u in range(2000) for j in range(10)]
        out.append(([logs], ['  ' * d + acts[9 - d] + ' (2000)' for d in range(10)]))
    if uid == o.SNAP:
        calls = [('add', i) for i in range(1000)] + [('getIterator',)] + [('remove', i) for i in range(999)] + [('next', 0)] * 1000
        out.append((_ops('SnapshotSet', [], calls), [None] + [True] * 1000 + [0] + [True] * 999 + list(range(1000))))
    if uid in (o.TODO1, o.TODO2):
        ids = ['t' + str(i).zfill(4) for i in range(1000)]
        calls = [('add', t, 'job', 'TODO') for t in ids] + [('addDependency', ids[i], ids[i + 1]) for i in range(999)]
        exp = [None] + [None] * 1000 + [True] * 999
        if uid == o.TODO2:
            calls += [('addDependency', ids[999], ids[0]), ('getExecutionOrder',)]
            exp += [False, ids[::-1]]
        else:
            calls += [('addDependency', ids[999], ids[0]), ('getDependencies', ids[999])]
            exp += [True, [ids[0]]]
        out.append((_ops('ToDoList', [], calls), exp))
    if uid == o.VARIADIC:
        calls = [('register', 'f' + str(i), ['int'] * (i % 8 + 1), i % 2 == 0) for i in range(1500)] + [('findMatches', ['int'] * 12)] * 1500
        hits = sorted('f' + str(i) for i in range(1500) if i % 2 == 0)
        out.append((_ops('FunctionLibrary', [], calls), [None] * 1501 + [hits] * 1500))
    return out
