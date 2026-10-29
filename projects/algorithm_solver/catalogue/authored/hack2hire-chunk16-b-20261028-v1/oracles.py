"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (value-set comparison at
every cut, full re-sorting of lots, all-pairs differences, breadth-first search over coin states, a scan
of every bundle count, zero-flow-link enumeration, per-root breadth-first search, all-robot scans, flat
field lists, string reversal, permutation enumeration, regular-expression substitution, exact fractions,
recursive top-down search, whole-log scans and dictionary scans) and refuse inputs above a small budget.
"""
from collections import deque
from fractions import Fraction
from itertools import permutations
import re

H = 'hack2hire:'
MVB = H + '6a31cf175117d1b543567dcc'
MCG = H + '6796992ab10bc587828f27ae'
MAD = H + '69cac664ff3ebde766ced9a5'
MCF = H + '67803efe6fee41e51af73ddc'
MDP = H + '6a74eeddd713d873ca7a8195'
MRC = H + '6a31cd3f5117d1b543567dbe'
MRE = H + '69f1384f96981f58ae1f7687'
NID = H + '67888093402dc47b67a14948'
OFM = H + '69cda519ff3ebde766cee834'
PST = H + '68d89bb279db2fbcd7d7db16'
PDS = H + '6907b46fe1919109b6df119a'
PIG = H + '68f283fbf567e950995157d6'
PVO = H + '67cd196d3363b83a81fc99a7'
PFP = H + '68e8736a80f69c7a01706891'
PPQ = H + '68f68778a269f53ea0eff91d'
PPT = H + '68aceb961bf7d2097f647f62'

IDS = (MVB, MCG, MAD, MCF, MDP, MRC, MRE, NID, OFM, PST, PDS, PIG, PVO, PFP, PPQ, PPT)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    OFM: ('ObjectLayout', 2, {'getOffset': 1, 'fieldAt': 1, 'totalSize': 0, 'addField': 2, 'removeField': 1}, ()),
    PST: ('PalindromeStream', 0, {'track': 1, 'isPalindrome': 0}, ('track',)),
    PPT: ('ProductPrice', 0, {'update': 2, 'current': 0, 'maximum': 0, 'minimum': 0}, ('update',)),
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


def trace(uid, args, maximum=100001):
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


NUM = r'0|[1-9][0-9]*'


def mcg_domain(transactions):
    sized(transactions, 1, 100000)
    held, last = 0, 0
    for row in transactions:
        sized(row, 4, 4)
        text(row[0], NUM, 10); text(row[1], r'buy|sell', 4); text(row[2], NUM, 6); text(row[3], NUM, 8)
        stamp, amount, price = int(row[0]), int(row[2]), int(row[3])
        integer(stamp, last, 10**9); integer(amount, 1, 10**4); integer(price, 1, 10**6)
        last = stamp
        held += amount if row[1] == 'buy' else -amount
        if held < 0: raise ValueError('sell exceeds holdings')


def ofm_domain(args):
    calls = trace(OFM, args)
    names, sizes = args[1][0]
    sized(names, 0, 100000); intlist(sizes, 1, 10**4, len(names), len(names))
    for n in names: text(n, r'[a-z0-9_]{1,12}', 12)
    if len(set(names)) != len(names): raise ValueError('duplicate field')
    for op, row in calls:
        if op in ('getOffset', 'removeField', 'addField'): text(row[0], r'[a-z0-9_]{1,12}', 12)
        if op == 'addField': integer(row[1], 1, 10**4)
        if op == 'fieldAt': integer(row[0], 0, 10**10)


def pds_domain(pattern):
    text(pattern, r'[1-9?]{9}', 9)
    fixed = [c for c in pattern if c != '?']
    if len(set(fixed)) != len(fixed): raise ValueError('repeated fixed digit')


def pvo_domain(securities, funds):
    sized(securities, 1, 100000); integer(funds, 0, 10**12)
    for row in securities:
        sized(row, 4, 4); text(row[0], r'[A-Z]{1,5}', 5); integer(row[1], 1, 10**4); integer(row[2], 0, 10**4); integer(row[3], 0, 10**6)


def pfp_domain(ids, children, names, target):
    intlist(ids, 1, 10**9, 1); sized(children, len(ids), len(ids)); sized(names, len(ids), len(ids)); integer(target, 1, 10**9)
    if len(set(ids)) != len(ids): raise ValueError('duplicate id')
    known, seen = set(ids), set()
    for kids in children:
        intlist(kids, 1, 10**9, 0, 100000)
        for k in kids:
            if k not in known or k in seen: raise ValueError('child must be a known id with one parent')
            seen.add(k)
    for n in names: text(n, r'[A-Za-z0-9_]{1,10}', 10)
    # every node has at most one parent, so the structure is a forest iff a walk down from the top-level folders reaches every folder
    kids = dict(zip(ids, children)); stack = [i for i in ids if i not in seen]; reached = 0
    while stack:
        node = stack.pop(); reached += 1; stack.extend(kids[node])
    if reached != len(ids): raise ValueError('cycle')


ITEM = r'[A-Za-z0-9]+( [A-Za-z0-9]+)*'
DATE = r'20[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-8])'


def ppq_domain(log, queries):
    sized(log, 0, 100000); sized(queries, 1, 100000)
    seen = set()
    for entry in log:
        text(entry, r'(' + ITEM + r'), (' + DATE + r'), (' + NUM + r')', 50)
        m = re.fullmatch(r'(.*), (.*), (.*)', entry)
        if len(m.group(1)) > 20 or int(m.group(3)) > 10**9: raise ValueError('entry bounds')
        if (m.group(1), m.group(2)) in seen: raise ValueError('duplicate item date')
        seen.add((m.group(1), m.group(2)))
    for q in queries:
        sized(q, 2, 2); text(q[0], ITEM, 20); text(q[1], DATE, 10)


def tree_edges(n, a, b):
    integer(n, 1, 100000); intlist(a, 1, n, n - 1, n - 1); intlist(b, 1, n, n - 1, n - 1)
    root = list(range(n + 1))

    def find(v):
        while root[v] != v: root[v] = root[root[v]]; v = root[v]
        return v
    for u, v in zip(a, b):
        ru, rv = find(u), find(v)
        if ru == rv: raise ValueError('not a tree')
        root[ru] = rv


def validate_domain(uid, args):
    if uid == MVB: envelope(args, 1); intlist(args[0], 1, 10**9, 1)
    elif uid == MCG: envelope(args, 1); mcg_domain(args[0])
    elif uid == MAD:
        envelope(args, 1); intlist(args[0], -10**6, 10**6, 2)
        if len(set(args[0])) != len(args[0]): raise ValueError('values must be distinct')
    elif uid == MCF: envelope(args, 2); intlist(args[0], 1, 10**9, 1); integer(args[1], 1, 10**9)
    elif uid == MDP:
        envelope(args, 5); integer(args[0], 0, 10**9); integer(args[1], 0, 10**9)
        for c in args[2:]: integer(c, 1, 10**6)
    elif uid == MRC:
        envelope(args, 1); intlist(args[0], 0, 10**4, 1)
        if sum(args[0]) % len(args[0]): raise ValueError('total not divisible')
    elif uid == MRE: envelope(args, 3); tree_edges(*args)
    elif uid == NID:
        envelope(args, 2); intlist(args[0], -10**9, 10**9, 1); intlist(args[1], -10**9, 10**9, len(args[0]), len(args[0]))
        if len(set(zip(args[0], args[1]))) != len(args[0]): raise ValueError('positions must be distinct')
    elif uid == OFM: ofm_domain(args)
    elif uid == PST:
        for op, row in trace(PST, args):
            if op == 'track': text(row[0], r'[a-zA-Z0-9]', 1)
    elif uid == PDS: envelope(args, 1); pds_domain(args[0])
    elif uid == PIG: envelope(args, 1); text(args[0], r'([A-Za-z]+( [A-Za-z]+)*)?', 100000)
    elif uid == PVO: envelope(args, 2); pvo_domain(*args)
    elif uid == PFP: envelope(args, 4); pfp_domain(*args)
    elif uid == PPQ: envelope(args, 2); ppq_domain(*args)
    elif uid == PPT:
        for op, row in trace(PPT, args):
            if op == 'update': integer(row[0], 1, 10**9); integer(row[1], 1, 10**9)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_mvb(arr):
    pieces = 1
    for k in range(1, len(arr)):
        if not set(arr[:k]) & set(arr[k:]): pieces += 1
    return len(set(arr)) - pieces


def ref_mcg(transactions):
    lots, tenths = [], 0
    for _, kind, amount, price in transactions:
        amount, price = int(amount), int(price)
        if kind == 'buy': lots.append([price, amount]); continue
        lots = sorted(lots, key=lambda lot: -lot[0])
        profit = 0
        while amount:
            take = min(amount, lots[0][1])
            profit += (price - lots[0][0]) * take
            amount -= take; lots[0][1] -= take
            if lots[0][1] == 0: lots.pop(0)
        if profit > 0: tenths += profit
    return '%d.%d' % (tenths // 10, tenths % 10)


def ref_mad(values):
    best = min(abs(a - b) for i, a in enumerate(values) for b in values[i + 1:])
    return sorted([min(a, b), max(a, b)] for i, a in enumerate(values) for b in values[i + 1:] if abs(a - b) == best)


def ref_mcf(coins, top):
    # Coins sorted non-decreasingly cover 1..r iff each is at most 1 + the sum before it (r = total); BFS over (total, last coin).
    usable = sorted(set(c for c in coins if c <= top))
    if not usable or usable[0] != 1: return -1
    frontier, seen, steps = deque([(0, 0, 0)]), {(0, 0)}, {}
    while frontier:
        total, last, count = frontier.popleft()
        if total >= top: return count
        for c in usable:
            if c >= last and c <= total + 1 and (min(total + c, top), c) not in seen:
                seen.add((min(total + c, top), c)); frontier.append((min(total + c, top), c, count + 1))
    raise AssertionError('unreachable')


def ref_mdp(x, y, e, i, b):
    return min(k * b + max(0, x - k) * e + max(0, y - k) * i for k in range(max(x, y) + 1))


def ref_mrc(products):
    n = len(products); avg = sum(products) // n; best = None
    for direction in (1, -1):
        for zero in range(n):
            # flow[j] = units moving from j to j + direction; flow[zero] = 0; conservation: flow[j] = flow[j - direction] + products[j] - avg
            flow = {zero: 0}; j = zero
            for _ in range(n - 1):
                nxt = (j + direction) % n
                flow[nxt] = flow[j] + products[nxt] - avg; j = nxt
            if all(f >= 0 for f in flow.values()):
                cost = sum(flow.values())
                best = cost if best is None else min(best, cost)
    return best


def ref_mre(n, a, b):
    adj = {v: [] for v in range(1, n + 1)}
    for u, v in zip(a, b): adj[u].append((v, 0)); adj[v].append((u, 1))
    best = None
    for root in range(1, n + 1):
        cost, seen, queue = 0, {root}, deque([root])
        while queue:
            u = queue.popleft()
            for v, against in adj[u]:
                if v not in seen: seen.add(v); cost += against; queue.append(v)
        best = cost if best is None else min(best, cost)
    return best


def ref_nid(xs, ys):
    pts = list(zip(xs, ys)); count = 0
    for px, py in pts:
        up = any(qx == px and qy > py for qx, qy in pts); down = any(qx == px and qy < py for qx, qy in pts)
        right = any(qy == py and qx > px for qx, qy in pts); left = any(qy == py and qx < px for qx, qy in pts)
        count += up and down and left and right
    return count


def ref_ofm(names, sizes, calls):
    fields = [[n, s] for n, s in zip(names, sizes)]; out = [None]
    for op, row in calls:
        if op == 'getOffset':
            at, res = 0, -1
            for n, s in fields:
                if n == row[0]: res = at; break
                at += s
            out.append(res)
        elif op == 'fieldAt':
            at, res = 0, ''
            for n, s in fields:
                if at <= row[0] < at + s: res = n; break
                at += s
            out.append(res)
        elif op == 'totalSize': out.append(sum(s for _, s in fields))
        elif op == 'addField':
            if any(n == row[0] for n, _ in fields): out.append(False)
            else: fields.append([row[0], row[1]]); out.append(True)
        else:
            keep = [f for f in fields if f[0] != row[0]]
            out.append(len(keep) != len(fields)); fields = keep
    return out


def ref_pst(calls):
    s, out = '', [None]
    for op, row in calls:
        if op == 'track': s += row[0]; out.append(None)
        else: out.append(s == s[::-1])
    return out


def ref_pds(pattern):
    free = [i for i, c in enumerate(pattern) if c == '?']
    unused = [d for d in '123456789' if d not in pattern]
    count = 0
    for perm in permutations(unused):
        s = list(pattern)
        for i, d in zip(free, perm): s[i] = d
        if int(''.join(s[0:3])) + int(''.join(s[3:6])) == int(''.join(s[6:9])): count += 1
    return count


def ref_pig(sentence):
    return re.sub(r'[A-Za-z]+', lambda m: m.group(0) + 'way' if m.group(0)[0] in 'aeiouAEIOU' else m.group(0)[1:] + m.group(0)[0] + 'ay', sentence)


def ref_pvo(securities, funds):
    left, value = Fraction(funds), Fraction(0)
    for _, p, s, a in sorted(securities, key=lambda r: -Fraction(r[2], r[1])):
        q = min(Fraction(a), left / p)
        value += q * s; left -= q * p
    cents = (value * 100 + Fraction(1, 2)).__floor__()
    return '%d.%02d' % (cents // 100, cents % 100)


def ref_pfp(ids, children, names, target):
    name = dict(zip(ids, names)); kids = dict(zip(ids, children))
    tops = [i for i in ids if not any(i in c for c in children)]

    def search(node, path):
        path = path + [name[node]]
        if node == target: return path
        for k in kids[node]:
            found = search(k, path)
            if found: return found
        return None
    for t in tops:
        found = search(t, [])
        if found: return '/'.join(found)
    return ''


def ref_ppq(log, queries):
    out = []
    for item, date in queries:
        best = None
        for entry in log:
            m = re.fullmatch(r'(.*), (.*), (.*)', entry)
            if m.group(1) == item and m.group(2) <= date and (best is None or m.group(2) > best[0]): best = (m.group(2), int(m.group(3)))
        out.append(-1 if best is None else best[1])
    return out


def ref_ppt(calls):
    prices, out = {}, [None]
    for op, row in calls:
        if op == 'update': prices[row[0]] = row[1]; out.append(None)
        elif not prices: out.append(-1)
        elif op == 'current': out.append(prices[max(prices)])
        elif op == 'maximum': out.append(max(prices.values()))
        else: out.append(min(prices.values()))
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid == OFM:
            budget(len(args[1][0][0]) <= 300); return ref_ofm(*args[1][0], calls)
        if uid == PST: return ref_pst(calls)
        return ref_ppt(calls)
    if uid == MVB:
        budget(len(args[0]) <= 200); return ref_mvb(args[0])
    if uid == MCG:
        budget(len(args[0]) <= 300); return ref_mcg(args[0])
    if uid == MAD:
        budget(len(args[0]) <= 300); return ref_mad(args[0])
    if uid == MCF:
        budget(args[1] <= 300 and len(args[0]) <= 50); return ref_mcf(*args)
    if uid == MDP:
        budget(max(args[0], args[1]) <= 3000); return ref_mdp(*args)
    if uid == MRC:
        budget(len(args[0]) <= 120); return ref_mrc(args[0])
    if uid == MRE:
        budget(args[0] <= 300); return ref_mre(*args)
    if uid == NID:
        budget(len(args[0]) <= 300); return ref_nid(*args)
    if uid == PDS:
        budget(args[0].count('?') <= 8); return ref_pds(args[0])
    if uid == PIG: return ref_pig(args[0])
    if uid == PVO:
        budget(len(args[0]) <= 300); return ref_pvo(*args)
    if uid == PFP:
        budget(len(args[0]) <= 300); return ref_pfp(*args)
    budget(len(args[0]) * len(args[1]) <= 20000); return ref_ppq(*args)
