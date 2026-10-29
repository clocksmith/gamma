"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (exhaustive ordered
selections, pairwise connected components, repeated road scans, linear car scans, window sorting,
all-pairs distances, path-keyed dictionaries, day-by-day simulation, per-query interval scans,
enumeration of question marks, linear book scans, window rescans, rebuilt arrays, linear and minimum
scans, full replays with sorting and column-stack rendering with whole-board rescans) and refuse
inputs above a small budget.
"""
from itertools import permutations, product
import math
import re

H = 'hack2hire:'
BLP = H + '67cf33498f73eb6319edd230'
BFO = H + '685c61e88515b8a3b59d19f9'
CCP = H + '68c86e64df5a6365aa774b11'
CFS1 = H + '69b7856c8a0eeb9897a8d239'
CFS2 = H + '69b785888a0eeb9897a8d23b'
CPP = H + '69efd6f096981f58ae1f6dcf'
CPD = H + '690425df4845d25b8e994896'
CNS = H + '69c42c3e21f6ab4226965a1f'
CDS = H + '6775b4fd0d31dc201f712039'
CIC = H + '692fc0f4cd79766b0b3101a0'
CVB = H + '67844afb0e1dbb6a0938577f'
COM = H + '678ec4943d1b82777aa24f9a'
DWS1 = H + '696c54fe6b040fa4d120bca7'
DWS2 = H + '696c5f906b040fa4d120bcbe'
DKB = H + '68672293a2d59460201f2cae'
DVC1 = H + '6913fb43fa8a311e42671e69'
DVC2 = H + '69141530fa8a311e42671e8f'
DAS = H + '69334452e8ebbb1c53caf2c4'
DCF1 = H + '69bdbad91cbff60a929beb23'
DCF2 = H + '69dd348b95e80ae213e5b702'

IDS = (BLP, BFO, CCP, CFS1, CFS2, CPP, CPD, CNS, CDS, CIC, CVB, COM, DWS1, DWS2, DKB, DVC1, DVC2, DAS, DCF1, DCF2)
CFS = (CFS1, CFS2)
DWS = (DWS1, DWS2)
DVC = (DVC1, DVC2)
DCF = (DCF1, DCF2)
# results compared by numeric value for JavaScript (no integral-float tag in JavaScript); Python must return float
FLOATS = (CPD,)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    CIC: ('IntervalCounter', 1, {'count': 1}, ()),
    DAS: ('ArticleSystem', 0, {'addArticle': 1, 'upvoteArticle': 2, 'downvoteArticle': 2, 'getRecentFlips': 2, 'getTopArticles': 1}, ('upvoteArticle', 'downvoteArticle')),
    DCF1: ('ConnectFourBoard', 2, {'drop': 2}, ()),
    DCF2: ('ConnectFourBoard', 2, {'drop': 2, 'getWinner': 0}, ()),
}
WINDOW = 600000
CAMP = 'Campground'


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


def blp_domain(words):
    sized(words, 1, 100000)
    for w in words: text(w, r'[a-z]{1,10}', 10)
    if len({len(w) for w in words}) != 1: raise ValueError('equal lengths')


def bfo_domain(orders, prices, tiers):
    sized(orders, 0, 100000); sized(prices, 0, 100000); sized(tiers, 0, 20)
    priced = set()
    for row in prices:
        sized(row, 2, 2); text(row[0], r'[a-z]{1,10}', 10); integer(row[1], 1, 10000)
        if row[0] in priced: raise ValueError('duplicate price')
        priced.add(row[0])
    for row in orders:
        sized(row, 3, 3); text(row[0], r'[a-z]{1,10}', 10); text(row[1], r'[1-9][0-9]{0,3}', 4); text(row[2], r'0|[1-9][0-9]{0,13}', 14)
        if int(row[1]) > 1000 or int(row[2]) > 10**13 or row[0] not in priced: raise ValueError('order domain')
    last = 1
    for row in tiers:
        sized(row, 2, 2); integer(row[0], 2, 10**8); integer(row[1], 0, 100)
        if row[0] <= last: raise ValueError('tiers increasing')
        last = row[0]


def ccp_domain(roads, friends, start1, start2):
    sized(roads, 1, 100000); sized(friends, 0, 100000)
    nxt = {}
    for row in roads:
        sized(row, 3, 3); text(row[0], r'[A-Za-z0-9]{1,10}', 10); text(row[1], r'[A-Za-z0-9]{1,10}', 10); integer(row[2], 1, 10000)
        if row[0] in nxt or row[0] == CAMP or row[0] == row[1]: raise ValueError('road shape')
        nxt[row[0]] = row[1]
    done = {CAMP}
    for start in nxt:  # every route ends at the Campground (no cycles, no dead ends)
        path, seen, cur = [], set(), start
        while cur not in done:
            if cur in seen or cur not in nxt: raise ValueError('route must end at the Campground')
            seen.add(cur); path.append(cur); cur = nxt[cur]
        done.update(path)
    if type(start1) is not str or type(start2) is not str or start1 == start2 or start1 not in nxt or start2 not in nxt: raise ValueError('starts')
    on = set()
    for s in (start1, start2):
        cur = s
        while cur != CAMP: on.add(cur); cur = nxt[cur]
    names = set()
    for row in friends:
        sized(row, 2, 2); text(row[0], r'[A-Za-z0-9]{1,10}', 10); text(row[1], r'[A-Za-z0-9]{1,10}', 10)
        if row[0] in names or row[1] not in on: raise ValueError('friend domain')
        names.add(row[0])


def cfs_domain(uid, args):
    envelope(args, 1 if uid == CFS1 else 2)
    sized(args[0], 0, 100000)
    for row in args[0]:
        sized(row, 2, 2); integer(row[0], 0, 10**9); integer(row[1], 0, 10**9)
        if row[0] >= row[1]: raise ValueError('start < end')
    if uid == CFS2: integer(args[1], 1, 100000)


def cpd_domain(points):
    sized(points, 2, 50000)
    seen = set()
    for p in points:
        sized(p, 2, 2); integer(p[0], -10**7, 10**7); integer(p[1], -10**7, 10**7)
        if (p[0], p[1]) in seen: raise ValueError('distinct points')
        seen.add((p[0], p[1]))


def level_order_count(tree):
    """Validate a canonical LeetCode level-order list; return its node count."""
    if type(tree) is not list: raise ValueError('tree list')
    for v in tree:
        if v is not None: integer(v, -10**4, 10**4)
    if not tree: return 0
    if tree[0] is None or tree[-1] is None: raise ValueError('canonical level order')
    pending, i, count = 1, 1, 1
    while pending and i < len(tree):
        pending -= 1
        for _ in range(2):
            if i < len(tree):
                if tree[i] is not None: pending += 1; count += 1
                i += 1
    if i < len(tree): raise ValueError('extra level-order entries')
    return count


def cns_domain(trees):
    sized(trees, 1, 10)
    for t in trees:
        if level_order_count(t) > 10000: raise ValueError('tree size')


def cvb_domain(arr, pattern):
    intlist(arr, 1, 50, 0, 25); text(pattern, r'[01?]{1,50}', 50)


def com_domain(buys, sells, orders):
    intlist(buys, 1, 10**9); intlist(sells, 1, 10**9); sized(orders, 0, 100000)
    for row in orders:
        sized(row, 2, 2); integer(row[1], 1, 10**9)
        if row[0] not in ('buy', 'sell'): raise ValueError('side')


def dws_domain(uid, points, tag, k):
    sized(points, 0, 100000); text(tag, r'[a-z]{1,8}', 8); integer(k, 1, 10**9 if uid == DWS1 else 100000)
    last = -1
    for p in points:
        if type(p) is not dict or set(p) != {'tags', 'timestamp', 'value'}: raise ValueError('datapoint keys')
        sized(p['tags'], 0, 5)
        for t in p['tags']: text(t, r'[a-z]{1,8}', 8)
        if len(set(p['tags'])) != len(p['tags']): raise ValueError('distinct tags')
        integer(p['timestamp'], 0, 10**9); integer(p['value'], -10**9, 10**9)
        if p['timestamp'] <= last: raise ValueError('increasing timestamps')
        last = p['timestamp']


def version_key(v):
    text(v, r'(0|[1-9][0-9]{0,6})\.(0|[1-9][0-9]{0,6})\.(0|[1-9][0-9]{0,6})', 23)
    key = tuple(int(x) for x in v.split('.'))
    if max(key) > 10**6: raise ValueError('version component')
    return key


def dvc_domain(uid, versions, supported):
    sized(versions, 0, 100000); sized(supported, len(versions), len(versions))
    for s in supported:
        if type(s) is not bool: raise ValueError('boolean answers')
    keys = [version_key(v) for v in versions]
    if len(set(keys)) != len(keys): raise ValueError('distinct versions')
    if uid == DVC1 and any(keys[i] >= keys[i + 1] for i in range(len(keys) - 1)): raise ValueError('sorted versions')
    ordered = [supported[i] for i in sorted(range(len(keys)), key=keys.__getitem__)]
    if any(ordered[i] and not ordered[i + 1] for i in range(len(ordered) - 1)): raise ValueError('monotone answers')


def das_domain(args):
    calls = trace(DAS, args, 100001)
    articles = 0
    for op, row in calls:
        if op == 'addArticle':
            text(row[0], r'[a-z]{1,10}', 10); articles += 1
            if articles > 10000: raise ValueError('too many articles')
        elif op in ('upvoteArticle', 'downvoteArticle'): integer(row[0], 1, articles); integer(row[1], 1, 100000)
        elif op == 'getRecentFlips': integer(row[0], 1, 100000); integer(row[1], 1, 100)
        else: integer(row[0], 1, 100)


def dcf_domain(uid, args):
    calls = trace(uid, args, 100001)
    rows, cols = args[1][0]
    integer(rows, 1, 50); integer(cols, 1, 50)
    drops = 0
    for op, row in calls:
        if op == 'drop':
            text(row[0], r'[A-Z]', 1); integer(row[1], 0, cols - 1); drops += 1
    if drops * rows * cols > 10**6: raise ValueError('returned cells')


def validate_domain(uid, args):
    if uid == BLP: envelope(args, 1); blp_domain(args[0])
    elif uid == BFO: envelope(args, 3); bfo_domain(*args)
    elif uid == CCP: envelope(args, 4); ccp_domain(*args)
    elif uid in CFS: cfs_domain(uid, args)
    elif uid == CPP:
        envelope(args, 1); intlist(args[0], 1, 200000, 1, 200000)
        if sorted(args[0]) != list(range(1, len(args[0]) + 1)): raise ValueError('permutation')
    elif uid == CPD: envelope(args, 1); cpd_domain(args[0])
    elif uid == CNS: envelope(args, 1); cns_domain(args[0])
    elif uid == CDS: envelope(args, 2); intlist(args[0], 1, 100000, 1, 100000); integer(args[1], 1, 10**9)
    elif uid == CIC:
        calls = trace(uid, args, 100001)
        sized(args[1][0][0], 0, 100000)
        for row in args[1][0][0]:
            sized(row, 2, 2); integer(row[0], -10**9, 10**9); integer(row[1], row[0], 10**9)
        for _, row in calls: integer(row[0], -10**9, 10**9)
    elif uid == CVB: envelope(args, 2); cvb_domain(*args)
    elif uid == COM: envelope(args, 3); com_domain(*args)
    elif uid in DWS: envelope(args, 3); dws_domain(uid, *args)
    elif uid == DKB:
        envelope(args, 2); intlist(args[0], -10**9, 10**9, 1, 100000); integer(args[1], 1, len(args[0]))
    elif uid in DVC: envelope(args, 2); dvc_domain(uid, *args)
    elif uid == DAS: das_domain(args)
    elif uid in DCF: dcf_domain(uid, args)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_blp(words):
    best = 0
    for r in range(len(words) + 1):
        for perm in permutations(words, r):
            s = ''.join(perm)
            if s == s[::-1]: best = max(best, len(s))
    return best


def ref_bfo(orders, prices, tiers):
    price = {f: p for f, p in prices}
    n = len(orders); group = [-1] * n; total = 0
    for i in range(n):
        if group[i] >= 0: continue
        group[i] = i; members = [i]; stack = [i]
        while stack:
            a = stack.pop()
            for b in range(n):
                if group[b] < 0 and orders[b][0] == orders[a][0] and abs(int(orders[b][2]) - int(orders[a][2])) <= WINDOW:
                    group[b] = i; members.append(b); stack.append(b)
        q = sum(int(orders[m][1]) for m in members)
        pct = 0
        if len(members) >= 2:
            for lo, p in tiers:
                if lo <= q: pct = p
        total += q * price[orders[i][0]] * (100 - pct) // 100
    return total


def ref_route(roads, start):
    times, cur, t = {start: 0}, start, 0
    while cur != CAMP:
        for a, b, d in roads:
            if a == cur:
                t += d; cur = b; break
        times[cur] = t
    return times


def ref_ccp(roads, friends, start1, start2):
    t1, t2 = ref_route(roads, start1), ref_route(roads, start2)
    out = [[], []]
    for index, (name, home) in enumerate(friends):
        a, b = t1.get(home), t2.get(home)
        if b is None or (a is not None and a <= b): out[0].append((a, index, name))
        else: out[1].append((b, index, name))
    return [[x[2] for x in sorted(side)] for side in out]


def ref_cfs(leases, cars=None):
    order = sorted(range(len(leases)), key=lambda i: (leases[i][0], i))
    ends = [] if cars is None else [0] * cars
    out = [0] * len(leases)
    for i in order:
        s, e = leases[i]
        for car, end in enumerate(ends):
            if end <= s:
                ends[car] = e; out[i] = car + 1; break
        else:
            if cars is None: ends.append(e); out[i] = len(ends)
            else: out[i] = -1
    return out


def ref_cpp(p):
    n = len(p)
    return [any(sorted(p[i:i + k]) == list(range(1, k + 1)) for i in range(n - k + 1)) for k in range(1, n + 1)]


def ref_cpd(points):
    best = min((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for i, a in enumerate(points) for b in points[i + 1:])
    return math.sqrt(best)


def ref_paths(tree):
    out = {}
    if not tree: return out
    out[''] = tree[0]; queue = ['']; i = 1; head = 0
    while head < len(queue) and i < len(tree):
        p = queue[head]; head += 1
        for side in 'LR':
            if i < len(tree):
                if tree[i] is not None: out[p + side] = tree[i]; queue.append(p + side)
                i += 1
    return out


def ref_cns(trees):
    result = ref_paths(trees[-1])
    for t in trees[:-1]:
        src = ref_paths(t)
        for p, v in src.items():
            result[p] = result.get(p, 0) + v + src.get(p + 'L', 0) + src.get(p + 'R', 0)
    if '' not in result: return []
    out, queue, head = [result['']], [''], 0
    while head < len(queue):
        p = queue[head]; head += 1
        for side in 'LR':
            if p + side in result: out.append(result[p + side]); queue.append(p + side)
            else: out.append(None)
    while out[-1] is None: out.pop()
    return out


def ref_cds(intervals, goal):
    done, day = 0, 0
    while done < goal:
        day += 1
        if day > 5000: raise ValueError('reference budget')
        done += sum(1 for iv in intervals if (day - 1) % iv == 0)
    return day


def ref_cic(intervals, calls):
    return [None] + [sum(1 for l, r in intervals if l <= x <= r) for _, (x,) in calls]


def ref_cvb(arr, pattern):
    holes = [i for i, ch in enumerate(pattern) if ch == '?']
    count = 0
    for bits in product('01', repeat=len(holes)):
        s = list(pattern)
        for i, b in zip(holes, bits): s[i] = b
        if [len(x) for x in ''.join(s).split('0') if x] == arr: count += 1
    return count


def ref_com(buys, sells, orders):
    buys, sells, out = list(buys), list(sells), []
    for side, price in orders:
        if side == 'buy':
            ok = [s for s in sells if s <= price]
            if ok: m = min(ok); sells.remove(m); out.append(m)
            else: buys.append(price); out.append(-1)
        else:
            ok = [b for b in buys if b >= price]
            if ok: m = max(ok); buys.remove(m); out.append(m)
            else: sells.append(price); out.append(-1)
    return out


def ref_dws(uid, points, tag, k):
    tagged = [p for p in points if tag in p['tags']]
    if uid == DWS1:
        return [sum(q['value'] for q in tagged if p['timestamp'] - k + 1 <= q['timestamp'] <= p['timestamp']) for p in tagged]
    return [sum(q['value'] for q in tagged[max(0, i - k + 1):i + 1]) for i in range(len(tagged))]


def ref_dkb(nums, k):
    for i in range(len(nums) - k + 1):
        rest = nums[:i] + nums[i + k:]
        if sum(rest[0::2]) == sum(rest[1::2]): return i
    return -1


def ref_dvc(uid, versions, supported):
    if uid == DVC1:
        for v, s in zip(versions, supported):
            if s: return v
        return None
    good = [v for v, s in zip(versions, supported) if s]
    return min(good, key=lambda v: [int(x) for x in v.split('.')]) if good else None


def ref_das(calls):
    names, votes, flips, out = [], {}, [], [None]
    for op, row in calls:
        if op == 'addArticle': names.append(row[0]); out.append(len(names)); continue
        if op in ('upvoteArticle', 'downvoteArticle'):
            a, u = row; new = 1 if op == 'upvoteArticle' else -1
            old = votes.get((u, a), 0)
            if old != new:
                votes[(u, a)] = new
                if old == -new: flips.append((u, a))
            out.append(None); continue
        if op == 'getRecentFlips':
            u, k = row; seen = []
            for fu, fa in reversed(flips):
                if fu == u and fa not in seen: seen.append(fa)
            out.append([names[a - 1] for a in seen[:k]]); continue
        score = [0] * (len(names) + 1)
        for (_, a), v in votes.items(): score[a] += v
        ranked = sorted(range(1, len(names) + 1), key=lambda a: (-score[a], a))
        out.append([names[a - 1] for a in ranked[:row[0]]])
    return out


def ref_four(board, rows, cols):
    for r in range(rows):
        for c in range(cols):
            x = board[r][c]
            if x == '0': continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if all(0 <= r + i * dr < rows and 0 <= c + i * dc < cols and board[r + i * dr][c + i * dc] == x for i in range(4)): return x
    return '0'


def ref_dcf(rows, cols, calls):
    stacks, winner, out = [[] for _ in range(cols)], '0', [None]
    for op, row in calls:
        if op == 'drop':
            color, col = row
            if len(stacks[col]) < rows: stacks[col].append(color)
            board = [[stacks[c][rows - 1 - r] if rows - 1 - r < len(stacks[c]) else '0' for c in range(cols)] for r in range(rows)]
            if winner == '0': winner = ref_four(board, rows, cols)
            out.append(board)
        else: out.append(winner)
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == BLP:
        budget(len(args[0]) <= 6); return ref_blp(args[0])
    if uid == BFO:
        budget(len(args[0]) <= 300); return ref_bfo(*args)
    if uid == CCP:
        budget(len(args[0]) <= 300); return ref_ccp(*args)
    if uid in CFS:
        budget(len(args[0]) <= 400); return ref_cfs(*args)
    if uid == CPP:
        budget(len(args[0]) <= 60); return ref_cpp(args[0])
    if uid == CPD:
        budget(len(args[0]) <= 300); return ref_cpd(args[0])
    if uid == CNS:
        budget(sum(len(t) for t in args[0]) <= 600); return ref_cns(args[0])
    if uid == CDS:
        budget(len(args[0]) <= 50); return ref_cds(*args)
    if uid == CVB:
        budget(args[1].count('?') <= 12); return ref_cvb(*args)
    if uid == COM:
        budget((len(args[0]) + len(args[1]) + len(args[2])) * len(args[2]) <= 40000); return ref_com(*args)
    if uid in DWS:
        budget(len(args[0]) <= 300); return ref_dws(uid, *args)
    if uid == DKB:
        budget(len(args[0]) <= 200); return ref_dkb(*args)
    if uid in DVC:
        budget(len(args[0]) <= 2000); return ref_dvc(uid, *args)
    calls = trace(uid, args, 100001)
    if uid == CIC:
        budget(len(args[1][0][0]) * len(calls) <= 20000); return ref_cic(args[1][0][0], calls)
    if uid == DAS:
        budget(len(calls) <= 300); return ref_das(calls)
    rows, cols = args[1][0]
    budget(len(calls) * rows * cols <= 100000); return ref_dcf(rows, cols, calls)
