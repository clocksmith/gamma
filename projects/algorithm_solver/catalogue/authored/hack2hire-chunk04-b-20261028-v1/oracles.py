"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (linear scans, literal
simulation, exhaustive enumeration, fixed-point evaluation, matrix powers, Miller-Rabin, regexes).
"""
from collections import deque
from itertools import product
import re

H = 'hack2hire:'
BSV = H + '67955715010c9ed2f849b1f7'
BTC = H + '68f012a4742c37be9dc830dd'
TRANS = H + '6a222b9c981072682a6f1e5a'
CAKE = H + '67c7604e6c89e288437c3024'
EQ1 = H + '68811ae3f96758aa78e1d687'
EQ2 = H + '68811dddf96758aa78e1d688'
EQ3 = H + '68813e86f96758aa78e1d69b'
WAIT = H + '6796f907b10bc587828f27b2'
ELEV = H + '690cf5190a0bc710235894b8'
CHAT1 = H + '6a579fe2665efda9311f9375'
CHAT2 = H + '6a579fe4665efda9311f9376'
CHAT3 = H + '6a579fe5665efda9311f9377'
PWD = H + '67cd24763363b83a81fc99af'
CPRIME = H + '68fd47ba47bea664c0bba33c'
ALLOC = H + '6a1f2f7c8b879849ebc10f9a'
COINS = H + '6a4ffdfb665efda9311f57f2'
COLLATZ = H + '68d833b5ae12841706c1fc58'
HOUSES = H + '6818d209aa9eb23a3dba07f0'
LOAD = H + '69753e2817272b5c868d5eb3'
BED = H + '69e8f141fbaf3da641828530'

IDS = (BSV, BTC, TRANS, CAKE, EQ1, EQ2, EQ3, WAIT, ELEV, CHAT1, CHAT2, CHAT3, PWD, CPRIME, ALLOC, COINS, COLLATZ,
       HOUSES, LOAD, BED)

_CHAT_L1 = {'recordEvent': 3, 'getUserCount': 2}
_CHAT_L2 = {**_CHAT_L1, 'getChatCount': 2}
_CHAT_L3 = {**_CHAT_L2, 'getChatUserCount': 2}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    CHAT1: ('ChatEventAggregator', 1, _CHAT_L1, ('recordEvent',)),
    CHAT2: ('ChatEventAggregator', 1, _CHAT_L2, ('recordEvent',)),
    CHAT3: ('ChatEventAggregator', 1, _CHAT_L3, ('recordEvent',)),
}
SAFE = 2**53 - 1
MOD = 1000000007
DIGITS = r'0|[1-9][0-9]{0,9}'
EQ_VALUE_CAP = 10**15  # with <= 8 terms every left-to-right partial sum stays below 2**53
EQ_NAME = r'[A-Za-z][A-Za-z0-9_]{0,9}'
EQ_LITERAL = r'0|[1-9][0-9]{0,5}'
RULE_COST = {'LIGHT': 0, 'STANDARD': 2, 'HEAVY': 5}
BURST_SECONDS = 60
BURST_BONUS = 3


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


def rows_of(a, width, maximum):
    if type(a) is not list or len(a) > maximum: raise ValueError('row list size')
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


def eq_parse(uid, arr):
    """-> (target, {name: [(sign, token)]}); validates the inferred assignment grammar."""
    if type(arr) is not list or not 1 <= len(arr) <= 20001: raise ValueError('arr size')
    text(arr[0], EQ_NAME, 10)
    defs = {}
    signs = ('+',) if uid == EQ1 else ('+', '-')
    for line in arr[1:]:
        if type(line) is not str or len(line) > 120: raise ValueError('assignment string')
        parts = line.split(' ')
        if len(parts) < 3 or parts[1] != '=' or len(parts) % 2 == 0: raise ValueError('assignment shape')
        text(parts[0], EQ_NAME, 10)
        if parts[0] in defs: raise ValueError('variable assigned twice')
        terms = [('+', parts[2])] + [(parts[i], parts[i + 1]) for i in range(3, len(parts), 2)]
        if len(terms) > 8: raise ValueError('at most 8 terms')
        for sign, tok in terms:
            if sign not in signs: raise ValueError('operator domain')
            if re.fullmatch(EQ_LITERAL, tok) is None and re.fullmatch(EQ_NAME, tok) is None: raise ValueError('operand domain')
        defs[parts[0]] = terms
    return arr[0], defs


def eq_values(defs):
    """Fixed-point evaluation: repeatedly evaluate every assignment whose operands are all known (no DFS)."""
    known, changed = {}, True
    while changed:
        changed = False
        for name, terms in defs.items():
            if name in known: continue
            total = 0
            for sign, tok in terms:
                if tok[0].isdigit(): v = int(tok)
                elif tok in known: v = known[tok]
                else: break
                total = total + v if sign == '+' else total - v
            else:
                known[name] = total; changed = True
    return known


def chat_domain(uid, args):
    ops, rows = trace(uid, args, 30001)
    integer(rows[0][0], 1, 10**9)
    last, per_user = 0, {}
    for op, row in zip(ops[1:], rows[1:]):
        integer(row[0], 0, 10**9)
        if row[0] < last: raise ValueError('call timestamps non-decreasing')
        last = row[0]
        for v in row[1:]: text(v, r'[a-z0-9]{1,8}', 8)
        if op == 'recordEvent':
            if row[0] <= per_user.get(row[1], -1): raise ValueError('per-user event timestamps strictly increasing')
            per_user[row[1]] = row[0]


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == BSV:
        envelope(args, 2)
        array(args[0], -10**9, 10**9, 0, 100000); integer(args[1], -10**9, 10**9)
        if any(a > b for a, b in zip(args[0], args[0][1:])): raise ValueError('sorted non-decreasing')
    elif uid == BTC:
        envelope(args, 1)
        text(args[0], r'[A-Za-z]*', 100000)
    elif uid == TRANS:
        envelope(args, 1)
        rows_of(args[0], 3, 100000)
        seen = set()
        for ts, user, res in args[0]:
            text(ts, DIGITS, 10); text(user, r'[a-z0-9_]{1,12}', 12); text(res, r'[A-Za-z0-9/_.-]{1,30}', 30)
            if res in ('START', 'END'): raise ValueError('reserved resource name')
            if (user, int(ts)) in seen: raise ValueError('per-user timestamps distinct')
            seen.add((user, int(ts)))
            if int(ts) > SAFE: raise ValueError('timestamp range')
    elif uid == CAKE:
        envelope(args, 2)
        array(args[0], 0, 10**9, 3, 3)
        rows_of(args[1], 3, 100000)
        for o in args[1]: array(o, 0, 10**9, 3, 3)
    elif uid in (EQ1, EQ2, EQ3):
        envelope(args, 1)
        target, defs = eq_parse(uid, args[0])
        if sum(len(t) for t in defs.values()) > 100000: raise ValueError('term budget')
        if len(defs) > 400: values = eq_values_dfs_free_budget(defs)
        else: values = eq_values(defs)
        if uid != EQ3:
            if len(values) != len(defs) or target not in defs: raise ValueError('levels 1-2: every variable defined, acyclic, target assigned')
        for name, terms in defs.items():
            if name not in values: continue
            if abs(values[name]) > EQ_VALUE_CAP: raise ValueError('value magnitude')
            for sign, tok in terms:
                v = int(tok) if tok[0].isdigit() else values[tok]
                if abs(v) > EQ_VALUE_CAP: raise ValueError('operand magnitude')
    elif uid == WAIT:
        envelope(args, 1)
        array(args[0], 1, 10**4, 0, 100000)
    elif uid == ELEV:
        envelope(args, 2)
        rows_of(args[0], 2, 100000)
        for f, s in args[0]:
            text(f, r'0|[1-9][0-9]{0,8}', 9); text(s, r'up|down|idle', 4)
        if type(args[1]) is not list or len(args[1]) != 2: raise ValueError('request shape')
        text(args[1][0], r'0|[1-9][0-9]{0,8}', 9); text(args[1][1], r'up|down', 4)
    elif uid in (CHAT1, CHAT2, CHAT3):
        chat_domain(uid, args)
    elif uid == PWD:
        envelope(args, 2)
        strlist(args[0], r'[a-z]{1,100000}', 0, 10000, 100000); strlist(args[1], r'[a-z]{1,100000}', 0, 10000, 100000)
        if len(args[0]) != len(args[1]): raise ValueError('paired lists')
        if sum(map(len, args[0])) + sum(map(len, args[1])) > 400000: raise ValueError('text budget')
    elif uid == CPRIME:
        envelope(args, 1)
        integer(args[0], 1, 10**9)
    elif uid == ALLOC:
        envelope(args, 2)
        integer(args[0], 1, 2000)
        rows_of(args[1], 3, 2000)
        for kind, start, num in args[1]:
            text(kind, r'store|free', 5); text(start, DIGITS, 4); text(num, DIGITS, 4)
            if not int(start) < args[0] or not 1 <= int(num) <= args[0]: raise ValueError('request range')
    elif uid == COINS:
        envelope(args, 3)
        integer(args[0], 0, 10**9)
        array(args[1], 0, 10**4, 1, 700); array(args[2], 0, 10**9, 1, 700)
        if len(args[1]) != len(args[2]): raise ValueError('paired arrays')
    elif uid == COLLATZ:
        envelope(args, 1)
        integer(args[0], 1, 10**7)
    elif uid == HOUSES:
        envelope(args, 4)
        integer(args[0], 1, 10**9); integer(args[1], 1, 10**9)
        integer(args[2], 0, args[1] - 1); integer(args[3], 0, args[1] - 1)
    elif uid == LOAD:
        envelope(args, 2)
        rows_of(args[0], 2, 1000)
        ids = set()
        for sid, base in args[0]:
            text(sid, r'[a-z0-9-]{1,12}', 12); integer(base, 0, 10**6)
            if sid in ids: raise ValueError('unique server ids')
            ids.add(sid)
        rows_of(args[1], 3, 100000)
        for t, sid, rule in args[1]:
            integer(t, 0, 86399); text(sid, r'[a-z0-9-]{1,12}', 12); text(rule, r'LIGHT|STANDARD|HEAVY', 8)
    elif uid == BED:
        envelope(args, 2)
        strlist(args[0], r'[ -~]{0,500}', 0, 10000, 500)
        array(args[1], 0, 1, 0, 10000)
        if len(args[0]) != len(args[1]): raise ValueError('paired arrays')


def eq_values_dfs_free_budget(defs):
    """Large inputs: same fixed-point semantics, evaluated by Kahn's algorithm over the dependency graph."""
    users, indeg = {}, {}
    for name, terms in defs.items():
        deps = {tok for _, tok in terms if not tok[0].isdigit()}
        indeg[name] = len(deps)
        for d in deps: users.setdefault(d, []).append(name)
    ready = deque(n for n, d in indeg.items() if d == 0)
    known = {}
    while ready:
        name = ready.popleft()
        total = 0
        for sign, tok in defs[name]:
            v = int(tok) if tok[0].isdigit() else known[tok]
            total = total + v if sign == '+' else total - v
        known[name] = total
        for u in users.get(name, ()):
            indeg[u] -= 1
            if indeg[u] == 0: ready.append(u)
    return known


# ---------------------------------------------------------------- references


def ref_bsv(arr, target):
    for i, v in enumerate(arr):
        if v == target: return i
    best = -1
    for i, v in enumerate(arr):
        if v < target: best = i
    return best


def ref_btc(s):
    if not s: return None
    counts = {}
    for ch in s: counts[ch] = counts.get(ch, 0) + 1
    pool = []
    for i, ch in enumerate(sorted(counts)):
        pool.append((counts[ch], i, {'ch': ch, 'count': counts[ch], 'left': None, 'right': None}))
    nxt = len(pool)
    while len(pool) > 1:
        pool.sort(key=lambda x: (x[0], x[1]))
        a, b = pool[0], pool[1]
        pool = pool[2:] + [(a[0] + b[0], nxt, {'ch': '#', 'count': a[0] + b[0], 'left': a[2], 'right': b[2]})]
        nxt += 1
    return pool[0][2]


def ref_trans(logs):
    by_user = {}
    for ts, user, res in logs: by_user.setdefault(user, []).append((int(ts), res))
    counts = {}
    for user in by_user:
        path = ['START'] + [r for _, r in sorted(by_user[user])] + ['END']
        for a, b in zip(path, path[1:]): counts[(a, b)] = counts.get((a, b), 0) + 1
    return [[a, b, c] for (a, b), c in sorted(counts.items())]


def ref_cake(stock, orders):
    have, out = list(stock), []
    for o in orders:
        ok = all(have[i] >= o[i] for i in range(3))
        if ok: have = [have[i] - o[i] for i in range(3)]
        out.append(ok)
    return out


def ref_eq(uid, arr):
    target, defs = eq_parse(uid, arr)
    values = eq_values(defs)
    return values.get(target)


def ref_wait(arr):
    queue = deque((i, h) for i, h in enumerate(arr))
    clock, total = 0, 0
    while queue:
        i, h = queue.popleft()
        clock += 1
        if h == 1: total += clock - arr[i]
        else: queue.append((i, h - 1))
    return total


def ref_elev(elevators, request):
    pf, d = int(request[0]), request[1]
    best, best_dist = -1, None
    for i, (f, s) in enumerate(elevators):
        f = int(f)
        ok = s == 'idle' or (s == d == 'up' and f <= pf) or (s == d == 'down' and f >= pf)
        if ok and (best_dist is None or abs(f - pf) < best_dist): best, best_dist = i, abs(f - pf)
    return best


def ref_chat(ops, rows):
    m = rows[0][0]; events = []; out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        t = row[0]; low = t - m + 1
        if op == 'recordEvent': events.append((t, row[1], row[2])); out.append(None)
        elif op == 'getUserCount': out.append(sum(1 for e in events if e[1] == row[1] and low <= e[0] <= t))
        elif op == 'getChatCount': out.append(sum(1 for e in events if e[2] == row[1] and low <= e[0] <= t))
        else: out.append(len({e[1] for e in events if e[2] == row[1] and low <= e[0] <= t}))
    return out


def nxt(c): return chr((ord(c) - 97 + 1) % 26 + 97)


def ref_pwd(news, olds):
    out = []
    for new, old in zip(news, olds):
        # can[j] = old[:j] matchable within the processed prefix of new (prefix-DP, not two pointers)
        can = [True] + [False] * len(old)
        for c in new:
            for j in range(len(old), 0, -1):
                if can[j - 1] and old[j - 1] in (c, nxt(c)): can[j] = True
        out.append('YES' if can[len(old)] else 'NO')
    return out


def miller_rabin(n):
    if n < 2: return False
    for p in (2, 3, 5, 7):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for a in (2, 3, 5, 7):  # deterministic for n < 3215031751
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True


def ref_cprime(n):
    s = str(n)
    return all(miller_rabin(int(s[i:] + s[:i])) for i in range(len(s)))


def ref_alloc(total, requests):
    used = [False] * total; out = []
    for kind, start, num in requests:
        start, num = int(start), int(num)
        if kind == 'store':
            found = -1
            for off in range(total):
                p = (start + off) % total
                if all(not used[(p + j) % total] for j in range(num)):
                    found = p; break
            if found >= 0:
                for j in range(num): used[(found + j) % total] = True
            out.append(found)
        else:
            freed = 0
            for j in range(num):
                q = (start + j) % total
                if used[q]: freed += 1; used[q] = False
            out.append(freed)
    return out


def ref_coins(initial, energy, coins):
    n, best = len(energy), 0
    for choice in product((0, 1), repeat=n):  # 1 = take energy
        e, c = initial, 0
        for i in range(n):
            if i > 0:
                if e < 1: break
                e -= 1
            if choice[i]: e += energy[i]
            else: c += coins[i]
            best = max(best, c)
    return best


def ref_collatz(n):
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def mat_mul(a, b):
    return [[(a[0][0] * b[0][0] + a[0][1] * b[1][0]) % MOD, (a[0][0] * b[0][1] + a[0][1] * b[1][1]) % MOD],
            [(a[1][0] * b[0][0] + a[1][1] * b[1][0]) % MOD, (a[1][0] * b[0][1] + a[1][1] * b[1][1]) % MOD]]


def ref_houses(n, k, first, last):
    """States (ends in the last colour, ends in another colour); [A', B'] = [B, (k-1)A + (k-2)B]."""
    step = [[0, 1], [(k - 1) % MOD, (k - 2) % MOD]]
    power = [[1, 0], [0, 1]]; e = n - 1
    while e:
        if e & 1: power = mat_mul(power, step)
        step = mat_mul(step, step); e >>= 1
    a0, b0 = (1, 0) if first == last else (0, 1)
    # column vector [A, B] after n-1 steps is power @ [a0, b0]
    return (power[0][0] * a0 + power[0][1] * b0) % MOD


def ref_load(servers, requests):
    out = []
    for sid, base in servers:
        mine = [r for r in requests if r[1] == sid]
        score = base
        for i, (t, _, rule) in enumerate(mine):
            score += 1 + RULE_COST[rule]
            if any(j != i and t - BURST_SECONDS <= u <= t for j, (u, _, _) in enumerate(mine)): score += BURST_BONUS
        out.append([sid, score])
    return out


STUDIO = re.compile(r'(?<![a-z0-9])studio(?![a-z0-9])')
ONE_BED = re.compile(r'(?<![a-z0-9])((1|one)[^a-z0-9]+bedroom|1br|1bd)(?![a-z0-9])')


def ref_bed(descriptions, beds):
    out = []
    for d, b in zip(descriptions, beds):
        low = d.lower()
        s, o = STUDIO.search(low) is not None, ONE_BED.search(low) is not None
        out.append(0 if s and not o else 1 if o and not s else b)
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == BSV: return ref_bsv(*args)
    if uid == BTC: return ref_btc(args[0])
    if uid == TRANS: return ref_trans(args[0])
    if uid == CAKE: return ref_cake(*args)
    if uid in (EQ1, EQ2, EQ3):
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_eq(uid, args[0])
    if uid == WAIT:
        if sum(args[0]) > 200000: raise ValueError('reference budget')
        return ref_wait(args[0])
    if uid == ELEV: return ref_elev(*args)
    if uid in CLASSES:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_chat(*args)
    if uid == PWD:
        if sum(len(a) * len(b) for a, b in zip(*args)) > 300000: raise ValueError('reference budget')
        return ref_pwd(*args)
    if uid == CPRIME: return ref_cprime(args[0])
    if uid == ALLOC:
        if args[0] > 60: raise ValueError('reference budget')
        return ref_alloc(*args)
    if uid == COINS:
        if len(args[1]) > 13: raise ValueError('reference budget')
        return ref_coins(*args)
    if uid == COLLATZ: return ref_collatz(args[0])
    if uid == HOUSES: return ref_houses(*args)
    if uid == LOAD:
        if len(args[1]) > 400: raise ValueError('reference budget')
        return ref_load(*args)
    return ref_bed(*args)


def brute_houses(n, k, first, last):
    """Exhaustive enumeration for tiny n, k (cross-check of the matrix reference)."""
    if n == 1: return 1 if first == last else 0
    return sum(1 for mid in product(range(k), repeat=n - 2)
               if all(a != b for a, b in zip((first,) + mid, mid + (last,))))


def huffman_valid(s, tree):
    """Independent property: leaves are the distinct characters with their counts; internal counts sum."""
    if not s: return tree is None
    leaves, stack = {}, [tree]
    while stack:
        node = stack.pop()
        if node['left'] is None and node['right'] is None:
            if node['ch'] in leaves: return False
            leaves[node['ch']] = node['count']
        else:
            if node['ch'] != '#' or node['left'] is None or node['right'] is None: return False
            if node['count'] != node['left']['count'] + node['right']['count']: return False
            stack += [node['left'], node['right']]
    return leaves == {c: s.count(c) for c in set(s)}
