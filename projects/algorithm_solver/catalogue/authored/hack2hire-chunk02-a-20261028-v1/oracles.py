"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags. None is the official specification. References are
deliberately different (literal/brute-force) algorithms from the candidate designs in design.json.
"""
from fractions import Fraction
from itertools import product
import re

H = 'hack2hire:'
ADS1 = H + '6a7f6aa4d713d873ca7adb44'
ADS2 = H + '6a7f6b0ad713d873ca7adb47'
RECT = H + '6a18e226c81f779dc6a230e4'
GPU1 = H + '69117148869dd6a56c434054'
GPU2 = H + '6913b4310ac116974ccedd13'
NFT1 = H + '6791b00b74ebe9de6650635c'
NFT2 = H + '6791b3fa74ebe9de6650635d'
NFT3 = H + '6791b5ff74ebe9de6650635e'
LOAN1 = H + '6a611985c16dcdf8ba4ff8a2'
LOAN2 = H + '6a7231c748af2ae18e995d8b'
SELLER = H + '6768c33400d569e371e007ec'
AVG = H + '6a91ef7ccddc54478ddf4a34'
FIREWALL = H + '684bada44023c4f502877df5'
IPO = H + '6987b235fedd959e9aa44515'
TREE = H + '6a90b63acddc54478ddf423a'
FRAUD1 = H + '6a5941a8665efda9311fa417'
FRAUD2 = H + '6a5941f5665efda9311fa41e'
PAY1 = H + '697699035ed12b33b05f0f4e'
PAY2 = H + '6976e8995ed12b33b05f10f7'
TRANSPOSE = H + '6a226625981072682a6f216b'
PRISON = H + '69fa55d2661bab75bbca3b9d'
ISLAND = H + '6933c5c85f306485cc5f07c0'
INCR = H + '6a7253d448af2ae18e995e99'
MULTI = H + '67b36a7975074948935624c7'
IDS = (ADS1, ADS2, RECT, GPU1, GPU2, NFT1, NFT2, NFT3, LOAN1, LOAN2, SELLER, AVG, FIREWALL, IPO, TREE,
       FRAUD1, FRAUD2, PAY1, PAY2, TRANSPOSE, PRISON, ISLAND, INCR, MULTI)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    GPU1: ('CreditSystem', 0, {'addCredit': 4, 'revokeCredit': 2, 'getBalance': 1}, ('addCredit',)),
    GPU2: ('CreditSystem', 0, {'addCredit': 4, 'consumeCredit': 2, 'getBalance': 1}, ('addCredit',)),
    FIREWALL: ('IpFirewall', 1, {'isAllowed': 1}, ()),
    FRAUD1: ('DistinctPIIValuesCounter', 0, {'processEvent': 1, 'getDistinctPIICount': 0}, ('processEvent',)),
    FRAUD2: ('DistinctPIIValuesCounter', 0, {'processEvent': 1, 'getDistinctPIICount': 0, 'getSharedPIICount': 0}, ('processEvent',)),
    MULTI: ('MultiStreamReader', 1, {'read': 1}, ()),
}
# Maximum trace length per class problem (bounded so every generated case stays well under 1 CPU s jitless).
TRACE_MAX = {GPU1: 2000, GPU2: 400, FIREWALL: 3000, FRAUD1: 20000, FRAUD2: 20000, MULTI: 20000}

ID = r'[A-Za-z0-9_-]{1,12}'
WORD = r'[a-z0-9]{1,10}'
DATE = r'[0-9]{4}-[0-9]{2}-[0-9]{2}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def rows_of(a, width, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('rows size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')
    return a


def trace(uid, args):
    name, ctor, methods, _ = CLASSES[uid]
    envelope(args, 2)
    ops, rows = args
    if type(ops) is not list or type(rows) is not list or not 1 <= len(ops) <= TRACE_MAX[uid] or len(ops) != len(rows):
        raise ValueError('trace shape')
    if ops[0] != name or type(rows[0]) is not list or len(rows[0]) != ctor: raise ValueError('initial constructor')
    for op, row in zip(ops[1:], rows[1:]):
        if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
            raise ValueError('method or arity')
    return ops, rows


def decimal(v, maximum):
    if type(v) is not str or re.fullmatch(r'0|[1-9][0-9]{0,15}', v) is None or int(v) > maximum: raise ValueError('decimal string')


def ip_text(v):
    if type(v) is not str or re.fullmatch(r'(0|[1-9][0-9]{0,2})(\.(0|[1-9][0-9]{0,2})){3}', v) is None: raise ValueError('ip shape')
    if any(int(p) > 255 for p in v.split('.')): raise ValueError('ip octet')


def validate_traits(traits, weighted):
    if type(traits) is not list or not 1 <= len(traits) <= 8: raise ValueError('traits size')
    names = set()
    for t in traits:
        if type(t) is not list or len(t) != 2: raise ValueError('trait shape')
        text(t[0], WORD, 10)
        if t[0] in names: raise ValueError('duplicate trait')
        names.add(t[0])
        if type(t[1]) is not list or not 1 <= len(t[1]) <= 50: raise ValueError('trait values size')
        seen = set()
        for v in t[1]:
            if weighted:
                if type(v) is not list or len(v) != 2: raise ValueError('weighted value shape')
                text(v[0], WORD, 10); integer(v[1], 1, 10**6); v = v[0]
            else: text(v, WORD, 10)
            if v in seen: raise ValueError('duplicate trait value')
            seen.add(v)


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid in CLASSES:
        ops, rows = trace(uid, args)
        if uid in (GPU1, GPU2):
            added = set()
            for op, r in zip(ops[1:], rows[1:]):
                if op == 'addCredit':
                    text(r[0], ID, 12); integer(r[1], 1, 10**6); integer(r[2], 0, 10**9); integer(r[3], r[2], 10**9)
                    if r[0] in added: raise ValueError('credit id reused')
                    added.add(r[0])
                elif op == 'revokeCredit': text(r[0], ID, 12); integer(r[1], 0, 10**9)
                elif op == 'consumeCredit': integer(r[0], 1, 10**6); integer(r[1], 0, 10**9)
                else: integer(r[0], 0, 10**9)
        elif uid == FIREWALL:
            rules = rows_of(rows[0][0], 2, 0, 1000)
            for action, target in rules:
                if action not in ('ALLOW', 'DENY'): raise ValueError('rule action')
                if type(target) is not str: raise ValueError('rule target')
                base, _, k = target.partition('/')
                ip_text(base)
                if '/' in target and re.fullmatch(r'0|[1-9][0-9]?', k) is None or (k and int(k) > 32): raise ValueError('prefix length')
            for r in rows[1:]: ip_text(r[0])
        elif uid in (FRAUD1, FRAUD2):
            for op, r in zip(ops[1:], rows[1:]):
                if op == 'processEvent':
                    e = r[0]
                    if type(e) is not list or len(e) != 5: raise ValueError('event shape')
                    text(e[0], r'[A-Z_]{1,20}', 20)
                    for f in e[1:]: text(f, r'[A-Za-z0-9 @.+-]{0,30}', 30)
        elif uid == MULTI:
            streams = rows[0][0]
            if type(streams) is not list or len(streams) > 2000: raise ValueError('streams')
            total = 0
            for s in streams: text(s, r'[A-Za-z0-9]{0,100000}', 100000); total += len(s)
            if total > 200000: raise ValueError('total stream length')
            for r in rows[1:]: integer(r[0], 0, 200000)
        return
    if uid in (ADS1, ADS2):
        envelope(args, 2 if uid == ADS1 else 4)
        for r in rows_of(args[0], 2, 0, 100000): decimal(r[0], 10**12); text(r[1], ID, 12)
        integer(args[1], 1, 100000)
        if uid == ADS2: integer(args[2], 0, 10**12); integer(args[3], args[2], 10**12)
    elif uid == RECT:
        envelope(args, 1)
        for r in rows_of(args[0], 3, 0, 100000): integer(r[0], 0, 1); integer(r[1], 1, 10**9); integer(r[2], 1, 10**9)
    elif uid in (NFT1, NFT2, NFT3):
        envelope(args, 3)
        validate_traits(args[0], uid == NFT2)
        integer(args[1], 0, 10000)
        needed = args[1] * len(args[0]) if uid != NFT3 else args[1]
        array(args[2], 0, 10**15, needed, needed)
        if uid == NFT3 and args[1] * len(args[0]) > 200000: raise ValueError('output budget')
    elif uid in (LOAN1, LOAN2):
        envelope(args, 2)
        parents = rows_of(args[0], 2, 0, 50000)
        child_of = {}
        for c, p in parents:
            text(c, ID, 12); text(p, ID, 12)
            if c in child_of or c == p: raise ValueError('parent relation')
            child_of[c] = p
        acyclic(child_of)
        loans = rows_of(args[1], 2 if uid == LOAN1 else 3, 0, 50000)
        ids = set()
        for r in loans:
            text(r[0], ID, 12); text(r[1], ID, 12)
            if r[0] in ids: raise ValueError('loan id reused')
            ids.add(r[0])
            if uid == LOAN2: integer(r[2], 0, 10**9)
    elif uid == SELLER:
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 2000: raise ValueError('records')
        for rec in args[0]:
            if type(rec) is not list or len(rec) > 20: raise ValueError('record size')
            for s in rec: text(s, WORD, 10)
    elif uid == AVG:
        envelope(args, 1)
        for r in rows_of(args[0], 2, 0, 100000):
            text(r[0], r'[A-Za-z]{1,12}', 12)
            if type(r[1]) is not str or re.fullmatch(r'-?(0|[1-9][0-9]{0,8})', r[1]) is None or r[1] == '-0': raise ValueError('score string')
    elif uid == IPO:
        envelope(args, 2)
        bids = rows_of(args[0], 4, 0, 50000)
        users = set()
        for b in bids:
            integer(b[0], 0, 10**9); integer(b[1], 1, 10**9); integer(b[2], 1, 10**9); integer(b[3], 0, 10**9)
            if b[0] in users: raise ValueError('user id reused')
            users.add(b[0])
        integer(args[1], 0, 10**12)
    elif uid == TREE:
        envelope(args, 1)
        rel = rows_of(args[0], 2, 0, 100000)
        parent = {}
        for c, p in rel:
            integer(c, 0, 10**9); integer(p, 0, 10**9)
            if c in parent or c == p: raise ValueError('relation')
            parent[c] = p
        acyclic(parent)
    elif uid in (PAY1, PAY2):
        envelope(args, 2)
        if type(args[0]) is not list or type(args[1]) is not list or len(args[0]) > 20000 or len(args[1]) > 20000: raise ValueError('records')
        for p in args[0]: text(p, ID + r',(0|[1-9][0-9]{0,8}),[A-Za-z0-9 :,_-]{0,60}', 90)
        seen = set()
        for i in args[1]:
            text(i, ID + r',(0|[1-9][0-9]{0,8}),' + DATE, 40)
            if i.split(',')[0] in seen: raise ValueError('invoice id reused')
            seen.add(i.split(',')[0])
    elif uid == TRANSPOSE:
        envelope(args, 2)
        m = args[0]
        if type(m) is not list or not 1 <= len(m) <= 700: raise ValueError('matrix')
        for r in m: array(r, -10**9, 10**9, len(m), len(m))
        integer(args[1], 1, 64)
    elif uid == PRISON:
        envelope(args, 4)
        integer(args[0], 1, 10**5); integer(args[1], 1, 10**5)
        array(args[2], 1, args[0], 0, args[0]); array(args[3], 1, args[1], 0, args[1])
        if len(set(args[2])) != len(args[2]) or len(set(args[3])) != len(args[3]): raise ValueError('distinct bars')
    elif uid == ISLAND:
        envelope(args, 1)
        g = args[0]
        if type(g) is not list or not 1 <= len(g) <= 1000 or type(g[0]) is not list or not 1 <= len(g[0]) <= 1000: raise ValueError('grid')
        if len(g) * len(g[0]) > 250000: raise ValueError('grid area')
        for r in g:
            if type(r) is not list or len(r) != len(g[0]) or any(c not in ('0', '1') for c in r): raise ValueError('grid row')
    elif uid == INCR:
        envelope(args, 1)
        array(args[0], -10**9, 10**9, 0, 100000)


def acyclic(parent):
    state = {}
    for start in parent:
        path, x = [], start
        while x in parent and x not in state:
            state[x] = 1; path.append(x); x = parent[x]
        if state.get(x) == 1: raise ValueError('cycle')
        for y in path: state[y] = 2


def n_combos(traits):
    total = 1
    for _, values in traits: total *= len(values)
    return total


# ----------------------------------------------------------------------------- references

def _ads(impressions, k, lo=None, hi=None):
    names = []
    for ts, ad in impressions:
        if lo is None or lo <= int(ts) <= hi: names.append(ad)
    distinct = sorted(set(names), key=lambda a: (-names.count(a), a))
    return distinct[:k]


def _rect(operations):
    saved, out = [], []
    for t, a, b in operations:
        if t == 0: saved.append((a, b))
        else: out.append(all((x <= a and y <= b) or (y <= a and x <= b) for x, y in saved))
    return out


def _gpu1(ops, rows):
    grants, revoked, out = {}, {}, [None]
    for op, r in zip(ops[1:], rows[1:]):
        if op == 'addCredit': grants[r[0]] = (r[1], r[2], r[3]); out.append(None)
        elif op == 'revokeCredit':
            ok = r[0] in grants and r[0] not in revoked
            if ok: revoked[r[0]] = r[1]
            out.append(ok)
        else:
            t = r[0]; total = 0
            for cid, (amount, s, e) in grants.items():
                if s <= t <= e and not (cid in revoked and revoked[cid] <= t): total += amount
            out.append(total)
    return out


def _gpu2_replay(events, until_time, stop_index=None):
    """Literal unit-by-unit replay. events: list of (arrival, kind, payload). Returns (remaining dict, success map)."""
    grants = [e for e in events if e[1] == 'add' and e[2][2] <= until_time]
    consumes = [e for e in events if e[1] == 'use' and e[2][1] <= until_time]
    if stop_index is not None:
        own_time = [e for e in events if e[0] == stop_index][0][2][1]
        consumes = [e for e in consumes if e[2][1] < own_time or (e[2][1] == own_time and e[0] <= stop_index)]
    remaining = {e[2][0]: e[2][1] for e in grants}
    info = {e[2][0]: e[2] for e in grants}
    timeline = sorted([(e[2][2], 0, e[0], e) for e in grants] + [(e[2][1], 1, e[0], e) for e in consumes])
    result = {}
    for _, kind, arrival, e in timeline:
        if kind == 0: continue  # grant amounts are pre-loaded; activity is decided by its window
        amount, c = e[2]
        active = [cid for cid in remaining if info[cid][2] <= c <= info[cid][3] and remaining[cid] > 0]
        if sum(remaining[cid] for cid in active) < amount: result[arrival] = False; continue
        for _ in range(amount):
            best = min((cid for cid in active if remaining[cid] > 0), key=lambda cid: (info[cid][3], info[cid][2], cid))
            remaining[best] -= 1
        result[arrival] = True
    return remaining, info, result


def _gpu2(ops, rows):
    events, out = [], [None]
    for i, (op, r) in enumerate(zip(ops[1:], rows[1:])):
        if op == 'addCredit': events.append((i, 'add', tuple(r))); out.append(None)
        elif op == 'consumeCredit':
            events.append((i, 'use', tuple(r)))
            out.append(_gpu2_replay(events, r[1], i)[2][i])
        else:
            t = r[0]
            remaining, info, _ = _gpu2_replay(events, t)
            out.append(sum(v for cid, v in remaining.items() if info[cid][2] <= t <= info[cid][3]))
    return out


def _nft_plain(traits, n, randoms):
    out, k = [], 0
    for _ in range(n):
        nft = []
        for _, values in traits: nft.append(values[randoms[k] % len(values)]); k += 1
        out.append(nft)
    return out


def _nft_weighted(traits, n, randoms):
    out, k = [], 0
    for _ in range(n):
        nft = []
        for _, values in traits:
            expanded = [v for v, w in values for _ in range(w)] if sum(w for _, w in values) <= 64 else None
            total = sum(w for _, w in values); r = randoms[k] % total; k += 1
            if expanded is not None: nft.append(expanded[r]); continue
            acc = 0
            for v, w in values:
                acc += w
                if r < acc: nft.append(v); break
        out.append(nft)
    return out


def _nft_unique(traits, n, randoms):
    total = n_combos(traits)
    if n > total: return []
    if total > 200000: raise ValueError('reference budget')
    combos = [list(c) for c in product(*[values for _, values in traits])]
    for i in range(n):
        j = i + randoms[i] % (total - i)
        combos[i], combos[j] = combos[j], combos[i]
    return combos[:n]


def _top(parents, company):
    rel = dict((c, p) for c, p in parents)
    while company in rel: company = rel[company]
    return company


def _loans1(parents, loans):
    groups = {}
    for loan_id, company in loans: groups.setdefault(_top(parents, company), []).append(loan_id)
    return [[top, sorted(ids)] for top, ids in sorted(groups.items())]


def _loans2(parents, loans):
    totals = {}
    for _, company, amount in loans:
        top = _top(parents, company); totals[top] = totals.get(top, 0) + amount
    return [[top, total] for top, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))]


def _seller(records):
    stores = sorted({s for rec in records for s in rec})
    out = []
    for s in stores:
        counts = {t: sum(1 for rec in records if s in rec and t in rec) for t in stores if t != s}
        best = max(counts.values(), default=0)
        out.append([s, sorted(t for t, c in counts.items() if c == best and c > 0)])
    return out


def _avg(scores):
    if not scores: return 0
    names = {name for name, _ in scores}
    best = max(Fraction(sum(int(s) for n, s in scores if n == name), sum(1 for n, _ in scores if n == name)) for name in names)
    return best.numerator // best.denominator


def _bits(ip):
    return ''.join(format(int(p), '08b') for p in ip.split('.'))


def _firewall(ops, rows):
    rules, out = rows[0][0], [None]
    for r in rows[1:]:
        verdict = False
        for action, target in rules:
            base, _, k = target.partition('/')
            length = int(k) if k else 32
            if _bits(base)[:length] == _bits(r[0])[:length]: verdict = action == 'ALLOW'; break
        out.append(verdict)
    return out


def _ipo(bids, total):
    order = sorted(range(len(bids)), key=lambda i: (-bids[i][2], bids[i][3], i))
    got = {b[0]: 0 for b in bids}
    remaining = total
    pos = 0
    while pos < len(order) and remaining > 0:
        price = bids[order[pos]][2]
        level = []
        while pos < len(order) and bids[order[pos]][2] == price: level.append(order[pos]); pos += 1
        if remaining > 10**6 and sum(bids[i][1] for i in level) > remaining: raise ValueError('reference budget')
        progress = True
        while remaining > 0 and progress:  # literal one-share round robin
            progress = False
            for i in level:
                if remaining > 0 and got[bids[i][0]] < bids[i][1]: got[bids[i][0]] += 1; remaining -= 1; progress = True
    return sorted(u for u, g in got.items() if g == 0)


def _tree(relations):
    if not relations: return -1
    parent = {c: p for c, p in relations}
    nodes = set(parent) | set(parent.values())
    size = {}
    for x in nodes:
        r = x
        while r in parent: r = parent[r]
        size[r] = size.get(r, 0) + 1
    return min(size, key=lambda r: (-size[r], r))


def _fraud(ops, rows, shared):
    events, out = [], [None]
    for op, r in zip(ops[1:], rows[1:]):
        if op == 'processEvent': events.append(r[0]); out.append(None); continue
        pairs = [(f, e[f]) for e in events for f in range(1, 5) if e[f] != '']
        if op == 'getDistinctPIICount': out.append(len(set(pairs)))
        else: out.append(sum(1 for p in set(pairs) if sum(1 for e in events if e[p[0]] == p[1]) >= 2))
    return out


REF = re.compile(r'paying off:([A-Za-z0-9_-]+)')


def _pay(payments, invoices, fallback):
    inv = [i.split(',') for i in invoices]
    used, out = set(), []
    for p in payments:
        pid, amount, memo = p.split(',', 2)
        m = REF.search(memo)
        target = m.group(1) if m else None
        match = None
        if target is not None and any(i[0] == target for i in inv) and (not fallback or target not in used): match = target
        elif fallback:
            cands = [i for i in inv if i[0] not in used and int(i[1]) == int(amount)]
            if cands: match = min(cands, key=lambda i: (i[2], i[0]))[0]
        if fallback and match is not None: used.add(match)
        out.append([pid, match])
    return out


def _prison(n, m, h, v):
    def widest(count, removed):
        present = [0] + [b for b in range(1, count + 1) if b not in set(removed)] + [count + 1]
        return max(b - a for a, b in zip(present, present[1:]))
    if n > 2000 or m > 2000: raise ValueError('reference budget')
    return widest(n, h) * widest(m, v)


def _island(grid):
    rows, cols = len(grid), len(grid[0])
    parent = {}

    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == '1']
    for x in cells: parent[x] = x
    shared = []
    for r, c in cells:
        for nr, nc in ((r + 1, c), (r, c + 1)):
            if (nr, nc) in parent: parent[find((r, c))] = find((nr, nc)); shared.append((r, c))
    per = {}
    for x in cells: per[find(x)] = per.get(find(x), 0) + 4
    for x in shared: per[find(x)] -= 2
    return max(per.values(), default=0)


def _incr(arr):
    n = len(arr)
    if n > 14 or (arr and max(arr) - min(arr) > 60): raise ValueError('reference budget')
    span = (max(arr) - min(arr) + 1) if arr else 1
    best = None
    for mask in range(1 << n):
        if mask & (mask >> 1): continue
        for x in range(span + 1):
            if best is not None and x >= best: break
            b = [a + (x if mask >> i & 1 else 0) for i, a in enumerate(arr)]
            if all(p <= q for p, q in zip(b, b[1:])): best = x; break
    return -1 if best is None else best


def _multi(ops, rows):
    data, pos, out = ''.join(rows[0][0]), 0, [None]
    for r in rows[1:]: out.append(data[pos:pos + r[0]]); pos = min(len(data), pos + r[0])
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == ADS1: return _ads(args[0], args[1])
    if uid == ADS2: return _ads(args[0], args[1], args[2], args[3])
    if uid == RECT: return _rect(args[0])
    if uid == GPU1: return _gpu1(*args)
    if uid == GPU2: return _gpu2(*args)
    if uid == NFT1: return _nft_plain(*args)
    if uid == NFT2: return _nft_weighted(*args)
    if uid == NFT3: return _nft_unique(*args)
    if uid == LOAN1: return _loans1(*args)
    if uid == LOAN2: return _loans2(*args)
    if uid == SELLER: return _seller(args[0])
    if uid == AVG: return _avg(args[0])
    if uid == FIREWALL: return _firewall(*args)
    if uid == IPO: return _ipo(*args)
    if uid == TREE: return _tree(args[0])
    if uid == FRAUD1: return _fraud(*args, False)
    if uid == FRAUD2: return _fraud(*args, True)
    if uid == PAY1: return _pay(*args, False)
    if uid == PAY2: return _pay(*args, True)
    if uid == TRANSPOSE: return [list(col) for col in zip(*args[0])]
    if uid == PRISON: return _prison(*args)
    if uid == ISLAND: return _island(args[0])
    if uid == INCR: return _incr(args[0])
    if uid == MULTI: return _multi(*args)
    raise ValueError('unknown identity')
