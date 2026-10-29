"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (substring enumeration
with greedy subsequence tests, sort-and-scan after every insertion, all-substring checks, quadratic
prefix scans, share-by-share liquidation over a list ledger, border filtering of whole squares, subset
enumeration, unit-step budget search, pairwise scans and explicit path enumeration).
"""
from itertools import combinations
import re

H = 'hack2hire:'
LCSS = H + '6a0237332608e589a944a2be'
HOUSES = H + '69a351986e73e4abccc9bf81'
SEMI = H + '6854ca09c201117d348a25d5'
UNDER = H + '6a974f580ca9cc4e1c789f3b'
CASE = H + '67fbdd34216af53465a721a5'
MARGIN1 = H + '67d266555e44a1b0c201ee79'
MARGIN2 = H + '67d2675b5e44a1b0c201ee7a'
MARGIN3 = H + '67d2675c5e44a1b0c201ee7b'
FRAME = H + '6a1c7cfc8b879849ebc0f85d'
NONOVER = H + '6827f7c3f13ac663af91d7a5'
FLOOR = H + '69e933bdfbaf3da641828694'
BXOR = H + '6a725ef948af2ae18e995ee1'
HEALTH = H + '676efc4fb2c9d428b406a287'
SPLIT = H + '6a724c9748af2ae18e995e5e'
REWARD = H + '68c2e2221f64f4312b0a3df8'
TESTEFF = H + '6a8664a4701a76fc6843b36e'
EXPR = H + '69a361ab6e73e4abccc9bfd0'
BOARD = H + '67d33f6a488516fd8ad5a064'

IDS = (LCSS, HOUSES, SEMI, UNDER, CASE, MARGIN1, MARGIN2, MARGIN3, FRAME, NONOVER, FLOOR, BXOR, HEALTH, SPLIT, REWARD,
       TESTEFF, EXPR, BOARD)
CLASSES = {}  # no native-class variants in this cohort
MARGINS = (MARGIN1, MARGIN2, MARGIN3)


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def grid(g, maximum):
    if type(g) is not list or not 1 <= len(g) <= maximum or type(g[0]) is not list or not 1 <= len(g[0]) <= maximum: raise ValueError('grid shape')
    for row in g:
        if type(row) is not list or len(row) != len(g[0]): raise ValueError('ragged grid')


def decimal(v, lo, hi):
    if type(v) is not str or re.fullmatch(r'0|[1-9][0-9]{0,9}', v) is None or not lo <= int(v) <= hi: raise ValueError('decimal string domain')


def validate_domain(uid, args):
    if uid == LCSS:
        envelope(args, 2)
        for s in args: text(s, r'[a-z]*', 1000)
    elif uid == HOUSES:
        envelope(args, 1); array(args[0], -10**9, 10**9, 1, 100000)
    elif uid == SEMI:
        envelope(args, 1); text(args[0], r'[ -~]*', 200000)
    elif uid == UNDER:
        envelope(args, 2); array(args[0], 1, 10**9, 1, 100000); integer(args[1], 1, 10**15)
    elif uid == CASE:
        envelope(args, 1); text(args[0], r'[A-Za-z]+', 200000)
    elif uid in MARGINS:
        envelope(args, 1); trades = args[0]
        if type(trades) is not list or not 1 <= len(trades) <= 1000: raise ValueError('trade count')
        symbol = r'[A-NP-Z]{1,5}O?' if uid == MARGIN3 else r'[A-Z]{1,6}'
        last = -1
        for t in trades:
            if type(t) is not list or len(t) != 5: raise ValueError('trade shape')
            decimal(t[0], 0, 10**10 - 1)
            if int(t[0]) < last: raise ValueError('timestamps out of order')
            last = int(t[0])
            text(t[1], symbol, 6); text(t[2], r'[BS]', 1); decimal(t[3], 1, 1000); decimal(t[4], 1, 10000)
    elif uid == FRAME:
        envelope(args, 2); grid(args[0], 100)
        for row in args[0]:
            for v in row: integer(v, -10**6, 10**6)
        integer(args[1], 1, min(len(args[0]), len(args[0][0])))
    elif uid == NONOVER:
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 100000: raise ValueError('task count')
        for t in args[0]:
            if type(t) is not list or len(t) != 2: raise ValueError('task shape')
            integer(t[0], 0, 10**9); integer(t[1], 0, 10**9)
            if not t[0] < t[1]: raise ValueError('start < end required')
    elif uid == FLOOR:
        envelope(args, 3); array(args[0], 1, 10**9, 1, 100000); array(args[1], 1, 10**4, 1, 100000); integer(args[2], 0, 10**9)
        if len(args[0]) != len(args[1]): raise ValueError('length mismatch')
    elif uid == BXOR:
        envelope(args, 3); lo, hi, k = args
        integer(lo, 1, 10**9); integer(hi, 1, 10**9); integer(k, 1, 2**31 - 1)
        if not lo < hi: raise ValueError('lo < hi required')
        # smallest XOR of a pair: 1 when some even a has a + 1 in range, else the single pair (lo, lo + 1)
        smallest = 1 if (lo % 2 == 0 or lo + 2 <= hi) else lo ^ (lo + 1)
        if smallest > k: raise ValueError('no valid pair')
    elif uid == HEALTH:
        envelope(args, 3); array(args[0], 1, 10**6, 1, 100000)
        if type(args[1]) is not list or len(args[1]) != len(args[0]): raise ValueError('length mismatch')
        for s in args[1]: text(s, r'[a-z0-9]{1,8}', 8)
        integer(args[2], 1, 100000)
    elif uid == SPLIT:
        envelope(args, 1); array(args[0], -10**9, 10**9, 2, 100000)
    elif uid == REWARD:
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 100000: raise ValueError('task count')
        for t in args[0]:
            if type(t) is not list or len(t) != 3: raise ValueError('task shape')
            text(t[0], r'[A-Za-z0-9_]{1,10}', 10); decimal(t[1], 0, 10**9); decimal(t[2], 0, 10**6)
    elif uid == TESTEFF:
        envelope(args, 1); array(args[0], 0, 10**9, 1, 100000)
    elif uid == EXPR:
        envelope(args, 1); grid(args[0], 300); digits = 0
        for row in args[0]:
            for v in row:
                text(v, r'[0-9+-]', 1); digits += v.isdigit()
        if not digits: raise ValueError('at least one digit required')
    elif uid == BOARD:
        envelope(args, 1); array(args[0], -10**9, 10**9, 1, 100000)
    else:
        raise ValueError('unknown uid')


def budget(cost, limit):
    if cost > limit: raise ValueError('reference budget')


def is_subsequence(t, s):
    pos = 0
    for ch in t:
        pos = s.find(ch, pos)
        if pos < 0: return False
        pos += 1
    return True


def ref_lcss(x, y):
    budget(len(y) ** 2 * (len(x) + 1), 3000000)
    best = 0
    for i in range(len(y)):
        for j in range(i + 1, len(y) + 1):
            if j - i > best and is_subsequence(y[i:j], x): best = j - i
    return best


def ref_houses(queries):
    budget(len(queries) ** 2, 250000)
    occupied, out = set(), []
    for p in queries:
        if p not in occupied and not (p - 1 in occupied and p + 1 in occupied): occupied.add(p)
        points, best, run = sorted(occupied), 0, 0
        for i, q in enumerate(points):
            run = run + 1 if i and points[i - 1] == q - 1 else 1
            best = max(best, run)
        out.append(best)
    return out


def ref_semi(s):
    budget(len(s) ** 3, 2000000)
    best = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            t = s[i:j]
            if all(not (t[q] == t[q + 1] == t[q + 2]) for q in range(len(t) - 2)): best = max(best, j - i)
    return best


def ref_under(a, k):
    budget(len(a) ** 2, 1000000)
    best = 0
    for i in range(len(a)):
        for j in range(i, len(a)):
            if sum(a[i:j + 1]) <= k: best = max(best, j - i + 1)
    return best


def ref_case(s):
    budget(len(s) ** 2, 1000000)
    count = 0
    for letter in set(s.lower()):
        lower = [i for i, ch in enumerate(s) if ch == letter]
        upper = [i for i, ch in enumerate(s) if ch == letter.upper()]
        if all(i < j for i in lower for j in upper): count += 1
    return count


def ref_margin(uid, trades):
    """Share-by-share replay over a list ledger [[symbol, shares, latest price], ...]."""
    budget(sum(int(t[3]) for t in trades) * len(trades), 4000000)
    cash, ledger = 1000, []

    def entry(symbol):
        for e in ledger:
            if e[0] == symbol: return e
        e = [symbol, 0, 0]; ledger.append(e); return e

    def sellable(e):
        if uid != MARGIN3 or e[0].endswith('O'): return e[1]
        option = [o for o in ledger if o[0] == e[0] + 'O']
        return max(0, e[1] - (option[0][1] if option else 0))

    for t in trades:
        e = entry(t[1]); q, price = int(t[3]), int(t[4]); e[2] = price
        if t[2] == 'B': cash -= q * price; e[1] += q
        else:
            q = min(q, e[1]); cash += q * price; e[1] -= q
        if uid == MARGIN1: continue
        while cash < 0:
            choices = [c for c in ledger if sellable(c) > 0]
            if not choices: break
            top = max(c[2] for c in choices)
            best = min(c[0] for c in choices if c[2] == top)
            b = entry(best); b[1] -= 1; cash += b[2]
    return [['CASH', str(cash)]] + [[e[0], str(e[1])] for e in sorted(ledger) if e[1] > 0]


def ref_frame(matrix, k):
    m, n = len(matrix), len(matrix[0])
    budget((m - k + 1) * (n - k + 1) * k * k, 3000000)
    best = None
    for r in range(m - k + 1):
        for c in range(n - k + 1):
            values = set()
            for i in range(k):
                for j in range(k):
                    if i in (0, k - 1) or j in (0, k - 1): values.add(matrix[r + i][c + j])
            best = sum(values) if best is None else max(best, sum(values))
    return best


def ref_nonover(tasks):
    n = len(tasks); budget(2 ** n * n, 200000)
    best = 0
    for mask in range(1 << n):
        chosen = [tasks[i] for i in range(n) if mask >> i & 1]
        if len(chosen) > best and all(not (a[0] < b[1] and b[0] < a[1]) for a, b in combinations(chosen, 2)): best = len(chosen)
    return best


def ref_floor(values, costs, total):
    budget(len(values) * (total + 1), 3000000)
    t = min(values)
    while sum(max(0, t + 1 - v) * c for v, c in zip(values, costs)) <= total: t += 1
    return t


def ref_bxor(lo, hi, k):
    budget((hi - lo + 1) ** 2, 40000)
    return max(a ^ b for a in range(lo, hi + 1) for b in range(a + 1, hi + 1) if a ^ b <= k)


def ref_health(health, series, k):
    names = sorted(set(series))
    budget(2 ** len(names) * len(health), 300000)
    best = 0
    for size in range(1, min(k, len(names)) + 1):
        for pick in combinations(names, size):
            best = max(best, sum(h for h, s in zip(health, series) if s in pick))
    return best


def ref_split(arr):
    budget(len(arr) ** 2, 1000000)
    return max(len(set(arr[:i])) + len(set(arr[i:])) for i in range(1, len(arr)))


def ref_reward(tasks):
    n = len(tasks); budget(2 ** n * n, 200000)
    best = 0
    for mask in range(1 << n):
        chosen = [tasks[i] for i in range(n) if mask >> i & 1]
        deadlines = sorted(int(t[1]) for t in chosen)
        if all(d >= i + 1 for i, d in enumerate(deadlines)): best = max(best, sum(int(t[2]) for t in chosen))
    return best


def ref_testeff(arrivals):
    budget(len(arrivals) ** 3, 2000000)
    return max(sum(1 for x in arrivals if t1 <= x <= t2) - (t2 - t1) for t1 in arrivals for t2 in arrivals if t1 <= t2)


def ref_expr(matrix):
    m, n = len(matrix), len(matrix[0])
    budget(m * n * 2 ** (m + n), 300000)
    best = None

    def walk(r, c, text_):
        nonlocal best
        text_ += matrix[r][c]
        kinds = ['d' if ch.isdigit() else 'o' for ch in text_]
        if any(kinds[i] == kinds[i + 1] for i in range(len(kinds) - 1)) or kinds[0] == 'o': return
        if kinds[-1] == 'd':
            value = sum(int(sign + digit) for sign, digit in re.findall(r'([+-]?)([0-9])', text_))
            best = value if best is None else max(best, value)
        if r + 1 < m: walk(r + 1, c, text_)
        if c + 1 < n: walk(r, c + 1, text_)

    for r in range(m):
        for c in range(n): walk(r, c, '')
    return best


def ref_board(arr):
    span = max(arr) - min(arr)
    budget(len(arr) * (span + 2), 1000000)
    length = 1
    while True:
        points, boards, i = sorted(arr), 0, 0
        while i < len(points):
            end = points[i] + length; boards += 1
            while i < len(points) and points[i] <= end: i += 1
        if boards <= 2: return length
        length += 1


def reference(uid, args):
    validate_domain(uid, args)
    if uid == LCSS: return ref_lcss(*args)
    if uid == HOUSES: return ref_houses(*args)
    if uid == SEMI: return ref_semi(*args)
    if uid == UNDER: return ref_under(*args)
    if uid == CASE: return ref_case(*args)
    if uid in MARGINS: return ref_margin(uid, *args)
    if uid == FRAME: return ref_frame(*args)
    if uid == NONOVER: return ref_nonover(*args)
    if uid == FLOOR: return ref_floor(*args)
    if uid == BXOR: return ref_bxor(*args)
    if uid == HEALTH: return ref_health(*args)
    if uid == SPLIT: return ref_split(*args)
    if uid == REWARD: return ref_reward(*args)
    if uid == TESTEFF: return ref_testeff(*args)
    if uid == EXPR: return ref_expr(*args)
    return ref_board(*args)
