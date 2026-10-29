"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (parent-chain walks,
pairwise Fraction scores, label propagation, fixed-point relaxation, interval recursion, minute-by-minute
simulation, all-window scans, exhaustive fly/rest masks, direct replays, augmenting-path flow,
per-cell searches, point counting, simple-path enumeration, quadratic DP, nested recursive merges and
plain list scans) and refuse inputs above a small budget.
"""
from fractions import Fraction
import re

H = 'hack2hire:'
LMN = H + '68dc2e1c9736cfa4e906240c'
LUR1 = H + '697c3db29731315964cfb08b'
LUR2 = H + '697d9ce2b8c468a441586158'
LUR3 = H + '697da047b8c468a441586160'
LFC = H + '67cf7ef7aca6a2fa74a72d1f'
LVP = H + '6789c01711318cc872dd83ee'
MES = H + '6866f15ea2d59460201f2c7e'
MCO = H + '67800c576fee41e51af73dd8'
MFD = H + '67fd5511d2adf72ba62b0ec8'
MLE = H + '69efd5e296981f58ae1f6dc7'
MBT = H + '6a8615b8701a76fc6843aed0'
MBH = H + '67c766dc6c89e288437c3026'
MIO = H + '68eda9cd5abdefad4f6693be'
MMP = H + '67e4468750b60b77022f381c'
MVF = H + '69953e87312381f4e70fdb95'
MNT = H + '688b838d3867670cfb89414c'
MRP = H + '68d849afae12841706c1fc74'
MMQ = H + '68d84fa6ae12841706c1fc81'

IDS = (LMN, LUR1, LUR2, LUR3, LFC, LVP, MES, MCO, MFD, MLE, MBT, MBH, MIO, MMP, MVF, MNT, MRP, MMQ)
LUR = (LUR1, LUR2, LUR3)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    MMQ: ('MinMaxQueue', 0, {'enqueue': 1, 'dequeue': 0, 'getMin': 0, 'getMax': 0}, ('enqueue',)),
}


# ---------------------------------------------------------------- domain helpers
def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def intlist(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: integer(v, lo, hi)


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
    return list(zip(ops[1:], rows[1:]))


# N-ary trees use the LeetCode level-order form: root, null, then each node's children in BFS order,
# each group closed by null, trailing nulls removed; [] is the empty tree.
def nary_parse(a):
    if not a: return [], []
    if a[0] is None or (len(a) > 1 and a[1] is not None): raise ValueError('tree root')
    vals, kids, i, q = [a[0]], [[]], 2, 0
    while i < len(a):
        if q >= len(vals): raise ValueError('child group without parent')
        while i < len(a) and a[i] is not None:
            vals.append(a[i]); kids.append([]); kids[q].append(len(vals) - 1); i += 1
        i += 1; q += 1
    return vals, kids


def nary_serialize(vals, kids):
    if not vals: return []
    out = [vals[0], None]
    for q in range(len(vals)):
        out.extend(vals[c] for c in kids[q]); out.append(None)
    while out and out[-1] is None: out.pop()
    return out


def nary_domain(a, maximum=100000):
    if type(a) is not list or len(a) > 2 * maximum + 1: raise ValueError('tree list')
    for v in a:
        if v is not None: integer(v, -10**9, 10**9)
    vals, kids = nary_parse(a)
    if len(vals) > maximum: raise ValueError('tree size')
    if nary_serialize(vals, kids) != a: raise ValueError('non-canonical tree')
    return vals, kids


def nary_parents(a):
    vals, kids = nary_parse(a)
    parent = [-1] * len(vals)
    for p, cs in enumerate(kids):
        for c in cs: parent[c] = p
    return vals, kids, parent


FIELD = r'[a-z]{1,10}'
CELL = r'[A-Za-z0-9@._-]{0,12}'
DEC = r'[01](?:\.[0-9]{1,4})?'


def units(s):
    whole, _, frac = s.partition('.')
    return int(whole) * 10000 + int((frac + '0000')[:4])


def threshold_text(t):
    if type(t) is int: return str(t)
    if type(t) is float: return repr(t)
    raise ValueError('threshold type')


def lur_domain(records, weights, threshold):
    if type(records) is not list or not 1 <= len(records) <= 501: raise ValueError('records size')
    header = records[0]
    if type(header) is not list or not 2 <= len(header) <= 6 or 'id' not in header or len(set(map(str, header))) != len(header):
        raise ValueError('header')
    for f in header: text(f, FIELD, 10)
    ids, k = set(), header.index('id')
    for row in records[1:]:
        if type(row) is not list or len(row) != len(header): raise ValueError('row width')
        for v in row: text(v, CELL, 12)
        if row[k] == '' or row[k] in ids: raise ValueError('ids')
        ids.add(row[k])
    if type(weights) is not list or not 1 <= len(weights) <= len(header) - 1: raise ValueError('weights size')
    seen, total = set(), 0
    for w in weights:
        if type(w) is not str: raise ValueError('weight type')
        m = re.fullmatch(r'(%s):(%s)' % (FIELD, DEC), w)
        if m is None or m.group(1) == 'id' or m.group(1) not in header or m.group(1) in seen or units(m.group(2)) > 10000:
            raise ValueError('weight entry')
        seen.add(m.group(1)); total += units(m.group(2))
    if total != 10000: raise ValueError('weights must sum to 1')
    s = threshold_text(threshold)
    if re.fullmatch(DEC, s) is None or units(s) > 10000: raise ValueError('threshold domain')


NAME = r'[a-z0-9_]{1,10}'


def lfc_domain(deps, entry):
    if type(deps) is not list or len(deps) > 200000: raise ValueError('dependencies size')
    text(entry, NAME, 10)
    seen, nodes = set(), {entry}
    for e in deps:
        if type(e) is not list or len(e) != 2: raise ValueError('edge shape')
        text(e[0], NAME, 10); text(e[1], NAME, 10)
        if e[0] == e[1] or (e[0], e[1]) in seen: raise ValueError('self or duplicate edge')
        seen.add((e[0], e[1])); nodes.update(e)
    if len(nodes) > 100001: raise ValueError('service count')
    out, indeg = {v: [] for v in nodes}, dict.fromkeys(nodes, 0)
    for a, b in deps: out[a].append(b); indeg[b] += 1
    order = [v for v in nodes if indeg[v] == 0]
    for v in order:
        for w in out[v]:
            indeg[w] -= 1
            if indeg[w] == 0: order.append(w)
    if len(order) != len(nodes): raise ValueError('cycle')
    count = dict.fromkeys(nodes, 0); count[entry] = 1
    for v in order:
        for w in out[v]: count[w] += count[v]
    if max(count.values()) > 2**53 - 1: raise ValueError('load exceeds 2**53 - 1')


def grid_domain(grid, alphabet, maximum=200000):
    if type(grid) is not list or not grid: raise ValueError('grid rows')
    for row in grid: text(row, '[%s]+' % re.escape(alphabet), maximum)
    if len({len(r) for r in grid}) != 1 or len(grid) * len(grid[0]) > maximum: raise ValueError('grid shape')


def mmp_domain(n, edges, start, end):
    integer(n, 1, 12)
    if type(edges) is not list or len(edges) > n * (n - 1): raise ValueError('edges size')
    seen = set()
    for e in edges:
        if type(e) is not list or len(e) != 3: raise ValueError('edge shape')
        integer(e[0], 0, n - 1); integer(e[1], 0, n - 1); integer(e[2], 0, 10)
        if e[0] == e[1] or (e[0], e[1]) in seen: raise ValueError('self or duplicate edge')
        seen.add((e[0], e[1]))
    integer(start, 0, n - 1); integer(end, 0, n - 1)


def mvf_domain(days):
    if type(days) is not list or not days: raise ValueError('cities')
    width = None
    for row in days:
        intlist(row, 0, 7, 1, 200000)
        if width is None: width = len(row)
        if len(row) != width: raise ValueError('ragged weeks')
    if len(days) * width > 200000: raise ValueError('size')


def mmq_domain(args):
    calls = trace(MMQ, args, 200001)
    size = 0
    for op, row in calls:
        if op == 'enqueue': integer(row[0], -10**9, 10**9); size += 1
        else:
            if size == 0: raise ValueError('queue empty')
            if op == 'dequeue': size -= 1


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid in (LMN, MRP):
        envelope(args, 1); nary_domain(args[0])
    elif uid in LUR:
        envelope(args, 3); lur_domain(*args)
    elif uid == LFC:
        envelope(args, 2); lfc_domain(*args)
    elif uid == LVP:
        envelope(args, 1); text(args[0], r'[(){}\[\]]*', 100000)
    elif uid == MES:
        envelope(args, 1); grid_domain(args[0], 'UP.X')
        if sum(r.count('U') for r in args[0]) != 1: raise ValueError('exactly one start')
    elif uid == MCO:
        envelope(args, 2); text(args[0], '[01]+', 100000); integer(args[1], 0, 100000)
    elif uid == MFD:
        envelope(args, 2); intlist(args[0], 0, 10**9, 1); integer(args[1], 0, 100000)
        if len(args[0]) * args[1] > 10**6: raise ValueError('n * k')
    elif uid == MLE:
        envelope(args, 3); intlist(args[0], 0, 10**9, 1); intlist(args[1], 0, 10**9, len(args[0]), len(args[0])); integer(args[2], 0, 10**14)
    elif uid == MBT:
        envelope(args, 2); integer(args[0], 1, 100000); intlist(args[1], 1, 10**9)
    elif uid == MBH:
        envelope(args, 1); grid_domain(args[0], 'P-X')
    elif uid == MIO:
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 100000: raise ValueError('intervals size')
        for iv in args[0]:
            if type(iv) is not list or len(iv) != 2: raise ValueError('interval shape')
            integer(iv[0], -10**9, 10**9); integer(iv[1], iv[0], 10**9)
    elif uid == MMP:
        envelope(args, 4); mmp_domain(*args)
    elif uid == MVF:
        envelope(args, 1); mvf_domain(args[0])
    elif uid == MNT:
        envelope(args, 2); nary_domain(args[0]); nary_domain(args[1])
    elif uid == MMQ: mmq_domain(args)


# ---------------------------------------------------------------- references
def ref_lmn(root):
    vals, _, parent = nary_parents(root)
    if not vals: return 0
    counts = {}
    for v in range(len(vals)):
        level, x = 1, v
        while parent[x] != -1: x = parent[x]; level += 1
        counts[level] = counts.get(level, 0) + 1
    best = max(counts.values())
    return min(level for level, c in counts.items() if c == best)


def lur_scorer(records, weights, threshold):
    header, rows = records[0], records[1:]
    w = {}
    for item in weights:
        f, v = item.split(':'); w[header.index(f)] = Fraction(v)
    t = Fraction(threshold_text(threshold))

    def score(a, b): return sum((wt for k, wt in w.items() if a[k] != '' and a[k] == b[k]), Fraction(0))
    return rows, header.index('id'), score, t


def ref_lur1(records, weights, threshold):
    rows, k, score, t = lur_scorer(records, weights, threshold)
    return [[rows[i][k], rows[j][k]] for i in range(len(rows)) for j in range(i + 1, len(rows)) if score(rows[i], rows[j]) >= t]


def ref_lur2(records, weights, threshold):
    rows, k, score, t = lur_scorer(records, weights, threshold)
    label = list(range(len(rows)))
    pairs = [(i, j) for i in range(len(rows)) for j in range(i + 1, len(rows)) if score(rows[i], rows[j]) >= t]
    changed = True
    while changed:
        changed = False
        for i, j in pairs:
            low = min(label[i], label[j])
            if label[i] != low or label[j] != low: label[i] = label[j] = low; changed = True
    groups = []
    for root in sorted(set(label)):
        members = [rows[i][k] for i in range(len(rows)) if label[i] == root]
        if len(members) >= 2: groups.append(members)
    return groups


def ref_lur3(records, weights, threshold):
    rows, k, score, t = lur_scorer(records, weights, threshold)
    out = []
    for i in range(len(rows)):
        options = [(score(rows[i], rows[j]), -j) for j in range(len(rows)) if j != i and score(rows[i], rows[j]) >= t]
        out.append(rows[-max(options)[1]][k] if options else '')
    return out


def ref_lfc(deps, entry):
    nodes = sorted({entry} | {v for e in deps for v in e})
    load = dict.fromkeys(nodes, 0)
    for _ in range(len(nodes) + 1):
        new = {v: (1 if v == entry else 0) + sum(load[a] for a, b in deps if b == v) for v in nodes}
        if new == load: break
        load = new
    return [[v, load[v]] for v in nodes]


RANK = {'(': 1, '[': 2, '{': 3}
OPENER = {')': '(', ']': '[', '}': '{'}


def ref_lvp(s):
    memo = {}

    def valid(i, j):  # s[i:j] is a valid concatenation of pairs under the rank rule
        if i == j: return True
        if (i, j) not in memo:
            memo[(i, j)] = s[i] in RANK and any(
                OPENER.get(s[k]) == s[i] and all(RANK.get(c, 0) <= RANK[s[i]] for c in s[i + 1:k]) and valid(i + 1, k) and valid(k + 1, j)
                for k in range(i + 1, j))
        return memo[(i, j)]
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if valid(i, j)), default=0)


def neighbours(grid, r, c):
    m, n = len(grid), len(grid[0])
    return [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < m and 0 <= c + dc < n and grid[r + dr][c + dc] != 'X']


def ref_mes(grid):
    m, n = len(grid), len(grid[0])
    cells = [(r, c) for r in range(m) for c in range(n) if grid[r][c] != 'X']
    pos = {p for p in cells if grid[p[0]][p[1]] == 'U'}
    fire = {p for p in cells if grid[p[0]][p[1]] == 'P'}
    for t in range(len(cells) + 1):
        if any(r in (0, m - 1) or c in (0, n - 1) for r, c in pos): return t
        moved = {q for p in pos for q in neighbours(grid, *p)}
        fire = fire | {q for p in fire for q in neighbours(grid, *p)}
        pos = moved - fire
        if not pos: return -1
    return -1


def ref_mco(states, k):
    best = 0
    for i in range(len(states)):
        blocks = 0
        for j in range(i, len(states)):
            if states[j] == '0' and (j == i or states[j - 1] == '1'): blocks += 1
            if blocks <= k: best = max(best, j - i + 1)
    return best


def ref_mfd(arr, k):
    best = 0
    for mask in range(1 << len(arr)):
        energy, total = k, 0
        for i, a in enumerate(arr):
            if mask >> i & 1:
                if energy == 0: break
                energy -= 1; total += a
            else: energy = min(k, energy + 1)
        else: best = max(best, total)
    return best


def ref_mle(layers, energy, K):
    out = []
    for i in range(len(layers)):
        e, score = K, 0
        for j in range(i, len(layers)):
            e -= layers[j]
            if e < energy[j]: break
            score += 1
        out.append(score)
    return out


def ref_mbt(m, task):
    types = sorted(set(task))
    for t in range(len(task) // m, -1, -1):
        # nodes 0..m-1, types m.., source S, sink T; augmenting paths on unit/finite capacities
        S, T = m + len(types), m + len(types) + 1
        cap = {}

        def add(u, v, c): cap[(u, v)] = cap.get((u, v), 0) + c; cap.setdefault((v, u), 0)
        for node in range(m):
            add(S, node, t)
            for j in range(len(types)): add(node, m + j, 1)
        for j, ty in enumerate(types): add(m + j, T, task.count(ty))
        adj = {}
        for u, v in cap: adj.setdefault(u, []).append(v)
        flow = 0
        while True:
            prev, stack = {S: None}, [S]
            while stack and T not in prev:
                u = stack.pop()
                for v in adj.get(u, []):
                    if v not in prev and cap[(u, v)] > 0: prev[v] = u; stack.append(v)
            if T not in prev: break
            v = T
            while prev[v] is not None: cap[(prev[v], v)] -= 1; cap[(v, prev[v])] += 1; v = prev[v]
            flow += 1
        if flow == m * t: return m * t
    return 0


def ref_mbh(grid):
    best = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != '-': continue
            seen, frontier, d, found = {(r, c)}, [(r, c)], 0, None
            while frontier and found is None:
                if any(grid[a][b] == 'P' for a, b in frontier): found = d; break
                nxt = []
                for p in frontier:
                    for q in neighbours(grid, *p):
                        if q not in seen: seen.add(q); nxt.append(q)
                frontier, d = nxt, d + 1
            if found is None: return -1
            best = max(best, found)
    return best


def ref_mio(intervals):
    return max((sum(1 for s, e in intervals if s <= p <= e) for p, _ in intervals), default=0)


def ref_mmp(n, edges, start, end):
    out = {}
    for u, v, w in edges: out.setdefault(u, []).append((v, w))
    best = -1

    def walk(u, product, seen):
        nonlocal best
        if u == end: best = max(best, product); return
        for v, w in out.get(u, []):
            if v not in seen: walk(v, product * w, seen | {v})
    walk(start, 1, {start})
    return best


def ref_mvf(days):
    m, n = len(days), len(days[0])
    best = [(days[c][0], -(c != 0)) for c in range(m)]
    for w in range(1, n):
        best = [max((best[p][0] + days[c][w], best[p][1] - (p != c)) for p in range(m)) for c in range(m)]
    d, f = max(best)
    return [d, -f]


def nested(a):
    vals, kids = nary_parse(a)

    def build(i): return (vals[i], [build(c) for c in kids[i]])
    return build(0) if vals else None


def merge_nested(x, y):
    if x is None: return y
    if y is None: return x
    kx, ky = x[1], y[1]
    return (x[0] + y[0], [merge_nested(kx[i] if i < len(kx) else None, ky[i] if i < len(ky) else None) for i in range(max(len(kx), len(ky)))])


def serialize_nested(t):
    if t is None: return []
    vals, kids, queue = [t[0]], [], [t]
    for node in queue:
        kids.append([])
        for child in node[1]:
            kids[-1].append(len(vals)); vals.append(child[0]); queue.append(child)
    return nary_serialize(vals, kids)


def ref_mnt(a, b): return serialize_nested(merge_nested(nested(a), nested(b)))


def ref_mrp(root):
    vals, kids, parent = nary_parents(root)
    sums = []
    for v in range(len(vals)):
        if kids[v]: continue
        total, x = 0, v
        while x != -1: total += vals[x]; x = parent[x]
        sums.append(total)
    return min(sums, default=0)


def ref_mmq(calls):
    items, out = [], [None]
    for op, row in calls:
        if op == 'enqueue': items.append(row[0]); out.append(None)
        elif op == 'dequeue': out.append(items.pop(0))
        elif op == 'getMin': out.append(min(items))
        else: out.append(max(items))
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def tree_size(a): return sum(v is not None for v in a)


def reference(uid, args):
    validate_domain(uid, args)
    if uid == LMN:
        budget(tree_size(args[0]) <= 300); return ref_lmn(args[0])
    if uid in LUR:
        budget(len(args[0]) <= 41)
        return {LUR1: ref_lur1, LUR2: ref_lur2, LUR3: ref_lur3}[uid](*args)
    if uid == LFC:
        budget(len(args[0]) * (len(args[0]) + 1) <= 4000); return ref_lfc(*args)
    if uid == LVP:
        budget(len(args[0]) <= 22); return ref_lvp(args[0])
    if uid == MES:
        budget(len(args[0]) * len(args[0][0]) <= 120); return ref_mes(args[0])
    if uid == MCO:
        budget(len(args[0]) <= 300); return ref_mco(*args)
    if uid == MFD:
        budget(len(args[0]) <= 14); return ref_mfd(*args)
    if uid == MLE:
        budget(len(args[0]) <= 300); return ref_mle(*args)
    if uid == MBT:
        budget(args[0] <= 5 and len(args[1]) <= 14); return ref_mbt(*args)
    if uid == MBH:
        budget(len(args[0]) * len(args[0][0]) <= 120); return ref_mbh(args[0])
    if uid == MIO:
        budget(len(args[0]) <= 300); return ref_mio(args[0])
    if uid == MMP:
        budget(args[0] <= 8); return ref_mmp(*args)
    if uid == MVF:
        budget(len(args[0]) ** 2 * len(args[0][0]) <= 20000); return ref_mvf(args[0])
    if uid == MNT:
        budget(tree_size(args[0]) <= 150 and tree_size(args[1]) <= 150); return ref_mnt(*args)
    if uid == MRP:
        budget(tree_size(args[0]) <= 300); return ref_mrp(args[0])
    calls = trace(uid, args, 200001)
    budget(len(calls) <= 600)
    return ref_mmq(calls)
