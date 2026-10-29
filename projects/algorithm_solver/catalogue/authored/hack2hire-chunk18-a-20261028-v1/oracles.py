"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (per-group sorting,
per-plate log rescans, per-peak height trials, exhaustive target enumeration, direct command
application, exhaustive sign assignment, linear slot scans, exhaustive path enumeration, quadratic
partition dynamic programming and all-pairs reachability) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
HSM = H + '68f5af31a269f53ea0eff8a0'
HWC = H + '677f3733edc5bbd98ac0ea5a'
MAB = H + '677de134052a260e01657068'
MPN = H + '67873a44e20f8f324213c29a'
MTC = H + '69a357a36e73e4abccc9bf9c'
MNS = H + '67a4d4ca2a9ed767fa215433'
MTS = H + '67735a0732f9cd104fc349d4'
MGJ1 = H + '6a57ce72665efda9311f94c4'
MGJ2 = H + '6a57d29e665efda9311f950a'
MGJ3 = H + '6a57d9ca665efda9311f954c'
MGJ4 = H + '6a57dafb665efda9311f9556'
MBS = H + '67874b97e20f8f324213c29c'
MVT = H + '68c4484970268e95f5f43d5e'

IDS = (HSM, HWC, MAB, MPN, MTC, MNS, MTS, MGJ1, MGJ2, MGJ3, MGJ4, MBS, MVT)
MGJ = (MGJ1, MGJ2, MGJ3, MGJ4)

# uid -> (class name, constructor arity, {method: arity}, void methods); no variant here is a class
CLASSES = {}
FLOATS = frozenset()
LIMIT = 2**53 - 1
MOD = 1000000007
TIME_LIMIT = 60


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


def grid(board, cells, lo, hi):
    sized(board, 1, cells)
    if type(board[0]) is not list: raise ValueError('row')
    m = len(board[0])
    if m < 1 or len(board) * m > cells: raise ValueError('grid size')
    for row in board: intlist(row, lo, hi, m, m)
    return len(board), m


CHECKPOINT = r'[A-Z]{1,3}(?:0|[1-9][0-9]{0,8})'
NUM = r'(?:0|[1-9][0-9]{0,5})'


def validate_domain(uid, args):
    if type(uid) is not str or uid not in IDS: raise ValueError('unknown uid')
    if uid == HSM:
        envelope(args, 3); scores, groups, k = args
        intlist(scores, 0, 10**9, 1); sized(groups, 1, 100000); integer(k, 1, 100000)
        total = 0
        for g in groups:
            intlist(g, 0, len(scores) - 1, 1, len(scores))
            if len(set(g)) != len(g): raise ValueError('duplicate id in group')
            total += len(g)
        if total > 200000: raise ValueError('total group size')
        return
    if uid == HWC:
        envelope(args, 1); sized(args[0], 0, 100000)
        for r in args[0]:
            sized(r, 2, 2); text(r[0], r'[A-Z0-9]{1,10}', 10); text(r[1], CHECKPOINT, 12)
        return
    if uid == MAB:
        envelope(args, 1); intlist(args[0], 0, 10**9, 1)
        if max(args[0]) < 1: raise ValueError('no positive element')
        return
    if uid == MPN:
        envelope(args, 1); intlist(args[0], 1, 10**9, 1); return
    if uid == MTC:
        envelope(args, 2); n, m = grid(args[0], 100000, -10**9, 10**9); sized(args[1], 0, 100000)
        for c in args[1]:
            text(c, r'reverseRow ' + NUM + r'|swap ' + NUM + ' ' + NUM, 40)
            if any(int(x) >= n for x in c.split(' ')[1:]): raise ValueError('row index')
        return
    if uid == MNS:
        envelope(args, 1); intlist(args[0], 1, 10**9, 1); return
    if uid == MTS:
        envelope(args, 3); integer(args[0], 1, 100000); integer(args[1], 1, 100000); intlist(args[2], 1, 10**9); return
    if uid in MGJ:
        if uid == MGJ1:
            envelope(args, 2); n, m = grid(args[0], 100000, -10**4, 10**4); integer(args[1], 0, m - 1); return
        envelope(args, 3); n, m = grid(args[0], 20000, -10**4, 10**4); integer(args[1], 0, m - 1); integer(args[2], 0, n)
        if n * m * (args[2] + 1) > 100000: raise ValueError('state budget')
        return
    if uid == MBS:
        envelope(args, 1); intlist(args[0], 1, 10**9, 1); return
    envelope(args, 2); integer(args[0], 1, 100000); sized(args[1], 0, 100000)
    for e in args[1]: intlist(e, 0, args[0] - 1, 2, 2)


# ---------------------------------------------------------------- references
def ref_hsm(scores, groups, k):
    best, index = None, None
    for i, g in enumerate(groups):
        s = sum(sorted((scores[x] for x in g), reverse=True)[:k])
        if best is None or s > best: best, index = s, i
    return index


def ref_hwc(records):
    out = []
    for plate in sorted({r[0] for r in records}):
        prev, total = None, 0
        for p, c in records:
            if p != plate: continue
            pos = int(''.join(ch for ch in c if ch.isdigit()))
            if prev is not None: total += abs(pos - prev) * 10
            prev = pos
        out.append([plate, total])
    return out


def ref_mab(arr):
    n = len(arr); best = 0
    for c in range(n):
        for k in range(min(c + 1, n - c), 0, -1):
            if all(arr[c + d] >= k - abs(d) for d in range(-(k - 1), k)):
                best = max(best, k * k); break
    return sum(arr) - best


def ref_mpn(power):
    n, top = len(power), max(power)
    # targets c with power[i] <= c[i] <= top, non-decreasing; cost of increments d = sum of positive rises of d (d[-1] = 0)
    states = {}
    for c0 in range(power[0], top + 1):
        d0 = c0 - power[0]; states[(c0, d0)] = min(states.get((c0, d0), 10**30), d0)
    for i in range(1, n):
        nxt = {}
        for (c, d), cost in states.items():
            for ci in range(max(c, power[i]), top + 1):
                di = ci - power[i]; key = (ci, di); v = cost + max(0, di - d)
                if v < nxt.get(key, 10**30): nxt[key] = v
        states = nxt
    return min(states.values())


def ref_mtc(matrix, commands):
    a = [list(r) for r in matrix]
    for cmd in commands:
        parts = cmd.split(' ')
        if parts[0] == 'reverseRow':
            r = int(parts[1]); a[r] = a[r][::-1]
        else:
            r1, r2 = int(parts[1]), int(parts[2]); a[r1], a[r2] = a[r2], a[r1]
    return a


def ref_mns(a):
    n, best = len(a), 0
    for mask in range(1 << n):
        if mask & 1: continue
        s, ok = 0, True
        for i in range(n):
            s += -a[i] if mask >> i & 1 else a[i]
            if s <= 0: ok = False; break
        if ok: best = max(best, bin(mask).count('1'))
    return best


def ref_mts(n, m, tasks):
    slots = [0] * min(n * m, len(tasks)); done = 0
    for t in sorted(tasks):
        j = min(range(len(slots)), key=lambda x: slots[x])
        if slots[j] + t > TIME_LIMIT: break
        slots[j] += t; done += 1
    return done


def mgj_paths(board, p, k, jumps):
    """Every path from (0, p) as (score, cells), enumerated depth first."""
    n, m = len(board), len(board[0]); out = []
    stack = [((0, p), board[0][p], k, [[0, p]])]
    while stack:
        (i, j), s, left, cells = stack.pop()
        if i == n - 1: out.append((s, cells)); continue
        moves = [(i + 1, j + dj) for dj in (-1, 0, 1)]
        for (a, b) in moves:
            if 0 <= b < m: stack.append(((a, b), s + board[a][b], left, cells + [[a, b]]))
        if jumps and left > 0 and i + 2 <= n - 1:
            stack.append(((i + 2, j), s + board[i + 2][j], left - 1, cells + [[i + 2, j]]))
    return out


def ref_mgj(uid, args):
    board, p = args[0], args[1]; k = args[2] if uid != MGJ1 else 0
    paths = mgj_paths(board, p, k, uid != MGJ1)
    best = max(s for s, _ in paths)
    if uid in (MGJ1, MGJ2): return best
    if uid == MGJ3: return min(c for s, c in paths if s == best)
    return sum(1 for s, _ in paths if s == best) % MOD


def ref_mbs(w):
    n = len(w); NEG = None
    best = [NEG] * (n + 1); best[0] = 0
    for t in range(1, n + 1):
        for j in range(t):
            seg = w[j:t]
            if best[j] is not None and seg[-1] < max(seg):
                if best[t] is None or best[j] + 1 > best[t]: best[t] = best[j] + 1
    return best[n] or 0


def ref_mvt(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges: adj[u].add(v)
    reach = []
    for s in range(n):
        seen = {s}; todo = [s]
        while todo:
            x = todo.pop()
            for y in adj[x]:
                if y not in seen: seen.add(y); todo.append(y)
        reach.append(seen)
    classes = set()
    for u in range(n):
        if all(v in reach[u] for v in range(n) if u in reach[v]):
            classes.add(frozenset(v for v in range(n) if v in reach[u] and u in reach[v]))
    return len(classes)


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == HSM:
        budget(sum(len(g) for g in args[1]) <= 400); return ref_hsm(*args)
    if uid == HWC:
        budget(len(args[0]) <= 300); return ref_hwc(args[0])
    if uid == MAB:
        budget(len(args[0]) <= 60); return ref_mab(args[0])
    if uid == MPN:
        budget(len(args[0]) <= 8 and max(args[0]) <= 12); return ref_mpn(args[0])
    if uid == MTC:
        budget(len(args[1]) * len(args[0][0]) <= 20000); return ref_mtc(*args)
    if uid == MNS:
        budget(len(args[0]) <= 13); return ref_mns(args[0])
    if uid == MTS:
        budget(len(args[2]) <= 300); return ref_mts(*args)
    if uid in MGJ:
        budget(len(args[0]) <= 7 and len(args[0][0]) <= 5); return ref_mgj(uid, args)
    if uid == MBS:
        budget(len(args[0]) <= 60); return ref_mbs(args[0])
    budget(args[0] <= 40); return ref_mvt(*args)
