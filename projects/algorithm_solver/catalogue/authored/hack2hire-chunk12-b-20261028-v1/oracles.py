"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (all-pairs scans,
linear parameter searches, sorted saving lists, linear lookups, count-vector enumeration, union-find,
flip-subset enumeration, per-start overlap counts, recursive path enumeration, step-by-step
simulation, per-start sets, bitmask breadth-first search, day-by-day leaf removal, repeated string
reduction, recursive descent and integer increments) and refuse inputs above a small budget.
"""
from collections import deque
from itertools import combinations
import re

H = 'hack2hire:'
MDA = H + '688a81d832b6b01c49be543b'
MVS = H + '686839500ed1b6fe83428ac8'
MCV = H + '686833a90ed1b6fe83428ac3'
MSD = H + '68c327671f64f4312b0a3e1e'
MCC = H + '69646297b481f959f9e384ee'
MDP = H + '688cdf12b6c09ad9a4fcc2cc'
MFG = H + '67a93084ea201244f8fae263'
MIK = H + '699e789b6e73e4abccc9b2c8'
MMT = H + '6a04d7ad3141bbc31efdd5c2'
MRL = H + '6910bee571ea59cda5a81a94'
MSB = H + '67d88d261989183df5382503'
MSK = H + '69e93d83fbaf3da6418286c9'
MSE = H + '68f842c4d7ff180d0ab950eb'
NTL = H + '68a615443a368733bb104245'
NSB1 = H + '69d1807e17b72775cc49c008'
NSB2 = H + '69d1828717b72775cc49c028'
NGP = H + '67883eb4e20f8f324213c2a2'

IDS = (MDA, MVS, MCV, MSD, MCC, MDP, MFG, MIK, MMT, MRL, MSB, MSK, MSE, NTL, NSB1, NSB2, NGP)

# uid -> (class name, constructor arity, {method: arity}, void methods); every inferred interface here is a function
CLASSES = {}


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


def nondecreasing(a):
    if any(a[i] > a[i + 1] for i in range(len(a) - 1)): raise ValueError('not sorted')


NAME = r'[A-Za-z0-9 ]{1,20}'


def msd_domain(products, shopping):
    if type(products) is not list or len(products) > 100000: raise ValueError('products size')
    seen = set()
    for p in products:
        if type(p) is not list or len(p) != 2: raise ValueError('product pair')
        text(p[0], NAME, 20); text(p[1], NAME, 20)
        if p[0] in seen: raise ValueError('duplicate product')
        seen.add(p[0])
    if type(shopping) is not list or len(shopping) > 100000: raise ValueError('list size')
    for s in shopping: text(s, NAME, 20)


def mfg_domain(grid):
    if type(grid) is not list or not grid: raise ValueError('grid rows')
    for row in grid:
        if type(row) is not str: raise ValueError('grid row type')
    m = len(grid[0])
    if m == 0 or any(len(r) != m for r in grid) or len(grid) * m > 250000: raise ValueError('grid shape')
    for row in grid: text(row, r'[BW]+', m)


def mmt_domain(tasks):
    if type(tasks) is not list or len(tasks) > 100000: raise ValueError('tasks size')
    for t in tasks:
        if type(t) is not list or len(t) != 2: raise ValueError('task pair')
        integer(t[0], 0, 10**9 - 1); integer(t[1], t[0] + 1, 10**9)


def binary_level_order(a):
    """Decode a LeetCode binary-tree level-order list into (values, left, right); raise on a non-canonical list."""
    if type(a) is not list or len(a) > 200001: raise ValueError('tree list')
    for v in a:
        if v is not None: integer(v, -10**9, 10**9)
    if not a: return [], [], []
    if a[0] is None or a[-1] is None: raise ValueError('root or trailing null')
    values, left, right = [a[0]], [-1], [-1]
    queue, head, i = [0], 0, 1
    while i < len(a):
        if head >= len(queue): raise ValueError('entries without a parent')
        node = queue[head]; head += 1
        for side in (left, right):
            if i < len(a):
                if a[i] is not None:
                    values.append(a[i]); left.append(-1); right.append(-1); side[node] = len(values) - 1; queue.append(len(values) - 1)
                i += 1
    if len(values) > 100000: raise ValueError('node count')
    return values, left, right


def nary_level_order(a):
    """Decode a canonical LeetCode N-ary level-order list into (values, children); raise otherwise."""
    if type(a) is not list or len(a) > 200002: raise ValueError('tree list')
    for v in a:
        if v is not None: integer(v, -10**9, 10**9)
    if not a: return [], []
    if a[0] is None: raise ValueError('null root')
    values, children = [a[0]], [[]]
    head, i = 0, 2
    if len(a) > 1 and a[1] is not None: raise ValueError('missing separator after root')
    while i < len(a):
        if head >= len(values): raise ValueError('children without a parent')
        parent = head; head += 1
        while i < len(a) and a[i] is not None:
            values.append(a[i]); children.append([]); children[parent].append(len(values) - 1); i += 1
        i += 1
    if len(values) > 100000: raise ValueError('node count')
    # canonical form: re-serialise and compare (no trailing nulls, no surplus separators)
    out = [values[0], None]
    for node in range(len(values)):
        out.extend(values[c] for c in children[node]); out.append(None)
    while out and out[-1] is None: out.pop()
    if out != a: raise ValueError('non-canonical serialisation')
    return values, children


def nested_list_grammar(s):
    """Check s against list := '(' [item (',' item)*] ')', item := [a-z]+ | list, with depth <= 100."""
    text(s, r'[a-z,()]{2,100000}', 100000)
    if s[0] != '(': raise ValueError('must open with (')
    depth, prev = 0, ''
    allowed = {'(': set('abcdefghijklmnopqrstuvwxyz()'), 'a': set('abcdefghijklmnopqrstuvwxyz,)'), ',': set('abcdefghijklmnopqrstuvwxyz('), ')': set(',)')}
    for i, ch in enumerate(s):
        kind = 'a' if ch.isalpha() else ch
        if prev and ch not in allowed[prev]: raise ValueError('grammar')
        if depth == 0 and i > 0: raise ValueError('text after the outer list')
        if ch == '(':
            depth += 1
            if depth > 100: raise ValueError('nesting depth')
        elif ch == ')': depth -= 1
        prev = kind
    if depth != 0: raise ValueError('unbalanced')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == MDA:
        envelope(args, 2)
        for a in args: intlist(a, -10**9, 10**9, 1); nondecreasing(a)
    elif uid == MVS:
        envelope(args, 2); intlist(args[0], -10**9, 10**9, 1); integer(args[1], 0, 10**9)
    elif uid == MCV:
        envelope(args, 2); intlist(args[0], 0, 10**9); integer(args[1], 0, 100000)
    elif uid == MSD:
        envelope(args, 2); msd_domain(*args)
    elif uid == MCC:
        envelope(args, 2); intlist(args[0], 1, 10000, 1, 50); integer(args[1], 0, 10000)
        if len(set(args[0])) != len(args[0]): raise ValueError('repeated denomination')
    elif uid == MDP:
        envelope(args, 1); intlist(args[0], -10**9, 10**9, 1)
    elif uid == MFG:
        envelope(args, 1); mfg_domain(args[0])
    elif uid == MIK:
        envelope(args, 2); text(args[0], r'[ab]{1,100000}', 100000); integer(args[1], 0, len(args[0]))
    elif uid == MMT:
        envelope(args, 1); mmt_domain(args[0])
    elif uid == MRL:
        envelope(args, 1); binary_level_order(args[0])
    elif uid == MSB:
        envelope(args, 1); intlist(args[0], -10**9, 10**9, 1)
    elif uid == MSK:
        envelope(args, 2); intlist(args[0], 1, 10**9, 1); integer(args[1], 1, 100000)
    elif uid == MSE:
        envelope(args, 1); intlist(args[0], -10**9, 10**9)
    elif uid == NTL:
        envelope(args, 1); nary_level_order(args[0])
    elif uid == NSB1:
        envelope(args, 1); text(args[0], r'[a-z,()]{0,100000}', 100000)
    elif uid == NSB2:
        envelope(args, 1); nested_list_grammar(args[0])
    elif uid == NGP:
        envelope(args, 1); text(args[0], r'[1-9][0-9]{0,99999}', 100000)


# ---------------------------------------------------------------- references
def ref_mda(A, B):
    return list(min((abs(a - b), a, b) for a in A for b in B)[1:])


def ref_mvs(scores, k):
    positive = [s for s in scores if s > 0]
    if not positive: return 1
    for x in range(1, max(positive) + 1):
        if sum(-(-s // x) for s in positive) <= k: return x
    return -1


def ref_mcv(price, vouchers):
    savings = []
    for p in price:
        while p > 0: savings.append(p - p // 2); p //= 2
    savings.sort(reverse=True)
    return sum(price) - sum(savings[:vouchers])


def ref_msd(products, shopping):
    seen = []
    for item in shopping:
        for name, dept in products:
            if name == item:
                if dept not in seen: seen.append(dept)
                break
    return len(seen)


def ref_mcc(coins, target):
    order = sorted(range(len(coins)), key=lambda i: -coins[i])
    best = None

    def go(pos, left, counts):
        nonlocal best
        if pos == len(order):
            if left == 0:
                key = (sum(counts), [-c for c in counts])
                if best is None or key < best[0]: best = (key, list(counts))
            return
        c = coins[order[pos]]
        for t in range(left // c, -1, -1):
            counts.append(t); go(pos + 1, left - t * c, counts); counts.pop()

    go(0, target, [])
    if best is None: return []
    out = [0] * len(coins)
    for slot, i in enumerate(order): out[i] = best[1][slot]
    return out


def ref_mdp(nums):
    total, x = min((sum(abs(x - v) for v in nums), x) for x in nums)
    return [x, total]


def ref_mfg(grid):
    n, m = len(grid), len(grid[0]); parent = list(range(n * m))

    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for i in range(n):
        for j in range(m):
            for a, b in ((i, m - 1 - j), (n - 1 - i, j)):
                parent[find(i * m + j)] = find(a * m + b)
    groups = {}
    for i in range(n):
        for j in range(m): groups.setdefault(find(i * m + j), []).append(grid[i][j])
    return sum(min(g.count('B'), g.count('W')) for g in groups.values())


def longest_run(s):
    best = run = 1
    for i in range(1, len(s)):
        run = run + 1 if s[i] == s[i - 1] else 1; best = max(best, run)
    return best


def ref_mik(s, k):
    best = len(s)
    for size in range(k + 1):
        for chosen in combinations(range(len(s)), size):
            t = list(s)
            for i in chosen: t[i] = 'a' if t[i] == 'b' else 'b'
            best = min(best, longest_run(t))
    return best


def ref_mmt(tasks):
    return max((sum(1 for a, b in tasks if a <= s < b) for s, _ in tasks), default=0)


def ref_mrl(a):
    if not a: return []
    nodes = [{'v': v, 'l': None, 'r': None} if v is not None else None for v in a]
    real = [nodes[0]]; i = 1; q = 0
    while i < len(a):
        node = real[q]; q += 1
        if i < len(a): node['l'] = nodes[i]; real += [nodes[i]] if nodes[i] else []; i += 1
        if i < len(a): node['r'] = nodes[i]; real += [nodes[i]] if nodes[i] else []; i += 1
    paths = []

    def go(node, path):
        path = path + [node['v']]
        if node['l'] is None and node['r'] is None: paths.append(path); return
        for child in (node['l'], node['r']):
            if child is not None: go(child, path)
    go(nodes[0], [])
    return min(paths, key=sum)  # min keeps the first (leftmost) path among equal sums


def ref_msb(usage):
    b = 1
    while True:
        level, ok = b, True
        for u in usage:
            level -= u
            if level <= 0: ok = False; break
        if ok: return b
        b += 1


def ref_msk(arr, k):
    best = -1
    for i in range(len(arr)):
        seen = set()
        for j in range(i, len(arr)):
            seen.add(arr[j])
            if len(seen) >= k:
                if best == -1 or j - i + 1 < best: best = j - i + 1
                break
    return best


def ref_mse(nums):
    n = len(nums)
    start = sum(1 << i for i, v in enumerate(nums) if v % 2)
    evens = n - bin(start).count('1')
    goal = sum(1 << i for i in range(evens, n))
    dist = {start: 0}; queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal: return dist[cur]
        for i in range(n):
            for j in range(i + 1, n):
                if (cur >> i & 1) != (cur >> j & 1):
                    nxt = cur ^ (1 << i) ^ (1 << j)
                    if nxt not in dist: dist[nxt] = dist[cur] + 1; queue.append(nxt)
    raise AssertionError('unreachable')


def ref_ntl(a):
    values, children = nary_level_order(a)
    alive, days = set(range(len(values))), []
    while alive:
        leaves = [v for v in alive if not any(c in alive for c in children[v])]
        days.append(sorted(values[v] for v in leaves)); alive -= set(leaves)
    return days


def ref_nsb1(s):
    t = re.sub(r'[a-z,]', '', s)
    while '()' in t: t = t.replace('()', '')
    return t == ''


def ref_nsb2(s):
    def item(i):
        if s[i] == '(': return lst(i)
        j = i
        while s[j].isalpha(): j += 1
        return s[i:j], j

    def lst(i):
        out = []; i += 1
        if s[i] == ')': return out, i + 1
        while True:
            value, i = item(i); out.append(value)
            if s[i] == ')': return out, i + 1
            i += 1
    value, end = lst(0)
    assert end == len(s)
    return value


def ref_ngp(n):
    v = int(n) + 1
    while str(v) != str(v)[::-1]: v += 1
    return str(v)


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == MDA:
        budget(len(args[0]) * len(args[1]) <= 4000); return ref_mda(*args)
    if uid == MVS:
        budget(len(args[0]) <= 200 and max(args[0]) <= 3000); return ref_mvs(*args)
    if uid == MCV:
        budget(len(args[0]) <= 300); return ref_mcv(*args)
    if uid == MSD:
        budget(len(args[0]) * max(1, len(args[1])) <= 20000); return ref_msd(*args)
    if uid == MCC:
        budget(len(args[0]) <= 6 and args[1] <= 80); return ref_mcc(*args)
    if uid == MDP:
        budget(len(args[0]) <= 400); return ref_mdp(*args)
    if uid == MFG:
        budget(len(args[0]) * len(args[0][0]) <= 400); return ref_mfg(*args)
    if uid == MIK:
        budget(len(args[0]) <= 12); return ref_mik(*args)
    if uid == MMT:
        budget(len(args[0]) <= 300); return ref_mmt(*args)
    if uid == MRL:
        budget(len(args[0]) <= 300); return ref_mrl(*args)
    if uid == MSB:
        budget(len(args[0]) <= 60 and sum(u for u in args[0] if u > 0) <= 600); return ref_msb(*args)
    if uid == MSK:
        budget(len(args[0]) <= 200); return ref_msk(*args)
    if uid == MSE:
        budget(len(args[0]) <= 10); return ref_mse(*args)
    if uid == NTL:
        budget(len(args[0]) <= 300); return ref_ntl(*args)
    if uid == NSB1:
        budget(len(args[0]) <= 400); return ref_nsb1(*args)
    if uid == NSB2:
        budget(len(args[0]) <= 400); return ref_nsb2(*args)
    budget(len(args[0]) <= 7); return ref_ngp(*args)
