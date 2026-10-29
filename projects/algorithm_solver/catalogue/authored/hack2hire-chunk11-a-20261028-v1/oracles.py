"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (exhaustive digit
choices, manager rescans, per-letter fill tests, full sorts, breadth-first search over strings,
per-score rescans, divide-and-conquer move counting, explicitly built Fibonacci trees, hop-layered
relaxation, regular expressions, exhaustive subsets, step-by-step board walks, flat entry lists,
menu rescans, character-level layout and whole-history recomputation) and refuse inputs above a
small budget.
"""
from collections import deque
from itertools import combinations
import re

H = 'hack2hire:'
GT = H + '6789754f11318cc872dd83ec'
LCM = H + '67cb459e9db31a8671abf92c'
FMS = H + '6a1cd98b8b879849ebc0fdaf'
MED = H + '68c2d9291f64f4312b0a3df2'
FMO = H + '67a25626c5f86173882e3d8f'
MST = H + '68ae7b5ec8631a6568126dbe'
FOM = H + '678e72f4fa7ce9616e190fbc'
FPT = H + '685303fe1af0034b3227652e'
MBN = H + '68a5e98e3a368733bb10422e'
PMW = H + '6a1f3ca28b879849ebc10ffb'
LSS = H + '69e51800ad1522fdaff14d5f'
FWP = H + '6795a8a1010c9ed2f849b1fd'
F2D = H + '68dd9212fb98b196fa540558'
FDS1 = H + '68799c22ef2889afac734164'
FDS2 = H + '6879a663ef2889afac734167'
FAW = H + '69fe591f574d87bc4900686f'
MOV1 = H + '68e2c59adab409e303d92947'
MOV2 = H + '68e2d042dab409e303d92952'

IDS = (GT, LCM, FMS, MED, FMO, MST, FOM, FPT, MBN, PMW, LSS, FWP, F2D, FDS1, FDS2, FAW, MOV1, MOV2)
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    F2D: ('Vector2D', 1, {'next': 0, 'hasNext': 0, 'remove': 0, 'getVector': 0}, ()),
    FDS1: ('FoodDeliverySystem', 2, {'getBestOption': 3}, ()),
    FDS2: ('FoodDeliverySystem', 2, {'getBestOption': 3, 'getBestOrder': 3}, ()),
    MOV2: ('MovieFriends', 1, {'watch': 2, 'getFriends': 1}, ('watch',)),
}
MAX_OPS = 100001

# ---------------------------------------------------------------- domain helpers
LOWER = r'[a-z]+'
NAME = r'[A-Za-z0-9_]{1,15}'
WORD = r'[a-z0-9]{1,10}'
SCORE = r'0|[1-9][0-9]{0,9}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def lst(a, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')


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
    return list(zip(ops[1:], rows[1:]))


def fib_size(n):
    """Node count of the order-n Fibonacci tree: S(0) = 0, S(1) = 1, S(n) = 1 + S(n - 2) + S(n - 1)."""
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b + 1
    return a


def fds_ctor(restaurants, menu):
    lst(restaurants, 1, 200); lst(menu, 0, 20000)
    ids = set()
    for r in restaurants:
        envelope(r, 3); text(r[0], NAME); integer(r[1], -10**6, 10**6); integer(r[2], -10**6, 10**6)
        if r[0] in ids: raise ValueError('duplicate restaurant')
        ids.add(r[0])
    seen = set()
    for m in menu:
        envelope(m, 3); text(m[0], NAME); text(m[1], NAME); integer(m[2], 1, 10**6)
        if m[0] not in ids or (m[0], m[1]) in seen: raise ValueError('menu row')
        seen.add((m[0], m[1]))


def validate_domain(uid, args):
    if uid == GT:
        envelope(args, 1); lst(args[0], 3, 50)
        for d in args[0]: integer(d, 0, 9)
    elif uid == LCM:
        envelope(args, 3); rows = args[0]; lst(rows, 1, 100000)
        names, children = [], 0
        for r in rows:
            envelope(r, 2); text(r[0], NAME); lst(r[1], 0, 100000)
            for c in r[1]: text(c, NAME)
            names.append(r[0]); children += len(r[1])
        index = {x: i for i, x in enumerate(names)}
        if len(index) != len(names) or children != len(names) - 1: raise ValueError('tree shape')
        seen, todo = {names[0]}, [0]
        while todo:
            for c in rows[todo.pop()][1]:
                if c not in index or c in seen: raise ValueError('tree shape')
                seen.add(c); todo.append(index[c])
        if len(seen) != len(names) or args[1] not in index or args[2] not in index: raise ValueError('tree shape')
    elif uid == FMS:
        envelope(args, 2); text(args[0], LOWER); lst(args[1], 0, 10000)
        for s in args[1]:
            text(s, r'[a-z-]*')
            if len(s) != len(args[0]): raise ValueError('skeleton length')
    elif uid == MED:
        envelope(args, 1); lst(args[0], 1, 200000)
        for v in args[0]: integer(v, -10**9, 10**9)
    elif uid == FMO:
        envelope(args, 1); text(args[0], r'[01]+', 200000)
    elif uid == MST:
        envelope(args, 2); lst(args[0], 0, 100000)
        for g in args[0]:
            envelope(g, 2); text(g[0], SCORE)
            if int(g[0]) > 10**9 or g[1] not in ('win', 'lose'): raise ValueError('game')
        t = args[1]
        if type(t) not in (int, float) or not 0 <= t <= 1: raise ValueError('threshold')
    elif uid == FOM:
        envelope(args, 1); lst(args[0], 1, 100000)
        for v in args[0]: integer(v, 0, 10**9)
    elif uid == FPT:
        envelope(args, 3); integer(args[0], 1, 75)
        size = fib_size(args[0]); integer(args[1], 0, size - 1); integer(args[2], 0, size - 1)
    elif uid == MBN:
        envelope(args, 3); integer(args[0], 2, 20000); lst(args[1], 0, 50000); integer(args[2], 1, 100000)
        for e in args[1]:
            envelope(e, 3); integer(e[0], 1, args[0]); integer(e[1], 1, args[0]); integer(e[2], 1, 10**9)
            if e[0] == e[1]: raise ValueError('self loop')
    elif uid == PMW:
        envelope(args, 2); lst(args[0], 1, 1000)
        for w in args[0]: text(w, LOWER, 30)
        if len(set(args[0])) != len(args[0]): raise ValueError('duplicate word')
        text(args[1], r'[a-z?.]+', 30)
    elif uid == LSS:
        envelope(args, 1); lst(args[0], 1, 100000)
        for v in args[0]: integer(v, 1, 10**9)
    elif uid == FWP:
        envelope(args, 1); text(args[0], LOWER, 20000)
    elif uid == FAW:
        envelope(args, 2); lst(args[0], 1, 1000); integer(args[1], 1, 1000)
        total = 0
        for a in args[0]:
            text(a, r'[!-~]+(?: [!-~]+)*', 200000); total += len(a)
            if max(len(w) for w in a.split(' ')) > args[1]: raise ValueError('word too long')
        if total > 200000: raise ValueError('total size')
    elif uid == MOV1:
        envelope(args, 3); ids, movies, k = args
        lst(ids, 1, 10000); lst(movies, len(ids), len(ids)); integer(k, 1, 50)
        total = 0
        for c in ids: text(c, WORD)
        if len(set(ids)) != len(ids): raise ValueError('duplicate id')
        for m in movies:
            lst(m, 0, 1000); total += len(m)
            for x in m: text(x, WORD)
        if total > 200000: raise ValueError('total size')
    elif uid == F2D:
        calls = trace(uid, args)
        vec = args[1][0][0]; lst(vec, 0, 10000); total = 0
        for row in vec:
            lst(row, 0, 100000); total += len(row)
            for v in row: integer(v, -10**9, 10**9)
        if total > 100000: raise ValueError('total size')
        returned, removed, last, snap = 0, 0, False, 0
        for op, row in calls:
            if op == 'next':
                if returned == total: raise ValueError('next past end')
                returned += 1; last = True
            elif op == 'remove':
                if last: removed += 1
                last = False
            elif op == 'getVector': snap += total - removed
        if snap > 2000000: raise ValueError('snapshot output budget')
    elif uid in (FDS1, FDS2):
        calls = trace(uid, args, 20001); fds_ctor(*args[1][0])
        for op, row in calls:
            integer(row[1], -10**6, 10**6); integer(row[2], -10**6, 10**6)
            if op == 'getBestOption': text(row[0], NAME)
            else:
                lst(row[0], 1, 10)
                for x in row[0]: text(x, NAME)
                if len(set(row[0])) != len(row[0]): raise ValueError('duplicate item')
    elif uid == MOV2:
        calls = trace(uid, args, 50001); integer(args[1][0][0], 1, 50)
        customers = set()
        for op, row in calls:
            text(row[0], WORD)
            if op == 'watch': text(row[1], WORD); customers.add(row[0])
        if len(customers) > 1000: raise ValueError('too many customers')
    else:
        raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_gt(digits):
    best = 0
    for size in (1, 2, 3):
        for pick in combinations(digits, size):
            best = max(best, int(''.join(map(str, pick))))
    return best


def ref_lcm(rows, a, b):
    def manager(x):
        for name, reports in rows:
            if x in reports: return name
        return None
    chain = [a]
    while manager(chain[-1]) is not None: chain.append(manager(chain[-1]))
    x = b
    while x not in chain: x = manager(x)
    return x


def ref_fms(word, skeletons):
    out = []
    for s in skeletons:
        if any(s.replace('-', c) == word for c in 'abcdefghijklmnopqrstuvwxyz'): out.append(s)
    return out


def ref_med(nums):
    s = sorted(nums); n = len(s)
    if n % 2: return s[n // 2]
    total = s[n // 2 - 1] + s[n // 2]
    return total // 2 if total % 2 == 0 else total / 2


def ref_fmo(image):
    target = image[::-1]; dist = {image: 0}; queue = deque([image])
    while queue:
        s = queue.popleft()
        if s == target: return dist[s]
        for i in range(len(s)):
            t = s[:i] + s[i + 1:] + s[i]
            if t not in dist: dist[t] = dist[s] + 1; queue.append(t)
    raise AssertionError('unreachable')


def ref_mst(games, threshold):
    best = -1
    for s in sorted({int(g[0]) for g in games}, reverse=True):
        sel = [g for g in games if int(g[0]) >= s]
        if sum(g[1] == 'lose' for g in sel) / len(sel) >= threshold: best = s
    return best


def ref_fom(arr):
    def moves(lo, hi, base):
        if lo >= hi: return 0
        m = min(arr[lo:hi]); total = m - base; i = lo
        while i < hi:
            if arr[i] == m: i += 1; continue
            j = i
            while j < hi and arr[j] != m: j += 1
            total += moves(i, j, m); i = j
        return total
    return moves(0, len(arr), 0)


def ref_fpt(n, start, dest):
    parent, children, counter = {}, {}, [0]
    def build(order, up, side):
        if order == 0: return None
        me = counter[0]; counter[0] += 1; parent[me] = (up, side); children[me] = {}
        left = build(order - 2, me, 'L') if order >= 2 else None
        right = build(order - 1, me, 'R') if order >= 2 else None
        if left is not None: children[me]['L'] = left
        if right is not None: children[me]['R'] = right
        return me
    build(n, None, None)
    prev = {start: None}; queue = deque([start])
    while queue:
        x = queue.popleft()
        if x == dest: break
        steps = [('U', parent[x][0])] if parent[x][0] is not None else []
        steps += [(d, c) for d, c in children[x].items()]
        for d, y in steps:
            if y not in prev: prev[y] = (x, d); queue.append(y)
    path, x = [], dest
    while prev[x] is not None: path.append(prev[x][1]); x = prev[x][0]
    return ''.join(reversed(path))


def ref_mbn(n, edges, k):
    inf = float('inf'); best = [inf] * (n + 1); best[1] = 0
    for _ in range(min(k, n)):
        nxt = best[:]
        for u, v, w in edges:
            for a, b in ((u, v), (v, u)):
                if best[a] < inf: nxt[b] = min(nxt[b], max(best[a], w))
        best = nxt
    return -1 if best[n] == inf else best[n]


def ref_pmw(words, pattern):
    rx = re.compile(''.join('.' if c == '?' else '.+' if c == '.' else c for c in pattern))
    return [w for w in words if rx.fullmatch(w)]


def ref_lss(arr):
    best = 0
    for size in range(1, len(arr) + 1):
        for pick in combinations(arr, size):
            acc = pick[0]
            for v in pick[1:]: acc &= v
            if acc > 0: best = size
    return best


def ref_fwp(word):
    def pos(c):
        i = ord(c) - 97; return i // 5, i % 5
    def ok(r, c): return (r, c) == (5, 0) or (0 <= r <= 4 and 0 <= c <= 4)
    r = c = 0; out = []
    for ch in word:
        tr, tc = pos(ch)
        while (r, c) != (tr, tc):
            for d, dr, dc, need in (('U', -1, 0, tr < r), ('L', 0, -1, tc < c), ('D', 1, 0, tr > r), ('R', 0, 1, tc > c)):
                if need and ok(r + dr, c + dc):
                    out.append(d); r += dr; c += dc; break
            else: raise AssertionError('stuck')
        out.append('!')
    return ''.join(out)


def ref_f2d(vec, calls):
    flat = [[r, v, True] for r, row in enumerate(vec) for v in row]
    pos, last, out = 0, None, [None]
    for op, _ in calls:
        if op == 'next':
            last = pos; out.append(flat[pos][1]); pos += 1
        elif op == 'hasNext': out.append(pos < len(flat))
        elif op == 'remove':
            if last is not None and flat[last][2]:
                flat[last][2] = False; out.append(True)
            else: out.append(False)
            last = None
        else:
            snap = [[] for _ in vec]
            for r, v, alive in flat:
                if alive: snap[r].append(v)
            out.append(snap)
    return out


def ref_fds(restaurants, menu, calls):
    out = [None]
    for op, row in calls:
        items = [row[0]] if op == 'getBestOption' else row[0]
        prices, times = [], []
        for rid, x, y in restaurants:
            got = [m[2] for it in items for m in menu if m[0] == rid and m[1] == it]
            if len(got) == len(items):
                prices.append(sum(got)); times.append(abs(x - row[1]) + abs(y - row[2]))
        out.append([min(prices), min(times)] if prices else [-1, -1])
    return out


def ref_faw(articles, width):
    lines = []
    for n, a in enumerate(articles):
        if n: lines.append('')
        line, col = [], 0
        for w in a.split(' '):
            need = len(w) if col == 0 else col + 1 + len(w)
            if col and need > width:
                lines.append(''.join(line)); line, col = [], 0; need = len(w)
            if col: line.append(' ')
            for ch in w: line.append(ch)
            col = need
        lines.append(''.join(line))
    return lines


def ref_mov1(ids, movies, k):
    keys = [set(m[-k:]) if len(m) >= k else None for m in movies]
    used, groups = set(), []
    for i in range(len(ids)):
        if keys[i] is None or i in used: continue
        g = [j for j in range(i, len(ids)) if keys[j] is not None and keys[j] == keys[i]]
        used.update(g)
        if len(g) >= 2: groups.append([ids[j] for j in g])
    return groups


def ref_mov2(k, calls):
    hist, out = {}, [None]
    for op, row in calls:
        if op == 'watch':
            hist.setdefault(row[0], []).append(row[1]); out.append(None); continue
        def key(c):
            h = hist.get(c, [])
            return set(h[-k:]) if len(h) >= k else None
        me = key(row[0])
        out.append([] if me is None else sorted(c for c in hist if c != row[0] and key(c) == me))
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == GT: return ref_gt(*args)
    if uid == LCM:
        budget(len(args[0]) <= 300); return ref_lcm(*args)
    if uid == FMS:
        budget(len(args[1]) * len(args[0]) <= 20000); return ref_fms(*args)
    if uid == MED:
        budget(len(args[0]) <= 5000); return ref_med(*args)
    if uid == FMO:
        budget(len(args[0]) <= 9); return ref_fmo(*args)
    if uid == MST:
        budget(len(args[0]) <= 300); return ref_mst(*args)
    if uid == FOM:
        budget(len(args[0]) <= 300); return ref_fom(*args)
    if uid == FPT:
        budget(args[0] <= 14); return ref_fpt(*args)
    if uid == MBN:
        budget(args[0] <= 60 and len(args[1]) <= 200); return ref_mbn(*args)
    if uid == PMW:
        budget(len(args[0]) <= 300); return ref_pmw(*args)
    if uid == LSS:
        budget(len(args[0]) <= 12); return ref_lss(*args)
    if uid == FWP:
        budget(len(args[0]) <= 2000); return ref_fwp(*args)
    if uid == FAW:
        budget(sum(map(len, args[0])) <= 5000); return ref_faw(*args)
    if uid == MOV1:
        budget(len(args[0]) <= 300); return ref_mov1(*args)
    calls = trace(uid, args)
    budget(len(calls) <= 600)
    if uid == F2D: return ref_f2d(args[1][0][0], calls)
    if uid in (FDS1, FDS2):
        budget(len(args[1][0][1]) <= 300); return ref_fds(*args[1][0], calls)
    return ref_mov2(args[1][0][0], calls)
