"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (string comparison of
substituted types, full log scans, substring enumeration, linear next-center scans, list-scan
eviction, per-start automaton simulation, full board recounts, line-string building, linear worker
scans, leftmost-zero scans, repeated rescans, per-start simulation, recursive descent with exact
fractions, sorting, Cartesian products, per-block coordinate scans and backtracking) and refuse
inputs above a small budget.
"""
from fractions import Fraction
from itertools import product
import re

H = 'hack2hire:'
TLG1 = H + '69166e5710632c00111ca0eb'
TLG2 = H + '6916714410632c00111ca0f3'
VLA = H + '68094bed31dc778b35c5d171'
VSS = H + '67fdb0ced2adf72ba62b0eda'
WPA = H + '699926ca6e73e4abccc9a376'
WCA = H + '68d30311d490dee995152f5b'
WSE = H + '68815970f96758aa78e1d6b1'
WDG = H + '69c81f4621f6ab4226966b28'
WSL = H + '68e86c2f80f69c7a01706886'
WTM1 = H + '697a5a552ae9e181e44b7b96'
WTM2 = H + '697a5dbe2ae9e181e44b7b9d'
WTM3 = H + '697a5dbf2ae9e181e44b7b9e'
ABA = H + '69a35cd56e73e4abccc9bfb7'
AEG = H + '68ad961ccdaebe9459ce9a83'
BSM = H + '6763722dcc8f5deed53ccd73'
BCA = H + '692d0f861abcca80b112238f'
BSD1 = H + '6a4d607d60d5cca82da2fdb8'
BSD2 = H + '6a4d62db60d5cca82da2fdda'
BCB = H + '68eabd503a3bb8f8354249a7'
BSA = H + '687e9cfe7bd121d1f502daa2'

IDS = (TLG1, TLG2, VLA, VSS, WPA, WCA, WSE, WDG, WSL, WTM1, WTM2, WTM3, ABA, AEG, BSM, BCA, BSD1, BSD2, BCB, BSA)
TLG = (TLG1, TLG2)
WTM = (WTM1, WTM2, WTM3)
BSD = (BSD1, BSD2)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    VLA: ('ViolationLogAnalyzer', 1, {'countPolicies': 3, 'countPosts': 3, 'countViolations': 2}, ()),
    WCA: ('WeightedCache', 1, {'put': 3, 'get': 1}, ('put',)),
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


PRIMITIVES = ('int', 'char', 'float')


def tlg_nodes(node, allow_generic):
    """Validate one type node iteratively; return its node count."""
    count, stack = 0, [(node, 1)]
    while stack:
        v, d = stack.pop(); count += 1
        if type(v) is str:
            if v not in PRIMITIVES and not (allow_generic and re.fullmatch(r'T[0-9]', v)): raise ValueError('type node')
        elif type(v) is list:
            if not v or d > 20: raise ValueError('tuple shape or depth')
            stack.extend((x, d + 1) for x in v)
        else: raise ValueError('type node')
    return count


def tlg_domain(uid, args):
    envelope(args, 2 if uid == TLG1 else 3)
    sized(args[0], 0, 10000)
    total = sum(tlg_nodes(x, True) for x in args[0]) + tlg_nodes(args[1], True)
    if uid == TLG2:
        sized(args[2], 0, 10000)
        total += sum(tlg_nodes(x, False) for x in args[2])
    if total > (20000 if uid == TLG1 else 40000): raise ValueError('node budget')


DATE = r'20[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-8])'


def vla_domain(args):
    calls = trace(VLA, args, 101)
    logs = args[1][0][0]; sized(logs, 0, 10000); last = ''
    for log in logs:
        sized(log, 3, 3); text(log[0], r'[a-z0-9]{1,8}'); text(log[1], r'[a-z]{1,10}'); text(log[2], DATE)
        if log[2] < last: raise ValueError('logs not sorted by date')
        last = log[2]
    for op, row in calls:
        if op != 'countViolations': text(row[0], r'[a-z0-9]{1,8}' if op == 'countPolicies' else r'[a-z]{1,10}')
        for d in row[-2:]: text(d, DATE)


def wpa_domain(caps, log):
    intlist(caps, 1, 10**9, 1, 10000); sized(log, 0, 100000)
    closed, open_count = set(), len(caps)
    for entry in log:
        if entry == 'PACKAGE': continue
        text(entry, r'CLOSURE (0|[1-9][0-9]{0,4})')
        i = int(entry[8:])
        if i >= len(caps) or i in closed or open_count == 1: raise ValueError('closure')
        closed.add(i); open_count -= 1


def wca_domain(args):
    calls = trace(WCA, args, 100001)
    integer(args[1][0][0], 1, 10**12)
    for op, row in calls:
        text(row[0], r'[a-z0-9]{1,10}')
        if op == 'put': integer(row[1], 0, 10**9); integer(row[2], 1, 10**9)


def edge(move):
    sized(move, 4, 4)
    for v in move: integer(v, 0, 8)
    a, b = (move[0], move[1]), (move[2], move[3])
    if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1: raise ValueError('not adjacent')
    return min(a, b), max(a, b)


def wdg_domain(moves):
    sized(moves, 0, 144)
    if len({edge(m) for m in moves}) != len(moves): raise ValueError('repeated stick')


def wsl_domain(board, word):
    sized(board, 1, 50); width = len(board[0]) if type(board[0]) is list else -1
    for row in board:
        sized(row, 1, 50)
        if len(row) != width: raise ValueError('ragged board')
        for c in row: text(c, r'[A-Za-z]', 1)
    text(word, r'[A-Za-z]{1,50}', 50)


def wtm_domain(uid, args):
    envelope(args, {WTM1: 2, WTM2: 4, WTM3: 5}[uid])
    workers = args[0]; sized(workers, 1, 1000)
    for w in workers: text(w, r'[a-z]{1,10}')
    if len(set(workers)) != len(workers): raise ValueError('duplicate worker')
    tasks = args[-2] if uid != WTM1 else args[1]; sized(tasks, 0, 100000)
    for t in tasks:
        sized(t, 2, 2); integer(t[0], 0, 10**9); integer(t[1], 1, 10000)
    if len({t[0] for t in tasks}) != len(tasks): raise ValueError('duplicate task id')
    if uid == WTM1: return
    specialties, types = args[1], args[-1]
    sized(specialties, len(workers), len(workers)); sized(types, len(tasks), len(tasks))
    for s in specialties:
        sized(s, 0, 5)
        for t in s: text(t, r'[a-z]{1,8}')
        if len(set(s)) != len(s): raise ValueError('duplicate specialty')
    for t in types: text(t, r'[a-z]{1,8}')
    if uid == WTM3: intlist(args[2], 0, 100000, len(workers), len(workers))


def aba_domain(arr, ops):
    intlist(arr, 0, 1, 1, 100000); sized(ops, 0, 100000)
    for op in ops:
        if op == '1': continue
        text(op, r'2 (0|[1-9][0-9]{0,5})')
        if int(op[2:]) >= len(arr): raise ValueError('index')


def aeg_domain(words, categories, username):
    sized(words, 0, 10000)
    for w in words: text(w, r'[a-z]{1,15}')
    sized(categories, 0, 1000)
    for pair in categories:
        sized(pair, 2, 2); text(pair[0], r'[a-z]{1,15}'); text(pair[1], r'[A-Za-z]{1,15}')
    if len({p[0] for p in categories}) != len(categories): raise ValueError('duplicate keyword')
    text(username, r'[A-Za-z0-9]{1,20}')


def bsm_domain(initial, transactions):
    integer(initial, 0, 10**9); intlist(transactions, -10**9, 10**9)
    if 0 in transactions: raise ValueError('zero transaction')


BOUND = 10**15


def bca_value(s):
    """Validate the expression grammar and evaluate it iteratively (shunting-yard) with exact bounds checks."""
    text(s, r'[0-9+\-*/()]{1,100000}', 100000)
    values, ops = [], []
    prec = {'+': 1, '-': 1, '*': 2, '/': 2}

    def check(v):
        if abs(v) > BOUND: raise ValueError('magnitude bound')
        return v

    def apply():
        op = ops.pop()
        if op == 'u': values.append(-values.pop()); return
        b, a = values.pop(), values.pop()
        if op == '+': values.append(check(a + b))
        elif op == '-': values.append(check(a - b))
        elif op == '*': values.append(check(a * b))
        else:
            if b == 0: raise ValueError('division by zero')
            q = abs(a) // abs(b); values.append(q if (a < 0) == (b < 0) else -q)

    expect_operand, depth, i = True, 0, 0
    while i < len(s):
        c = s[i]
        if c.isdigit():
            if not expect_operand: raise ValueError('syntax')
            j = i
            while j < len(s) and s[j].isdigit(): j += 1
            lit = s[i:j]
            if len(lit) > 1 and lit[0] == '0' or int(lit) > 10**9: raise ValueError('literal')
            values.append(int(lit)); i = j; expect_operand = False
            while ops and ops[-1] == 'u': apply()
            continue
        if expect_operand:
            if c == '-': ops.append('u')
            elif c == '(':
                ops.append('('); depth += 1
                if depth > 50000: raise ValueError('nesting')
            else: raise ValueError('syntax')
        elif c == ')':
            while ops and ops[-1] != '(': apply()
            if not ops: raise ValueError('unbalanced')
            ops.pop(); depth -= 1
            while ops and ops[-1] == 'u': apply()
        elif c in prec:
            while ops and ops[-1] in prec and prec[ops[-1]] >= prec[c]: apply()
            ops.append(c); expect_operand = True
        else: raise ValueError('syntax')
        i += 1
    if expect_operand or depth: raise ValueError('incomplete expression')
    while ops: apply()
    return values[0]


def bsd_domain(uid, scores, width=None):
    tmax, vmax, cells = (1000, 1000, 200000) if uid == BSD1 else (200, 100, 20000)
    sized(scores, 1, tmax); v = len(scores[0]) if type(scores[0]) is list else 0
    if not 1 <= v <= vmax or len(scores) * v > cells: raise ValueError('shape')
    for row in scores:
        intlist(row, -10**6, 10**6, v, v)
    if uid == BSD2: integer(width, 1, 20)


def bcb_domain(m, n, coordinates):
    integer(m, 2, 100000); integer(n, 2, 100000); sized(coordinates, 0, 10000)
    for c in coordinates:
        sized(c, 2, 2); integer(c[0], 0, m - 1); integer(c[1], 0, n - 1)
    if len({tuple(c) for c in coordinates}) != len(coordinates): raise ValueError('duplicate cell')


def bsa_domain(blocks, target):
    sized(blocks, 0, 100)
    for b in blocks:
        sized(b, 1, 26)
        for c in b: text(c, r'[a-z]', 1)
    text(target, r'[a-z]{0,100}')


def validate_domain(uid, args):
    if uid in TLG: tlg_domain(uid, args)
    elif uid == VLA: vla_domain(args)
    elif uid == VSS: envelope(args, 1); text(args[0], r'[a-z]{0,100000}', 100000)
    elif uid == WPA: envelope(args, 2); wpa_domain(*args)
    elif uid == WCA: wca_domain(args)
    elif uid == WSE: envelope(args, 2); text(args[0], r'[a-z*]{0,100000}', 100000); text(args[1], r'[a-z]{0,100000}', 100000)
    elif uid == WDG: envelope(args, 1); wdg_domain(args[0])
    elif uid == WSL: envelope(args, 2); wsl_domain(*args)
    elif uid in WTM: wtm_domain(uid, args)
    elif uid == ABA: envelope(args, 2); aba_domain(*args)
    elif uid == AEG: envelope(args, 3); aeg_domain(*args)
    elif uid == BSM: envelope(args, 2); bsm_domain(*args)
    elif uid == BCA: envelope(args, 1); bca_value(args[0])
    elif uid in BSD: envelope(args, 1 if uid == BSD1 else 2); bsd_domain(uid, *args)
    elif uid == BCB: envelope(args, 3); bcb_domain(*args)
    elif uid == BSA: envelope(args, 2); bsa_domain(*args)
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_format(node):
    if type(node) is str: return node
    out = '['
    for k, x in enumerate(node):
        if k: out = out + ', '
        out = out + ref_format(x)
    return out + ']'


def ref_tlg1(params, ret):
    return '(' + ', '.join(ref_format(p) for p in params) + ') -> ' + ref_format(ret)


def ref_subst(node, binding):
    if type(node) is str: return binding.get(node, node)
    return [ref_subst(x, binding) for x in node]


def ref_tlg2(params, ret, args):
    if len(params) != len(args): return None
    binding, stack = {}, list(zip(params, args))
    while stack:
        p, a = stack.pop()
        if type(p) is str and p[0] == 'T':
            binding.setdefault(p, a)
        elif type(p) is list and type(a) is list and len(p) == len(a):
            stack.extend(zip(p, a))
    if ref_format(ref_subst(params, binding)) != ref_format(args): return None
    return ref_format(ref_subst(ret, binding))


def ref_vla(logs, calls):
    out = [None]
    for op, row in calls:
        lo, hi = row[-2], row[-1]
        if op == 'countPolicies': keys = {l[1] for l in logs if l[0] == row[0] and lo <= l[2] <= hi}
        elif op == 'countPosts': keys = {l[0] for l in logs if l[1] == row[0] and lo <= l[2] <= hi}
        else: keys = {(l[0], l[1]) for l in logs if lo <= l[2] <= hi}
        out.append(len(keys))
    return out


def ref_vss(s):
    total = 0
    for i in range(len(s)):
        seen = set()
        for j in range(i, len(s)):
            if s[j] not in 'aeiou': break
            seen.add(s[j])
            if len(seen) == 5: total += 1
    return total


def ref_wpa(caps, log):
    n = len(caps); closed = [False] * n; got = [0] * n; cur, used = 0, 0

    def nxt(i):
        j = (i + 1) % n
        while closed[j]: j = (j + 1) % n
        return j
    for entry in log:
        if entry == 'PACKAGE':
            got[cur] += 1; used += 1
            if used == caps[cur]: cur, used = nxt(cur), 0
        else:
            i = int(entry.split()[1]); closed[i] = True
            if i == cur: cur, used = nxt(cur), 0
    best = 0
    for i in range(n):
        if got[i] >= got[best]: best = i
    return best


def ref_wca(limit, calls):
    items, out, clock = [], [None], 0   # [key, value, weight, stamp]
    for op, row in calls:
        if op == 'get':
            hit = [it for it in items if it[0] == row[0]]
            out.append(hit[0][1] if hit else -1); continue
        clock += 1
        items = [it for it in items if it[0] != row[0]] + [[row[0], row[1], row[2], clock]]
        while sum(it[2] for it in items) > limit:
            victim = items[0]
            for it in items:
                if it[2] > victim[2] or it[2] == victim[2] and it[3] < victim[3]: victim = it
            items.remove(victim)
        out.append(None)
    return out


def ref_wse(pattern, s):
    m = len(pattern)

    def close(states):
        states = set(states); grew = True
        while grew:
            grew = False
            for p in list(states):
                if p < m and pattern[p] == '*' and p + 1 not in states: states.add(p + 1); grew = True
        return states
    for i in range(len(s) + 1):
        states = close({0})
        if m in states: return i
        for c in s[i:]:
            states = close({p + 1 for p in states if p < m and pattern[p] == c} | {p for p in states if p < m and pattern[p] == '*'})
            if m in states: return i
            if not states: break
    return -1


def ref_wdg(moves):
    sticks, score = set(), [0, 0]

    def boxes():
        done = 0
        for r in range(8):
            for c in range(8):
                sides = [((r, c), (r, c + 1)), ((r + 1, c), (r + 1, c + 1)), ((r, c), (r + 1, c)), ((r, c + 1), (r + 1, c + 1))]
                done += all(sd in sticks for sd in sides)
        return done
    for k, mv in enumerate(moves):
        before = boxes()
        a, b = (mv[0], mv[1]), (mv[2], mv[3]); sticks.add((min(a, b), max(a, b)))
        score[k % 2] += boxes() - before
    return 0 if score[0] == score[1] else (1 if score[0] > score[1] else 2)


def ref_wsl(board, word):
    m, n = len(board), len(board[0]); lines = []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for r in range(m):
            for c in range(n):
                if 0 <= r - dr < m and 0 <= c - dc < n: continue   # not a line start
                cells, rr, cc = '', r, c
                while 0 <= rr < m and 0 <= cc < n: cells += board[rr][cc]; rr += dr; cc += dc
                lines += [cells, cells[::-1]]
    return any(word in line for line in lines)


def ref_wtm(uid, args):
    workers = args[0]; tasks = args[1] if uid == WTM1 else args[-2]
    spec = args[1] if uid != WTM1 else [None] * len(workers)
    limit = args[2] if uid == WTM3 else [10**9] * len(workers)
    types = args[-1] if uid != WTM1 else [None] * len(tasks)
    load = [0] * len(workers); lists = [[] for _ in workers]; left = []
    for (tid, dur), typ in zip(tasks, types):
        best = -1
        for i in range(len(workers)):
            if uid != WTM1 and typ not in spec[i]: continue
            if len(lists[i]) >= limit[i]: continue
            if best < 0 or (load[i], workers[i]) < (load[best], workers[best]): best = i
        if best < 0: left.append(tid); continue
        load[best] += dur; lists[best].append(tid)
    return lists if uid == WTM1 else lists + [left]


def ref_aba(arr, ops):
    a = list(arr)
    for op in ops:
        if op == '1':
            for i in range(len(a)):
                if a[i] == 0: a[i] = 1; break
        else: a[int(op[2:])] = 0
    return a


def ref_aeg(words, categories, username):
    lines = ['Dear ' + username + ',']
    cats = sorted({c for k, c in categories if k in words})
    if not cats: return lines[0] + '\nNo violations found.'
    for cat in cats:
        kws = [k for k, c in categories if c == cat]
        order = []
        for w in words:
            if w in kws and w not in order: order.append(w)
        lines.append(cat + ': ' + ', '.join('%s (%d)' % (w, words.count(w)) for w in order))
    return '\n'.join(lines)


def ref_bsm(initial, tx):
    best = 0
    for s in range(len(tx)):
        bal, k = initial, s
        while k < len(tx) and bal + tx[k] >= 0: bal += tx[k]; k += 1
        best = max(best, k - s)
    return best


def ref_bca(s):
    pos = [0]

    def peek(): return s[pos[0]] if pos[0] < len(s) else ''

    def expr():
        v = term()
        while peek() in ('+', '-') and peek():
            op = s[pos[0]]; pos[0] += 1; w = term()
            v = v + w if op == '+' else v - w
        return v

    def term():
        v = factor()
        while peek() in ('*', '/') and peek():
            op = s[pos[0]]; pos[0] += 1; w = factor()
            v = v * w if op == '*' else Fraction(int(Fraction(v, w)))
        return v

    def factor():
        c = peek()
        if c == '-': pos[0] += 1; return -factor()
        if c == '(':
            pos[0] += 1; v = expr(); pos[0] += 1; return v
        j = pos[0]
        while pos[0] < len(s) and s[pos[0]].isdigit(): pos[0] += 1
        return Fraction(int(s[j:pos[0]]))
    value = expr()
    assert value.denominator == 1
    return int(value)


def ref_bsd1(scores):
    return [sorted(range(len(row)), key=lambda j: (-row[j], j))[0] for row in scores]


def ref_bsd2(scores, width):
    seqs = sorted(product(*[range(len(r)) for r in scores]), key=lambda q: (-sum(scores[i][j] for i, j in enumerate(q)), q))
    return [list(q) for q in seqs[:width]]


def ref_bcb(m, n, coords):
    corners = set()
    for x, y in coords:
        for a in (x - 1, x):
            for b in (y - 1, y):
                if 0 <= a < m - 1 and 0 <= b < n - 1: corners.add((a, b))
    out = [[], [], [], []]
    for a, b in sorted(corners):
        k = sum(1 for x, y in coords if a <= x <= a + 1 and b <= y <= b + 1)
        out[k - 1].append([a, b])
    return out


def ref_bsa(blocks, target):
    used = [False] * len(blocks)

    def go(i):
        if i == len(target): return True
        for b, block in enumerate(blocks):
            if not used[b] and target[i] in block:
                used[b] = True
                if go(i + 1): return True
                used[b] = False
        return False
    return len(target) <= len(blocks) and go(0)


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == TLG1:
        budget(len(args[0]) <= 200); return ref_tlg1(*args)
    if uid == TLG2:
        budget(len(args[0]) <= 200); return ref_tlg2(*args)
    if uid == VSS:
        budget(len(args[0]) <= 400); return ref_vss(args[0])
    if uid == WPA:
        budget(len(args[0]) * len(args[1]) <= 20000); return ref_wpa(*args)
    if uid == WSE:
        budget(len(args[0]) * len(args[1]) <= 2000); return ref_wse(*args)
    if uid == WDG: return ref_wdg(args[0])
    if uid == WSL:
        budget(len(args[0]) * len(args[0][0]) <= 400); return ref_wsl(*args)
    if uid in WTM:
        budget(len(args[0]) * len(args[-2] if uid != WTM1 else args[1]) <= 20000); return ref_wtm(uid, args)
    if uid == ABA:
        budget(len(args[0]) * len(args[1]) <= 40000); return ref_aba(*args)
    if uid == AEG:
        budget(len(args[0]) * len(args[1]) <= 20000); return ref_aeg(*args)
    if uid == BSM:
        budget(len(args[1]) <= 400); return ref_bsm(*args)
    if uid == BCA:
        budget(len(args[0]) <= 300); return ref_bca(args[0])
    if uid == BSD1:
        budget(len(args[0]) * len(args[0][0]) <= 5000); return ref_bsd1(args[0])
    if uid == BSD2:
        budget(len(args[0][0]) ** len(args[0]) <= 4000); return ref_bsd2(*args)
    if uid == BCB:
        budget(len(args[2]) <= 200); return ref_bcb(*args)
    if uid == BSA:
        budget(len(args[0]) <= 9); return ref_bsa(*args)
    if uid == VLA:
        calls = trace(uid, args, 101)
        budget(len(args[1][0][0]) * len(calls) <= 20000); return ref_vla(args[1][0][0], calls)
    calls = trace(uid, args, 100001)
    budget(len(calls) <= 300); return ref_wca(args[1][0][0], calls)
