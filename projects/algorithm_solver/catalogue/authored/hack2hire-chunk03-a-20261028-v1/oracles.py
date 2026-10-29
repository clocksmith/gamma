"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (literal replay,
exhaustive enumeration, quadratic scans, per-query rescans, exact Fractions).
"""
from fractions import Fraction
from itertools import product
import math
import re

H = 'hack2hire:'
ITOA = H + '69c87bbe21f6ab4226966de6'
TOKEN = H + '69e2411e95e80ae213e5d633'
ILV = H + '678d6982fa7ce9616e190fb3'
JUMP = H + '69e931b2fbaf3da641828684'
KTH = H + '6a04f7473141bbc31efdd6f1'
TEAM = H + '6a73bf2fd713d873ca7a77c6'
LEAGUE = H + '6a4fb090665efda9311f5615'
TREE1 = H + '69bc554c1cbff60a929be332'
TREE2 = H + '69bc55661cbff60a929be333'
LERP = H + '69bef92321f6ab4226963c6b'
FILLPTS = H + '696c36906b040fa4d120bc68'
SHIFT = H + '6a19022ac81f779dc6a231ab'
TILES = H + '67a96e45017965d66059a736'
LEAF = H + '6769dd5b11bbd512d60ce762'
DEPLOY = H + '6a949604cddc54478ddf5f33'
CALLS = H + '696336dcf731aa3969ef52a7'
STAB = H + '67a574f4b571d6ff0a4bd23a'

IDS = (ITOA, TOKEN, ILV, JUMP, KTH, TEAM, LEAGUE, TREE1, TREE2, LERP, FILLPTS, SHIFT, TILES, LEAF, DEPLOY, CALLS, STAB)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    ILV: ('InterleaveIterator', 2, {'hasNext': 0, 'next': 0}, ()),
}
DAY_MS = 86400000
MAX_TREE_DEPTH = 99  # node levels; each level adds a dict and a list, so JSON nesting stays below 200


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


def walk_tree(root, max_nodes=100000):
    """N-ary tree of {'id', 'children'} nodes; returns {id: [child ids]} and the root id."""
    children, stack = {}, [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_TREE_DEPTH: raise ValueError('tree depth')
        if type(node) is not dict or set(node) != {'id', 'children'} or type(node['children']) is not list:
            raise ValueError('node shape')
        integer(node['id'], 0, 10**6)
        if node['id'] in children: raise ValueError('duplicate id')
        children[node['id']] = [c['id'] if type(c) is dict and 'id' in c else None for c in node['children']]
        if len(children) > max_nodes: raise ValueError('tree size')
        for c in node['children']: stack.append((c, depth + 1))
    return children, root['id']


def parse_level_order(values):
    """LeetCode level-order list -> (vals, left, right) index arrays; strict consumption."""
    if type(values) is not list or not 1 <= len(values) <= 200001 or values[0] is None: raise ValueError('tree list')
    vals, left, right = [], [], []
    for v in values:
        if v is not None: integer(v, -10**9, 10**9)
    vals.append(values[0]); left.append(-1); right.append(-1)
    queue, qi, i = [0], 0, 1
    while i < len(values):
        if qi >= len(queue): raise ValueError('dangling entries')
        parent = queue[qi]; qi += 1
        for side in (left, right):
            if i < len(values):
                if values[i] is not None:
                    vals.append(values[i]); left.append(-1); right.append(-1)
                    side[parent] = len(vals) - 1; queue.append(len(vals) - 1)
                i += 1
    if len(vals) > 100000: raise ValueError('tree size')
    return vals, left, right


def validate_domain(uid, args):
    if uid == ITOA:
        envelope(args, 1); integer(args[0], -2**31, 2**31 - 1)
    elif uid == TOKEN:
        envelope(args, 2); text_, alpha = args
        text(text_, r'[a-z]*', 100000)
        if type(alpha) is not list or not 1 <= len(alpha) <= 5000: raise ValueError('alphabet size')
        for t in alpha: text(t, r'[a-z]{1,30}', 30)
        if len(set(alpha)) != len(alpha): raise ValueError('duplicate token')
        k = 0
        while k < len(alpha) and len(alpha[k]) == 1: k += 1
        if k == 0 or any(len(t) == 1 for t in alpha[k:]): raise ValueError('single-character prefix')
        if not set(text_) <= set(alpha[:k]): raise ValueError('text character without a token')
    elif uid == ILV:
        ops, rows = trace(uid, args, 100001)
        arrays, cycle = rows[0]
        if type(arrays) is not list or len(arrays) > 10000 or type(cycle) is not bool: raise ValueError('constructor')
        total = 0
        for a in arrays:
            array(a, -10**9, 10**9, 0, 100000); total += len(a)
        if total > 100000: raise ValueError('total elements')
    elif uid == JUMP:
        envelope(args, 1); array(args[0], -10**4, 10**4, 1, 5000)
    elif uid == KTH:
        envelope(args, 2); arr, k = args
        array(arr, 1, 100000, 1, 100000)
        if sorted(arr) != list(range(1, len(arr) + 1)): raise ValueError('not a permutation')
        integer(k, 1, len(arr))
    elif uid == TEAM:
        envelope(args, 1); array(args[0], 1, 10**9, 1, 100000)
    elif uid == LEAGUE:
        envelope(args, 4); leagues, caps, silver, target = args
        if type(leagues) is not list or not 2 <= len(leagues) <= 100000: raise ValueError('club count')
        for name in leagues: text(name, r'[A-Za-z][A-Za-z0-9 ]{0,29}', 30)
        array(caps, 1, 100000, len(leagues), len(leagues)); array(silver, 0, 100, len(leagues), len(leagues))
        text(target, r'[A-Za-z][A-Za-z0-9 ]{0,29}', 30)
        if not 2 <= leagues.count(target) <= 10000: raise ValueError('target league size')
    elif uid in (TREE1, TREE2):
        envelope(args, 2)
        children, root = walk_tree(args[0])
        if uid == TREE1:
            dels = args[1]
            array(dels, 0, 10**6, 0, 100000)
            if len(set(dels)) != len(dels) or root in dels or not set(dels) <= set(children): raise ValueError('deleted ids')
        else:
            integer(args[1], 1, 100)
    elif uid == LERP:
        envelope(args, 2); points, queries = args
        if type(points) is not list or not 1 <= len(points) <= 100000: raise ValueError('points size')
        for p in points:
            if type(p) is not list or len(p) != 2: raise ValueError('point shape')
            integer(p[0], -10**6, 10**6); integer(p[1], -10**6, 10**6)
        array(queries, -10**6, 10**6, 0, 100000)
    elif uid == FILLPTS:
        envelope(args, 2); interval, points = args
        integer(interval, 1, 10**6)
        if type(points) is not list or not 1 <= len(points) <= 100000: raise ValueError('points size')
        out = len(points)
        for i, p in enumerate(points):
            if type(p) is not list or len(p) != 2: raise ValueError('point shape')
            integer(p[0], -10**6, 10**6); integer(p[1], -10**6, 10**6)
            if i:
                gap = p[0] - points[i - 1][0]
                if gap <= 0: raise ValueError('x not strictly increasing')
                if gap > interval:
                    if gap % interval: raise ValueError('gap not divisible by interval')
                    out += gap // interval - 1
        if out > 100000: raise ValueError('output size')
    elif uid == SHIFT:
        envelope(args, 1); array(args[0], -10**9, 10**9, 1, 100000)
    elif uid == TILES:
        envelope(args, 2); integer(args[0], 0, 10**9); integer(args[1], 0, 10**9)
    elif uid == LEAF:
        envelope(args, 1); parse_level_order(args[0])
    elif uid == DEPLOY:
        envelope(args, 1); array(args[0], 1, 10**9, 3, 100000)
    elif uid == CALLS:
        envelope(args, 1); calls = args[0]
        if type(calls) is not list or len(calls) > 100000: raise ValueError('call count')
        ids = set()
        for c in calls:
            if type(c) is not list or len(c) != 4: raise ValueError('call shape')
            integer(c[0], 1, 10**6); text(c[1], r'[a-z0-9]{1,12}', 12); integer(c[2], 0, 10**12)
            integer(c[3], c[2] + 1, c[2] + 3 * DAY_MS)
            if c[1] in ids: raise ValueError('duplicate call id')
            ids.add(c[1])
    elif uid == STAB:
        envelope(args, 2); avail, rel = args
        array(avail, 0, 10**6, 1, 100000); array(rel, 0, 10**4, len(avail), len(avail))
    else:
        raise ValueError('unknown uid')


# ---------------------------------------------------------------- references

def ref_itoa(v):
    return str(v)


def ref_token(text_, alpha):
    k = 0
    while k < len(alpha) and len(alpha[k]) == 1: k += 1
    seq = [alpha.index(c) for c in text_]
    for j in range(k, len(alpha)):
        out, i = [], 0
        while i < len(seq):
            if i + 1 < len(seq) and alpha[seq[i]] + alpha[seq[i + 1]] == alpha[j]:
                out.append(j); i += 2
            else:
                out.append(seq[i]); i += 1
        seq = out
    return seq


def ref_ilv(ops, rows):
    arrays, cycle = rows[0]
    one_pass = []
    for r in range(max((len(a) for a in arrays), default=0)):
        one_pass += [a[r] for a in arrays if len(a) > r]
    out, produced = [None], 0
    for op in ops[1:]:
        has = produced < len(one_pass) or (cycle and len(one_pass) > 0)
        if op == 'hasNext': out.append(has)
        elif not has: out.append(None)
        else:
            out.append(one_pass[produced % len(one_pass)]); produced += 1
    return out


def is_prime(p):
    return p >= 2 and all(p % d for d in range(2, math.isqrt(p) + 1))


def ref_jump(nums):
    n = len(nums); best = [None] * n; best[0] = nums[0]
    for i in range(1, n):
        cands = [best[j] for j in range(i) if i - j == 1 or (is_prime(i - j) and (i - j) % 10 == 3)]
        best[i] = nums[i] + max(cands)
    return best[-1]


def ref_kth(arr, k):
    return [sorted(arr[:i], reverse=True)[k - 1] for i in range(k, len(arr) + 1)]


def ref_team(skills):
    s = sorted(skills); best = run = 0; prev = None
    for v in s:
        run = run + 1 if prev is not None and v - prev <= 1 else 1
        best = max(best, run); prev = v
    return best


def ref_league(leagues, caps, silver, target):
    clubs = [i for i, name in enumerate(leagues) if name == target]
    total = matches = 0
    for h in clubs:
        for a in clubs:
            if h != a:
                total += caps[h] * (silver[h] + silver[a]); matches += 1
    cents = math.floor(Fraction(total * 100, matches) + Fraction(1, 2))
    return [total, '%d.%02d' % (cents // 100, cents % 100)]


def _rebuild(node, deleted):
    kids = [t for c in node['children'] for t in _rebuild(c, deleted)]
    return kids if node['id'] in deleted else [kids]


def _height(forest_node):
    return 1 + max((_height(c) for c in forest_node), default=0)


def ref_tree_height(root, deleted):
    return _height(_rebuild(root, set(deleted))[0])


def ref_tree_min_deletions(root, max_height):
    children, rid = walk_tree(root)
    others = [i for i in children if i != rid]
    for size in range(len(others) + 1):
        for chosen in _combinations(others, size):
            if ref_tree_height(root, chosen) <= max_height: return size
    raise AssertionError('unreachable: deleting every non-root node gives height 1')


def _combinations(items, size):
    if size == 0: yield []; return
    for i in range(len(items) - size + 1):
        for rest in _combinations(items[i + 1:], size - 1): yield [items[i]] + rest


def frac_text(q):
    q = Fraction(q)
    return str(q.numerator) if q.denominator == 1 else '%d/%d' % (q.numerator, q.denominator)


def ref_lerp(points, queries):
    out = []
    for q in queries:
        at = [y for x, y in points if x == q]
        if at: out.append(frac_text(max(at))); continue
        lower = [x for x, _ in points if x < q]; upper = [x for x, _ in points if x > q]
        if not lower:
            x2 = min(upper); out.append(frac_text(min(y for x, y in points if x == x2))); continue
        if not upper:
            x1 = max(lower); out.append(frac_text(max(y for x, y in points if x == x1))); continue
        x1, x2 = max(lower), min(upper)
        y1 = max(y for x, y in points if x == x1); y2 = min(y for x, y in points if x == x2)
        out.append(frac_text(Fraction(y1) + Fraction(y2 - y1, x2 - x1) * (q - x1)))
    return out


def ref_fill(interval, points):
    out = [[points[0][0], frac_text(points[0][1])]]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x2 - x1 > interval:
            for x in range(x1 + interval, x2, interval):
                out.append([x, frac_text(Fraction(y1) + Fraction((y2 - y1) * (x - x1), x2 - x1))])
        out.append([x2, frac_text(y2)])
    return out


def ref_shift(nums):
    n = len(nums)
    for t in range(n):
        s = nums[n - t:] + nums[:n - t]
        if all(s[i] >= s[i + 1] for i in range(n - 1)): return t
    return -1


def ref_tiles(m, n):
    s = math.isqrt(m + 4 * n)
    while s > 0:
        if s * s - 4 * min(n, (s // 2) ** 2) <= m: return s
        s -= 1
    return 0


def ref_leaf(values):
    vals, left, right = parse_level_order(values)
    parent = [-1] * len(vals)
    for v in range(len(vals)):
        for c in (left[v], right[v]):
            if c >= 0: parent[c] = v
    leaves = [v for v in range(len(vals)) if left[v] < 0 and right[v] < 0]
    if len(leaves) == 1: return vals[leaves[0]]

    def chain(v):
        out = []
        while v >= 0: out.append(v); v = parent[v]
        return out
    best = None
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            ca, cb = chain(a), chain(b); sb = set(cb)
            lca = next(v for v in ca if v in sb)
            nodes = ca[:ca.index(lca) + 1] + cb[:cb.index(lca)]
            s = sum(vals[v] for v in nodes)
            best = s if best is None or s > best else best
    return best


def ref_deploy(d):
    best = None
    for labels in product(range(3), repeat=len(d)):
        groups = [[x for x, g in zip(d, labels) if g == k] for k in range(3)]
        if not all(groups): continue
        s = abs(max(groups[0]) - min(groups[1])) + abs(max(groups[1]) - min(groups[2]))
        best = s if best is None or s > best else best
    return best


def ref_calls(calls):
    out = []
    for cid in sorted({c[0] for c in calls}):
        mine = [c for c in calls if c[0] == cid]
        days = sorted({d for c in mine for d in range(c[2] // DAY_MS, (c[3] - 1) // DAY_MS + 1)})
        for day in days:
            lo, hi = day * DAY_MS, (day + 1) * DAY_MS
            instants = [lo] + [c[2] for c in mine if lo <= c[2] < hi]
            peak = max(sum(1 for c in mine if c[2] <= t < c[3]) for t in instants)
            if peak: out.append([cid, day, peak])
    return out


def ref_stab(avail, rel):
    n = len(avail)
    if n <= 12:
        best = None
        for mask in range(1, 1 << n):
            chosen = [i for i in range(n) if mask >> i & 1]
            v = min(avail[i] for i in chosen) * sum(rel[i] for i in chosen)
            best = v if best is None or v > best else best
        return best
    return max(a * sum(rel[i] for i in range(n) if avail[i] >= a) for a in set(avail))


BUDGET = {TOKEN: 3000000, JUMP: 400, KTH: 400, LEAGUE: 400, TREE2: 13, LERP: 200000, SHIFT: 400, LEAF: 80,
          DEPLOY: 8, CALLS: 300, STAB: 400}


def reference(uid, args):
    validate_domain(uid, args)
    if uid == ITOA: return ref_itoa(args[0])
    if uid == TOKEN:
        if len(args[0]) * len(args[1]) > BUDGET[TOKEN]: raise ValueError('reference budget')
        return ref_token(*args)
    if uid == ILV: return ref_ilv(*args)
    size = {JUMP: lambda: len(args[0]), KTH: lambda: len(args[0]), LEAGUE: lambda: args[0].count(args[3]),
            TREE2: lambda: len(walk_tree(args[0])[0]), LERP: lambda: len(args[0]) * max(1, len(args[1])),
            SHIFT: lambda: len(args[0]), LEAF: lambda: sum(v is not None for v in args[0]), DEPLOY: lambda: len(args[0]),
            CALLS: lambda: len(args[0]), STAB: lambda: len(args[0])}
    if uid in size and size[uid]() > BUDGET[uid]: raise ValueError('reference budget')
    if uid == JUMP: return ref_jump(args[0])
    if uid == KTH: return ref_kth(*args)
    if uid == TEAM: return ref_team(args[0])
    if uid == LEAGUE: return ref_league(*args)
    if uid == TREE1: return ref_tree_height(*args)
    if uid == TREE2: return ref_tree_min_deletions(*args)
    if uid == LERP: return ref_lerp(*args)
    if uid == FILLPTS: return ref_fill(*args)
    if uid == SHIFT: return ref_shift(args[0])
    if uid == TILES: return ref_tiles(*args)
    if uid == LEAF: return ref_leaf(args[0])
    if uid == DEPLOY: return ref_deploy(args[0])
    if uid == CALLS: return ref_calls(args[0])
    return ref_stab(*args)
