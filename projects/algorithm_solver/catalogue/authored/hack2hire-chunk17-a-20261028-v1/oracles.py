"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (index-permutation
replay, subset enumeration, report scans with exact fractions, unit-step simulation, recursive descent,
permutation enumeration, whole-history replay, repeated selection, all-key comparison, direct window
counts, suffix scans, bucket insertion, timestamp lists, regular-expression parsing, Bellman-Ford style
relaxation and list rescans) and refuse inputs above a small budget.
"""
from fractions import Fraction
from itertools import combinations, permutations
import re

H = 'hack2hire:'
RPA = H + '68ac67eb1bf7d2097f647efe'
RDG = H + '6770783f366afdc1233e4ff8'
RSQ = H + '69c1e01c21f6ab4226964e08'
SSS = H + '6a7fdd1bd713d873ca7adf14'
SEX = H + '677b092f78175fce2ecdfc0e'
SLP = H + '6760ef452f1ff3d3c88bf915'
SMP = H + '68f29e6ef567e950995157ea'
STR = H + '68dc6c86dd5418be11109b14'
TOK = H + '6941b7e8b9d646bec48c68bc'
SMT = H + '68ac3bd61bf7d2097f647eec'
SMC = H + '6a51443a665efda9311f60c6'
TL1 = H + '69ab8d9d4b133b6a8f3a699f'
TL2 = H + '69ab90f64b133b6a8f3a69a3'
THA = H + '6a97291f0ca9cc4e1c789d82'
TP1 = H + '68c9aaf3212d48d6e0f5977c'
TP2 = H + '68c9ac13212d48d6e0f5977d'
TTL = H + '6a4d6a5560d5cca82da2fe23'
URL = H + '68e02ab4846fd9cdeb438e4e'

IDS = (RPA, RDG, RSQ, SSS, SEX, SLP, SMP, STR, TOK, SMT, SMC, TL1, TL2, THA, TP1, TP2, TTL, URL)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    RSQ: ('RoadwaySpeedTracker', 0, {'addReport': 3, 'removeReport': 3, 'getAverageSpeed': 1}, ('addReport',)),
    STR: ('StockTracker', 0, {'recordTrade': 2, 'getRankedStocks': 0}, ('recordTrade',)),
    TTL: ('MutexTaskLock', 0, {'acquire': 2, 'release': 1}, ()),
}

# uids whose results contain floats: JavaScript cannot tag an integral float, so JavaScript float results compare by numeric value
FLOATS = (RSQ,)


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


def rpa_domain(nums, k, ints):
    intlist(nums, -10**9, 10**9, 1); integer(k, 1, len(nums))
    if len(nums) % k: raise ValueError('k must divide n')
    intlist(ints, 0, 10**9, len(nums) - 1, len(nums) - 1)


def sex_domain(e):
    """Iterative grammar check: operands are variables or groups; unary '-' only at a group start."""
    text(e, r'[a-z()+-]+', 100000)
    depth, expect, start, i = 0, True, True, 0
    while i < len(e):
        c = e[i]
        if expect:
            if c == '-' and start: start = False; i += 1; continue
            start = False
            if c == '(':
                depth += 1; start = True; i += 1; continue
            if not c.isalpha(): raise ValueError('operand expected')
            while i < len(e) and e[i].isalpha(): i += 1
            expect = False
        else:
            if c in '+-': expect = True
            elif c == ')':
                depth -= 1
                if depth < 0: raise ValueError('unbalanced')
            else: raise ValueError('operator expected')
            i += 1
    if expect or depth: raise ValueError('incomplete expression')


def str_domain(args):
    calls = trace(STR, args); out = 0; names = set()
    for op, row in calls:
        if op == 'recordTrade':
            text(row[0], r'[A-Z]{1,10}', 10); integer(row[1], 1, 10**6); names.add(row[0])
        else: out += len(names)
    if out > 2000000: raise ValueError('ranking output bound')


def tok_domain(t, dictionary):
    text(t, r'[a-z ]*', 100000); sized(dictionary, 1, 10000); keys = set(); total = 0
    for entry in dictionary:
        text(entry, r'[a-z]{1,20}:[0-9]{1,9}', 30)
        key = entry.split(':')[0]
        if key in keys: raise ValueError('duplicate key')
        keys.add(key); total += len(key)


LOG = r'([A-Za-z0-9]{1,8}):([A-Za-z0-9]{1,8}):(' + NUM + r'):[ -~]{0,30}'


def log_domain(logs):
    sized(logs, 0, 100000)
    for entry in logs:
        text(entry, LOG, 60)
        integer(int(entry.split(':')[2]), 0, 10**9)


def tp_table(teleporters, last):
    sized(teleporters, 0, max(0, last - 1)); table = {}
    for t in teleporters:
        text(t, '(' + NUM + '),(' + NUM + ')', 13)
        a, b = map(int, t.split(','))
        integer(a, 1, last - 1); integer(b, 0, last)
        if a == b or a in table: raise ValueError('teleporter rule')
        table[a] = b
    return table


def ttl_domain(args):
    calls = trace(TTL, args); seen = set(); running = set(); waiting = []; kind = None
    for op, row in calls:  # tracks admission with the reference rule so that release is only called for running jobs
        if op == 'acquire':
            integer(row[0], 0, 10**9)
            if type(row[1]) is not str or row[1] not in ('gen', 'score'): raise ValueError('job type')
            if row[0] in seen: raise ValueError('job ids must be distinct')
            seen.add(row[0])
            if not waiting and (not running or kind == row[1]): running.add(row[0]); kind = row[1]
            else: waiting.append(row)
        else:
            integer(row[0], 0, 10**9)
            if row[0] not in running: raise ValueError('release of a job that is not running')
            running.discard(row[0])
            if not running and waiting:
                kind = waiting[0][1]
                while waiting and waiting[0][1] == kind: running.add(waiting.pop(0)[0])


def validate_domain(uid, args):
    if uid == RPA: envelope(args, 3); rpa_domain(*args)
    elif uid == RDG:
        envelope(args, 3); intlist(args[0], 1, 10**9, 1); integer(args[1], 1, len(args[0])); integer(args[2], 1, 10**9)
    elif uid == RSQ:
        for op, row in trace(RSQ, args):
            if op == 'getAverageSpeed': integer(row[0], 0, 10**6)
            else:
                integer(row[0], 0, 10**6 - 1); integer(row[1], row[0] + 1, 10**6); integer(row[2], 1, 10**6)
    elif uid == SSS:
        envelope(args, 2); integer(args[0], 1, 10**9); intlist(args[1], 0, 10**9)
        if len(set(args[1])) != len(args[1]): raise ValueError('positions must be distinct')
    elif uid == SEX: envelope(args, 1); sex_domain(args[0])
    elif uid == SLP:
        envelope(args, 1); text(args[0], r'[a-z]{1,100000}', 100000)
        if args[0] != args[0][::-1]: raise ValueError('s must be a palindrome')
    elif uid == SMP:
        envelope(args, 3); intlist(args[0], 0, 10**6, 1); sized(args[1], 1, 200000)
        if len(args[0]) * len(args[1]) > 200000: raise ValueError('grid size')
        for day in args[1]: intlist(day, 0, 1000, len(args[0]), len(args[0]))
        integer(args[2], 0, 1000)
    elif uid == STR: str_domain(args)
    elif uid == TOK: envelope(args, 2); tok_domain(*args)
    elif uid == SMT:
        envelope(args, 3); intlist(args[0], -10**9, 10**9, 1); integer(args[1], 0, len(args[0]) - 1); integer(args[2], 1, len(args[0]))
    elif uid == SMC: envelope(args, 2); intlist(args[0], -10**9, 10**9, 1); intlist(args[1], 0, len(args[0]) - 1)
    elif uid in (TL1, TL2): envelope(args, 1); log_domain(args[0])
    elif uid == THA:
        envelope(args, 3); intlist(args[0], 0, 10**4, 1); integer(args[1], 1, 10**5); integer(args[2], 0, 10**4)
    elif uid == TP1:
        envelope(args, 4); integer(args[1], 1, 12); integer(args[3], 1, 10**5); integer(args[2], 0, args[3] - 1); tp_table(args[0], args[3])
    elif uid == TP2:
        envelope(args, 3); integer(args[1], 1, 12); integer(args[2], 1, 10**5); tp_table(args[0], args[2])
    elif uid == TTL: ttl_domain(args)
    elif uid == URL: envelope(args, 1); text(args[0], r'[A-Za-z0-9/:.~=&?-]*', 100000)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_rpa(nums, k, ints):
    n = len(nums); order = list(range(n)); swaps = []
    for t, i in enumerate(range(n - 1, 0, -1)): swaps.append((i, ints[t] % (i + 1)))
    for i, j in swaps: order[i], order[j] = order[j], order[i]
    values = [nums[p] for p in order]; size = n // k
    return [values[s * size:(s + 1) * size] for s in range(k)]


def ref_rdg(prices, k, threshold):
    n = len(prices)
    for r in range(n + 1):
        for removed in combinations(range(n), r):
            gone = set(removed); rest = sorted((prices[i] for i in range(n) if i not in gone), reverse=True)
            if len(rest) < k or sum(rest[:k]) <= threshold: return r
    raise AssertionError('unreachable')


def ref_rsq(calls):
    live, out = [], [None]
    for op, row in calls:
        if op == 'addReport': live.append(tuple(row)); out.append(None)
        elif op == 'removeReport':
            if tuple(row) in live: live.remove(tuple(row)); out.append(True)
            else: out.append(False)
        else:
            speeds = [s for a, b, s in live if a <= row[0] < b]
            out.append(float(Fraction(sum(speeds), len(speeds))) if speeds else -1.0)
    return out


def ref_sss(finish, scooters):
    at, battery, walked = set(scooters), 0, 0
    for p in range(finish):
        if p in at: battery = 10
        if battery: battery -= 1
        else: walked += 1
    return walked


def ref_sex(e):
    pos = [0]

    def group(sign):  # expression until ')' or end, as a list of (sign, name)
        terms, first = [], True
        while pos[0] < len(e) and e[pos[0]] != ')':
            s = 1
            if e[pos[0]] in '+-':
                s = -1 if e[pos[0]] == '-' else 1; pos[0] += 1
            elif not first: raise AssertionError('operator expected')
            first = False
            if e[pos[0]] == '(':
                pos[0] += 1; terms += group(sign * s); pos[0] += 1
            else:
                m = re.match(r'[a-z]+', e[pos[0]:]); terms.append((sign * s, m.group())); pos[0] += m.end()
        return terms
    terms = group(1)
    out = ''.join(('-' if s < 0 else '+') + name for s, name in terms)
    return out[1:] if out[0] == '+' else out


def ref_slp(s):
    return min(''.join(p) for p in set(permutations(s)) if p == p[::-1])


def ref_smp(base, snow, melt):
    out = []
    for d in range(len(snow)):
        acc = [0] * len(base)
        for day in snow[:d + 1]:
            acc = [max(0, a + f - melt) for a, f in zip(acc, day)]
        h = [b + a for b, a in zip(base, acc)]
        out.append(sum(max(0, y - x) for x, y in zip(h, h[1:])))
    return out


def ref_str(calls):
    total, out = {}, [None]
    for op, row in calls:
        if op == 'recordTrade': total[row[0]] = total.get(row[0], 0) + row[1]; out.append(None)
        else:
            left, rank = dict(total), []
            while left:
                best = None
                for name, q in left.items():
                    if best is None or q > left[best] or (q == left[best] and name < best): best = name
                rank.append(best); del left[best]
            out.append(rank)
    return out


def ref_tok(t, dictionary):
    pairs = [entry.split(':') for entry in dictionary]; out, i = [], 0
    while i < len(t):
        best = None
        for key, ident in pairs:
            if t[i:i + len(key)] == key and (best is None or len(key) > len(best[0])): best = (key, ident)
        if best: out.append(best[1]); i += len(best[0])
        else: out.append(t[i]); i += 1
    return out


def ref_smt(nums, target_index, w):
    target = nums[target_index]
    counts = [sum(1 for v in nums[i:i + w] if v == target) for i in range(len(nums) - w + 1)]
    return counts.index(max(counts))


def ref_smc(nums, query):
    return [nums[q:].count(max(nums[q:])) for q in query]


def parse_log(entry):
    pid, tid, ts, content = entry.split(':', 3)
    return pid, tid, int(ts), content


def ref_tl1(logs):
    buckets = {}
    for entry in logs:
        pid, tid, ts, _ = parse_log(entry)
        rows = buckets.setdefault((pid, tid), [])
        k = len(rows)
        while k > 0 and rows[k - 1][0] > ts: k -= 1
        rows.insert(k, (ts, entry))
    return [entry for key in sorted(buckets) for _, entry in buckets[key]]


def ref_tl2(logs):
    stamps = {}
    for entry in logs:
        pid, tid, ts, _ = parse_log(entry)
        stamps.setdefault((pid, tid), []).append(ts)
    return ['%s:%s:%d:%d:%d' % (p, t, len(v), min(v), max(v)) for (p, t), v in sorted(stamps.items())]


def ref_tha(calls, k, threshold):
    return sum(1 for i in range(k - 1, len(calls)) if sum(calls[i - k + 1:i + 1]) >= threshold * k)


def table(teleporters):
    return {int(m.group(1)): int(m.group(2)) for m in (re.fullmatch(r'(\d+),(\d+)', t) for t in teleporters)}


def turn(tab, square, roll, last):
    land = square + roll
    return last if land >= last else tab.get(land, land)


def ref_tp1(teleporters, die, current, last):
    tab = table(teleporters)
    return sorted({turn(tab, current, r, last) for r in range(1, die + 1)})


def ref_tp2(teleporters, die, last):
    tab = table(teleporters); inf = float('inf')
    dist = [inf] * (last + 1); dist[0] = 0; changed = True
    while changed:
        changed = False
        for sq in range(last):
            if dist[sq] == inf: continue
            for r in range(1, die + 1):
                nxt = turn(tab, sq, r, last)
                if dist[sq] + 1 < dist[nxt]: dist[nxt] = dist[sq] + 1; changed = True
    return -1 if dist[last] == inf else dist[last]


def ref_ttl(calls):
    running, waiting, out = [], [], [None]
    for op, row in calls:
        if op == 'acquire':
            kinds = {k for _, k in running}
            if not waiting and kinds <= {row[1]}: running.append((row[0], row[1])); out.append(True)
            else: waiting.append((row[0], row[1])); out.append(False)
        else:
            running = [r for r in running if r[0] != row[0]]; admitted = []
            if not running and waiting:
                head = waiting[0][1]
                while waiting and waiting[0][1] == head:
                    running.append(waiting[0]); admitted.append(waiting[0][0]); waiting = waiting[1:]
            out.append(admitted)
    return out


def ref_url(url):
    if '?' not in url: return {}
    values = {}
    for m in re.finditer(r'(?:^|&)([^&=]*)(?:=([^&]*))?(?=&|$)', url.partition('?')[2]):
        key, value = m.group(1), m.group(2) or ''
        if key: values.setdefault(key, []).append(value)
    return {k: v[0] if len(v) == 1 else v for k, v in values.items()}


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid == RSQ: return ref_rsq(calls)
        if uid == STR: return ref_str(calls)
        return ref_ttl(calls)
    if uid == RPA:
        budget(len(args[0]) <= 2000); return ref_rpa(*args)
    if uid == RDG:
        budget(len(args[0]) <= 9); return ref_rdg(*args)
    if uid == SSS:
        budget(args[0] <= 3000); return ref_sss(*args)
    if uid == SEX:
        budget(len(args[0]) <= 300); return ref_sex(args[0])
    if uid == SLP:
        budget(len(args[0]) <= 8); return ref_slp(args[0])
    if uid == SMP:
        budget(len(args[0]) * len(args[1]) ** 2 <= 20000); return ref_smp(*args)
    if uid == TOK:
        budget(len(args[0]) * len(args[1]) <= 20000); return ref_tok(*args)
    if uid == SMT:
        budget(len(args[0]) <= 500); return ref_smt(*args)
    if uid == SMC:
        budget(len(args[0]) * (len(args[1]) + 1) <= 20000); return ref_smc(*args)
    if uid == TL1:
        budget(len(args[0]) <= 500); return ref_tl1(args[0])
    if uid == TL2:
        budget(len(args[0]) <= 500); return ref_tl2(args[0])
    if uid == THA:
        budget(len(args[0]) <= 500); return ref_tha(*args)
    if uid == TP1: return ref_tp1(*args)
    if uid == TP2:
        budget(args[2] <= 200); return ref_tp2(*args)
    budget(len(args[0]) <= 2000); return ref_url(args[0])
