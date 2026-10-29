"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (linear list searches,
second-by-second clocks, augmenting-path flows, Bellman-Ford relaxation, binary-string prefix scans,
nested-loop joins, repeated full rescans, eager filtering, step-capped walks, sort-everything queries,
memoised suffix sets, set intersections, subset enumeration, per-window sorts, pair and triple
enumeration) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
FBT = H + '68e6bf5c605ab8e954684812'
FSQ = H + '69c7f82d21f6ab4226966a80'
GUU = H + '699bb8776e73e4abccc9aa11'
GDS = H + '67fda0b6d2adf72ba62b0ed9'
HOP = H + '68c4834e97640ed3834dc7ca'
IPR = H + '687eda22cdb08328ca5a8483'
DSJ1 = H + '6a1a0cc4c81f779dc6a2376b'
DSJ2 = H + '6a1a0ed3c81f779dc6a2377c'
DSJ3 = H + '6a1a0ee5c81f779dc6a2377d'
DSJ4 = H + '6a1a0f0dc81f779dc6a2377e'
ITS = H + '68a61ebd3a368733bb10424d'
IWF = H + '678dc780fa7ce9616e190fb7'
JBH = H + '6a14d69a7b0582b352787fa8'
KVP = H + '68099e1fcbb5948f87732b56'
KLC = H + '67e3915487527b3f41af78b6'
LCB = H + '67709b6d366afdc1233e4ffc'
LGS = H + '69ae2fec4b133b6a8f3a7345'
LKW = H + '6910e7e971ea59cda5a81ac4'
LRA1 = H + '69a4fb4e3d95612a1782bbd2'
LRA2 = H + '69b62ed7666464810ca36212'

IDS = (FBT, FSQ, GUU, GDS, HOP, IPR, DSJ1, DSJ2, DSJ3, DSJ4, ITS, IWF, JBH, KVP, KLC, LCB, LGS, LKW, LRA1, LRA2)
DSJ = (DSJ1, DSJ2, DSJ3, DSJ4)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    ITS: ('TaskScheduler', 0, {'addTask': 2, 'getExecutionOrder': 0}, ()),
    IWF: ('FilterIterator', 2, {'hasNext': 0, 'next': 0}, ()),
    KVP: ('KVStore', 0, {'set': 2, 'get': 1, 'update': 2, 'deleteKey': 1, 'prefixSearch': 1}, ('set', 'update', 'deleteKey')),
}


# ---------------------------------------------------------------- domain helpers
def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def intlist(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
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


USER = r'[a-z0-9]{1,10}'
NUM = r'0|[1-9][0-9]{0,9}'
FBT_FORMS = [r'v1/REGISTER/(%s)/(%s)' % (USER, NUM), r'v1/FRIEND_REQUEST/(%s)/(%s)' % (USER, USER),
             r'v1/ACCEPT_FRIEND_REQUEST/([0-9]{1,6})', r'v1/TRANSFER/(%s)/(%s)/([1-9][0-9]{0,9})' % (USER, USER), r'v1/BALANCE/(%s)' % USER]


def fbt_domain(requests):
    if type(requests) is not list or len(requests) > 100000: raise ValueError('requests')
    seen = set()
    for pair in requests:
        if type(pair) is not list or len(pair) != 2: raise ValueError('pair')
        text(pair[0], r'[0-9]{1,6}', 6)
        if pair[0] in seen: raise ValueError('duplicate sequence number')
        seen.add(pair[0])
        if type(pair[1]) is not str or len(pair[1]) > 60 or not any(re.fullmatch(f, pair[1]) for f in FBT_FORMS): raise ValueError('request form')
        m = re.fullmatch(FBT_FORMS[3], pair[1])
        if m and int(m.group(3)) > 10**9: raise ValueError('amount')
        m = re.fullmatch(FBT_FORMS[0], pair[1])
        if m and int(m.group(2)) > 10**9: raise ValueError('balance')


def guu_domain(names):
    if type(names) is not list or len(names) > 10000: raise ValueError('names')
    for name in names: text(name, r'[A-Za-z]{1,12}(?: [A-Za-z]{1,12}){1,4}', 70)


def gds_domain(intervals, n):
    if type(intervals) is not list or len(intervals) > 100000: raise ValueError('intervals')
    for iv in intervals:
        if type(iv) is not list or len(iv) != 2: raise ValueError('interval')
        integer(iv[0], 9, 16); integer(iv[1], iv[0] + 1, 17)
    integer(n, 1, 100000)


DIRECTIVES = r'(?:[LR](?:[1-9][0-9]{0,5})?){1,6}'


def hop_domain(s, start):
    if type(s) is not list or not 1 <= len(s) <= 100000: raise ValueError('board')
    for cell in s:
        if cell != 'X': text(cell, DIRECTIVES, 42)
        for step in re.findall(r'[0-9]+', cell):
            if int(step) > 100000: raise ValueError('step')
    integer(start, 0, len(s) - 1)


OCTET = r'(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])'
IP = r'%s(?:\.%s){3}' % (OCTET, OCTET)


def ipr_domain(routes, queries):
    if type(routes) is not list or len(routes) > 20000 or type(queries) is not list or len(queries) > 20000: raise ValueError('sizes')
    for r in routes:
        if type(r) is not list or len(r) != 2: raise ValueError('route')
        text(r[0], IP + r'/(?:3[0-2]|[12][0-9]|[0-9])', 18); text(r[1], r'[a-z0-9.-]{1,20}', 20)
    for q in queries: text(q, IP, 15)


COLUMN = r'[A-Za-z0-9_]{1,10}'
VALUE = r'[A-Za-z0-9_.-]{0,10}'


def csv_file(rows):
    if type(rows) is not list or not 1 <= len(rows) <= 20001: raise ValueError('file size')
    for r in rows:
        if type(r) is not str or len(r) > 120: raise ValueError('row')
    header = rows[0].split(',')
    if len(header) > 10 or len(set(header)) != len(header): raise ValueError('header')
    for h in header: text(h, COLUMN, 10)
    table = []
    for r in rows[1:]:
        values = r.split(',')
        if len(values) != len(header): raise ValueError('row width')
        for v in values: text(v, VALUE, 10)
        table.append(values)
    return header, table


def dsj_domain(uid, args):
    envelope(args, 3)
    ch, ct = csv_file(args[0]); ph, pt = csv_file(args[1])
    keys = args[2] if uid == DSJ4 else [args[2]]
    if uid == DSJ4 and (type(keys) is not list or not 1 <= len(keys) <= 3 or len(set(keys)) != len(keys)): raise ValueError('field names')
    for k in keys:
        if type(k) is not str or k not in ch or k not in ph: raise ValueError('field name')
    ci = [ch.index(k) for k in keys]; pi = [ph.index(k) for k in keys]
    count = {}
    for r in pt:
        key = tuple(r[i] for i in pi); count[key] = count.get(key, 0) + 1
    out = sum(count.get(tuple(r[i] for i in ci), 0) or (uid in (DSJ2, DSJ3)) for r in ct)
    if uid == DSJ3: out += len(pt)
    if out > 100000: raise ValueError('output rows')


ID = r'[a-z0-9]{1,8}'
FILTERS = ('even', 'odd', 'positive', 'negative', 'nonzero')


def accepts(name, v):
    return {'even': v % 2 == 0, 'odd': v % 2 != 0, 'positive': v > 0, 'negative': v < 0, 'nonzero': v != 0}[name]


def its_domain(args):
    for op, row in trace(ITS, args, 2501):
        if op == 'addTask':
            text(row[0], ID, 8)
            if type(row[1]) is not list or len(row[1]) > 10: raise ValueError('dependencies')
            for d in row[1]: text(d, ID, 8)
            if len(set(row[1])) != len(row[1]): raise ValueError('repeated dependency')


def iwf_domain(args):
    calls = trace(IWF, args, 200001)
    nums, name = args[1][0]
    intlist(nums, -10**9, 10**9)
    if name not in FILTERS: raise ValueError('filter name')
    remaining = sum(1 for v in nums if accepts(name, v))
    for op, _ in calls:
        if op == 'next':
            if remaining == 0: raise ValueError('next past the end')
            remaining -= 1


KEY = r'[a-z]{1,10}'


def kvp_domain(args):
    present = set()
    for op, row in trace(KVP, args, 100001):
        if op == 'prefixSearch': text(row[0], r'[a-z]{0,10}', 10); continue
        text(row[0], KEY, 10)
        if op in ('set', 'update'): integer(row[1], -10**9, 10**9)
        if op == 'set':
            if row[0] in present: raise ValueError('set of a present key')
            present.add(row[0])
        elif op == 'update' and row[0] not in present: raise ValueError('update of an absent key')
        elif op == 'deleteKey': present.discard(row[0])


KEYPAD = {'1': 'ABC', '2': 'DEF', '3': 'GHI', '4': 'JKL', '5': 'MNO', '6': 'PQR', '7': 'ST', '8': 'UVW', '9': 'XY', '0': 'Z'}


def klc_count(digits):
    """Number of decodings, by a DP over positions (domain bound only)."""
    ways = [0] * (len(digits) + 1); ways[len(digits)] = 1
    for i in range(len(digits) - 1, -1, -1):
        g = 1
        while g <= len(KEYPAD[digits[i]]) and i + g <= len(digits) and digits[i + g - 1] == digits[i]:
            ways[i] += ways[i + g]; g += 1
    return ways[0]


def level_order(a):
    """Decode a LeetCode level-order array into (values, left, right) index lists; root at 0."""
    if type(a) is not list or not a or type(a[0]) is not int: raise ValueError('tree')
    vals, left, right = [a[0]], [-1], [-1]
    queue, head, i = [0], 0, 1
    while i < len(a):
        if head >= len(queue): raise ValueError('dangling entries')
        parent = queue[head]; head += 1
        for side in (left, right):
            if i < len(a):
                if a[i] is not None:
                    if type(a[i]) is not int: raise ValueError('value type')
                    vals.append(a[i]); left.append(-1); right.append(-1); side[parent] = len(vals) - 1; queue.append(len(vals) - 1)
                i += 1
    if a[-1] is None: raise ValueError('trailing null')
    return vals, left, right


def bst_domain(a):
    if type(a) is not list or len(a) > 200001: raise ValueError('array size')
    vals, left, right = level_order(a)
    if len(vals) > 100000: raise ValueError('node count')
    out, stack, node = [], [], 0
    while stack or node != -1:
        while node != -1: stack.append(node); node = left[node]
        node = stack.pop(); out.append(vals[node]); node = right[node]
    for v in out: integer(v, -10**9, 10**9)
    if any(b <= a_ for a_, b in zip(out, out[1:])): raise ValueError('not a strict BST')


def lgs_domain(n, connections):
    integer(n, 1, 100000)
    if type(connections) is not list or len(connections) > n - 1: raise ValueError('connections')
    parent = list(range(n))

    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for e in connections:
        if type(e) is not list or len(e) != 2: raise ValueError('edge')
        integer(e[0], 0, n - 1); integer(e[1], 0, n - 1)
        a, b = find(e[0]), find(e[1])
        if a == b: raise ValueError('cycle, self-pair or repeated pair')
        parent[a] = b


def points_domain(points, maximum):
    if type(points) is not list or len(points) > maximum: raise ValueError('points')
    seen = set()
    for p in points:
        if type(p) is not list or len(p) != 2: raise ValueError('point')
        integer(p[0], 0, 40000); integer(p[1], 0, 40000)
        if tuple(p) in seen: raise ValueError('duplicate point')
        seen.add(tuple(p))


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == FBT:
        envelope(args, 1); fbt_domain(args[0])
    elif uid == FSQ:
        envelope(args, 4); intlist(args[0], 1, 10**9)
        for v in args[1:]: integer(v, 0, 10**9)
    elif uid == GUU:
        envelope(args, 1); guu_domain(args[0])
    elif uid == GDS:
        envelope(args, 2); gds_domain(*args)
    elif uid == HOP:
        envelope(args, 2); hop_domain(*args)
    elif uid == IPR:
        envelope(args, 2); ipr_domain(*args)
    elif uid in DSJ: dsj_domain(uid, args)
    elif uid == ITS: its_domain(args)
    elif uid == IWF: iwf_domain(args)
    elif uid == JBH:
        envelope(args, 2); intlist(args[0], 0, 100000, 1); integer(args[1], 0, len(args[0]) - 1)
    elif uid == KVP: kvp_domain(args)
    elif uid == KLC:
        envelope(args, 1); text(args[0], r'[0-9]{0,60}', 60)
        if klc_count(args[0]) > 200000: raise ValueError('result count')
    elif uid == LCB:
        envelope(args, 2); bst_domain(args[0]); bst_domain(args[1])
    elif uid == LGS:
        envelope(args, 2); lgs_domain(*args)
    elif uid == LKW:
        envelope(args, 3); intlist(args[0], -10**9, 10**9, 1, 20000); integer(args[2], 1, len(args[0])); integer(args[1], 1, args[2])
        if (len(args[0]) - args[2] + 1) * args[1] > 200000: raise ValueError('output size')
    elif uid == LRA1:
        envelope(args, 1); points_domain(args[0], 500)
    elif uid == LRA2:
        envelope(args, 1); points_domain(args[0], 300)


# ---------------------------------------------------------------- references
def ref_fbt(requests):
    users, friends, pending, out = [], [], [], []  # users: [name, balance]; friends: [a, b]; pending: [seq, a, b]

    def user(name):
        for u in users:
            if u[0] == name: return u
        return None

    def are_friends(a, b): return [a, b] in friends or [b, a] in friends
    for seq, request in requests:
        parts = request.split('/')[1:]
        kind = parts[0]
        if kind == 'REGISTER':
            if user(parts[1]) is None: users.append([parts[1], int(parts[2])]); out.append('OK')
            else: out.append('ERROR')
        elif kind == 'FRIEND_REQUEST':
            a, b = parts[1], parts[2]
            if user(a) is None or user(b) is None or a == b or are_friends(a, b): out.append('ERROR')
            else: pending.append([seq, a, b]); out.append('OK')
        elif kind == 'ACCEPT_FRIEND_REQUEST':
            hit = [p for p in pending if p[0] == parts[1]]
            if not hit: out.append('ERROR'); continue
            pending.remove(hit[0])
            if not are_friends(hit[0][1], hit[0][2]): friends.append([hit[0][1], hit[0][2]])
            out.append('OK')
        elif kind == 'TRANSFER':
            a, b, amount = user(parts[1]), user(parts[2]), int(parts[3])
            if a is None or b is None or a is b or not are_friends(a[0], b[0]) or a[1] < amount: out.append('ERROR')
            else: a[1] -= amount; b[1] += amount; out.append('OK')
        else:
            u = user(parts[1]); out.append('ERROR' if u is None else str(u[1]))
    return out


def ref_fsq(demands, x, y, z):
    """Second-by-second clock."""
    fuel, busy_until, waits, front, t = [x, y, z], [0, 0, 0], [], 0, 0
    while front < len(demands):
        d = demands[front]
        if max(fuel) < d: return -1
        seated = False
        for i in range(3):
            if busy_until[i] <= t and fuel[i] >= d:
                fuel[i] -= d; busy_until[i] = t + d; waits.append(t); front += 1; seated = True; break
        if not seated: t += 1
    return max(waits) if waits else 0


def ref_guu(names):
    issued = []
    for name in names:
        words = name.split(' ')
        base = (words[0][0] + words[-1]).lower()[:8]
        k = 0
        while True:
            candidate = base if k == 0 else base[:8 - len(str(k))] + str(k)
            if candidate not in issued: break
            k += 1
        issued.append(candidate)
    return issued


def ref_gds(intervals, n):
    """Maximum flow recipient -> hour slot (capacity n) by augmenting paths."""
    slot_of = [None] * len(intervals)
    load = {h: [] for h in range(9, 17)}

    def augment(i, seen):
        for h in range(intervals[i][0], intervals[i][1]):
            if h in seen: continue
            seen.add(h)
            if len(load[h]) < n:
                load[h].append(i); slot_of[i] = h; return True
            for j in list(load[h]):
                if augment(j, seen):
                    load[h].remove(j); load[h].append(i); slot_of[i] = h; return True
        return False
    return sum(1 for i in range(len(intervals)) if augment(i, set()))


def ref_hop(s, start):
    n = len(s); inf = float('inf')
    edges = []
    for i, cell in enumerate(s):
        if cell == 'X': continue
        for d, k in re.findall(r'([LR])([0-9]*)', cell):
            j = i + (int(k or '1') if d == 'R' else -int(k or '1'))
            if 0 <= j < n and s[j] != 'X': edges.append((i, j))
    if s[start] == 'X': return -1
    dist = [inf] * n; dist[start] = 0
    for _ in range(n):
        changed = False
        for i, j in edges:
            if dist[i] + 1 < dist[j]: dist[j] = dist[i] + 1; changed = True
        if not changed: break
    return -1 if dist[n - 1] == inf else dist[n - 1]


def bits(ip): return ''.join(format(int(o), '08b') for o in ip.split('.'))


def ref_ipr(routes, queries):
    out = []
    for q in queries:
        qb, best, hop = bits(q), -1, ''
        for prefix, nxt in routes:
            base, k = prefix.split('/'); k = int(k)
            if bits(base)[:k] == qb[:k] and k >= best: best, hop = k, nxt
        out.append(hop)
    return out


def ref_dsj(uid, customer, processor, keys):
    keys = keys if uid == DSJ4 else [keys]
    ch, ph = customer[0].split(','), processor[0].split(',')
    out, used = [customer[0] + ',' + processor[0]], set()
    for c in customer[1:]:
        cv, hit = c.split(','), False
        for pi, p in enumerate(processor[1:]):
            pv = p.split(',')
            if all(cv[ch.index(k)] == pv[ph.index(k)] for k in keys):
                out.append(','.join(cv + pv)); hit = True; used.add(pi)
        if not hit and uid in (DSJ2, DSJ3): out.append(','.join(cv + [''] * len(ph)))
    if uid == DSJ3:
        for pi, p in enumerate(processor[1:]):
            if pi not in used: out.append(','.join([''] * len(ch) + p.split(',')))
    return out


def acyclic(edges):
    nodes = {a for e in edges for a in e}
    edges = list(edges)
    while nodes:
        free = [v for v in nodes if not any(b == v for a, b in edges)]
        if not free: return False
        nodes -= set(free); edges = [(a, b) for a, b in edges if a not in free]
    return True


def ref_its(calls):
    tasks, out = {}, [None]  # id -> dependencies
    for op, row in calls:
        if op == 'addTask':
            tid, deps = row
            edges = [(d, t) for t, ds in tasks.items() for d in ds] + [(d, tid) for d in deps]
            if tid in tasks or not acyclic(edges): out.append(False)
            else: tasks[tid] = list(deps); out.append(True)
        else:
            runnable = set(tasks)
            while True:  # fixpoint: drop tasks with a missing or non-runnable prerequisite
                drop = {t for t in runnable if any(d not in runnable for d in tasks[t])}
                if not drop: break
                runnable -= drop
            order = []
            while len(order) < len(runnable):
                ready = [t for t in runnable if t not in order and all(d in order for d in tasks[t])]
                order.append(min(ready))
            out.append(order)
    return out


def ref_iwf(args, calls):
    nums, name = args[1][0]
    kept, i, out = [v for v in nums if accepts(name, v)], 0, [None]
    for op, _ in calls:
        if op == 'hasNext': out.append(i < len(kept))
        else: out.append(kept[i]); i += 1
    return out


def ref_jbh(nums, index):
    pos, height, left, jumps = index, nums[index], True, 0
    for _ in range(2 * len(nums) + 2):
        target = pos - height if left else pos + height
        if not 0 <= target < len(nums): return jumps
        pos, height, left, jumps = target, nums[target], not left, jumps + 1
    return -1


def ref_kvp(calls):
    store, out = {}, [None]
    for op, row in calls:
        if op in ('set', 'update'): store[row[0]] = row[1]; out.append(None)
        elif op == 'get': out.append(store.get(row[0], -1))
        elif op == 'deleteKey': store.pop(row[0], None); out.append(None)
        else: out.append([store[k] for k in sorted(store) if k.startswith(row[0])])
    return out


def ref_klc(digits):
    if not digits: return []
    memo = {len(digits): {''}}
    for i in range(len(digits) - 1, -1, -1):
        found = set()
        for g in range(1, len(KEYPAD[digits[i]]) + 1):
            if i + g <= len(digits) and set(digits[i:i + g]) == {digits[i]}:
                found |= {KEYPAD[digits[i]][g - 1] + rest for rest in memo[i + g]}
        memo[i] = found
    return sorted(memo[0])


def ref_lcb(a, b):
    common = {v for v in a if v is not None} & {v for v in b if v is not None}
    return max(common) if common else -1


def ref_lgs(n, connections):
    best = 0
    for mask in range(1 << n):
        if bin(mask).count('1') > best and all(not (mask >> a & 1 and mask >> b & 1) for a, b in connections):
            best = bin(mask).count('1')
    return best


def ref_lkw(nums, k, w):
    return [sorted(nums[i:i + w], reverse=True)[:k] for i in range(len(nums) - w + 1)]


def ref_lra1(points):
    best = 0
    for p in points:
        for q in points:
            if p[0] < q[0] and p[1] < q[1] and [p[0], q[1]] in points and [q[0], p[1]] in points:
                best = max(best, (q[0] - p[0]) * (q[1] - p[1]))
    return best


def ref_lra2(points):
    best = 0
    for p in points:
        for q in points:
            for r in points:
                if p == q or p == r or q == r: continue
                u, v = (q[0] - p[0], q[1] - p[1]), (r[0] - p[0], r[1] - p[1])
                if u[0] * v[0] + u[1] * v[1] == 0 and [q[0] + r[0] - p[0], q[1] + r[1] - p[1]] in points:
                    best = max(best, abs(u[0] * v[1] - u[1] * v[0]))
    return best


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == FBT:
        budget(len(args[0]) <= 400); return ref_fbt(args[0])
    if uid == FSQ:
        budget(len(args[0]) <= 60 and sum(args[0]) <= 3000); return ref_fsq(*args)
    if uid == GUU:
        budget(len(args[0]) <= 300); return ref_guu(args[0])
    if uid == GDS:
        budget(len(args[0]) <= 80); return ref_gds(*args)
    if uid == HOP:
        budget(len(args[0]) <= 80); return ref_hop(*args)
    if uid == IPR:
        budget(len(args[0]) * len(args[1]) <= 3000); return ref_ipr(*args)
    if uid in DSJ:
        budget(len(args[0]) * len(args[1]) <= 3000); return ref_dsj(uid, *args)
    if uid == KLC:
        budget(len(args[0]) <= 24); return ref_klc(args[0])
    if uid == LCB:
        budget(len(args[0]) + len(args[1]) <= 2000); return ref_lcb(*args)
    if uid == LGS:
        budget(args[0] <= 13); return ref_lgs(*args)
    if uid == LKW:
        budget(len(args[0]) <= 300); return ref_lkw(*args)
    if uid == LRA1:
        budget(len(args[0]) <= 40); return ref_lra1(args[0])
    if uid == LRA2:
        budget(len(args[0]) <= 16); return ref_lra2(args[0])
    if uid == JBH:
        budget(len(args[0]) <= 2000); return ref_jbh(*args)
    calls = trace(uid, args, 100001)
    budget(len(calls) <= 600)
    if uid == ITS:
        budget(len(calls) <= 60); return ref_its(calls)
    if uid == IWF: return ref_iwf(args, calls)
    return ref_kvp(calls)
