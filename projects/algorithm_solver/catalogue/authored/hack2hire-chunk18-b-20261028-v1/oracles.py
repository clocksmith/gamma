"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (alphabet stepping,
per-cell column comparison, recursive descent, Python regular expressions, union-find, a literal
least-loaded greedy, regex label parsing with pairwise checks, list-based LRU caches with recursive
equality, day-by-day full-grid simulation, a brute-force stair walk per switch floor and label
propagation) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
NCT = H + '69a367fe6e73e4abccc9bfe1'
OHE = H + '68f599dba269f53ea0eff890'
PTP = H + '67806bd26fee41e51af73dde'
RPM = H + '67a23c6bc5f86173882e3d8d'
SIM = H + '678dd668fa7ce9616e190fba'
DLS = H + '69fc0ee4574d87bc49005a3d'
DLV = H + '69fc131a574d87bc49005a6c'
FCC = H + '6a2db7bc5117d1b543565e24'
FCS = H + '6a2db7be5117d1b543565e25'
CSD = H + '69d414a179bf03c0074bcec1'
CIA = H + '69d414a379bf03c0074bcec2'
CFG = H + '69d414a479bf03c0074bcec5'
CGD = H + '6a4ff2eb665efda9311f57a7'
CID = H + '6a4ff779665efda9311f57b5'
OTE = H + '69ebd458068f42e15508912a'
PAE = H + '68dc36c49736cfa4e9062419'

IDS = (NCT, OHE, PTP, RPM, SIM, DLS, DLV, FCC, FCS, CSD, CIA, CFG, CGD, CID, OTE, PAE)
CELLULAR = (CSD, CIA, CFG, CGD, CID)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    FCC: ('FunctionCallCache', 1, {'call': 3}, ()),
    FCS: ('FunctionCallCache', 2, {'call': 3}, ()),
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


def trace(uid, args, maximum=20001):
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


def matrix(grid, lo, hi, maximum=200):
    sized(grid, 1, maximum)
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= maximum: raise ValueError('row width')
    for row in grid: intlist(row, lo, hi, len(grid[0]), len(grid[0]))


NAME = r'[a-z_][a-z0-9_]{0,15}'
KEY = r'[a-z_]{1,8}'


def value(v, depth=3):
    """JSON argument value: null, bool, int, short printable string, or a small list/object nested at most `depth` levels."""
    if v is None or type(v) is bool: return
    if type(v) is int: return integer(v, -10**9, 10**9)
    if type(v) is str: return text(v, r'[ -~]*', 12)
    if depth == 0: raise ValueError('value nesting')
    if type(v) is list:
        sized(v, 0, 6)
        for x in v: value(x, depth - 1)
        return
    if type(v) is dict:
        if len(v) > 6: raise ValueError('object size')
        for k, x in v.items(): text(k, KEY, 8); value(x, depth - 1)
        return
    raise ValueError('value type')


def call_shape(row):
    text(row[0], NAME, 16); sized(row[1], 0, 6)
    for x in row[1]: value(x)
    if type(row[2]) is not dict or len(row[2]) > 6: raise ValueError('kwargs')
    for k, x in row[2].items(): text(k, KEY, 8); value(x)


def signatures(sig):
    if type(sig) is not dict or not 1 <= len(sig) <= 50: raise ValueError('signatures')
    for name, params in sig.items():
        text(name, NAME, 16); sized(params, 0, 6)
        names, defaulted = set(), False
        for p in params:
            if type(p) is not list or len(p) not in (1, 2): raise ValueError('parameter shape')
            text(p[0], KEY, 8)
            if p[0] in names: raise ValueError('repeated parameter')
            names.add(p[0])
            if len(p) == 2: value(p[1]); defaulted = True
            elif defaulted: raise ValueError('required parameter after a default')


def bindable(params, row):
    names = [p[0] for p in params]
    if len(row[1]) > len(names): raise ValueError('too many positional arguments')
    for k in row[2]:
        if k not in names or names.index(k) < len(row[1]): raise ValueError('unknown or doubly bound keyword')
    for i, p in enumerate(params):
        if len(p) == 1 and i >= len(row[1]) and p[0] not in row[2]: raise ValueError('missing required argument')


def prefix_valid(expression):
    """Right-to-left operand counting (independent of the recursive reference)."""
    text(expression, r'[A-Za-z0-9+\-*/^]+', 100000)
    count = 0
    for ch in reversed(expression):
        if ch in '+-*/^':
            if count < 2: raise ValueError('operator lacks operands')
            count -= 1
        else: count += 1
    if count != 1: raise ValueError('not a single expression')


def validate_domain(uid, args):
    if type(uid) is not str or uid not in IDS: raise ValueError('unknown uid')
    if uid in CLASSES:
        calls = trace(uid, args); integer(args[1][0][0], 1, 10**4)
        if uid == FCS: signatures(args[1][0][1])
        for _, row in calls:
            call_shape(row)
            if uid == FCS:
                if row[0] not in args[1][0][1]: raise ValueError('unknown function')
                bindable(args[1][0][1][row[0]], row)
        return calls
    if uid == NCT:
        envelope(args, 1); text(args[0], r'[a-z]+', 100000); return
    if uid == OHE:
        envelope(args, 1); intlist(args[0], -10**9, 10**9, 1, 1000); return
    if uid == PTP:
        envelope(args, 1); return prefix_valid(args[0])
    if uid == RPM:
        envelope(args, 2); text(args[0], r'[a-z]*', 1000); text(args[1], r'(?:(?:[a-z.]|\([a-z.]+\))\*?)+', 200); return
    if uid == SIM:
        envelope(args, 1); return matrix(args[0], 0, 10**6)
    if uid in (DLS, DLV):
        envelope(args, 4 if uid == DLS else 5)
        integer(args[0], 1, 10**5); integer(args[1], 1, 10**4); integer(args[2], 1, 10**4)
        integer(args[3], 1, 50)
        if args[0] * args[3] > 10**5: raise ValueError('schedule size')
        if uid == DLV:
            sized(args[4], 0, 100000)
            for t in args[4]:
                sized(t, 3, 3)
                for s in t: text(s, r'[a-z0-9]{1,8}', 8)
        return
    if uid in CELLULAR:
        envelope(args, 3 if uid == CGD else 2); matrix(args[0], 0, 1); integer(args[1], 1, 8)
        if uid == CGD: integer(args[2], 0, 10**9)
        return
    if uid == OTE:
        envelope(args, 5); integer(args[0], 1, 1000)
        for v in args[1:4]: integer(v, 1, 10**6)
        integer(args[4], 1, 10**9); return
    envelope(args, 2); intlist(args[0], -10**9, 10**9, 1); sized(args[1], 0, 100000)
    for p in args[1]: intlist(p, -10**9, 10**9, 2, 2)


# ---------------------------------------------------------------- references
def ref_nct(s):
    out = ''
    for ch in s:
        if ch in 'aeiou': out += ch; continue
        code = ord(ch)
        while True:
            code = 97 if code == 122 else code + 1
            if chr(code) not in 'aeiou': break
        out += chr(code)
    return out


def ref_ohe(arr):
    cols = sorted(set(arr))
    return [[1 if c == x else 0 for c in cols] for x in arr]


def ref_ptp(expression):
    def parse(i):
        ch = expression[i]
        if ch not in '+-*/^': return ch, i + 1
        left, i = parse(i + 1); right, i = parse(i)
        return left + right + ch, i
    return parse(0)[0]


def ref_rpm(text_, pattern):
    regex = pattern.replace('.', '[a-z]').replace('(', '(?:')
    return re.fullmatch(regex, text_) is not None


def ref_sim(grid):
    m, n = len(grid), len(grid[0]); parent = list(range(m * n))

    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    for i in range(m):
        for j in range(n):
            if grid[i][j] <= 0: continue
            for a, b in ((i + 1, j), (i, j + 1)):
                if a < m and b < n and grid[a][b] > 0: parent[find(a * n + b)] = find(i * n + j)
    sums = {}
    for i in range(m):
        for j in range(n):
            if grid[i][j] > 0: r = find(i * n + j); sums[r] = sums.get(r, 0) + grid[i][j]
    return max(sums.values(), default=0)


def ref_dls(tasks, models, humans, k):
    if k > humans or k > models: return []
    hload, mload, out = [0] * humans, [0] * models, []
    for t in range(tasks):
        used_h, used_m = set(), set()
        for _ in range(k):
            h = min((x for x in range(humans) if x not in used_h), key=lambda x: (hload[x], x))
            m = min((x for x in range(models) if x not in used_m), key=lambda x: (mload[x], x))
            used_h.add(h); used_m.add(m); hload[h] += 1; mload[m] += 1
            out.append(['t%d' % (t + 1), 'm%d' % (m + 1), 'h%d' % (h + 1)])
    return out


def ref_dlv(tasks, models, humans, k, schedule):
    def label(s, letter, top):
        hit = re.fullmatch(letter + r'([1-9][0-9]*)', s)
        return hit is not None and int(hit.group(1)) <= top
    by_task = {}
    for t, m, h in schedule:
        if not (label(t, 't', tasks) and label(m, 'm', models) and label(h, 'h', humans)): return False
        by_task.setdefault(t, []).append((m, h))
    if len(by_task) != tasks or any(len(v) != k for v in by_task.values()): return False
    for v in by_task.values():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                if v[i][0] == v[j][0] or v[i][1] == v[j][1]: return False
    return True


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if type(a) is dict: return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    return a == b


def lru(capacity, keys):
    entries, out = [], [None]
    for key in keys:
        hit = next((i for i, e in enumerate(entries) if same(e, key)), None)
        if hit is not None: entries.append(entries.pop(hit)); out.append(True); continue
        entries.append(key)
        if len(entries) > capacity: entries.pop(0)
        out.append(False)
    return out


def ref_fcc(capacity, calls):
    return lru(capacity, [[row[0], row[1], row[2]] for _, row in calls])


def ref_fcs(capacity, sig, calls):
    keys = []
    for _, (name, pos, kw) in calls:
        params = sig[name]; bound = {}
        for i, p in enumerate(params):
            bound[p[0]] = pos[i] if i < len(pos) else kw[p[0]] if p[0] in kw else p[1]
        keys.append([name, bound])
    return lru(capacity, keys)


def ref_cells(grid, threshold):
    """Day-by-day simulation; returns the infection-day matrix (-1 never)."""
    m, n = len(grid), len(grid[0])
    state = [list(r) for r in grid]
    day = [[0 if v else -1 for v in r] for r in grid]
    d = 0
    while True:
        d += 1; new = []
        for i in range(m):
            for j in range(n):
                if state[i][j]: continue
                c = sum(state[a][b] for a in range(i - 1, i + 2) for b in range(j - 1, j + 2) if (a, b) != (i, j) and 0 <= a < m and 0 <= b < n)
                if c >= threshold: new.append((i, j))
        if not new: return day
        for i, j in new: state[i][j] = 1; day[i][j] = d


def ref_cellular(uid, args):
    day = ref_cells(args[0], args[1])
    last = max(0, max(max(r) for r in day))
    if uid == CSD: return last
    if uid == CIA: return -1 if any(-1 in r for r in day) else last
    if uid == CFG: return [[1 if v >= 0 else 0 for v in r] for r in day]
    if uid == CGD: return [[1 if 0 <= v <= args[2] else 0 for v in r] for r in day]
    return day


def ref_ote(n, e1, t1, e2, c):
    best = None
    for k in range(n + 1):
        energy, time, ok = k * e1, k * t1, True
        for _ in range(n - k):
            if energy <= 0: ok = False; break
            time += -(-c // energy); energy -= e2
        if ok and (best is None or time < best): best = time
    return best


def ref_pae(nums, pairs):
    label = {v: v for v in nums}
    for a, b in pairs: label.setdefault(a, a); label.setdefault(b, b)
    changed = True
    while changed:
        changed = False
        for a, b in pairs:
            low = min(label[a], label[b])
            if label[a] != low or label[b] != low: label[a] = label[b] = low; changed = True
    groups, order = {}, []
    for v in nums:
        if label[v] not in groups: groups[label[v]] = []; order.append(label[v])
        groups[label[v]].append(v)
    return [groups[g] for g in order]


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid == FCC: return ref_fcc(args[1][0][0], calls)
        return ref_fcs(args[1][0][0], args[1][0][1], calls)
    if uid == NCT:
        budget(len(args[0]) <= 2000); return ref_nct(args[0])
    if uid == OHE:
        budget(len(args[0]) <= 100); return ref_ohe(args[0])
    if uid == PTP:
        budget(len(args[0]) <= 400); return ref_ptp(args[0])
    if uid == RPM:
        budget(len(args[0]) <= 14 and len(args[1]) <= 24); return ref_rpm(*args)
    if uid == SIM:
        budget(len(args[0]) * len(args[0][0]) <= 400); return ref_sim(args[0])
    if uid == DLS:
        budget(args[0] * args[3] * (args[1] + args[2]) <= 20000); return ref_dls(*args)
    if uid == DLV:
        budget(len(args[4]) <= 400); return ref_dlv(*args)
    if uid in CELLULAR:
        budget(len(args[0]) * len(args[0][0]) <= 400); return ref_cellular(uid, args)
    if uid == OTE:
        budget(args[0] <= 300); return ref_ote(*args)
    budget(len(args[0]) + len(args[1]) <= 300); return ref_pae(*args)
