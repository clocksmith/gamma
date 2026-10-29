"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (full sorts per window,
per-offset splitting, per-user and per-pair rescans, linear scans over registered paths, literal
pairwise collision scans, sorted-letter comparisons per query, plain memoised recursion, literal grid
rounds, permutation enumeration, per-unit time marking) and refuse inputs above a small budget.
"""
import itertools
import re

H = 'hack2hire:'
ZBP = H + '69cb2283ff3ebde766cedbdd'
VPS = H + '68ad8c5bcdaebe9459ce9a7f'
WAK = H + '67886e3c402dc47b67a14940'
TOK1 = H + '6a1a06bfc81f779dc6a23737'
TOK2 = H + '6a1a06e9c81f779dc6a2373a'
TOK3 = H + '6a1a0712c81f779dc6a2373b'
API = H + '6862f418eb0810914237ab13'
ARD1 = H + '69fe5a7f574d87bc4900687d'
ARD2 = H + '69fe5a9a574d87bc4900687e'
DRL = H + '6a7a3b72d713d873ca7aaf62'
AST = H + '679dc578996c3c60bd38b5bc'
ACP = H + '6a9748740ca9cc4e1c789f00'
BPG = H + '67775b978df5ec401f786db0'
BMD = H + '6965d17bd0c1ba0f117959a2'
BUB = H + '6a7fc7a7d713d873ca7ade7b'
BSN1 = H + '68dd8441fb98b196fa54054b'
BSN2 = H + '68dd8827fb98b196fa54054e'
SPK = H + '67d842e41989183df53824ed'
CPU = H + '6787150fe20f8f324213c295'
CAE = H + '699f73ca6e73e4abccc9b540'

IDS = (ZBP, VPS, WAK, TOK1, TOK2, TOK3, API, ARD1, ARD2, DRL, AST, ACP, BPG, BMD, BUB, BSN1, BSN2, SPK, CPU, CAE)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    API: ('APIMatchingSystem', 0, {'registerPath': 2, 'matchPath': 1}, ('registerPath',)),
    DRL: ('DomainRateLimiter', 2, {'allowRequest': 1}, ()),
}
DIGITS = r'0|[1-9][0-9]{0,12}'
MAX_OPS = 100001


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def decimal(v, lo, hi):
    text(v, DIGITS, 13)
    if not lo <= int(v) <= hi: raise ValueError('decimal range')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


def rows_of(a, width, maximum, minimum=0):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('row list size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


def trace(uid, args, maximum=MAX_OPS):
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


USER = r'[a-z0-9_]{1,20}'
PLAN = r'[A-Za-z0-9_]{1,20}'
SMALL = r'0|[1-9][0-9]{0,6}'


def tok_domain(uid, sessions, pricing):
    width = {TOK1: 3, TOK2: 5, TOK3: 6}[uid]
    strlist(pricing, r'[^\s]{1,200}', 1, 100, 200)
    plans = {}
    for row in pricing:
        f = row.split(',')
        if len(f) != width: raise ValueError('pricing width')
        text(f[0], PLAN, 20)
        if f[0] in plans: raise ValueError('unique plans')
        decimal(f[1], 0, 1000); decimal(f[2], 0, 1000)
        if width >= 5: decimal(f[3], 0, 10**6); decimal(f[4], 0, 10**9)
        if width == 6: decimal(f[5], 0, 10**12)
        plans[f[0]] = True
    strlist(sessions, r'[^\s]{1,80}', 0, 100000, 80)
    for row in sessions:
        f = row.split(',')
        if len(f) != 4: raise ValueError('session width')
        text(f[0], USER, 20); text(f[1], SMALL, 7); text(f[2], SMALL, 7)
        if int(f[1]) > 10**6 or int(f[2]) > 10**6: raise ValueError('tokens')
        if f[3] not in plans: raise ValueError('unknown plan')


SEG = r'[a-z0-9]{1,10}'
PATH = r'/|(?:/[a-z0-9]{1,10}){1,20}'


def api_domain(args):
    ops, rows = trace(API, args)
    for op, row in zip(ops[1:], rows[1:]):
        text(row[0], PATH, 300)
        if op == 'registerPath': text(row[1], r'[A-Za-z0-9_]{1,20}', 20)


EMAIL1 = r'[A-Za-z0-9._+]{1,20}@[a-z0-9.]{1,20}'
EMAIL2 = r'[A-Za-z0-9._+]{1,20}@[A-Za-z0-9.]{1,20}'
PHONE = r'(?=.*[0-9])[0-9 ()+-]{1,20}'


def ard_domain(uid, names, emails, phones):
    strlist(names, r'[A-Za-z ]{1,30}', 0, 100000, 30)
    strlist(emails, EMAIL1 if uid == ARD1 else EMAIL2, 0, 100000, 41)
    strlist(phones, PHONE, 0, 100000, 20)
    if not len(names) == len(emails) == len(phones): raise ValueError('parallel lists')


def drl_domain(args):
    ops, rows = trace(DRL, args)
    integer(rows[0][0], 1, 100000); integer(rows[0][1], 1, 10**9)
    for row in rows[1:]: text(row[0], r'[a-z0-9.]{1,30}', 30)


DATE = r'[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])'


def bmd_domain(participants):
    rows_of(participants, 3, 10000)
    total = 0
    for name, country, dates in participants:
        text(name, r'[A-Za-z]{1,20}', 20); text(country, r'[A-Za-z ]{1,30}', 30)
        strlist(dates, DATE, 0, 100000, 10)
        total += len(dates)
    if total > 100000: raise ValueError('total dates')


def bub_domain(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 50: raise ValueError('rows')
    for row in grid: array(row, 1, 10**6, 1, 50)
    if len({len(r) for r in grid}) != 1: raise ValueError('rectangular')


def cpu_domain(logs):
    rows_of(logs, 3, 100000)
    stack, last = [], 0
    for name, action, ts in logs:
        text(name, r'[A-Za-z0-9_]{1,20}', 20); decimal(ts, 0, 10**9)
        if int(ts) < last: raise ValueError('timestamps decrease')
        last = int(ts)
        if action == 'enter': stack.append(name)
        elif action == 'exit':
            if not stack or stack.pop() != name: raise ValueError('not well nested')
        else: raise ValueError('action')
    if stack: raise ValueError('unclosed task')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == ZBP:
        envelope(args, 1); array(args[0], -10**9, 10**9)
    elif uid == VPS:
        envelope(args, 2); integer(args[0], 1, 100000); array(args[1], 1, args[0])
    elif uid == WAK:
        envelope(args, 3); array(args[0], -10**9, 10**9, 1)
        integer(args[1], 1, len(args[0])); integer(args[2], 0, args[1] - 1)
    elif uid in (TOK1, TOK2, TOK3):
        envelope(args, 2); tok_domain(uid, *args)
    elif uid == API: api_domain(args)
    elif uid in (ARD1, ARD2):
        envelope(args, 3); ard_domain(uid, *args)
    elif uid == DRL: drl_domain(args)
    elif uid == AST:
        envelope(args, 2); array(args[0], 1, 10**6); array(args[1], -10**6, 10**6)
        if len(args[0]) != len(args[1]) or 0 in args[1]: raise ValueError('speeds')
    elif uid == ACP:
        envelope(args, 2); strlist(args[0], r'[a-z]{1,100}', 0, 1000); strlist(args[1], r'[a-z]{1,100}', 0, 1000)
    elif uid == BPG:
        envelope(args, 1); array(args[0], -10**4, 10**4, 0, 500)
    elif uid == BMD:
        envelope(args, 1); bmd_domain(args[0])
    elif uid == BUB:
        envelope(args, 1); bub_domain(args[0])
    elif uid == BSN1:
        envelope(args, 1); array(args[0], 0, 9, 1)
    elif uid == BSN2:
        envelope(args, 1); array(args[0], 0, 10**9, 1, 1000)
        if sum(len(str(x)) for x in args[0]) > 10000: raise ValueError('total digits')
    elif uid == SPK:
        envelope(args, 1); array(args[0], -10**9, 10**9)
    elif uid == CPU:
        envelope(args, 1); cpu_domain(args[0])
    elif uid == CAE:
        envelope(args, 2); text(args[0], r'[ -~]{0,100000}', 100000); integer(args[1], -10**9, 10**9)


# ---------------------------------------------------------------- references
def ref_zbp(nums):
    return sorted(nums) == list(range(len(nums)))


def ref_vps(n, seq):
    if not seq: return True
    for o in range(n):
        cuts = [0] + list(range(o, len(seq), n)) + [len(seq)]
        if all(len(set(seq[a:b])) == b - a for a, b in zip(cuts, cuts[1:])): return True
    return False


def ref_wak(nums, w, k):
    out = []
    for i in range(len(nums) - w + 1):
        rest = sorted(nums[i:i + w])[:w - k]
        out.append(sum(rest) // len(rest))
    return out


def ref_tok(uid, sessions, pricing):
    plans = [r.split(',') for r in pricing]

    def price(plan):  # linear scan over pricing rows
        for f in plans:
            if f[0] == plan: return [int(x) for x in f[1:]]
    users = sorted({s.split(',')[0] for s in sessions})
    out = []
    for u in users:  # rescan every session per user
        total = 0
        mine = [s.split(',') for s in sessions if s.split(',')[0] == u]
        for plan in sorted({f[3] for f in mine}):
            pr = price(plan); free = pr[3] if uid != TOK1 else 0; usage = 0
            for f in mine:
                if f[3] != plan: continue
                for tokens, unit in ((int(f[1]), pr[0]), (int(f[2]), pr[1])):
                    for_free = min(tokens, free); free -= for_free
                    usage += (tokens - for_free) * unit
            if uid == TOK3: usage = min(usage, pr[4])
            total += usage + (pr[2] if uid != TOK1 else 0)
        out.append([u, total])
    return out


def segments(p): return [] if p == '/' else p[1:].split('/')


def ref_api(ops, rows):
    registered, out = [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'registerPath':
            registered = [r for r in registered if r[0] != row[0]] + [(row[0], row[1])]
            out.append(None)
        else:
            q = segments(row[0]); best, depth = '', -1
            for p, h in registered:
                s = segments(p)
                if q[:len(s)] == s and len(s) > depth: best, depth = h, len(s)
            out.append(best)
    return out


def norm_email(e):
    e = e.lower(); local, domain = e.split('@', 1)
    return local.split('+', 1)[0].replace('.', '') + '@' + domain


def norm_phone(p): return ''.join(c for c in p if c.isdigit())


def ref_ard(uid, names, emails, phones):
    if uid == ARD2: emails = [norm_email(e) for e in emails]; phones = [norm_phone(p) for p in phones]
    registered, dup = [], []
    for i in range(len(names)):
        if any(emails[j] == emails[i] or phones[j] == phones[i] for j in registered): dup.append(i)
        else: registered.append(i)
    return dup


def ref_drl(ops, rows):
    limit, window = rows[0]; accepted = []; out = [None]
    for t, row in enumerate(rows[1:], 1):
        n = sum(1 for s, d in accepted if d == row[0] and s > t - window)
        if n < limit: accepted.append((t, row[0])); out.append(True)
        else: out.append(False)
    return out


def ref_ast(masses, speeds):
    row = [[m, s] for m, s in zip(masses, speeds)]
    while True:
        for i in range(len(row) - 1):
            if row[i][1] > 0 and row[i + 1][1] < 0:
                a, b = row[i][0] * row[i][1], -row[i + 1][0] * row[i + 1][1]
                row = row[:i] + ([row[i]] if a > b else [row[i + 1]] if b > a else []) + row[i + 2:]
                break
        else: return row


def ref_acp(words, queries):
    return [[w for w in words if sorted(w) == sorted(q)] for q in queries]


def ref_bpg(balls):
    memo = {}

    def best(l, r):  # score difference for the player to move on balls[l:r]
        if l >= r: return 0
        if (l, r) not in memo:
            opts = [balls[l] - best(l + 1, r), balls[r - 1] - best(l, r - 1)]
            if r - l >= 2: opts += [balls[l] + balls[l + 1] - best(l + 2, r), balls[r - 1] + balls[r - 2] - best(l, r - 2)]
            memo[(l, r)] = max(opts)
        return memo[(l, r)]
    return (sum(balls) + best(0, len(balls))) // 2


def ref_bmd(participants):
    out = []
    for country in sorted({p[1] for p in participants}):
        people = [p for p in participants if p[1] == country]
        dates = sorted({d for p in people for d in p[2]})
        if not dates: continue
        counts = [(sum(1 for p in people if d in p[2]), d) for d in dates]
        top = max(c for c, _ in counts)
        date = min(d for c, d in counts if c == top)
        out.append([country, date, [p[0] for p in people if date in p[2]]])
    return out


def ref_bub(grid):
    g = [list(r) for r in grid]; m, n = len(g), len(g[0])
    while True:
        marked = set()
        for r in range(m):
            for c in range(n):
                if not g[r][c]: continue
                same = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= r + dr < m and 0 <= c + dc < n and g[r + dr][c + dc] == g[r][c]]
                if len(same) >= 2: marked.add((r, c)); marked.update(same)
        if not marked: return g
        for r, c in marked: g[r][c] = 0
        for c in range(n):
            col = [g[r][c] for r in range(m) if g[r][c]]
            col = [0] * (m - len(col)) + col
            for r in range(m): g[r][c] = col[r]


def ref_bsn(nums):
    best = None
    for perm in itertools.permutations([str(x) for x in nums]):
        s = ''.join(perm)
        if s[0] == '0' and s.strip('0'): continue
        if best is None or s < best: best = s
    return best if best.strip('0') else '0'


def ref_spk(arr):
    if not arr: return 0
    best = 0
    for peak in sorted(set(arr)):  # try every peak; each side uses distinct smaller values
        below = len({x for x in arr if x < peak}); twice = len({x for x in arr if x < peak and arr.count(x) >= 2})
        best = max(best, 1 + below + twice)
    return best


def ref_cpu(logs):
    if not logs: return []
    start, end = int(logs[0][2]), int(logs[-1][2])
    total = {}
    for name, _, _ in logs: total[name] = 0
    for unit in range(start, end):  # mark every unit [unit, unit + 1)
        stack = []
        for name, action, ts in logs:
            if int(ts) > unit: break
            if action == 'enter': stack.append(name)
            else: stack.pop()
        if stack: total[stack[-1]] += 1
    return [[k, total[k]] for k in sorted(total)]


def ref_cae(message, shift):
    out = []
    for ch in message:
        for alphabet in ('abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            if ch in alphabet:
                ch = alphabet[(alphabet.index(ch) + shift) % 26]; break
        out.append(ch)
    return ''.join(out)


def reference(uid, args):
    validate_domain(uid, args)
    if uid == ZBP:
        return ref_zbp(args[0])
    if uid == VPS:
        if args[0] * (len(args[1]) + 1) > 40000: raise ValueError('reference budget')
        return ref_vps(*args)
    if uid == WAK:
        if len(args[0]) * args[1] > 200000: raise ValueError('reference budget')
        return ref_wak(*args)
    if uid in (TOK1, TOK2, TOK3):
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_tok(uid, *args)
    if uid == API:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_api(*args)
    if uid in (ARD1, ARD2):
        if len(args[0]) > 1000: raise ValueError('reference budget')
        return ref_ard(uid, *args)
    if uid == DRL:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_drl(*args)
    if uid == AST:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_ast(*args)
    if uid == ACP:
        if len(args[0]) * len(args[1]) > 40000: raise ValueError('reference budget')
        return ref_acp(*args)
    if uid == BPG:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_bpg(args[0])
    if uid == BMD:
        if len(args[0]) > 200: raise ValueError('reference budget')
        return ref_bmd(args[0])
    if uid == BUB:
        if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
        return ref_bub(args[0])
    if uid in (BSN1, BSN2):
        if len(args[0]) > 7: raise ValueError('reference budget')
        return ref_bsn(args[0])
    if uid == SPK:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_spk(args[0])
    if uid == CPU:
        if not args[0]: return []
        if len(args[0]) * (int(args[0][-1][2]) - int(args[0][0][2]) + 1) > 200000: raise ValueError('reference budget')
        return ref_cpu(args[0])
    if len(args[0]) > 5000: raise ValueError('reference budget')
    return ref_cae(*args)
