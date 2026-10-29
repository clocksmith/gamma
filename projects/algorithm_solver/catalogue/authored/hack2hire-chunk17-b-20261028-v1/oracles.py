"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (full route scans,
index-pair dynamic programming, a prefix dynamic-programming table, all-pairs position checks, per-write
block scans, per-query segment checks, step-by-step simulation, subset dynamic programming, triple loops,
per-call log rescans, recursive descent, per-row window counts, exhaustive path enumeration, per-entry
attendance counts, direct substring checks and per-ticket filling) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
URD = H + '68fa7c5e0fa32e4d82f4fc1f'
UNE = H + '686b0a7af56e0403f35f23ee'
WCM = H + '67799006dcf91f8e3c1c310d'
WPM = H + '67e45b2850b60b77022f382e'
WDB = H + '67730b5ddd9437f8aa275b04'
ABA = H + '679da470996c3c60bd38b5ba'
AGS = H + '678876fe402dc47b67a14944'
BSD = H + '67a56d81b571d6ff0a4bd238'
CRT = H + '67840e27d0faf7ec64cc3adb'
CDT = H + '6897c08aa543d38b79706ca6'
ESE = H + '678d3e738c349080cddc5f5e'
FFE = H + '687e65b7eab243475a7dfbf7'
LPD = H + '6775decc2c61a9f93e698ba0'
FPE = H + '69279ce99c0536c47b291a80'
FRS = H + '677041e0366afdc1233e4ff4'
GOT = H + '69b78e4e8a0eeb9897a8d2a5'

IDS = (URD, UNE, WCM, WPM, WDB, ABA, AGS, BSD, CRT, CDT, ESE, FFE, LPD, FPE, FRS, GOT)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    URD: ('Router', 0, {'addRoute': 2, 'callRoute': 1}, ('addRoute',)),
    WDB: ('DiskBlockManager', 2, {'write': 0}, ()),
    ABA: ('AlienBaseAttack', 1, {'attack': 1, 'isDestroyed': 0}, ('attack',)),
    CDT: ('PurchaseAnalyzer', 2, {'crossDayDiverseUsers': 0}, ()),
}
LIMIT = 2**53 - 1


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


SEG = r'[a-z0-9]{1,10}'


def route(v, wildcard):
    seg = '(' + SEG + (r'|\*' if wildcard else '') + ')'
    text(v, r'/|(/' + seg + r'){1,8}', 89)


def urd_domain(args):
    calls = trace(URD, args, 10001)
    for op, row in calls:
        if op == 'addRoute': route(row[0], True); text(row[1], r'[A-Za-z][A-Za-z0-9_]{0,19}', 20)
        else: route(row[0], False)


def log_rows(logs):
    sized(logs, 0, 100000)
    for row in logs:
        sized(row, 4, 4)
        text(row[0], r'20[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-8])', 10)
        text(row[1], r'[a-z0-9_]{1,12}', 12); text(row[2], r'[a-z]{1,12}', 12); text(row[3], r'(0|[1-9][0-9]{0,8})(\.[0-9]{1,2})?', 12)


TOKEN = re.compile(r' +|\(|\)|add|mul|-?(?:0|[1-9][0-9]*)')


def ese_domain(expression):
    """Iterative syntax and magnitude check (independent of the recursive reference)."""
    text(expression, r'[0-9a-z() -]+', 100000)
    pos, stack, done, last = 0, [], None, None  # stack frames: [op or None, values]
    while pos < len(expression):
        m = TOKEN.match(expression, pos)
        if m is None: raise ValueError('bad token')
        tok = m.group(); pos = m.end()
        if tok[0] == ' ':
            last = ' '; continue
        if done is not None: raise ValueError('trailing input')
        word = tok not in '()'
        if word and last == 'w': raise ValueError('adjacent words must be separated by a space')
        if tok == '(':
            if stack and stack[-1][0] is None: raise ValueError('operation expected')
            stack.append([None, []])
        elif tok == ')':
            if not stack or stack[-1][0] is None or len(stack[-1][1]) < 2: raise ValueError('call needs an operation and two arguments')
            op, vals = stack.pop(); value = 0 if op == 'add' else 1
            for v in vals:
                value = value + v if op == 'add' else value * v
                if abs(value) > LIMIT: raise ValueError('intermediate magnitude')
            if stack: stack[-1][1].append(value)
            else: done = value
        elif tok in ('add', 'mul'):
            if not stack or stack[-1][0] is not None or stack[-1][1]: raise ValueError('misplaced operation')
            stack[-1][0] = tok
        else:
            if tok == '-0' or len(tok.lstrip('-')) > 10 or abs(int(tok)) > 10**9: raise ValueError('literal domain')
            if stack:
                if stack[-1][0] is None: raise ValueError('operation expected')
                stack[-1][1].append(int(tok))
            else: done = int(tok)
        last = tok[-1] if tok in '()' else 'w'
        if len(stack) > 50000: raise ValueError('nesting depth')
    if stack or done is None: raise ValueError('incomplete expression')


def ffe_domain(logs, k):
    sized(logs, 0, 100000); integer(k, 1, 100000)
    for row in logs:
        sized(row, 3, 3); text(row[0], r'[a-z0-9]{1,10}', 10); integer(row[1], 0, 10**9); text(row[2], r'[a-z_]{1,10}', 10)


def lpd_domain(edges):
    sized(edges, 0, 10000)
    succ, indeg, seen = {}, {}, set()
    for e in edges:
        sized(e, 2, 2); text(e[0], r'[A-Z]{1,5}', 5); text(e[1], r'[A-Z]{1,5}', 5)
        if e[0] == e[1] or (e[0], e[1]) in seen: raise ValueError('self-loop or repeated edge')
        seen.add((e[0], e[1]))
        succ.setdefault(e[0], []).append(e[1]); succ.setdefault(e[1], [])
        indeg[e[1]] = indeg.get(e[1], 0) + 1; indeg.setdefault(e[0], 0)
    ready = [v for v in indeg if indeg[v] == 0]; removed = 0
    while ready:
        v = ready.pop(); removed += 1
        for w in succ[v]:
            indeg[w] -= 1
            if indeg[w] == 0: ready.append(w)
    if removed != len(indeg): raise ValueError('cycle')


def validate_domain(uid, args):
    if type(uid) is not str or uid not in IDS: raise ValueError('unknown uid')
    if uid == URD: return urd_domain(args)
    if uid == WDB:
        calls = trace(WDB, args); integer(args[1][0][0], 1, 100000); integer(args[1][0][1], 1, 10**9); return calls
    if uid == ABA:
        calls = trace(ABA, args); integer(args[1][0][0], 1, 10**9)
        for op, row in calls:
            if op == 'attack': integer(row[0], -10**9, 10**9)
        return
    if uid == CDT:
        calls = trace(CDT, args, 101); log_rows(args[1][0][0]); log_rows(args[1][0][1]); return calls
    if uid == UNE:
        envelope(args, 2); intlist(args[0], 1, 10**9, 1, 5000); integer(args[1], 0, min(len(args[0]), 50)); return
    if uid == WCM:
        envelope(args, 2); text(args[0], r'[a-z]*', 2000); text(args[1], r'[a-z*]*', 2000); return
    if uid == WPM:
        envelope(args, 2); text(args[0], r'[a-z]+', 1000); sized(args[1], 0, 10000)
        for w in args[1]: text(w, r'[a-z]*', 1000)
        if sum(len(w) for w in args[1]) > 200000: raise ValueError('total word length')
        return
    if uid == AGS:
        envelope(args, 3); intlist(args[0], 1, 10**9, 1); text(args[1], r'[01]+', 100000); integer(args[2], 1, 100000)
        if len(args[1]) != len(args[0]) or '1' not in args[1]: raise ValueError('state shape')
        return
    if uid == BSD:
        envelope(args, 3); intlist(args[0], 1, 100, 1, 50000); intlist(args[1], 1, 10**4, len(args[0]), len(args[0])); integer(args[2], 1, 10**4); return
    if uid == CRT:
        envelope(args, 1); intlist(args[0], -10**9, 10**9); return
    if uid == ESE:
        envelope(args, 1); return ese_domain(args[0])
    if uid == FFE:
        envelope(args, 2); return ffe_domain(*args)
    if uid == LPD:
        envelope(args, 1); return lpd_domain(args[0])
    if uid == FPE:
        envelope(args, 1); sized(args[0], 1, 100000)
        for iv in args[0]:
            intlist(iv, 0, 10**9, 2, 2)
            if iv[0] >= iv[1]: raise ValueError('entry < exit')
        return
    if uid == FRS:
        envelope(args, 3); text(args[0], r'[a-z]+', 100000); integer(args[1], -10**5, 10**5); integer(args[2], -10**5, 10**5); return
    envelope(args, 2); integer(args[0], 1, 100000); sized(args[1], 0, 100000)
    for t in args[1]:
        intlist(t, 0, args[0] - 1, 2, 2)
        if t[0] > t[1]: raise ValueError('entry <= exit')


# ---------------------------------------------------------------- references
def ref_urd(calls):
    routes, out = {}, [None]
    for op, row in calls:
        if op == 'addRoute':
            routes[row[0]] = row[1]; out.append(None); continue
        parts = row[0].split('/')[1:] if row[0] != '/' else []
        best = None
        for pattern, handler in routes.items():
            pp = pattern.split('/')[1:] if pattern != '/' else []
            if len(pp) != len(parts) or any(a != '*' and a != b for a, b in zip(pp, parts)): continue
            key = (pp.count('*'), [a == '*' for a in pp])
            if best is None or key < best[0]: best = (key, handler)
        out.append('' if best is None else best[1])
    return out


def ref_une(a, k):
    n = len(a)
    f = [[0] * (k + 1) for _ in range(n)]  # f[i][j]: longest good subsequence ending at index i using exactly <= j changes
    best = 0
    for i in range(n):
        for j in range(k + 1):
            v = 1
            for p in range(i):
                c = j - (a[p] != a[i])
                if c >= 0: v = max(v, f[p][c] + 1)
            f[i][j] = v; best = max(best, v)
    return best


def ref_wcm(s, p):
    n, m = len(s), len(p)
    t = [[False] * (m + 1) for _ in range(n + 1)]
    t[0][0] = True
    for j in range(1, m + 1): t[0][j] = t[0][j - 1] and p[j - 1] == '*'
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            t[i][j] = (t[i][j - 1] or t[i - 1][j]) if p[j - 1] == '*' else (t[i - 1][j - 1] and p[j - 1] == s[i - 1])
    return t[n][m]


def ref_wpm(pattern, words):
    out = []
    for w in words:
        ok = len(w) == len(pattern)
        for i in range(len(w) if ok else 0):
            for j in range(i + 1, len(w)):
                if (pattern[i] == pattern[j]) != (w[i] == w[j]): ok = False
        out.append(ok)
    return out


def ref_wdb(n, cycles, calls):
    left, out = [cycles] * n, [None]
    for _ in calls:
        pick = -1
        for i in range(n):
            if left[i] > 0 and (pick < 0 or left[i] < left[pick]): pick = i
        if pick >= 0: left[pick] -= 1
        out.append(pick)
    return out


def ref_aba(n, calls):
    hits, out = [], [None]
    for op, row in calls:
        if op == 'attack': hits.append(row[0]); out.append(None)
        else: out.append(all(i in hits for i in range(n)))
    return out


def ref_ags(arr, state, m):
    st, out = list(state), []
    for _ in range(m):
        out.append(max(arr[i] for i in range(len(arr)) if st[i] == '1'))
        st = [('1' if c == '1' or (i > 0 and st[i - 1] == '1') else '0') for i, c in enumerate(st)]
    return out


def ref_bsd(request, health, k):
    n = len(request); t = [-(-h // k) for h in health]
    dp = {0: 0}
    for mask in range(1 << n):
        if mask not in dp: continue
        elapsed = sum(t[i] for i in range(n) if mask >> i & 1)
        for i in range(n):
            if not mask >> i & 1:
                cost = dp[mask] + request[i] * (elapsed + t[i]); nxt = mask | 1 << i
                if nxt not in dp or cost < dp[nxt]: dp[nxt] = cost
    return dp[(1 << n) - 1]


def ref_crt(nums):
    n = len(nums)
    return sum(1 for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n) if nums[i] > nums[j] > nums[k])


def ref_cdt(day1, day2, calls):
    out = [None]
    for _ in calls:
        users = sorted({r[1] for r in day1} & {r[1] for r in day2})
        out.append([u for u in users if len({r[2] for r in day1 + day2 if r[1] == u}) >= 2])
    return out


def ref_ese(expression):
    tokens = re.findall(r'\(|\)|[a-z]+|-?[0-9]+', expression)

    def parse(i):
        if tokens[i] != '(': return int(tokens[i]), i + 1
        op = tokens[i + 1]; i += 2; vals = []
        while tokens[i] != ')':
            v, i = parse(i); vals.append(v)
        acc = 0 if op == 'add' else 1
        for v in vals: acc = acc + v if op == 'add' else acc * v
        return acc, i + 1
    return parse(0)[0]


def ref_ffe(logs, k):
    found = set()
    for u, t0, e in logs:
        if sum(1 for u2, t, e2 in logs if u2 == u and e2 == e and t0 <= t < t0 + 86400) >= k: found.add(e)
    return sorted(found)


def ref_lpd(edges):
    succ = {}
    for a, b in edges: succ.setdefault(a, []).append(b); succ.setdefault(b, [])
    best = []

    def walk(path):
        nonlocal best
        if len(path) > len(best) or (len(path) == len(best) and path < best): best = list(path)
        for w in succ[path[-1]]: walk(path + [w])
    for v in succ: walk([v])
    return best if edges else []


def ref_fpe(intervals):
    best = None
    for t in sorted({e for e, _ in intervals}):
        c = sum(1 for e, x in intervals if e <= t < x)
        if best is None or c > best[0]: best = (c, t)
    return best[1]


def ref_frs(word, a, b):
    total = 0
    for i in range(len(word)):
        v = c = 0
        for j in range(i, len(word)):
            if word[j] in 'aeiou': v += 1
            else: c += 1
            if j - i + 1 == a * v + b * c: total += 1
    return total


def ref_got(n, tickets):
    out = [0] * n
    for e, x in tickets:
        for t in range(e, x + 1): out[t] += 1
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid == URD: return ref_urd(calls)
        if uid == WDB:
            budget(args[1][0][0] <= 300); return ref_wdb(*args[1][0], calls)
        if uid == ABA:
            budget(args[1][0][0] <= 300); return ref_aba(args[1][0][0], calls)
        budget(len(args[1][0][0]) + len(args[1][0][1]) <= 300); return ref_cdt(*args[1][0], calls)
    if uid == UNE:
        budget(len(args[0]) <= 60); return ref_une(*args)
    if uid == WCM:
        budget(len(args[0]) * len(args[1]) <= 40000); return ref_wcm(*args)
    if uid == WPM:
        budget(len(args[0]) <= 60 and len(args[1]) <= 100); return ref_wpm(*args)
    if uid == AGS:
        budget(len(args[0]) * args[2] <= 20000); return ref_ags(*args)
    if uid == BSD:
        budget(len(args[0]) <= 10); return ref_bsd(*args)
    if uid == CRT:
        budget(len(args[0]) <= 60); return ref_crt(args[0])
    if uid == ESE:
        budget(len(args[0]) <= 400); return ref_ese(args[0])
    if uid == FFE:
        budget(len(args[0]) <= 300); return ref_ffe(*args)
    if uid == LPD:
        budget(len(args[0]) <= 20); return ref_lpd(args[0])
    if uid == FPE:
        budget(len(args[0]) <= 300); return ref_fpe(args[0])
    if uid == FRS:
        budget(len(args[0]) <= 300); return ref_frs(*args)
    budget(args[0] * (len(args[1]) + 1) <= 40000); return ref_got(*args)
