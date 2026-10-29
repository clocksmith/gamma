"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (literal replay,
full snapshots, exhaustive enumeration, quadratic scans, closed-form counting).
"""
from fractions import Fraction
from itertools import permutations, product
from math import comb
import re

H = 'hack2hire:'
CREDIT1 = H + '6aa32d070ca9cc4e1c790398'
CREDIT2 = H + '6aa32de80ca9cc4e1c7903a3'
ROUTE1 = H + '6ace8e7e2e3a0349b3a8e1d0'
ROUTE2 = H + '6ace8eea2e3a0349b3a8e1d4'
ROUTE3 = H + '6ace8f102e3a0349b3a8e1d5'
SNAP1 = H + '69b191c3a4e93c007df4004d'
SNAP2 = H + '69b192f6a4e93c007df40052'
SNAP3 = H + '69b1936ca4e93c007df40055'
STAY = H + '68baf390b5314dcd938cba02'
ITER = H + '677bf4df5cbaff553b53b068'
STOCK = H + '6961f1ef8742114304441d28'
LOVE = H + '67f9969355e478de52401ddd'
INC1 = H + '6acd8f922e3a0349b3a8d6fc'
INC2 = H + '6acd8fb12e3a0349b3a8d701'
INC3 = H + '6acd8fd52e3a0349b3a8d706'
TREE = H + '6aa882a68c97c56cdbdc954f'
TIME = H + '6796ba03b10bc587828f27b0'
SCHED = H + '67fc7863216af53465a7221c'
ATM = H + '69bf17cc21f6ab4226963dc2'
BAL1 = H + '69810d3cf8f2604d5eecfff4'
BAL2 = H + '69811c44f8f2604d5eed0020'
BAL3 = H + '6981207ff8f2604d5eed002c'
ADD = H + '6862ed30eb0810914237aaf3'
AGG = H + '6a629dc8190ed618c6e6b223'
MINE = H + '6a516506665efda9311f618d'

IDS = (CREDIT1, CREDIT2, ROUTE1, ROUTE2, ROUTE3, SNAP1, SNAP2, SNAP3, STAY, ITER, STOCK, LOVE, INC1, INC2, INC3,
       TREE, TIME, SCHED, ATM, BAL1, BAL2, BAL3, ADD, AGG, MINE)

_CREDIT_L1 = {'addAccount': 1, 'addAccountWithReferral': 2, 'getTotalCredit': 1}
_CREDIT_L2 = {**_CREDIT_L1, 'getTopAccounts': 1}
_ROUTER = {'processCommand': 1}
_SNAP_L1 = {'follow': 2, 'unfollow': 2, 'snapshot': 0, 'isFollowing': 3}
_SNAP_L2 = {**_SNAP_L1, 'getFollowees': 2}
_SNAP_L3 = {**_SNAP_L2, 'recommend': 3}
_ITER = {'hasNext': 0, 'next': 0}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    CREDIT1: ('AccountCreditTracker', 0, _CREDIT_L1, ()), CREDIT2: ('AccountCreditTracker', 0, _CREDIT_L2, ()),
    ROUTE1: ('RequestRouter', 0, _ROUTER, ()), ROUTE2: ('RequestRouter', 0, _ROUTER, ()), ROUTE3: ('RequestRouter', 0, _ROUTER, ()),
    SNAP1: ('SocialNetwork', 0, _SNAP_L1, ('follow', 'unfollow')), SNAP2: ('SocialNetwork', 0, _SNAP_L2, ('follow', 'unfollow')),
    SNAP3: ('SocialNetwork', 0, _SNAP_L3, ('follow', 'unfollow')),
    ITER: ('SubarrayFirstIterator', 2, _ITER, ()),
}
SAFE = 2**53 - 1
NAME = r'[a-z0-9_]{1,12}'
MOD = 10**9 + 7


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


def rows_of(a, width, maximum=100000):
    if type(a) is not list or len(a) > maximum: raise ValueError('rows size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


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


INT_TOKEN = r'-?(0|[1-9][0-9]{0,8})'
CANON = r'(0|[1-9][0-9]{0,9})'
DECIMAL = r'(0|[1-9][0-9]{0,8})(\.[0-9]{1,2})?'
WORD = r'[A-Za-z0-9_]{1,20}'


def tree_count(groups):
    n = sum(len(g) for g in groups); k = len(groups); total = 1
    for g in groups: total *= len(g)
    return total * n ** (k - 2) if k >= 2 else 1


def schedule_count(pattern, work, day):
    """Number of fillings (count only; used for the output-size bound)."""
    ways = {0: 1}
    for ch in pattern:
        nxt = {}
        for s, w in ways.items():
            for v in ([int(ch)] if ch != '?' else range(day + 1)):
                if s + v <= work: nxt[s + v] = nxt.get(s + v, 0) + w
        ways = nxt
    return ways.get(work, 0)


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid in (CREDIT1, CREDIT2):
        ops, rows = trace(uid, args, 20001)
        n = 0
        for op, row in zip(ops[1:], rows[1:]):
            if op in ('addAccount', 'addAccountWithReferral'):
                integer(row[0], 0, 10**6)
                if op == 'addAccountWithReferral': integer(row[1], 0, n - 1)
                n += 1
            elif op == 'getTotalCredit': integer(row[0], 0, n - 1)
            else: integer(row[0], 1, 20)
    elif uid in (ROUTE1, ROUTE2, ROUTE3):
        ops, rows = trace(uid, args, 3001)
        for row in rows[1:]: text(row[0], r'[!-~]+( [!-~]+){0,7}', 100)
    elif uid in (SNAP1, SNAP2, SNAP3):
        ops, rows = trace(uid, args, 20001)
        snaps = 0
        for op, row in zip(ops[1:], rows[1:]):
            if op in ('follow', 'unfollow', 'isFollowing'):
                integer(row[0], 0, 10**9); integer(row[1], 0, 10**9)
                if row[0] == row[1]: raise ValueError('self follow outside inferred domain')
                if op == 'isFollowing': integer(row[2], 0, snaps - 1)
            elif op == 'snapshot': snaps += 1
            elif op == 'getFollowees': integer(row[0], 0, 10**9); integer(row[1], 0, snaps - 1)
            elif op == 'recommend': integer(row[0], 0, 10**9); integer(row[1], 0, snaps - 1); integer(row[2], 1, 100)
    elif uid == STAY:
        envelope(args, 3)
        avail, start, end = args
        if type(avail) is not list or len(avail) > 300: raise ValueError('listings')
        total = 0
        for days in avail: array(days, 0, 10**6, 0, 2000); total += len(days)
        if total > 60000: raise ValueError('total days')
        integer(start, 0, 10**6); integer(end, start, 10**6)
    elif uid == ITER:
        ops, rows = trace(uid, args, 200001)
        a, b = rows[0]
        array(a, -10**9, 10**9, 0, 100000); array(b, -10**9, 10**9, 0, 100000)
        bs = set(b); left = len(b) + sum(1 for x in a if x not in bs)
        for op in ops[1:]:
            if op == 'next':
                if left == 0: raise ValueError('next() only while hasNext() is true')
                left -= 1
    elif uid == STOCK:
        envelope(args, 3)
        integer(args[0], 0, 500); integer(args[1], 0, 500); integer(args[2], 0, 500)
    elif uid == LOVE:
        envelope(args, 2)
        rows_of(args[0], 3, 100000)
        for r in args[0]:
            text(r[0], NAME, 12); text(r[1], NAME, 12); text(r[2], r'[ -~]{0,50}', 50)
        integer(args[1], 1, 100000)
    elif uid in (INC1, INC2, INC3):
        envelope(args, 3 if uid == INC1 else 4)
        strlist(args[0], r'(0|[1-9][0-9]{0,8}),' + NAME + r',(200|[45][0-9][0-9]),(0|[1-9][0-9]{0,5})', 0, 50000, 40)
        integer(args[1], 1, 10**9)
        if uid == INC1: integer(args[2], 1, 10**12)
        else: integer(args[2], 1, 10**12); integer(args[3], 0, 100)
    elif uid == TREE:
        envelope(args, 2)
        groups, rank = args
        if type(groups) is not list or not 1 <= len(groups) <= 500: raise ValueError('groups')
        seen = set()
        for g in groups:
            array(g, 0, 10**9, 1, 2000)
            seen.update(g)
        n = sum(len(g) for g in groups)
        if n > 2000 or len(seen) != n: raise ValueError('disjoint groups, at most 2000 nodes')
        text(rank, r'0|[1-9][0-9]{0,4999}', 5000)
        if int(rank) >= tree_count(groups): raise ValueError('rank outside [0, count)')
    elif uid == TIME:
        envelope(args, 4)
        for v in args: integer(v, 0, 9)
    elif uid == SCHED:
        envelope(args, 3)
        text(args[0], r'[0-8?]{7}', 7); integer(args[1], 0, 56); integer(args[2], 0, 8)
        if schedule_count(*args) > 20000: raise ValueError('output size bound')
    elif uid == ATM:
        envelope(args, 2)
        array(args[0], 1, 10**9, 1, 100000); integer(args[1], 1, 10**9)
    elif uid in (BAL1, BAL2, BAL3):
        envelope(args, 1)
        strlist(args[0], WORD + ',' + WORD + ',' + INT_TOKEN + ',' + CANON, 0, 100000, 80)
        for line in args[0]:
            if int(line.split(',')[3]) > 10**9: raise ValueError('timestamp')
    elif uid == ADD:
        envelope(args, 2)
        for a in args:
            if type(a) is not list or not 1 <= len(a) <= 4 or any(type(c) is not str for c in a): raise ValueError('char array')
            s = ''.join(a)
            if any(len(c) != 1 for c in a) or re.fullmatch(r'-?[0-9]+', s) is None or not -100 <= int(s) <= 100:
                raise ValueError('signed array domain')
    elif uid == AGG:
        envelope(args, 2)
        rows_of(args[0], 5, 100000)
        for r in args[0]:
            text(r[0], DECIMAL, 12); text(r[1], NAME, 12)
            if r[2] not in ('COMPLETED', 'PENDING', 'FAILED'): raise ValueError('status')
            text(r[3], NAME, 12); text(r[4], CANON, 10)
        text(args[1], CANON, 10)
    elif uid == MINE:
        envelope(args, 2)
        accounts, txs = args
        rows_of(accounts, 2, 10000); rows_of(txs, 4, 100000)
        names = set()
        for a in accounts:
            text(a[0], r'[0-9]{1,12}', 12); text(a[1], CANON, 10)
            if int(a[1]) > 10**9: raise ValueError('balance')
            names.add(a[0])
        if len(names) != len(accounts): raise ValueError('unique account numbers')
        for t in txs:
            text(t[0], WORD, 20); text(t[1], r'[0-9]{1,12}', 12); text(t[2], r'[0-9]{1,12}', 12); text(t[3], CANON, 10)
            if int(t[3]) > 10**9: raise ValueError('amount')


# ---------------------------------------------------------------- references

def ref_credit(ops, rows):
    if len(ops) > 3000: raise ValueError('reference budget')
    own, referrer, out = [], [], [None]
    total = lambda i: own[i] + sum(own[j] for j in range(len(own)) if referrer[j] == i)
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addAccount': own.append(row[0]); referrer.append(None); out.append(len(own) - 1)
        elif op == 'addAccountWithReferral': own.append(row[0]); referrer.append(row[1]); out.append(len(own) - 1)
        elif op == 'getTotalCredit': out.append(total(row[0]))
        else:
            ranked = sorted(range(len(own)), key=lambda i: (-total(i), i))
            out.append(ranked[:row[0]])
    return out


def _int_token(s, lo, hi):
    if re.fullmatch(INT_TOKEN, s) is None: return None
    v = int(s)
    return v if lo <= v <= hi else None


def ref_router(uid, ops, rows):
    level = (ROUTE1, ROUTE2, ROUTE3).index(uid) + 1
    dcs, out = [], [None]  # list of dicts in registration order
    for row in rows[1:]:
        t = row[0].split(' ')
        res = 'ERROR'
        if t[0] == 'REGISTER' and len(t) == 5:
            lat, lon, cap = _int_token(t[2], -90, 90), _int_token(t[3], -180, 180), _int_token(t[4], 1, 10**9)
            if None not in (lat, lon, cap) and all(d['name'] != t[1] for d in dcs):
                dcs.append({'name': t[1], 'lat': lat, 'lon': lon, 'cap': cap, 'up': True, 'load': 0}); res = 'OK'
        elif t[0] == 'ROUTE' and len(t) == 3:
            lat, lon = _int_token(t[1], -90, 90), _int_token(t[2], -180, 180)
            if None not in (lat, lon):
                ok = [d for d in dcs if d['up'] and d['load'] < d['cap']]
                if ok:
                    best = min(ok, key=lambda d: ((d['lat'] - lat) ** 2 + (d['lon'] - lon) ** 2, d['load'], [ord(c) for c in d['name']]))
                    best['load'] += 1; res = best['name']
        elif level >= 2 and t[0] in ('UP', 'DOWN') and len(t) == 2:
            hit = [d for d in dcs if d['name'] == t[1]]
            if hit: hit[0]['up'] = t[0] == 'UP'; res = 'OK'
        elif level >= 3 and t[0] == 'RELEASE' and len(t) == 2:
            hit = [d for d in dcs if d['name'] == t[1] and d['load'] > 0]
            if hit: hit[0]['load'] -= 1; res = 'OK'
        out.append(res)
    return out


def ref_snap(ops, rows):
    if len(ops) > 800: raise ValueError('reference budget')
    edges, snaps, out = set(), [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'follow': edges.add((row[0], row[1])); out.append(None)
        elif op == 'unfollow': edges.discard((row[0], row[1])); out.append(None)
        elif op == 'snapshot': snaps.append(frozenset(edges)); out.append(len(snaps) - 1)
        elif op == 'isFollowing': out.append((row[0], row[1]) in snaps[row[2]])
        elif op == 'getFollowees': out.append(sorted(e for f, e in snaps[row[1]] if f == row[0]))
        else:
            user, s, k = row; g = snaps[s]
            mine = {e for f, e in g if f == user}
            score = {}
            for f, e in g:
                if f in mine and e != user and e not in mine: score[e] = score.get(e, 0) + 1
            out.append(sorted(score, key=lambda w: (-score[w], w))[:k])
    return out


def ref_stay(avail, start, end):
    if len(avail) ** 2 * (end - start + 1) > 400000: raise ValueError('reference budget')
    sets = [set(d) for d in avail]
    covers = lambda i, a, b: all(x in sets[i] for x in range(a, b + 1))
    singles = [[i] for i in range(len(avail)) if covers(i, start, end)]
    pairs = [[i, j] for i in range(len(avail)) for j in range(len(avail))
             if i != j and any(covers(i, start, k) and covers(j, k + 1, end) for k in range(start, end))]
    return singles + pairs


def ref_iter(ops, rows):
    a, b = rows[0]
    if len(a) * (len(b) + 1) > 400000: raise ValueError('reference budget')
    seq = list(b) + [x for x in a if x not in b]
    out, pos = [None], 0
    for op in ops[1:]:
        if op == 'hasNext': out.append(pos < len(seq))
        else: out.append(seq[pos]); pos += 1
    return out


def ref_stock(initial, target, m):
    """Closed form: ballot/reflection count of +-1 paths of length L from initial to target never below 0."""
    total = 0
    for length in range(m + 1):
        if (length + target - initial) % 2: continue
        up = (length + target - initial) // 2
        if not 0 <= up <= length: continue
        bad_up = (length + target + initial + 2) // 2  # paths from -initial-2 (reflection about -1)
        total += comb(length, up) - (comb(length, bad_up) if 0 <= bad_up <= length else 0)
    return total % MOD


def ref_love(messages, k):
    pairs = sorted({(s, r) for s, r, _ in messages})
    names = sorted({r for _, r in pairs})
    counts = {r: len([p for p in pairs if p[1] == r]) for r in names}
    return sorted(names, key=lambda r: (-counts[r], [ord(c) for c in r]))[:k]


def ref_incident(uid, logs, window, *params):
    if len(logs) > 2500: raise ValueError('reference budget')
    recs = [(int(t), m, int(c), int(n)) for t, m, c, n in (line.split(',') for line in logs)]
    points = sorted({(t, m) for t, m, _, _ in recs}, key=lambda p: (p[0], [ord(c) for c in p[1]]))
    active, fired, out = set(), set(), []
    for t, m in points:
        inside = [(c, n) for (tt, mm, c, n) in recs if mm == m and t - window + 1 <= tt <= t]
        total = sum(n for _, n in inside)
        codes = sorted({c for c, _ in inside if c != 200} | {c for (mm, c) in active if mm == m})
        for c in codes:
            cnt = sum(n for cc, n in inside if cc == c)
            if uid == INC1: cond = cnt >= params[0]
            else: cond = cnt >= params[0] and cnt * 100 >= params[1] * total
            if uid == INC3:
                if cond and (m, c) not in active: active.add((m, c)); out.append('%d,%s,%d' % (t, m, c))
                elif not cond: active.discard((m, c))
            elif cond and (m, c) not in fired:
                fired.add((m, c)); out.append('%d,%s,%d' % (t, m, c))
    return out


def ref_tree(groups, rank):
    """Naive O(K^2) Pruefer decoding of the inferred rank bijection."""
    k = len(groups)
    if k == 1: return []
    nodes = [(x, gi) for gi, g in enumerate(groups) for x in g]
    r = int(rank); leaf_pick = []
    for g in groups: leaf_pick.append(g[r % len(g)]); r //= len(g)
    code = []
    for _ in range(k - 2): code.append(nodes[r % len(nodes)]); r //= len(nodes)
    alive = list(range(k)); edges = []
    for j, (node, gi) in enumerate(code):
        rest = [c[1] for c in code[j:]]
        leaf = min(g for g in alive if g not in rest)
        edges.append([leaf_pick[leaf], node]); alive.remove(leaf)
    u, v = alive
    edges.append([leaf_pick[u], leaf_pick[v]])
    return edges


def tree_is_valid(groups, edges):
    """Independent property: K-1 cross-group edges over existing nodes connecting all groups (forest check)."""
    where = {x: gi for gi, g in enumerate(groups) for x in g}
    if len(edges) != len(groups) - 1: return False
    parent = list(range(len(groups)))

    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for u, v in edges:
        if u not in where or v not in where: return False
        a, b = find(where[u]), find(where[v])
        if a == b: return False
        parent[a] = b
    return True


def ref_time(*digits):
    want = sorted(digits)
    return sum(1 for h in range(24) for m in range(60) if sorted(int(c) for c in '%02d%02d' % (h, m)) == want)


def ref_sched(pattern, work, day):
    q = pattern.count('?')
    if (day + 1) ** q > 300000: raise ValueError('reference budget')
    out = []
    for fill in product(range(day + 1), repeat=q):
        it = iter(fill)
        s = ''.join(str(next(it)) if ch == '?' else ch for ch in pattern)
        if sum(map(int, s)) == work: out.append(s)
    return sorted(out)


def ref_atm(amounts, k):
    if sum(-(-a // k) for a in amounts) > 300000: raise ValueError('reference budget')
    queue = [[i + 1, a] for i, a in enumerate(amounts)]; out = []
    while queue:
        person = queue.pop(0)
        person[1] -= min(k, person[1])
        if person[1]: queue.append(person)
        else: out.append(person[0])
    return out


def ref_balance(uid, logs):
    if len(logs) > 3000: raise ValueError('reference budget')
    recs = [line.split(',') for line in logs]
    if uid != BAL1:
        recs = [r for i, r in enumerate(recs) if all(p[0] != r[0] for p in recs[:i])]
    bal = {}
    for r in recs: bal.setdefault(r[1], 0)
    rejected = []
    order = recs if uid != BAL3 else sorted(recs, key=lambda r: int(r[3]))
    for r in order:
        amt = int(r[2])
        if uid == BAL3 and bal[r[1]] + amt < 0: rejected.append(r[0]); continue
        bal[r[1]] += amt
    rows = [[a, bal[a]] for a in sorted(bal, key=lambda s: [ord(c) for c in s])]
    return [rows, rejected] if uid == BAL3 else rows


def ref_add(a, b):
    return int(''.join(a)) + int(''.join(b))


def ref_agg(txs, now):
    cur = int(now); tot = {}
    for amount, merchant, status, _, start in txs:
        hours = (cur - int(start)) // 3600
        if status == 'COMPLETED' and 0 <= hours < 24:
            c = int(Fraction(amount) * 100)
            t = tot.setdefault(merchant, [0, 0]); t[0] += c; t[1] += 1
    return [[m, '%d.%02d' % divmod(tot[m][0], 100), tot[m][1]] for m in sorted(tot)]


def ref_mine(accounts, txs):
    if len(accounts) * len(txs) > 2000000: raise ValueError('reference budget')
    bal = [[a, int(b)] for a, b in accounts]
    for _, src, dst, amount in txs:
        s = [r for r in bal if r[0] == src]; d = [r for r in bal if r[0] == dst]
        if s and d and src != dst and s[0][1] >= int(amount):
            s[0][1] -= int(amount); d[0][1] += int(amount)
    return [[a, str(b)] for a, b in sorted(bal, key=lambda r: (-r[1], r[0]))]


def reference(uid, args):
    validate_domain(uid, args)
    if uid in (CREDIT1, CREDIT2): return ref_credit(*args)
    if uid in (ROUTE1, ROUTE2, ROUTE3):
        if len(args[0]) > 1500: raise ValueError('reference budget')
        return ref_router(uid, *args)
    if uid in (SNAP1, SNAP2, SNAP3): return ref_snap(*args)
    if uid == STAY: return ref_stay(*args)
    if uid == ITER: return ref_iter(*args)
    if uid == STOCK: return ref_stock(*args)
    if uid == LOVE: return ref_love(*args)
    if uid in (INC1, INC2, INC3): return ref_incident(uid, *args)
    if uid == TREE: return ref_tree(*args)
    if uid == TIME: return ref_time(*args)
    if uid == SCHED: return ref_sched(*args)
    if uid == ATM: return ref_atm(*args)
    if uid in (BAL1, BAL2, BAL3): return ref_balance(uid, args[0])
    if uid == ADD: return ref_add(*args)
    if uid == AGG: return ref_agg(*args)
    return ref_mine(*args)
