"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (per-line window
scans, all-pairs breadth-first search, full rescans of a totals map, exact fractions, repeated
rescans of remaining tasks, direct prefix/suffix comparison, all label permutations, all change
subsets, all triple partitions, repeated subtraction, depth-first path enumeration, day-by-day
expansion, direct overlap comparison, sorting of all events, half-unit grid painting and set
sorting) and refuse inputs above a small budget.
"""
from fractions import Fraction
from itertools import combinations, permutations
import re

H = 'hack2hire:'
GWC1 = H + '69c2f1d121f6ab422696534f'
GWC2 = H + '69c2f5a621f6ab4226965367'
GES = H + '67896bfb11318cc872dd83ea'
HEE = H + '6a038c052608e589a944ac93'
JBS = H + '67fd5bf3d2adf72ba62b0ecc'
LOT = H + '693903ffb03e15724c2174c5'
LPS = H + '67a922ffea201244f8fae261'
MES = H + '67ccb2bb3363b83a81fc996a'
MNK = H + '6854bafdc201117d348a25d2'
MST = H + '67d8a1d71989183df538251a'
MPQ = H + '69bdad5c1cbff60a929beab2'
MSS = H + '68c301d01f64f4312b0a3e0a'
MSP = H + '676f7445366afdc1233e4ff1'
MCS = H + '6800861ac48db1937ce88f5d'
MJE = H + '695572104a0202df9569e960'
MTI = H + '67df6ae706b62d81733ab893'
MUA = H + '6a48164d3588ba8acc693047'

IDS = (GWC1, GWC2, GES, HEE, JBS, LOT, LPS, MES, MNK, MST, MPQ, MSS, MSP, MCS, MJE, MTI, MUA)
GWC = (GWC1, GWC2)
FLOATS = (JBS,)

# uid -> (class name, constructor arity, {method: arity}, void methods); no native-class variants in this cohort
CLASSES = {}


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


def sorted_list(a):
    for x, y in zip(a, a[1:]):
        if x > y: raise ValueError('not sorted')


def gwc_domain(uid, args):
    envelope(args, 3 if uid == GWC1 else 4)
    lines, target = args[0], args[1]
    sized(lines, 0, 100000); chars = 0
    for line in lines: text(line, r'[ -~]*', 200); chars += len(line)
    if chars > 1000000: raise ValueError('text budget')
    text(target, r'[ -~]{1,50}', 50)
    for v in args[2:]: integer(v, 0, 100000)


NAME = r'[a-z0-9]{1,10}'


def ges_domain(elements):
    sized(elements, 0, 100000); ids = set()
    for e in elements:
        sized(e, 4, 4); integer(e[0], 0, 10**9)
        if e[0] in ids: raise ValueError('duplicate id')
        ids.add(e[0])
        for p in e[1:]: text(p, NAME, 10)


def hee_domain(ops, names, deltas):
    sized(ops, 1, 100000); sized(names, len(ops), len(ops)); sized(deltas, len(ops), len(ops))
    for op, name, d in zip(ops, names, deltas):
        if op not in ('U', 'Q') or type(op) is not str: raise ValueError('operation')
        text(name, NAME if op == 'U' else r'[a-z0-9]{0,10}', 10); integer(d, -10**9, 10**9)


def jbs_domain(s1, s2):
    for s in (s1, s2): text(s, r'([!-~]+( [!-~]+)*)?', 100000)


def lot_domain(tasks, deps):
    sized(tasks, 0, 100000); sized(deps, 0, 100000)
    for t in tasks: text(t, r'[a-z]{1,10}', 10)
    names = set(tasks)
    if len(names) != len(tasks): raise ValueError('duplicate task')
    seen = set()
    for d in deps:
        sized(d, 2, 2)
        if type(d[0]) is not str or type(d[1]) is not str or d[0] not in names or d[1] not in names or d[0] == d[1]: raise ValueError('dependency endpoints')
        if (d[0], d[1]) in seen: raise ValueError('duplicate dependency')
        seen.add((d[0], d[1]))


def mes_domain(n, edges):
    integer(n, 1, 100000); sized(edges, 0, 100000); seen = set()
    for e in edges:
        sized(e, 2, 2); integer(e[0], 0, n - 1); integer(e[1], 0, n - 1)
        key = (min(e), max(e))
        if e[0] == e[1] or key in seen: raise ValueError('self-loop or repeated edge')
        seen.add(key)


def mss_domain(routes, checkpoints):
    sized(routes, 0, 100000); sized(checkpoints, 0, 100000); out = {}
    for r in routes:
        sized(r, 3, 3); text(r[0], NAME, 10); integer(r[1], 0, 10**6); text(r[2], NAME, 10)
        out.setdefault(r[0], []).append(r[2]); out.setdefault(r[2], [])
    seen = set()
    for c in checkpoints:
        sized(c, 2, 2); text(c[0], NAME, 10); integer(c[1], 0, 10**6)
        if c[0] in seen: raise ValueError('duplicate checkpoint')
        seen.add(c[0])
    indeg = {v: 0 for v in out}
    for v in out:
        for w in out[v]: indeg[w] += 1
    stack = [v for v in out if indeg[v] == 0]; done = 0
    while stack:
        v = stack.pop(); done += 1
        for w in out[v]:
            indeg[w] -= 1
            if indeg[w] == 0: stack.append(w)
    if done != len(out): raise ValueError('routes contain a cycle')


SERVER = r'[a-z][a-z0-9]{0,9}'


def mje_domain(logs):
    if type(logs) is not dict or not 1 <= len(logs) <= 1000: raise ValueError('logs object')
    total = 0
    for sid, events in logs.items():
        text(sid, SERVER, 10); sized(events, 0, 100000); total += len(events); last = 0
        for e in events:
            if type(e) is not dict or set(e) not in ({'time', 'type'}, {'time', 'type', 'target'}): raise ValueError('event fields')
            integer(e['time'], 0, 10**9); text(e['type'], r'[a-z]{1,10}', 10)
            if 'target' in e: text(e['target'], SERVER, 10)
            if e['time'] < last: raise ValueError('events not sorted by time')
            last = e['time']
    if total > 100000: raise ValueError('event budget')


def intervals(a):
    sized(a, 0, 100000); last = None
    for iv in a:
        sized(iv, 2, 2); integer(iv[0], -10**9, 10**9); integer(iv[1], -10**9, 10**9)
        if iv[0] > iv[1]: raise ValueError('empty interval')
        if last is not None and iv[0] <= last: raise ValueError('intervals overlap or touch inside one list')
        last = iv[1]


def validate_domain(uid, args):
    if uid in GWC: gwc_domain(uid, args); return
    if uid == GES: envelope(args, 1); ges_domain(args[0]); return
    if uid == HEE: envelope(args, 3); hee_domain(*args); return
    if uid == JBS: envelope(args, 2); jbs_domain(*args); return
    if uid == LOT: envelope(args, 2); lot_domain(*args); return
    if uid == LPS: envelope(args, 1); text(args[0], r'[a-z]{1,100000}', 100000); return
    if uid == MES: envelope(args, 2); mes_domain(*args); return
    if uid == MNK:
        envelope(args, 2); text(args[0], r'[1-9][0-9]{0,99999}', 100000); integer(args[1], 0, 100000); return
    if uid == MST: envelope(args, 1); intlist(args[0], 1, 10**9); return
    if uid == MPQ:
        envelope(args, 3); intlist(args[0], 1, 10**9, 1); intlist(args[1], 1, 10**4, len(args[0]), len(args[0])); integer(args[2], 0, 10**9); return
    if uid == MSS: envelope(args, 2); mss_domain(*args); return
    if uid == MSP:
        envelope(args, 2); intlist(args[0], 1, 100000, 1); integer(args[1], 1, sum(args[0])); return
    if uid == MCS:
        envelope(args, 2)
        for s in args: text(s, r'[a-z]{1,100000}', 100000)
        return
    if uid == MJE: envelope(args, 1); mje_domain(args[0]); return
    if uid == MTI: envelope(args, 2); intervals(args[0]); intervals(args[1]); return
    if uid == MUA:
        envelope(args, 2)
        for a in args: intlist(a, -10**9, 10**9); sorted_list(a)
        return
    raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_gwc1(lines, target, around):
    out = []
    for i in range(len(lines)):
        if any(target in lines[j] for j in range(max(0, i - around), min(len(lines), i + around + 1))): out.append(lines[i])
    return out


def ref_gwc2(lines, target, before, after):
    keep = [any(target in lines[j] for j in range(max(0, i - after), min(len(lines), i + before + 1))) for i in range(len(lines))]
    blocks = []
    for i, k in enumerate(keep):
        if not k: continue
        if i > 0 and keep[i - 1]: blocks[-1].append(lines[i])
        else: blocks.append([lines[i]])
    return blocks


def ref_ges(elements):
    n = len(elements); seen = [False] * n; groups = []
    for s in range(n):
        if seen[s]: continue
        seen[s] = True; queue = [s]; comp = []
        while queue:
            a = queue.pop(); comp.append(elements[a][0])
            for b in range(n):
                if not seen[b] and any(elements[a][p] == elements[b][p] for p in (1, 2, 3)):
                    seen[b] = True; queue.append(b)
        groups.append(sorted(comp))
    return sorted(groups)


def ref_hee(ops, names, deltas):
    totals, out = {}, []
    for op, name, d in zip(ops, names, deltas):
        if op == 'U': totals[name] = totals.get(name, 0) + d; continue
        best = ''
        for k, v in totals.items():
            if best == '' or v > totals[best] or (v == totals[best] and k < best): best = k
        out.append(best)
    return out


def ref_jbs(s1, s2):
    a = set(s1.split(' ')) if s1 else set(); b = set(s2.split(' ')) if s2 else set()
    if not a and not b: return 1.0
    v = Fraction(len(a & b), len(a | b)) * 100 + Fraction(1, 2)
    return float(Fraction(v.numerator // v.denominator, 100))


def ref_lot(tasks, deps):
    done, levels = set(), []
    while len(done) < len(tasks):
        level = sorted(t for t in tasks if t not in done and all(f in done for f, to in deps if to == t))
        if not level: return []
        levels.append(level); done.update(level)
    return levels


def ref_lps(s):
    for L in range(len(s) - 1, 0, -1):
        if s[:L] == s[len(s) - L:]: return L
    return 0


def ref_mes(n, edges):
    return max(sum(lab[a] + lab[b] for a, b in edges) for lab in permutations(range(1, n + 1)))


def ref_mnk(s, k):
    best = int(s)
    for c in range(1, min(k, len(s)) + 1):
        for pos in combinations(range(len(s)), c):
            t = list(s)
            for p in pos:
                if t[p] == '5': break
                t[p] = '5'
            else: best = max(best, int(''.join(t)))
    return str(best)


def ref_mst(values):
    def go(rest, need):
        if need == 0: return 0
        if len(rest) < 3 * need: return None
        best = go(rest[1:], need) if len(rest) > 3 * need else None
        for i, j in combinations(range(1, len(rest)), 2):
            trio = sorted((rest[0], rest[i], rest[j]))
            sub = go([x for t, x in enumerate(rest) if t not in (0, i, j)], need - 1)
            if sub is not None and (best is None or trio[1] + sub > best): best = trio[1] + sub
        return best
    return go(list(values), len(values) // 3)


def ref_mpq(times, profits, k):
    best = [0, -1]
    for i, (t, p) in enumerate(zip(times, profits)):
        left, runs = k, 0
        while left >= t: left -= t; runs += 1
        if runs and runs * p > best[0]: best = [runs * p, i]
    return best


def ref_mss(routes, checkpoints):
    reward = {c[0]: c[1] for c in checkpoints}
    best = None

    def dfs(v, score):
        nonlocal best
        nxt = [r for r in routes if r[0] == v]
        if not nxt:
            best = score if best is None else max(best, score); return
        for _, cost, w in nxt: dfs(w, score + reward.get(w, 0) - cost)
    dfs('lodge', 0)
    return best


def ref_msp(days, k):
    seq = [j for d in days for j in range(1, d + 1)]
    return max(sum(seq[(s + t) % len(seq)] for t in range(k)) for s in range(len(seq)))


def ref_mcs(a, b):
    for L in range(min(len(a), len(b)), 0, -1):
        if a.endswith(b[:L]): return a + b[L:]
    return a + b


def ref_mje(logs):
    rows = []
    for sid, events in logs.items():
        for pos, e in enumerate(events): rows.append((e['time'], sid, pos, e))
    rows.sort(key=lambda r: r[:3])
    out = []
    for _, sid, _, e in rows:
        x = {'serverId': sid}; x.update(e); out.append(x)
    return out


def ref_mti(a, b):
    lo = min([iv[0] for iv in a + b], default=0)
    hi = max([iv[1] for iv in a + b], default=0)
    cover = [False] * (2 * (hi - lo) + 1)
    for s, e in a + b:
        for c in range(2 * (s - lo), 2 * (e - lo) + 1): cover[c] = True
    out, start = [], None
    for c, on in enumerate(cover + [False]):
        if on and start is None: start = c
        if not on and start is not None: out.append([start // 2 + lo, (c - 1) // 2 + lo]); start = None
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == GWC1:
        budget(len(args[0]) * (2 * args[2] + 1) <= 20000); return ref_gwc1(*args)
    if uid == GWC2:
        budget(len(args[0]) * (args[2] + args[3] + 1) <= 20000); return ref_gwc2(*args)
    if uid == GES:
        budget(len(args[0]) <= 120); return ref_ges(args[0])
    if uid == HEE:
        budget(len(args[0]) <= 400); return ref_hee(*args)
    if uid == JBS:
        budget(len(args[0]) + len(args[1]) <= 4000); return ref_jbs(*args)
    if uid == LOT:
        budget(len(args[0]) <= 60 and len(args[1]) <= 200); return ref_lot(*args)
    if uid == LPS:
        budget(len(args[0]) <= 400); return ref_lps(args[0])
    if uid == MES:
        budget(args[0] <= 6); return ref_mes(*args)
    if uid == MNK:
        budget(len(args[0]) <= 10); return ref_mnk(*args)
    if uid == MST:
        budget(len(args[0]) <= 9); return ref_mst(args[0])
    if uid == MPQ:
        budget(len(args[0]) <= 60 and all(args[2] // t <= 2000 for t in args[0])); return ref_mpq(*args)
    if uid == MSS:
        budget(len(args[0]) <= 30); return ref_mss(*args)
    if uid == MSP:
        budget(sum(args[0]) <= 300); return ref_msp(*args)
    if uid == MCS:
        budget(len(args[0]) + len(args[1]) <= 400); return ref_mcs(*args)
    if uid == MJE:
        budget(sum(len(v) for v in args[0].values()) <= 400); return ref_mje(args[0])
    if uid == MTI:
        lo = min([iv[0] for iv in args[0] + args[1]], default=0); hi = max([iv[1] for iv in args[0] + args[1]], default=0)
        budget(hi - lo <= 400); return ref_mti(*args)
    budget(len(args[0]) + len(args[1]) <= 4000); return sorted(set(args[0]) | set(args[1]))
