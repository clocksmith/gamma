"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (label propagation,
quadratic rescans, per-window recounts, materialised flattening, recursive expansion, point-level BFS,
permutation search, all-pairs comparison) and refuse inputs above a small budget.
"""
import math
import re

H = 'hack2hire:'
CBS = H + '6a02333a2608e589a944a29d'
CPS = H + '6a94a962cddc54478ddf6084'
CDG = H + '67eb0d624c9bb801bfd0ef6b'
CLL = H + '69bf10b121f6ab4226963d68'
CRA = H + '696294968742114304441df4'
CNT = H + '67e4db7050b60b77022f386f'
CPM = H + '677595ec0d31dc201f712037'
CAT = H + '68001116c48db1937ce88f45'
CDE = H + '67e08fffa59c3d249d3625e0'
CDR = H + '69fa8ff5661bab75bbca3e10'
CIP = H + '6a77ef3cd713d873ca7a9ab3'
CBD = H + '6a4fe73a665efda9311f575d'
COP = H + '681bafaba73bd75b806cb981'
CRC = H + '6a21d6fcd5c5b3e5f9c345f1'
CWT = H + '69beec3021f6ab4226963c1d'
CCF1 = H + '6a1a0a50c81f779dc6a23753'
CCF2 = H + '6a1a0a79c81f779dc6a23756'
CCF3 = H + '6a1a0a7ac81f779dc6a23757'

IDS = (CBS, CPS, CDG, CLL, CRA, CNT, CPM, CAT, CDE, CDR, CIP, CBD, COP, CRC, CWT, CCF1, CCF2, CCF3)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    CPM: ('PointMatrix', 0, {'addPoint': 2, 'isConnected': 2, 'getMinSteps': 2}, ('addPoint',)),
}
DIGITS = r'0|[1-9][0-9]{0,9}'
NAME20 = r'[A-Za-z0-9_]{1,20}'
MAX_OPS = 100001
BIG = 10**9


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def decimal(v, lo, hi):
    text(v, DIGITS, 10)
    if not lo <= int(v) <= hi: raise ValueError('decimal range')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


def rows_of(a, width, maximum, minimum=0):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('row list size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


def trace(uid, args, maximum=MAX_OPS):
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


def grid_shape(g, cell):
    if type(g) is not list or not g: raise ValueError('grid rows')
    width = len(g[0])
    if width < 1 or len(g) * width > 100000: raise ValueError('grid size')
    for row in g:
        if type(row) is not list or len(row) != width: raise ValueError('ragged grid')
        for v in row: cell(v)


def cbs_domain(board):
    grid_shape(board, lambda v: text(v, r'[A-Z][0-9]', 2))


def cdg_domain(prices):
    rows_of(prices, 2, 100000)
    for t, p in prices: integer(t, 0, BIG); integer(p, 1, BIG)
    if len({t for t, _ in prices}) != len(prices): raise ValueError('duplicate time')


def cll_domain(data, size):
    if type(data) is not list or len(data) > 100000: raise ValueError('data size')
    total = 0
    for inner in data:
        array(inner, -BIG, BIG); total += len(inner)
    if total > 100000: raise ValueError('total values')
    integer(size, 1, 100000)


def cra_domain(existing, new):
    for rows in (existing, new):
        rows_of(rows, 3, 100000)
        for company, contact, role in rows: text(company, NAME20, 20); text(contact, NAME20, 20); text(role, r'[A-Z_]{1,20}', 20)


def cnt_domain(tree, compressed):
    rows_of(tree, 2, 100000, 1)
    seen, parent_of = set(), {}
    for value, children in tree:
        integer(value, 0, BIG)
        if value in seen: raise ValueError('duplicate value')
        seen.add(value)
        array(children, 0, BIG)
        for c in children:
            if c in parent_of: raise ValueError('two parents')
            parent_of[c] = value
    root = tree[0][0]
    if root in parent_of or set(parent_of) != seen - {root}: raise ValueError('not a tree')
    # the rows must be exactly the preorder of the tree they describe
    children = {v: ch for v, ch in tree}
    order, stack = [], [root]
    while stack:
        v = stack.pop(); order.append(v)
        stack.extend(reversed(children[v]))
    if order != [v for v, _ in tree]: raise ValueError('rows not in preorder')
    array(compressed, 0, BIG)


def point(p):
    if type(p) is not list or len(p) != 2: raise ValueError('point shape')
    integer(p[0], -BIG, BIG); integer(p[1], -BIG, BIG)


def cpm_domain(args):
    ops, rows = trace(CPM, args)
    points, work = set(), 0
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addPoint':
            integer(row[0], -BIG, BIG); integer(row[1], -BIG, BIG); points.add((row[0], row[1]))
        else:
            point(row[0]); point(row[1])
            if op == 'getMinSteps': work += len(points)
    if work > 2000000: raise ValueError('query work budget')


def cip_price(v):
    if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= BIG: raise ValueError('price domain')


def cip_domain(products, prices, sold, sold_price):
    strlist(products, r'[A-Za-z0-9]{1,20}', 1, 100000, 20)
    if len(set(products)) != len(products): raise ValueError('duplicate product')
    strlist(sold, r'[A-Za-z0-9]{1,20}', 0, 100000, 20)
    if type(prices) is not list or type(sold_price) is not list or len(prices) != len(products) or len(sold_price) != len(sold):
        raise ValueError('length mismatch')
    for v in prices + sold_price: cip_price(v)
    known = set(products)
    if any(s not in known for s in sold): raise ValueError('unknown sold product')


def cop_domain(grid, ids):
    strlist(grid, r'[*_]{1,100000}', 1, 100000, 100000)
    width = len(grid[0])
    if any(len(r) != width for r in grid) or len(grid) * width > 100000: raise ValueError('grid shape')
    if type(ids) is not list or len(ids) != len(grid): raise ValueError('ids shape')
    for r, row in enumerate(ids):
        if type(row) is not list or len(row) != width: raise ValueError('ids row')
        for c, v in enumerate(row):
            if grid[r][c] == '*': integer(v, 1, BIG)
            elif v != 0 or type(v) is not int: raise ValueError('background id')


def crc_domain(perf, period):
    rows_of(perf, 3, 10000)
    for singer, role, year in perf: text(singer, NAME20, 20); text(role, NAME20, 20); decimal(year, 0, 9999)
    if len({r for _, r, _ in perf}) > 200: raise ValueError('distinct roles')
    integer(period, 0, 10000)


CARD = r'[0-9]{4,19}'
MERCHANT = r'[a-z0-9_]{1,20}'


def parse_request(s):
    text(s, r'[^,]+,[^,]+,[^,]+,[^,]+,[^,]+', 100)
    ts, uid, amount, card, merchant = s.split(',')
    decimal(ts, 0, BIG); text(uid, NAME20, 20); decimal(amount, 0, BIG); text(card, CARD, 19); text(merchant, MERCHANT, 20)
    return int(ts), uid, int(amount), card, merchant


def ccf_domain(uid, args):
    envelope(args, {CCF1: 1, CCF2: 2, CCF3: 3}[uid])
    if type(args[0]) is not list or len(args[0]) > 100000: raise ValueError('requests size')
    parsed = [parse_request(s) for s in args[0]]
    if len({p[1] for p in parsed}) != len(parsed): raise ValueError('duplicate id')
    if uid != CCF1:
        if type(args[1]) is not list or len(args[1]) > 100000: raise ValueError('rules size')
        for rule in args[1]:
            text(rule, r'[a-z_]+,[A-Za-z0-9_]+', 60)
            field, value = rule.split(',')
            if field == 'card_number': text(value, CARD, 19)
            elif field == 'merchant': text(value, MERCHANT, 20)
            elif field == 'max_amount': decimal(value, 0, BIG)
            else: raise ValueError('rule field')
    if uid == CCF3:
        if type(args[2]) is not list or len(args[2]) > 100000: raise ValueError('reports size')
        when = {p[1]: p[0] for p in parsed}
        for rep in args[2]:
            text(rep, r'[0-9]+,[A-Za-z0-9_]+', 40)
            ts, rid = rep.split(',')
            decimal(ts, 0, BIG)
            if rid not in when or int(ts) < when[rid]: raise ValueError('report target')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == CBS:
        envelope(args, 1); cbs_domain(args[0])
    elif uid == CPS:
        envelope(args, 1); array(args[0], -BIG, BIG)
    elif uid == CDG:
        envelope(args, 1); cdg_domain(args[0])
    elif uid == CLL:
        envelope(args, 2); cll_domain(*args)
    elif uid == CRA:
        envelope(args, 2); cra_domain(*args)
    elif uid == CNT:
        envelope(args, 2); cnt_domain(*args)
    elif uid == CPM: cpm_domain(args)
    elif uid == CAT:
        envelope(args, 4); array(args[0], 0, BIG); integer(args[1], 0, BIG); integer(args[2], 1, 100000); integer(args[3], 0, 100)
    elif uid == CDE:
        envelope(args, 2); array(args[0], -BIG, BIG, 1); integer(args[1], 1, len(args[0]))
    elif uid == CDR:
        envelope(args, 1); array(args[0], 1, BIG)
        if any(a > b for a, b in zip(args[0], args[0][1:])): raise ValueError('times not sorted')
    elif uid == CIP:
        envelope(args, 4); cip_domain(*args)
    elif uid == CBD:
        envelope(args, 2); array(args[0], 0, BIG, 0, 16); array(args[1], 0, BIG, 0, 16)
        if len(args[0]) != len(args[1]): raise ValueError('length mismatch')
    elif uid == COP:
        envelope(args, 2); cop_domain(*args)
    elif uid == CRC:
        envelope(args, 2); crc_domain(*args)
    elif uid == CWT:
        envelope(args, 2); text(args[0], r'[A-Za-z ]*', 100000); integer(args[1], 1, 100000)
    else: ccf_domain(uid, args)


# ---------------------------------------------------------------- references
def propagate(cells, linked):
    """Label propagation over cell indices until no label changes; returns the final labels."""
    label = {c: c for c in cells}
    changed = True
    while changed:
        changed = False
        for c in cells:
            for d in linked(c):
                if label[d] < label[c]: label[c] = label[d]; changed = True
    return label


def neighbours(r, c, R, C):
    return [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= r + dr < R and 0 <= c + dc < C]


def ref_cbs(board):
    R, C = len(board), len(board[0]); cells = [(r, c) for r in range(R) for c in range(C)]
    label = propagate(cells, lambda rc: [d for d in neighbours(*rc, R, C) if board[d[0]][d[1]][0] == board[rc[0]][rc[1]][0]])
    size, crowns = {}, {}
    for (r, c), lab in label.items():
        size[lab] = size.get(lab, 0) + 1; crowns[lab] = crowns.get(lab, 0) + int(board[r][c][1])
    return sum(size[k] * crowns[k] for k in size)


def ref_cps(p):
    out = []
    for i in range(len(p)):
        t = 0
        for j in range(len(p) - 1, i, -1):
            if p[j] < p[i]: t = j - i; break
        out.append(t)
    return out


def ref_cdg(prices):
    out = []
    for start in sorted({t - t % 10 for t, _ in prices}):
        inside = [(t, p) for t, p in prices if start <= t < start + 10]
        ps = [p for _, p in inside]
        out.append([start, max(ps), min(ps), min(inside)[1], max(inside)[1]])
    return out


def ref_cll(data, size):
    flat = []
    for inner in data:
        for v in inner: flat.append(v)
    out = [[] for _ in range((len(flat) + size - 1) // size)]
    for k, v in enumerate(flat): out[k // size].append(v)
    return out


def ref_cra(existing, new):
    current = [tuple(r) for r in existing]; out = []
    for r in new:
        t = tuple(r)
        if any(x == t for x in current): out.append('ALREADY_EXISTS')
        elif any(x[0] == t[0] and x[2] == t[2] for x in current): out.append('ROLE_TAKEN')
        else: out.append('VALID'); current.append(t)
    return out


def ref_cnt(tree, compressed):
    children = {v: list(ch) for v, ch in tree}; root = tree[0][0]
    gone = set(compressed) - {root}

    def expand(v):
        out = []
        for c in children[v]:
            out.extend(expand(c) if c in gone else [c])
        return out

    rows = []

    def emit(v):
        kids = expand(v); rows.append([v, kids])
        for c in kids: emit(c)
    emit(root)
    return rows


def ref_cpm(ops, rows):
    pts = []; out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addPoint':
            if (row[0], row[1]) not in pts: pts.append((row[0], row[1]))
            out.append(None); continue
        s, e = tuple(row[0]), tuple(row[1])
        dist = None
        if s in pts and e in pts:
            seen = {s: 0}; frontier = [s]
            while frontier:
                nxt = []
                for p in frontier:
                    for q in pts:
                        if q not in seen and (q[0] == p[0] or q[1] == p[1]): seen[q] = seen[p] + 1; nxt.append(q)
                frontier = nxt
            dist = seen.get(e)
        if op == 'isConnected': out.append(dist is not None)
        else: out.append(-1 if dist is None else dist)
    return out


def ref_cat(errors, threshold, duration, percent):
    n = 0
    for i in range(len(errors) - duration + 1):
        bad = len([e for e in errors[i:i + duration] if e > threshold])
        if bad * 100 >= percent * duration: n += 1
    return n


def ref_cde(nums, k):
    return [len(set(nums[i:i + k])) for i in range(len(nums) - k + 1)]


def ref_cdr(times):
    dropped = 0
    for i, t in enumerate(times):
        earlier = times[:i]
        if (len([x for x in earlier if x == t]) >= 3 or len([x for x in earlier if t - x < 10]) >= 20
                or len([x for x in earlier if t - x < 60]) >= 60):
            dropped += 1
    return dropped


def ref_cip(products, prices, sold, sold_price):
    bad = 0
    for name, entered in zip(sold, sold_price):
        if prices[products.index(name)] != entered: bad += 1
    return bad


def ref_cbd(lend, payback):
    n = len(lend); best = 0

    def dfs(last, used, days):
        nonlocal best
        best = max(best, days)
        if best == n: return
        for j in range(n):
            if not used[j] and (last is None or lend[j] >= payback[last]):
                used[j] = True; dfs(j, used, days + 1); used[j] = False
    dfs(None, [False] * n, 0)
    return best


def ref_cop(grid, ids):
    R, C = len(grid), len(grid[0])
    cells = [(r, c) for r in range(R) for c in range(C) if grid[r][c] == '*']

    def same(p, q): return grid[p[0]][p[1]] == '*' and grid[q[0]][q[1]] == '*' and ids[p[0]][p[1]] == ids[q[0]][q[1]]
    label = propagate(cells, lambda p: [q for q in neighbours(*p, R, C) if same(p, q)])
    return len(set(label.values()))


def ref_crc(perf, period):
    pairs = set()
    for i, (s1, r1, y1) in enumerate(perf):
        for s2, r2, y2 in perf[i + 1:]:
            if s1 == s2 and r1 != r2 and abs(int(y1) - int(y2)) <= period:
                pairs.add((s1, r1, r2)); pairs.add((s1, r2, r1))
    count = {}
    for _, a, b in pairs: count[(a, b)] = count.get((a, b), 0) + 1
    return [[a, b, str(count[(a, b)])] for a, b in sorted(count)]


def ref_cwt(text_, k):
    words = text_.lower().split()
    freq = {w: words.count(w) for w in set(words)}
    top = sorted(set(freq.values()), reverse=True)[:k]
    keep = sorted((-f, w) for w, f in freq.items() if f in top)
    return [[w, -negative] for negative, w in keep]


def ref_ccf(uid, args):
    reqs = [s.split(',') for s in args[0]]
    rules = [r.split(',') for r in args[1]] if uid != CCF1 else []
    reports = [r.split(',') for r in args[2]] if uid == CCF3 else []
    card_of = {r[1]: r[3] for r in reqs}
    remaining = list(range(len(reqs))); out = []
    while remaining:
        i = min(remaining, key=lambda k: (int(reqs[k][0]), k)); remaining.remove(i)
        ts, rid, amount, card, merchant = reqs[i]
        bad = False
        for field, value in rules:
            if (field == 'card_number' and card == value) or (field == 'merchant' and merchant == value) or (field == 'max_amount' and int(amount) > int(value)):
                bad = True
        for rts, target in reports:
            if card_of[target] == card and int(rts) < int(ts): bad = True
        out.append([rid, 'DECLINE' if bad else 'APPROVE'])
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == CBS:
        if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
        return ref_cbs(args[0])
    if uid == CPS:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_cps(args[0])
    if uid == CDG:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_cdg(args[0])
    if uid == CLL:
        if sum(map(len, args[0])) > 5000: raise ValueError('reference budget')
        return ref_cll(*args)
    if uid == CRA:
        if len(args[0]) + len(args[1]) > 600: raise ValueError('reference budget')
        return ref_cra(*args)
    if uid == CNT:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_cnt(*args)
    if uid == CPM:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_cpm(*args)
    if uid == CAT:
        if len(args[0]) * args[2] > 200000: raise ValueError('reference budget')
        return ref_cat(*args)
    if uid == CDE:
        if len(args[0]) * args[1] > 200000: raise ValueError('reference budget')
        return ref_cde(*args)
    if uid == CDR:
        if len(args[0]) > 1500: raise ValueError('reference budget')
        return ref_cdr(args[0])
    if uid == CIP:
        if len(args[0]) * len(args[2]) > 200000: raise ValueError('reference budget')
        return ref_cip(*args)
    if uid == CBD:
        if len(args[0]) > 8: raise ValueError('reference budget')
        return ref_cbd(*args)
    if uid == COP:
        if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
        return ref_cop(*args)
    if uid == CRC:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_crc(*args)
    if uid == CWT:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_cwt(*args)
    if len(args[0]) > 300 or sum(len(a) for a in args[1:]) > 300: raise ValueError('reference budget')
    return ref_ccf(uid, args)
