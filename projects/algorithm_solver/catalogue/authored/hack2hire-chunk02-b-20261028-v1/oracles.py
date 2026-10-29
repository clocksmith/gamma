"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags. None is the official specification.
"""
from collections import Counter
from decimal import Decimal
import re

H = 'hack2hire:'
ORG1 = H + '6941d017e79fe20cf9ff443f'
ORG2 = H + '6945a3fbe85c245612a9786c'
ORG3 = H + '6945a578e85c245612a9786f'
ORG4 = H + '6945ada2e85c245612a97880'
PIVOT = H + '6883f1d260cda5e061502874'
PCT = H + '6a4fb137665efda9311f561b'
PYTH = H + '6987d34fdce67a3d5ecc12bd'
QLOG = H + '695c6e4d68e2c0dd046c494f'
NEGATE = H + '6a04eafa3141bbc31efdd672'
PREFIX = H + '68ac50961bf7d2097f647ef5'
RCS = H + '6834d05d071112104d71e177'
REVERSI = H + '69c3477921f6ab42269655fa'
CART1 = H + '6abed50f2faad6972d969c67'
CART2 = H + '6abed5372faad6972d969c6a'
CART3 = H + '6abed6282faad6972d969c6f'
DFA = H + '6a4e6cd2665efda9311f4d82'
SNAP = H + '68504f81839fbdf76404b1d1'
DRAIN = H + '6987a577fedd959e9aa444e4'
TODO1 = H + '69dd8c3595e80ae213e5b9c7'
TODO2 = H + '69dd8d2795e80ae213e5b9cf'
NARY1 = H + '69c733a121f6ab4226966853'
NARY2 = H + '69c7438121f6ab4226966890'
MAZE1 = H + '69f3d14942791c82ab992e68'
MAZE2 = H + '69f4bff979b9906debda5492'
JOURNEY = H + '6a2091c38b879849ebc118ad'
VARIADIC = H + '677b491778175fce2ecdfc10'
IDS = (ORG1, ORG2, ORG3, ORG4, PIVOT, PCT, PYTH, QLOG, NEGATE, PREFIX, RCS, REVERSI, CART1, CART2, CART3,
       DFA, SNAP, DRAIN, TODO1, TODO2, NARY1, NARY2, MAZE1, MAZE2, JOURNEY, VARIADIC)

_TODO_L1 = {'add': 3, 'get': 1, 'updateStatus': 2, 'addDependency': 2, 'getDependencies': 1}
_TODO_L2 = {**_TODO_L1, 'getExecutionOrder': 0}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    SNAP: ('SnapshotSet', 0, {'add': 1, 'remove': 1, 'contains': 1, 'getIterator': 0, 'hasNext': 1, 'next': 1}, ()),
    TODO1: ('ToDoList', 0, _TODO_L1, ('add',)),
    TODO2: ('ToDoList', 0, _TODO_L2, ('add',)),
    VARIADIC: ('FunctionLibrary', 0, {'register': 3, 'findMatches': 1}, ('register',)),
}
ARITY = {ORG1: 1, ORG2: 1, ORG3: 2, ORG4: 3, PIVOT: 1, PCT: 2, PYTH: 6, QLOG: 1, NEGATE: 2, PREFIX: 1, RCS: 1,
         REVERSI: 4, CART1: 1, CART2: 1, CART3: 2, DFA: 4, DRAIN: 2, NARY1: 1, NARY2: 2, MAZE1: 1, MAZE2: 1,
         JOURNEY: 1, **{uid: 2 for uid in CLASSES}}

NAME = r'[A-Za-z][A-Za-z0-9]{0,9}'
WORD = r'[a-z0-9]+'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def trace(uid, args, maximum):
    name, ctor, methods, _ = CLASSES[uid]
    envelope(args, 2)
    ops, rows = args
    if type(ops) is not list or type(rows) is not list or not 1 <= len(ops) <= maximum or len(ops) != len(rows):
        raise ValueError('trace shape')
    if ops[0] != name or type(rows[0]) is not list or len(rows[0]) != ctor: raise ValueError('initial constructor')
    for op, row in zip(ops[1:], rows[1:]):
        if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
            raise ValueError('method or arity')
    return ops, rows


def org_parents(relationships):
    """Validate the org domain and return (parent map, ordered children map, root)."""
    if type(relationships) is not list or not 1 <= len(relationships) <= 20000: raise ValueError('relationships size')
    parent, children, total = {}, {}, 0
    for row in relationships:
        if type(row) is not list or not row: raise ValueError('row shape')
        for name in row: text(name, NAME, 10)
        total += len(row)
        if row[0] in children: raise ValueError('manager row repeated')
        children[row[0]] = list(row[1:])
        for report in row[1:]:
            if report in parent: raise ValueError('employee reports twice')
            parent[report] = row[0]
    if total > 40000: raise ValueError('total size')
    names = set(children) | set(parent)
    roots = [x for x in names if x not in parent]
    if len(roots) != 1: raise ValueError('exactly one top-level manager')
    seen, stack = {roots[0]}, [roots[0]]
    while stack:
        for c in children.get(stack.pop(), []):
            if c in seen: raise ValueError('not a tree')
            seen.add(c); stack.append(c)
    if seen != names: raise ValueError('disconnected or cyclic')
    return parent, children, roots[0]


def amount(v):
    text(v, r'(0|[1-9][0-9]{0,6})(\.[0-9]{1,2})?', 10)


def validate_pivot(records):
    if type(records) is not list or not 1 <= len(records) <= 10001: raise ValueError('records size')
    header = records[0]
    if type(header) is not list or not 5 <= len(header) <= 10: raise ValueError('header')
    for h in header: text(h, r'[a-z_]{1,12}', 12)
    if len(set(header)) != len(header) or not {'order_id', 'cost', 'sell_price', 'product', 'date'} <= set(header):
        raise ValueError('header columns')
    for row in records[1:]:
        if type(row) is not list or len(row) != len(header): raise ValueError('row width')
        for h, v in zip(header, row):
            if h in ('cost', 'sell_price'): amount(v)
            elif h == 'date':
                text(v, r'[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])', 10)
            elif h == 'product': text(v, r'[A-Za-z0-9_-]{1,20}', 20)
            else: text(v, r'[A-Za-z0-9_-]{0,20}', 20)


def validate_items(items):
    if type(items) is not list or not len(items) <= 1000: raise ValueError('items size')
    for item in items:
        text(item, r'[ -~]{0,40}', 40)
        for field in item.split('|'):
            if re.fullmatch(r'-?[0-9]+', field) and len(field.lstrip('-')) > 6: raise ValueError('numeric field width')


def validate_tree_nodes(nodes, unique_sibling_keys):
    if type(nodes) is not list or not 1 <= len(nodes) <= 20000: raise ValueError('nodes size')
    seen_child = [False] * len(nodes)
    for row in nodes:
        if type(row) is not list or len(row) < 2: raise ValueError('node row')
        text(row[0], r'[a-z]{1,4}', 4); integer(row[1], -10**6, 10**6)
        for c in row[2:]:
            integer(c, 1, len(nodes) - 1)
            if seen_child[c]: raise ValueError('child twice')
            seen_child[c] = True
        if unique_sibling_keys and len({nodes[c][0] for c in row[2:] if type(c) is int and 0 <= c < len(nodes) and type(nodes[c]) is list and nodes[c]}) != len(row) - 2:
            raise ValueError('sibling keys must be unique')
    if not all(seen_child[1:]): raise ValueError('every non-root row is a child exactly once')
    seen, stack = {0}, [0]
    while stack:
        for c in nodes[stack.pop()][2:]:
            if c in seen: raise ValueError('cycle')
            seen.add(c); stack.append(c)
    if len(seen) != len(nodes): raise ValueError('unreachable rows')


def validate_maze(maze, with_headers):
    if type(maze) is not dict or not len(maze) <= 5000: raise ValueError('maze size')
    keys = {'message', 'next'} | ({'headers', 'requiredHeaders'} if with_headers else set())
    total = 0
    for url, entry in maze.items():
        text(url, r'/[a-z0-9/]{0,20}', 21)
        if type(entry) is not dict or not {'message', 'next'} <= set(entry) or not set(entry) <= keys: raise ValueError('entry shape')
        text(entry['message'], r'[A-Za-z ]{0,20}', 20)
        if type(entry['next']) is not list: raise ValueError('next list')
        total += len(entry['next'])
        for u in entry['next']: text(u, r'/[a-z0-9/]{0,20}', 21)
        for k in ('headers', 'requiredHeaders'):
            if k in entry:
                if type(entry[k]) is not dict or len(entry[k]) > 4: raise ValueError('header map')
                for hk, hv in entry[k].items(): text(hk, r'[A-Za-z-]{1,12}', 12); text(hv, r'[a-z0-9]{1,8}', 8)
    if total > 50000: raise ValueError('edge budget')


def validate_snapshot_trace(ops, rows):
    live, iters = {}, []
    for op, row in zip(ops[1:], rows[1:]):
        if op in ('add', 'remove', 'contains'):
            integer(row[0], -10**9, 10**9)
            if op == 'add' and row[0] not in live: live[row[0]] = True
            if op == 'remove': live.pop(row[0], None)
        elif op == 'getIterator': iters.append(list(live))
        else:
            if not iters: raise ValueError('no iterator')
            integer(row[0], 0, len(iters) - 1)
            if op == 'next':
                if not iters[row[0]]: raise ValueError('next past end')
                iters[row[0]].pop(0)


def validate_todo_trace(ops, rows):
    for op, row in zip(ops[1:], rows[1:]):
        text(row[0], r'[a-z0-9]{1,8}', 8) if row else None
        if op == 'add': text(row[1], r'[a-z ]{0,20}', 20); text(row[2], r'[A-Z_]{1,12}', 12)
        elif op == 'updateStatus': text(row[1], r'[A-Z_]{1,12}', 12)
        elif op == 'addDependency': text(row[1], r'[a-z0-9]{1,8}', 8)


def validate_variadic_trace(ops, rows):
    names = set()
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'register':
            text(row[0], r'[A-Za-z][A-Za-z0-9]{0,9}', 10)
            if row[0] in names: raise ValueError('function names unique')
            names.add(row[0])
            if type(row[1]) is not list or len(row[1]) > 8: raise ValueError('parameter list')
            for t in row[1]: text(t, r'[a-z]{1,6}', 6)
            if type(row[2]) is not bool or (row[2] and not row[1]): raise ValueError('variadic needs a parameter')
        else:
            if type(row[0]) is not list or len(row[0]) > 12: raise ValueError('argument list')
            for t in row[0]: text(t, r'[a-z]{1,6}', 6)


def validate_domain(uid, args):
    if uid not in ARITY: raise ValueError('unknown identity')
    envelope(args, ARITY[uid])
    if uid in CLASSES:
        ops, rows = trace(uid, args, 3001)
        if uid == SNAP: validate_snapshot_trace(ops, rows)
        elif uid == VARIADIC: validate_variadic_trace(ops, rows)
        else: validate_todo_trace(ops, rows)
        return
    if uid in (ORG1, ORG2, ORG3, ORG4):
        parent, children, root = org_parents(args[0])
        names = set(children) | set(parent)
        for name in args[1:]:
            text(name, NAME, 10)
            if name not in names: raise ValueError('unknown employee')
    elif uid == PIVOT: validate_pivot(args[0])
    elif uid == PCT:
        if type(args[0]) is not list or not 1 <= len(args[0]) <= 100000: raise ValueError('records size')
        for r in args[0]:
            text(r, r'(0|[1-9][0-9]{0,8}),[1-9][0-9]{0,6}', 17)
            if int(r.split(',')[1]) > 10**6: raise ValueError('count bound')
        integer(args[1], 1, 100)
    elif uid == PYTH:
        n, a, b = args[0], args[1], args[2]
        integer(n, 1, 100000); array(a, 0, n - 1, n - 1, n - 1); array(b, 0, n - 1, n - 1, n - 1)
        for v in args[3:]: integer(v, 0, n - 1)
        root = list(range(n))
        def find(x):
            while root[x] != x: root[x] = root[root[x]]; x = root[x]
            return x
        for u, v in zip(a, b):
            ru, rv = find(u), find(v)
            if ru == rv: raise ValueError('not a tree')
            root[ru] = rv
    elif uid == QLOG:
        if type(args[0]) is not list or not len(args[0]) <= 5000: raise ValueError('stream size')
        for e in args[0]: text(e, r'[QL]: ' + WORD + r'( ' + WORD + r')*', 200)
    elif uid == NEGATE:
        array(args[0], -10**9, 10**9, 1, 100000)
        if type(args[1]) is not list or len(args[1]) > 100000: raise ValueError('updates size')
        for u in args[1]:
            if type(u) is not list or len(u) != 2: raise ValueError('update shape')
            integer(u[0], 1, len(args[0])); integer(u[1], u[0], len(args[0]))
    elif uid == PREFIX:
        if type(args[0]) is not list or not len(args[0]) <= 10000: raise ValueError('words size')
        for w in args[0]: text(w, r'[a-z]{1,50}', 50)
        if len(set(args[0])) != len(args[0]): raise ValueError('words unique')
    elif uid == RCS: text(args[0], r'[0-9]{1,20}', 20)
    elif uid == REVERSI:
        board = args[0]
        if type(board) is not list or not 1 <= len(board) <= 60: raise ValueError('board size')
        for row in board:
            if type(row) is not list or len(row) != len(board): raise ValueError('square board')
            for c in row:
                if c not in ('B', 'W', '.') or type(c) is not str: raise ValueError('cell')
        integer(args[1], 0, len(board) - 1); integer(args[2], 0, len(board) - 1)
        if args[3] not in ('B', 'W') or type(args[3]) is not str: raise ValueError('player')
    elif uid in (CART1, CART2, CART3):
        validate_items(args[0])
        if uid == CART3: integer(args[1], 1, 1000)
    elif uid == DFA:
        text(args[0], r'[ab]{0,100000}', 100000)
        table = args[1]
        if type(table) is not list or not 1 <= len(table) <= 100: raise ValueError('states')
        for row in table: array(row, 0, len(table) - 1, 2, 2)
        integer(args[2], 0, len(table) - 1)
        array(args[3], 0, len(table) - 1, 0, len(table))
        if len(set(args[3])) != len(args[3]): raise ValueError('accepting states distinct')
    elif uid == DRAIN:
        parent, flow = args
        array(parent, -1, 99999, 2, 100000); array(flow, 0, 10000, len(parent), len(parent))
        if parent[0] != -1 or any(p < 0 or p >= len(parent) for p in parent[1:]): raise ValueError('parent array')
        state = [0] * len(parent); state[0] = 2
        for start in range(len(parent)):
            path, x = [], start
            while state[x] == 0: state[x] = 1; path.append(x); x = parent[x]
            if state[x] == 1: raise ValueError('cycle')
            for y in path: state[y] = 2
    elif uid == NARY1: validate_tree_nodes(args[0], False)
    elif uid == NARY2:
        validate_tree_nodes(args[0], True); validate_tree_nodes(args[1], True)
        if args[0][0][0] != args[1][0][0]: raise ValueError('root keys equal')
    elif uid in (MAZE1, MAZE2): validate_maze(args[0], uid == MAZE2)
    elif uid == JOURNEY:
        logs = args[0]
        if type(logs) is not list or not len(logs) <= 20000: raise ValueError('logs size')
        stamps = set()
        for row in logs:
            if type(row) is not list or len(row) != 3: raise ValueError('log row')
            text(row[0], r'[a-z0-9]{1,6}', 6); text(row[1], r'0|[1-9][0-9]{0,17}', 18); text(row[2], r'[a-z_]{1,10}', 10)
            if (row[0], row[1]) in stamps: raise ValueError('distinct timestamps per user')
            stamps.add((row[0], row[1]))


# ---------------------------------------------------------------------------- references

def ref_org(uid, relationships, *names):
    parent, children, root = org_parents(relationships)
    everyone = set(children) | set(parent)
    if len(everyone) > 400: raise ValueError('reference budget')

    def chain(x):
        out = [x]
        while out[-1] in parent: out.append(parent[out[-1]])
        return out[::-1]
    if uid == ORG3: return chain(names[0])
    if uid == ORG4:
        a, b = chain(names[0]), chain(names[1])
        return [x for x in a if x in b][-1]
    key = {}
    for x in everyone:
        path = chain(x)
        key[x] = tuple(children[p].index(c) for p, c in zip(path, path[1:]))
    lines = []
    for x in sorted(everyone, key=lambda e: key[e]):
        line = '  ' * len(key[x]) + x
        if uid == ORG2: line += ' (' + str(sum(1 for y in everyone if y != x and x in chain(y))) + ')'
        lines.append(line)
    return lines


def ref_pivot(records):
    header = records[0]
    at = {h: i for i, h in enumerate(header)}
    table = {}
    for row in records[1:]:
        cell = (row[at['product']], row[at['date']][:7])
        table[cell] = table.get(cell, Decimal(0)) + Decimal(row[at['sell_price']]) - Decimal(row[at['cost']])
    products = sorted({p for p, _ in table}); months = sorted({m for _, m in table})
    out = [['product'] + months]
    for p in products:
        out.append([p] + ['{:.2f}'.format(table.get((p, m), Decimal(0)).quantize(Decimal('0.01'))) for m in months])
    return out


def ref_percentile(records, percentile):
    expanded = []
    for r in records:
        price, count = map(int, r.split(','))
        expanded.extend([price] * count)
        if len(expanded) > 300000: raise ValueError('reference budget')
    expanded.sort()
    rank = -(-percentile * len(expanded) // 100)
    return expanded[rank - 1]


def ref_pyth(n, a, b, x, y, z):
    if n > 120: raise ValueError('reference budget')
    inf = 10**9
    d = [[0 if i == j else inf for j in range(n)] for i in range(n)]
    for u, v in zip(a, b): d[u][v] = d[v][u] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]: d[i][j] = d[i][k] + d[k][j]
    count = 0
    for u in range(n):
        p, q, r = sorted((d[u][x], d[u][y], d[u][z]))
        count += p * p + q * q == r * r
    return count


def ref_qlog(stream):
    queries, out = [], []
    for e in stream:
        kind, body = e[0], e[3:]
        if kind == 'Q':
            queries.append(body.split(' ')); out.append('ACK: ' + body + '; ID=' + str(len(queries)))
        else:
            words = body.split(' ')
            hit = [str(i + 1) for i, q in enumerate(queries) if all(w in words for w in q)]
            if hit: out.append('M: ' + body + '; Q=' + ','.join(hit))
    return out


def ref_negate(data, updates):
    if len(data) * (len(updates) + 1) > 2 * 10**6: raise ValueError('reference budget')
    out = list(data)
    for l, r in updates:
        for i in range(l - 1, r): out[i] = -out[i]
    return out


def ref_prefix(words):
    if len(words) > 2000: raise ValueError('reference budget')
    return [w for w in words if not any(o != w and o.startswith(w) for o in words)]


def encode_count_say(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]: j += 1
        out.append(str(j - i) + s[i]); i = j
    return ''.join(out)


def ref_rcs(encoded):
    """Enumerate every cut into 2- or 3-character pieces, decode literally, keep exact re-encodings."""
    n, results = len(encoded), set()

    def cuts(i):
        if i == n: yield []; return
        for size in (2, 3):
            if i + size <= n:
                for rest in cuts(i + size): yield [encoded[i:i + size]] + rest
    for pieces in cuts(0):
        decoded = ''.join(p[-1] * int(p[:-1]) for p in pieces)
        if decoded and encode_count_say(decoded) == encoded: results.add(decoded)
    return sorted(results)


def ref_reversi(board, row, col, player):
    n = len(board)
    out = [list(r) for r in board]
    if board[row][col] != '.': return out
    other = 'W' if player == 'B' else 'B'
    flips = []
    for r in range(n):
        for c in range(n):
            if board[r][c] != other or (r, c) == (row, col): continue
            dr, dc = r - row, c - col
            k = max(abs(dr), abs(dc))
            if not ((dr == 0 or abs(dr) == k) and (dc == 0 or abs(dc) == k)): continue
            ur, uc = dr // k, dc // k
            if not all(board[row + ur * t][col + uc * t] == other for t in range(1, k)): continue
            t = k + 1
            while 0 <= row + ur * t < n and 0 <= col + uc * t < n and board[row + ur * t][col + uc * t] == other: t += 1
            if 0 <= row + ur * t < n and 0 <= col + uc * t < n and board[row + ur * t][col + uc * t] == player:
                flips.append((r, c))
    if flips:
        out[row][col] = player
        for r, c in flips: out[r][c] = player
    return out


def cart_valid(items):
    rows = []
    for item in items:
        m = re.fullmatch(r'([^|]+)\|([^|]+)\|([0-9]+)\|([0-9]+)', item)
        if m: rows.append((m.group(1), m.group(2), int(m.group(3)), int(m.group(4))))
    return rows


def ref_cart(uid, items, k=None):
    rows = cart_valid(items)
    if uid == CART1: return [sum(r[2] for r in rows), sum(r[2] * r[3] for r in rows)]
    qty, cost, name = Counter(), Counter(), {}
    for sku, prod_name, q, p in rows:
        name.setdefault(sku, prod_name); qty[sku] += q; cost[sku] += q * p
    fmt = lambda s: '|'.join([s, name[s], str(qty[s]), str(cost[s])])
    if uid == CART2: return [fmt(s) for s in sorted(name)]
    ranked = sorted(name, key=lambda s: (-cost[s], s))
    return [fmt(s) for s in ranked[:k]]


def ref_dfa(word, table, start, accepting):
    good = set(accepting)
    for ch in reversed(word):
        col = 0 if ch == 'a' else 1
        good = {s for s in range(len(table)) if table[s][col] in good}
    return start in good


def ref_drain(parent, flow):
    n = len(parent)
    if n > 300: raise ValueError('reference budget')
    adj = [[] for _ in range(n)]
    for i in range(1, n): adj[i].append(parent[i]); adj[parent[i]].append(i)
    total, best = sum(flow), None
    for cut in range(1, n):
        side, stack = {cut}, [cut]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in side and not (u == cut and v == parent[cut]):
                    side.add(v); stack.append(v)
        s = sum(flow[v] for v in side)
        d = abs(total - 2 * s)
        best = d if best is None else min(best, d)
    return best


def ref_nary1(nodes):
    if len(nodes) > 900: raise ValueError('reference budget')
    def walk(i): return [[nodes[i][0], nodes[i][1]]] + [x for c in nodes[i][2:] for x in walk(c)]
    return walk(0)


def ref_nary2(a, b):
    if len(a) + len(b) > 900: raise ValueError('reference budget')
    def tree(nodes, i): return (nodes[i][0], nodes[i][1], [tree(nodes, c) for c in nodes[i][2:]])
    def merge(x, y):
        if y is None: return x
        bkids = {k[0]: k for k in y[2]}
        akeys = {k[0] for k in x[2]}
        kids = [merge(k, bkids.get(k[0])) for k in x[2]] + [k for k in y[2] if k[0] not in akeys]
        return (x[0], x[1] + y[1], kids)
    merged = merge(tree(a, 0), tree(b, 0))
    order = []
    def number(t): order.append(t); [number(k) for k in t[2]]
    number(merged)
    index = {id(t): i for i, t in enumerate(order)}
    return [[t[0], t[1]] + [index[id(k)] for k in t[2]] for t in order]


def ref_maze(maze, with_headers):
    missing = {'message': 'Not Found', 'next': []}
    level, seen, sent = ['/'], {'/'}, {'/': {}}
    while level:
        upcoming = []
        for url in level:
            entry = maze.get(url, missing)
            if with_headers and entry.get('requiredHeaders') and any(sent[url].get(k) != v for k, v in entry['requiredHeaders'].items()):
                entry = {'message': 'Unauthorized', 'next': []}
            if entry['message'] == 'Congrats': return url
            for nxt in entry['next']:
                if nxt not in seen:
                    seen.add(nxt); upcoming.append(nxt); sent[nxt] = dict(entry.get('headers', {})) if with_headers else {}
        level = upcoming
    return ''


def ref_journey(logs):
    per_user = {}
    for user, stamp, action in logs: per_user.setdefault(user, []).append((int(stamp), action))
    counts = Counter()
    for user, events in per_user.items():
        path = tuple(a for _, a in sorted(events))
        for i in range(1, len(path) + 1): counts[path[:i]] += 1
    return ['  ' * (len(p) - 1) + p[-1] + ' (' + str(counts[p]) + ')' for p in sorted(counts)]


def ref_snapshot(ops, rows):
    if len(ops) > 3001: raise ValueError('reference budget')
    elements, iterators, out = [], [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'add':
            out.append(row[0] not in elements)
            if out[-1]: elements.append(row[0])
        elif op == 'remove':
            out.append(row[0] in elements)
            if out[-1]: elements.remove(row[0])
        elif op == 'contains': out.append(row[0] in elements)
        elif op == 'getIterator': iterators.append([list(elements), 0]); out.append(len(iterators) - 1)
        elif op == 'hasNext': it = iterators[row[0]]; out.append(it[1] < len(it[0]))
        else: it = iterators[row[0]]; out.append(it[0][it[1]]); it[1] += 1
    return out


def ref_todo(uid, ops, rows):
    if len(ops) > 3001: raise ValueError('reference budget')
    tasks, deps, out = {}, {}, [None]

    def closure(start):
        seen, frontier = set(), [start]
        while frontier:
            nxt = []
            for t in frontier:
                for d in deps[t]:
                    if d not in seen: seen.add(d); nxt.append(d)
            frontier = nxt
        return seen
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'add':
            if row[0] not in tasks: tasks[row[0]] = [row[0], row[1], row[2]]; deps[row[0]] = []
            out.append(None)
        elif op == 'get': out.append(list(tasks.get(row[0], [])))
        elif op == 'updateStatus':
            ok = row[0] in tasks
            if ok: tasks[row[0]][2] = row[1]
            out.append(ok)
        elif op == 'addDependency':
            t, d = row
            ok = t in tasks and d in tasks and t != d and d not in deps[t]
            if ok and uid == TODO2 and t in closure(d): ok = False
            if ok: deps[t].append(d)
            out.append(ok)
        elif op == 'getDependencies': out.append(list(deps.get(row[0], [])))
        else:
            done, order = set(), []
            while len(order) < len(tasks):
                ready = [t for t in tasks if t not in done and all(d in done for d in deps[t])]
                pick = min(ready); done.add(pick); order.append(pick)
            out.append(order)
    return out


def ref_variadic(ops, rows):
    if len(ops) > 3001: raise ValueError('reference budget')
    funcs, out = [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'register': funcs.append(tuple(row)); out.append(None)
        else:
            args, hits = row[0], []
            for name, params, variadic in funcs:
                if not variadic: ok = list(params) == args
                else:
                    extra = len(args) - len(params)
                    ok = extra >= 0 and list(params) + [params[-1]] * extra == args
                if ok: hits.append(name)
            out.append(sorted(hits))
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid in (ORG1, ORG2, ORG3, ORG4): return ref_org(uid, *args)
    if uid == PIVOT:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_pivot(args[0])
    if uid == PCT: return ref_percentile(*args)
    if uid == PYTH: return ref_pyth(*args)
    if uid == QLOG:
        if len(args[0]) > 600: raise ValueError('reference budget')
        return ref_qlog(args[0])
    if uid == NEGATE: return ref_negate(*args)
    if uid == PREFIX: return ref_prefix(args[0])
    if uid == RCS: return ref_rcs(args[0])
    if uid == REVERSI:
        if len(args[0]) > 20: raise ValueError('reference budget')
        return ref_reversi(*args)
    if uid in (CART1, CART2, CART3): return ref_cart(uid, *args)
    if uid == DFA: return ref_dfa(*args)
    if uid == DRAIN: return ref_drain(*args)
    if uid == NARY1: return ref_nary1(args[0])
    if uid == NARY2: return ref_nary2(*args)
    if uid in (MAZE1, MAZE2): return ref_maze(args[0], uid == MAZE2)
    if uid == JOURNEY:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_journey(args[0])
    if uid == SNAP: return ref_snapshot(*args)
    if uid in (TODO1, TODO2): return ref_todo(uid, *args)
    return ref_variadic(*args)
