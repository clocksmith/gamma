"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (nested list scans,
repeated full rescans, point-by-point enumeration, explicit swaps, fixed-point iteration, exact
fractions, recursive string building, linear plane scans, plain recency lists, quadratic chain
searches, Cartesian products, key-by-key coverage counts, subset enumeration, pair enumeration,
Bellman-Ford relaxation, full (cell, fuel) state search, dense matrices and per-index sums) and
refuse inputs above a small budget.
"""
from fractions import Fraction
from itertools import product
from math import isqrt
import re

H = 'hack2hire:'
RCF1 = H + '69557daa4a0202df9569e982'
RCF2 = H + '69557dad4a0202df9569e983'
RCP = H + '684dee4b5e4cf21833c0611f'
RMV = H + '69a32b466e73e4abccc9bf13'
RPS = H + '6801c3b66cd5d6c88778f20c'
RNC = H + '69cae7e2ff3ebde766ceda54'
SWH = H + '68aebce1c8631a6568126eb4'
SOP = H + '69752cb217272b5c868d5e84'
SHS = H + '678879df402dc47b67a14946'
SSR1 = H + '6a4809cfca956256d786d255'
SSR2 = H + '6a480ba0ca956256d786d277'
SSR3 = H + '6a480bbbca956256d786d279'
SVA = H + '699bb05f6e73e4abccc9a9e4'
SHR = H + '69a3c6546e73e4abccc9c150'
SUP = H + '6a32d45b65569fa70cc7eb97'
SRC1 = H + '6976850c5ed12b33b05f0f0f'
SRC2 = H + '697690985ed12b33b05f0f2c'
SRC3 = H + '697692bb5ed12b33b05f0f34'
SPG = H + '68dc5856dd5418be11109afb'
SMO = H + '690d00010a0bc710235894c4'
SAE = H + '67db949600e020b60078a44d'

IDS = (RCF1, RCF2, RCP, RMV, RPS, RNC, SWH, SOP, SHS, SSR1, SSR2, SSR3, SVA, SHR, SUP, SRC1, SRC2, SRC3, SPG, SMO, SAE)
RCF = (RCF1, RCF2)
SSR = (SSR1, SSR2, SSR3)
SRC = (SRC1, SRC2, SRC3)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    SHS: ('SearchHistory', 1, {'add': 1, 'getTopK': 1}, ('add',)),
    SMO: ('SparseMatrix', 1, {'get': 2, 'set': 3, 'add': 1, 'multiply': 1}, ('set',)),
}


# ---------------------------------------------------------------- domain helpers
def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def sized(a, minimum, maximum):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')


def intlist(a, lo, hi, minimum=0, maximum=100000):
    sized(a, minimum, maximum)
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


def rcf_domain(c2f, f2c, idx):
    sized(c2f, 0, 20000); sized(f2c, 0, 20000); integer(idx, -10, 100000)
    relation = []
    for side, outer, other, letter in ((0, c2f, f2c, 'F'), (1, f2c, c2f, 'C')):
        pairs, total = [], 0
        for i, members in enumerate(outer):
            sized(members, 0, 100000); total += len(members)
            if total > 100000: raise ValueError('membership budget')
            seen = set()
            for m in members:
                text(m, letter + r'(0|[1-9][0-9]{0,5})', 7)
                j = int(m[1:])
                if j >= len(other) or j in seen: raise ValueError('member id')
                seen.add(j)
                pairs.append((i, j) if side == 0 else (j, i))
        relation.append(sorted(pairs))
    if relation[0] != relation[1]: raise ValueError('lists disagree')


def rcp_domain(intervals, idx):
    sized(intervals, 0, 100000); integer(idx, 0, 4 * 10**9)
    for iv in intervals:
        sized(iv, 2, 2); integer(iv[0], -10**9, 10**9); integer(iv[1], -10**9, 10**9)
        if iv[0] >= iv[1]: raise ValueError('empty interval')
    s = sorted(map(tuple, intervals))
    if any(a[1] > b[0] for a, b in zip(s, s[1:])): raise ValueError('overlap')


def acyclic_parents(n, parents_idx):
    indeg = [len(p) for p in parents_idx]; children = [[] for _ in range(n)]
    for i, ps in enumerate(parents_idx):
        for p in ps: children[p].append(i)
    stack = [i for i in range(n) if indeg[i] == 0]; done = 0
    while stack:
        i = stack.pop(); done += 1
        for c in children[i]:
            indeg[c] -= 1
            if indeg[c] == 0: stack.append(c)
    if done != n: raise ValueError('cycle')


def rps_domain(roles, parents, allowed, disallowed):
    sized(roles, 1, 2000)
    for r in roles: text(r, r'[a-z0-9]{1,8}', 8)
    if len(set(roles)) != len(roles): raise ValueError('duplicate role')
    pos = {r: i for i, r in enumerate(roles)}; n = len(roles)
    for lst in (parents, allowed, disallowed): sized(lst, n, n)
    pidx, edges, privs = [], 0, set()
    for i, ps in enumerate(parents):
        sized(ps, 0, 2000); edges += len(ps)
        for p in ps: text(p, r'[a-z0-9]{1,8}', 8)
        if len(set(ps)) != len(ps) or any(p not in pos or p == roles[i] for p in ps): raise ValueError('parent')
        pidx.append([pos[p] for p in ps])
    if edges > 10000: raise ValueError('edge budget')
    for lst in (allowed, disallowed):
        for ps in lst:
            sized(ps, 0, 10)
            for p in ps: text(p, r'[a-z_]{1,10}', 10)
            if len(set(ps)) != len(ps): raise ValueError('duplicate privilege')
            privs.update(ps)
    if len(privs) > 50: raise ValueError('privilege budget')
    acyclic_parents(n, pidx)


def rnc_domain(coordinates, distances):
    sized(coordinates, 1, 500); intlist(distances, 0, 10**7, 0, 500)
    for p in coordinates:
        sized(p, 2, 2); integer(p[0], 0, 1000); integer(p[1], 0, 1000)
    for a, b in zip(coordinates, coordinates[1:]):
        q = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
        if q == 0 or isqrt(q) ** 2 != q: raise ValueError('segment length')


def tree_domain(tree):
    sized(tree, 1, 100000); n = len(tree); parent = [0] * n; parent[0] = 1
    for node in tree:
        sized(node, 2, 2); kids = node[1]; sized(kids, 0, 100000)
        if kids:
            if node[0] != '': raise ValueError('grouping text')
        else: text(node[0], r'[a-z]{1,10}', 10)
        for k in kids:
            integer(k, 1, n - 1)
            if parent[k]: raise ValueError('two parents')
            parent[k] = 1
    if not all(parent): raise ValueError('orphan')
    seen, stack = 1, [0]
    while stack:
        for k in tree[stack.pop()][1]: seen += 1; stack.append(k)
    if seen != n: raise ValueError('cycle')


def sop_domain(planes, orders):
    sized(planes, 0, 20000); sized(orders, 0, 20000)
    for p in planes:
        sized(p, 2, 2); integer(p[0], 0, 10**9); integer(p[1], 0, 10**9)
    if len({p[0] for p in planes}) != len(planes): raise ValueError('departure')
    total = 0
    for o in orders:
        sized(o, 2, 2); integer(o[0], 0, 10**9); intlist(o[1], 1, 10**9, 1, 20); total += len(o[1])
    if total > 100000: raise ValueError('item budget')


def chains(segments):
    """(heads sorted, number of segments reachable from heads); a cycle leaves segments unreached."""
    by_start = {s[0]: s for s in segments}; ends = {s[1] for s in segments}
    heads = sorted(s[0] for s in segments if s[0] not in ends); seen = 0
    for h in heads:
        cur = by_start[h]
        while True:
            seen += 1
            cur = by_start.get(cur[1])
            if cur is None: break
    return heads, seen


def ssr_domain(uid, segments):
    sized(segments, 0 if uid == SSR3 else 1, 100000)
    for s in segments:
        sized(s, 3, 3); text(s[0], r'[a-z0-9]{1,8}', 8); text(s[1], r'[a-z0-9]{1,8}', 8); text(s[2], r'[a-z]{0,10}', 10)
    if len({s[0] for s in segments}) != len(segments) or len({s[1] for s in segments}) != len(segments): raise ValueError('ids')
    if uid == SSR2: return
    heads, seen = chains(segments)
    if seen != len(segments): raise ValueError('cycle')
    if uid == SSR1 and len(heads) != 1: raise ValueError('not one chain')


def sva_options(word_set):
    groups = {}
    for w in word_set: groups.setdefault(''.join(sorted(w)), set()).add(w)
    return groups


def sva_domain(word_set, sentences):
    sized(word_set, 0, 10000); sized(sentences, 0, 1000)
    for w in word_set: text(w, r'[a-z]{1,10}', 10)
    if len(set(word_set)) != len(word_set): raise ValueError('duplicate word')
    groups = sva_options(word_set); total = 0
    for s in sentences:
        text(s, r'[a-z]{1,10}( [a-z]{1,10}){0,19}', 300)
        count = 1
        for w in s.split(' '): count *= len(groups.get(''.join(sorted(w)), set()) | {w})
        if count > 1000: raise ValueError('variation budget')
        total += count
    if total > 50000: raise ValueError('variation budget')


SHARD = r'([a-z0-9]{1,8}):(0|[1-9][0-9]{0,9}):(0|[1-9][0-9]{0,9})'


def shr_domain(limit, shards):
    integer(limit, 1, 10); sized(shards, 0, 20000); ids = set()
    for s in shards:
        text(s, SHARD, 30)
        i, a, b = re.fullmatch(SHARD, s).groups()
        if not int(a) <= int(b) <= 10**9 or i in ids: raise ValueError('shard')
        ids.add(i)


def sup_domain(population, unit):
    intlist(population, 0, 10**9, 1, 100000)
    text(unit, r'[01]*', 100000)
    if len(unit) != len(population): raise ValueError('length')


ROUTE = r'([A-Z]{2,3}):([A-Z]{2,3}):([A-Za-z]{1,10}):([1-9][0-9]{0,6})'


def parse_routes(routes):
    return [(m[0], m[1], m[2], int(m[3])) for m in (re.fullmatch(ROUTE, r).groups() for r in routes)]


def src_domain(uid, routes, source, target):
    sized(routes, 1, 2000)
    for r in routes: text(r, ROUTE, 40)
    text(source, r'[A-Z]{2,3}', 3); text(target, r'[A-Z]{2,3}', 3)
    parsed = parse_routes(routes)
    if any(a == b or c > 10**6 for a, b, _, c in parsed): raise ValueError('route')
    if len({p[:3] for p in parsed}) != len(parsed): raise ValueError('duplicate route')
    if uid != SRC3 and source == target: raise ValueError('same endpoints')
    if uid == SRC2:
        out, inn = {}, {}
        for a, b, _, _ in parsed:
            out[(a, b)] = out.get((a, b), 0) + 1
        mids = {b for a, b, _, _ in parsed if a == source and b != target}
        count = out.get((source, target), 0) + sum(out.get((source, x), 0) * out.get((x, target), 0) for x in mids)
        if count > 20000: raise ValueError('path budget')


def spg_domain(grid, fuel):
    sized(grid, 1, 50); integer(fuel, 0, 100)
    for row in grid: text(row, r'[.#SDG]{1,50}', 50)
    if len({len(r) for r in grid}) != 1: raise ValueError('ragged grid')
    joined = ''.join(grid)
    if joined.count('S') != 1 or joined.count('D') != 1: raise ValueError('endpoints')


def matrix(m, rmin=1, rmax=60, cmin=1, cmax=60):
    sized(m, rmin, rmax)
    for row in m: intlist(row, -1000, 1000, cmin, cmax)
    if len({len(r) for r in m}) != 1: raise ValueError('ragged matrix')
    return len(m), len(m[0])


def smo_domain(args):
    calls = trace(SMO, args, 301)
    rows, cols = matrix(args[1][0][0])
    for op, row in calls:
        if op in ('get', 'set'):
            integer(row[0], 0, rows - 1); integer(row[1], 0, cols - 1)
            if op == 'set': integer(row[2], -1000, 1000)
        elif op == 'add':
            if matrix(row[0]) != (rows, cols): raise ValueError('add shape')
        elif matrix(row[0])[0] != cols: raise ValueError('multiply shape')


def shs_domain(args):
    calls = trace(SHS, args, 100001)
    integer(args[1][0][0], 1, 100000)
    for op, row in calls:
        if op == 'add': text(row[0], r'[a-z]{1,10}', 10)
        else: integer(row[0], 0, 100)


def validate_domain(uid, args):
    if uid in RCF:
        envelope(args, 3); rcf_domain(*args)
    elif uid == RCP:
        envelope(args, 2); rcp_domain(*args)
    elif uid == RMV:
        envelope(args, 1); sized(args[0], 0, 100000)
        for w in args[0]: text(w, r'[A-Za-z]{1,20}', 20)
    elif uid == RPS:
        envelope(args, 4); rps_domain(*args)
    elif uid == RNC:
        envelope(args, 2); rnc_domain(*args)
    elif uid == SWH:
        envelope(args, 2); tree_domain(args[0]); tree_domain(args[1])
    elif uid == SOP:
        envelope(args, 2); sop_domain(*args)
    elif uid == SHS: shs_domain(args)
    elif uid in SSR:
        envelope(args, 1); ssr_domain(uid, args[0])
    elif uid == SVA:
        envelope(args, 2); sva_domain(*args)
    elif uid == SHR:
        envelope(args, 2); shr_domain(*args)
    elif uid == SUP:
        envelope(args, 2); sup_domain(*args)
    elif uid in SRC:
        envelope(args, 3); src_domain(uid, *args)
    elif uid == SPG:
        envelope(args, 2); spg_domain(*args)
    elif uid == SMO: smo_domain(args)
    elif uid == SAE:
        envelope(args, 1); intlist(args[0], 1, 10**9, 1, 100000)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_rcf1(c2f, f2c, idx):
    if not 0 <= idx < len(c2f): return []
    mine = c2f[idx]
    return ['C%d' % i for i in range(len(c2f)) if i != idx and any(f in c2f[i] for f in mine)]


def ref_rcf2(c2f, f2c, idx):
    if not 0 <= idx < len(c2f): return []
    reached = [idx]; changed = True
    while changed:
        changed = False
        for i in range(len(c2f)):
            if i not in reached and any(f in c2f[j] for j in reached for f in c2f[i]):
                reached.append(i); changed = True
    return ['C%d' % i for i in range(len(c2f)) if i in reached and i != idx]


def ref_rcp(intervals, idx):
    out, count = [], 0
    for s, e in intervals:
        hit = None
        for p in range(s, e):
            if count == idx: hit = p
            count += 1
        if hit is None: out.append([s, e])
        else:
            if s < hit: out.append([s, hit])
            if hit + 1 < e: out.append([hit + 1, e])
    return out


def ref_rmv(words):
    out = []
    for w in words:
        if len(w) >= 2 and w[0].lower() in 'aeiou' and w[-1].lower() in 'aeiou':
            chars = list(w); i, j = 1, len(w) - 2
            while i < j: chars[i], chars[j] = chars[j], chars[i]; i += 1; j -= 1
            out.append(''.join(chars))
        else: out.append(w)
    return out


def ref_rps(roles, parents, allowed, disallowed):
    pos = {r: i for i, r in enumerate(roles)}; final = [set() for _ in roles]
    for _ in range(len(roles) + 2):
        changed = False
        for i in range(len(roles)):
            new = set(allowed[i])
            for p in parents[i]: new |= final[pos[p]]
            new -= set(disallowed[i])
            if new != final[i]: final[i] = new; changed = True
        if not changed: return [sorted(s) for s in final]
    raise AssertionError('no fixed point')


def ref_rnc(coordinates, distances):
    out = []
    for d in distances:
        acc, pos = 0, None
        for a, b in zip(coordinates, coordinates[1:]):
            length = isqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
            if d <= acc + length:
                t = Fraction(d - acc, length); pos = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])); break
            acc += length
        if pos is None: pos = (Fraction(coordinates[-1][0]), Fraction(coordinates[-1][1]))
        dist = [(pos[0] - w[0]) ** 2 + (pos[1] - w[1]) ** 2 for w in coordinates]
        out.append(dist.index(min(dist)))
    return out


def ref_swh(t1, t2):
    def word(tree, k):
        node = tree[k]
        return node[0] if not node[1] else ''.join(word(tree, c) for c in node[1])
    return word(t1, 0) == word(t2, 0)


def ref_sop(planes, orders):
    fleet = sorted([list(p) for p in planes]); out = []
    for t, items in orders:
        backup = [p[1] for p in fleet]; chosen = []
        for size in items:
            for p in fleet:
                if p[0] > t and p[1] >= size: p[1] -= size; chosen.append(p[0]); break
            else:
                for p, c in zip(fleet, backup): p[1] = c
                chosen = None; break
        out.append(chosen if chosen is not None else [])
    return out


def ref_shs(capacity, calls):
    recent, out = [], [None]  # oldest first
    for op, row in calls:
        if op == 'add':
            if row[0] in recent: recent.remove(row[0])
            recent.append(row[0])
            if len(recent) > capacity: recent.pop(0)
            out.append(None)
        else: out.append(list(reversed(recent))[:row[0]])
    return out


def ref_walk(segments, head):
    parts, cur, steps = [], head, 0
    while True:
        nxt = [s for s in segments if s[0] == cur]
        if not nxt: return ''.join(parts), steps
        parts.append(nxt[0][2]); cur = nxt[0][1]; steps += 1
        if steps > len(segments): return None, steps


def ref_ssr(uid, segments):
    heads = sorted(s[0] for s in segments if all(t[1] != s[0] for t in segments))
    if uid == SSR3: return [ref_walk(segments, h)[0] for h in heads]
    if len(heads) != 1: return ''
    word, steps = ref_walk(segments, heads[0])
    return word if steps == len(segments) else ''


def ref_sva(word_set, sentences):
    out = []
    for s in sentences:
        options = [[w] + [x for x in word_set if x != w and sorted(x) == sorted(w)] for w in s.split(' ')]
        out.append(sorted({' '.join(c) for c in product(*options)}))
    return out


def ref_shr(limit, shards):
    parsed = sorted(((int(a), int(b), i) for i, a, b in (re.fullmatch(SHARD, s).groups() for s in shards)))
    kept = []
    for a, b, i in parsed:
        start = a
        for y in range(b, a - 1, -1):
            if sum(1 for s, e, _ in kept if s <= y <= e) >= limit: start = y + 1; break
        if start <= b: kept.append([start, b, i])
    kept.sort(key=lambda k: (k[0], k[1], k[2])); reach = None
    for k in kept:
        if reach is not None and k[0] > reach + 1: k[0] = reach + 1
        reach = k[1] if reach is None else max(reach, k[1])
    kept.sort(key=lambda k: (k[0], k[1], k[2]))
    return ['%s:%d:%d' % (i, s, e) for s, e, i in kept]


def ref_sup(population, unit):
    movable = [i for i in range(1, len(unit)) if unit[i] == '1']
    fixed = [i for i in range(len(unit)) if unit[i] == '1' and i == 0]
    best = 0
    for mask in range(1 << len(movable)):
        cities = set(fixed) | {i - 1 if mask >> k & 1 else i for k, i in enumerate(movable)}
        best = max(best, sum(population[c] for c in cities))
    return best


def ref_src(uid, routes, source, target):
    parsed = parse_routes(routes)
    if uid == SRC1:
        found = [(c, m) for a, b, m, c in parsed if a == source and b == target]
        ordered = []
        while found:  # selection by explicit pair comparison
            best = min(found); found.remove(best); ordered.append([best[1], best[0]])
        return ordered
    if uid == SRC2:
        paths = [(c, '%s:%s:%s' % (a, m, b)) for a, b, m, c in parsed if a == source and b == target]
        for a1, b1, m1, c1 in parsed:
            for a2, b2, m2, c2 in parsed:
                if a1 == source and b2 == target and b1 == a2 and b1 not in (source, target):
                    paths.append((c1 + c2, '%s:%s:%s:%s:%s' % (a1, m1, b1, m2, b2)))
        return [[p, c] for c, p in sorted(paths)]
    nodes = {source, target} | {p[0] for p in parsed} | {p[1] for p in parsed}
    dist = {source: 0}
    for _ in range(len(nodes)):
        for a, b, _m, c in parsed:
            if a in dist and (b not in dist or dist[a] + c < dist[b]): dist[b] = dist[a] + c
    return dist.get(target, -1)


def ref_spg(grid, fuel):
    m, n = len(grid), len(grid[0])
    start = next((r, c) for r in range(m) for c in range(n) if grid[r][c] == 'S')
    frontier, seen, steps = [(start[0], start[1], fuel)], {(start[0], start[1], fuel)}, 0
    while frontier:
        nxt = []
        for r, c, f in frontier:
            if grid[r][c] == 'D': return steps
            if f == 0: continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < m and 0 <= cc < n and grid[rr][cc] != '#':
                    state = (rr, cc, fuel if grid[rr][cc] == 'G' else f - 1)
                    if state not in seen: seen.add(state); nxt.append(state)
        frontier, steps = nxt, steps + 1
    return -1


def triples(dense):
    return [[i, j, v] for i, row in enumerate(dense) for j, v in enumerate(row) if v != 0]


def ref_smo(args, calls):
    a = [list(r) for r in args[1][0][0]]; out = [None]
    for op, row in calls:
        if op == 'get': out.append(a[row[0]][row[1]])
        elif op == 'set': a[row[0]][row[1]] = row[2]; out.append(None)
        elif op == 'add': out.append(triples([[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, row[0])]))
        else:
            b = row[0]
            out.append(triples([[sum(a[i][t] * b[t][j] for t in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]))
    return out


def ref_sae(nums):
    for i in range(len(nums) - 1):
        if sum(nums[:i + 1]) == sum(nums[i + 1:]): return i
    return -1


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in RCF:
        budget(len(args[0]) <= 60 and sum(map(len, args[0])) <= 400)
        return (ref_rcf1 if uid == RCF1 else ref_rcf2)(*args)
    if uid == RCP:
        budget(sum(e - s for s, e in args[0]) <= 5000); return ref_rcp(*args)
    if uid == RMV:
        budget(len(args[0]) <= 400); return ref_rmv(args[0])
    if uid == RPS:
        budget(len(args[0]) <= 40); return ref_rps(*args)
    if uid == RNC:
        budget(len(args[0]) * len(args[1]) <= 4000); return ref_rnc(*args)
    if uid == SWH:
        budget(len(args[0]) + len(args[1]) <= 600); return ref_swh(*args)
    if uid == SOP:
        budget(len(args[0]) * (1 + sum(len(o[1]) for o in args[1])) <= 20000); return ref_sop(*args)
    if uid in SSR:
        budget(len(args[0]) <= 200); return ref_ssr(uid, args[0])
    if uid == SVA:
        budget(len(args[0]) <= 60); return ref_sva(*args)
    if uid == SHR:
        budget(len(args[1]) <= 30 and all(int(s.split(':')[2]) <= 300 for s in args[1])); return ref_shr(*args)
    if uid == SUP:
        budget(args[1].count('1') <= 13); return ref_sup(*args)
    if uid in SRC:
        budget(len(args[0]) <= 60); return ref_src(uid, *args)
    if uid == SPG:
        budget(len(args[0]) * len(args[0][0]) * (args[1] + 1) <= 30000); return ref_spg(*args)
    if uid == SAE:
        budget(len(args[0]) <= 300); return ref_sae(args[0])
    calls = trace(uid, args, 100001)
    budget(len(calls) <= 600)
    if uid == SHS: return ref_shs(args[1][0][0], calls)
    budget(len(calls) <= 40); return ref_smo(args, calls)
