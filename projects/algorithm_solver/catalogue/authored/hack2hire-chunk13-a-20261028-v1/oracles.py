"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (label propagation,
plain-set replays, log rescans, exhaustive subset searches, linear scans, full list copies per version,
fixed-point relaxations, set comparison with every straight, parent-chain walks with list rescans,
per-rider rescans, selection by recounting, per-vehicle rescans, backtracking plus full re-sorting, and
repeated linear maximum scans) and refuse inputs above a small budget.
"""
from itertools import combinations
import re

H = 'hack2hire:'
NCP = H + '692d2a491abcca80b11223bf'
OPB = H + '6a1e2e688b879849ebc1089e'
OOV = H + '688aefae3867670cfb894129'
OSP = H + '6a513eaa665efda9311f609d'
OTS = H + '6a95d744cddc54478ddf6a6d'
OBS = H + '677de8b2052a260e0165706a'
PCI = H + '68ace5011bf7d2097f647f50'
PST = H + '677f4db36fee41e51af73dd6'
PBC1 = H + '6827b84d285cf34924f48286'
PBC2 = H + '6913ed33fa8a311e42671e5d'
PSS = H + '68fd5b9d47bea664c0bba367'
PEO = H + '691e0f0208ad7861624b5677'
RPW1 = H + '68e8779c80f69c7a01706899'
RPW2 = H + '68e9554c149617c9114ecdd1'
RSP = H + '6a00c4cbf1b0b7030ba32383'
RVC = H + '699f7bb56e73e4abccc9b565'
RHN = H + '67eae60e4c9bb801bfd0ef48'
RMK = H + '688fb256b3f942cc1004c00e'

IDS = (NCP, OPB, OOV, OSP, OTS, OBS, PCI, PST, PBC1, PBC2, PSS, PEO, RPW1, RPW2, RSP, RVC, RHN, RMK)
PBC = (PBC1, PBC2)
RPW = (RPW1, RPW2)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    OOV: ('VisitorTracker', 0, {'login': 1, 'getOldestOneTimeVisitor': 0}, ('login',)),
    PST: ('PStack', 0, {'push': 2, 'pop': 1, 'peek': 1, 'size': 1}, ()),
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


def ncp_domain(n, connections):
    integer(n, 1, 100000)
    if type(connections) is not list or len(connections) > 100000: raise ValueError('connections size')
    for e in connections:
        if type(e) is not list or len(e) != 2: raise ValueError('edge shape')
        integer(e[0], 0, n - 1); integer(e[1], 0, n - 1)
        if e[0] == e[1]: raise ValueError('self connection')


def opb_domain(operations):
    if type(operations) is not list or len(operations) > 100000: raise ValueError('operations size')
    for op in operations:
        if type(op) is not list or not op or op[0] not in (1, 2) or type(op[0]) is not int: raise ValueError('operation kind')
        if op[0] == 1:
            if len(op) != 2: raise ValueError('place shape')
            integer(op[1], 0, 10**9)
        else:
            if len(op) != 3: raise ValueError('check shape')
            integer(op[1], 1, 10**9); integer(op[2], 1, op[1])


USER = r'[a-z0-9_]{1,12}'


def oov_domain(args):
    for op, row in trace(OOV, args, 200001):
        if op == 'login': text(row[0], USER, 12)


def pst_domain(args):
    versions = 1
    sizes = [0]
    for op, row in trace(PST, args, 200001):
        integer(row[0], 0, versions - 1)
        if op == 'push':
            integer(row[1], -10**9, 10**9); sizes.append(sizes[row[0]] + 1); versions += 1
        elif op in ('pop', 'peek') and sizes[row[0]] == 0: raise ValueError('empty version')


def boards_domain(boards, pin1, pin2):
    if type(boards) is not list or len(boards) > 100000: raise ValueError('boards size')
    total = 0
    for b in boards:
        intlist(b, 1, 10**9, 1, 200000)
        if len(set(b)) != len(b): raise ValueError('repeated pin on a board')
        total += len(b)
    if total > 200000: raise ValueError('total pins')
    integer(pin1, 1, 10**9); integer(pin2, 1, 10**9)
    if pin1 == pin2: raise ValueError('pins must differ')


CARDS = ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')


def pss_domain(cards):
    if type(cards) is not list or len(cards) != 5: raise ValueError('five cards')
    for c in cards:
        if type(c) is not str or c not in CARDS: raise ValueError('card value')
    if len(set(cards)) != 5: raise ValueError('duplicate card')


EMP_ID = r'[A-Za-z0-9]{1,10}'
EMP_NAME = r'[A-Z][a-z]{0,11}(?: [A-Z][a-z]{0,11})?'


def peo_domain(employees):
    if type(employees) is not list or not 1 <= len(employees) <= 100000: raise ValueError('employees size')
    manager, name = {}, {}
    for e in employees:
        if type(e) is not list or len(e) != 3: raise ValueError('employee shape')
        text(e[0], EMP_ID, 10); text(e[1], EMP_ID, 10); text(e[2], EMP_NAME, 25)
        if e[0] in manager: raise ValueError('duplicate id')
        manager[e[0]] = e[1]; name[e[0]] = e[2]
    ceos = [i for i, m in manager.items() if i == m]
    if len(ceos) != 1: raise ValueError('exactly one CEO')
    depth = {ceos[0]: 0}
    for start in manager:  # iterative chain resolution with cycle detection
        path, x = [], start
        while x not in depth:
            if manager.get(x) is None: raise ValueError('unknown manager')
            path.append(x); x = manager[x]
            if len(path) > len(manager): raise ValueError('management cycle')
        d = depth[x]
        for y in reversed(path): d += 1; depth[y] = d
    size = sum(4 * depth[i] + len(name[i]) for i in manager) + len(manager) - 1
    if size > 4000000: raise ValueError('output too long')


RIDER = r'[A-Za-z]{1,12}'


def rpw_domain(races):
    if type(races) is not list or not 1 <= len(races) <= 10000: raise ValueError('races size')
    total = 0
    for race in races:
        if type(race) is not list or not race: raise ValueError('race shape')
        for r in race: text(r, RIDER, 12)
        if len(set(race)) != len(race): raise ValueError('repeated rider in a race')
        total += len(race)
    if total > 200000: raise ValueError('total entries')


def rsp_domain(pref):
    if type(pref) is not list or not pref: raise ValueError('users')
    m = None
    for p in pref:
        if type(p) is not list or not 1 <= len(p) <= 200: raise ValueError('songs')
        if m is None: m = len(p)
        if len(p) != m: raise ValueError('ragged preferences')
        for v in p: integer(v, 0, m - 1)
        if len(set(p)) != m: raise ValueError('not a permutation')
    if len(pref) * m > 200000: raise ValueError('size')


VEHICLE = r'[A-Za-z0-9_-]{1,10}'
CHUNKS = r'[a-z0-9]{1,8}(?: [a-z0-9]{1,8})*'


def rvc_domain(events):
    if type(events) is not list or len(events) > 100000: raise ValueError('events size')
    total = 0
    for e in events:
        if type(e) is not list or len(e) != 3: raise ValueError('event shape')
        if e[0] != 'server':
            text(e[0], VEHICLE, 10)
        text(e[1], CHUNKS, 1800000); text(e[2], VEHICLE, 10)
        if e[2] == 'server' or e[0] == e[2]: raise ValueError('receiver')
        total += e[1].count(' ') + 1
    if total > 200000: raise ValueError('total chunks')


def rhn_domain(houses):
    if type(houses) is not list or not 1 <= len(houses) <= 100000: raise ValueError('neighborhoods')
    total = 0
    for row in houses:
        intlist(row, 1, 10**9, 1, 200000); total += len(row)
    if total > 200000: raise ValueError('total houses')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == NCP:
        envelope(args, 2); ncp_domain(*args)
    elif uid == OPB:
        envelope(args, 1); opb_domain(args[0])
    elif uid == OOV: oov_domain(args)
    elif uid == OSP:
        envelope(args, 1); intlist(args[0], -10**9, 10**9, 1)
    elif uid == OTS:
        envelope(args, 2); intlist(args[0], 0, 10**9, 1); intlist(args[1], 0, 10**9, len(args[0]), len(args[0]))
    elif uid == OBS:
        envelope(args, 2); integer(args[0], 1, 100000); intlist(args[1], 1, args[0])
    elif uid == PCI:
        envelope(args, 2)
        for a, top in ((args[0], 100), (args[1], 200000)):
            if type(a) is not list or len(a) > top: raise ValueError('array size')
            for c in a: text(c, r'[ -~]', 1)
    elif uid == PST: pst_domain(args)
    elif uid in PBC:
        envelope(args, 3); boards_domain(*args)
    elif uid == PSS:
        envelope(args, 1); pss_domain(args[0])
    elif uid == PEO:
        envelope(args, 1); peo_domain(args[0])
    elif uid in RPW:
        envelope(args, 1); rpw_domain(args[0])
    elif uid == RSP:
        envelope(args, 1); rsp_domain(args[0])
    elif uid == RVC:
        envelope(args, 1); rvc_domain(args[0])
    elif uid == RHN:
        envelope(args, 1); rhn_domain(args[0])
    elif uid == RMK:
        envelope(args, 3); intlist(args[0], 0, 10**9, 1); integer(args[1], 0, 100000); integer(args[2], 1, 10**9 + 7)


# ---------------------------------------------------------------- references
def ref_ncp(n, connections):
    label = list(range(n))
    changed = True
    while changed:
        changed = False
        for a, b in connections:
            low = min(label[a], label[b])
            if label[a] != low or label[b] != low: label[a] = label[b] = low; changed = True
    return sum(1 for i in range(n) for j in range(i + 1, n) if label[i] != label[j])


def ref_opb(operations):
    placed, out = set(), ''
    for op in operations:
        if op[0] == 1: placed.add(op[1])
        else: out += '0' if any(op[1] - op[2] <= p <= op[1] - 1 for p in placed) else '1'
    return out


def ref_oov(calls):
    log, out = [], [None]
    for op, row in calls:
        if op == 'login': log.append(row[0]); out.append(None)
        else: out.append(next((u for u in log if log.count(u) == 1), ''))
    return out


def ref_osp(prices):
    best = None
    n = len(prices)
    for size in range(1, n + 1):
        for pick in combinations(range(n), size):
            if all(prices[j] + j >= prices[i] + i for i, j in zip(pick, pick[1:])):
                s = sum(prices[i] for i in pick)
                if best is None or s > best: best = s
    return best


def ref_ots(lower, higher):
    n = len(lower)
    for size in range(n, 0, -1):
        for team in combinations(range(n), size):
            if all(pos <= lower[i] and size - 1 - pos <= higher[i] for pos, i in enumerate(team)): return size
    return 0


def ref_obs(num, limit):
    count, out = [0] * num, []
    for lim in limit:
        best = 0
        for s in range(lim):
            if count[s] < count[best]: best = s
        count[best] += 1; out.append(best)
    return out


def ref_pci(ignore, chars):
    kept = [c for c in chars if c not in ignore]
    return kept == kept[::-1]


def ref_pst(calls):
    """Every version is a full copied list; pop answers with the version recorded as the one that was pushed onto."""
    versions, base, out = [[]], [None], [None]
    for op, row in calls:
        st = versions[row[0]]
        if op == 'push': versions.append(st + [row[1]]); base.append(row[0]); out.append(len(versions) - 1)
        elif op == 'pop':
            assert versions[base[row[0]]] == st[:-1]
            out.append(base[row[0]])
        elif op == 'peek': out.append(st[-1])
        else: out.append(len(st))
    return out


def board_components(boards):
    """Boards reachable from each other by shared pins, grown by repeated passes."""
    groups = [set(b) for b in boards]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if groups[i] and groups[j] and groups[i] & groups[j]:
                    groups[i] |= groups[j]; groups[j] = set(); merged = True
    return [g for g in groups if g]


def ref_pbc1(boards, p, q): return any(p in g and q in g for g in board_components(boards))


def ref_pbc2(boards, p, q):
    INF = float('inf')
    dist = [1 if p in b else INF for b in boards]
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(boards):
            for j, b in enumerate(boards):
                if dist[i] + 1 < dist[j] and set(a) & set(b): dist[j] = dist[i] + 1; changed = True
    best = min((dist[i] for i, b in enumerate(boards) if q in b), default=INF)
    return -1 if best == INF else best


def ref_pss(cards):
    rank = {c: i + 1 for i, c in enumerate(CARDS)}
    straights = [set(range(s, s + 5)) for s in range(1, 11)]
    low = {rank[c] for c in cards}
    high = {14 if c == 'A' else rank[c] for c in cards}
    return low in straights or high in straights


def ref_peo(employees):
    manager = {e[0]: e[1] for e in employees}
    name = {e[0]: e[2] for e in employees}

    def depth(i):
        d = 0
        while manager[i] != i: i = manager[i]; d += 1
        return d
    ceo = next(i for i in manager if manager[i] == i)
    lines = []

    def visit(i):
        lines.append('-' * (4 * depth(i)) + name[i])
        for e in employees:
            if e[1] == i and e[0] != i: visit(e[0])
    visit(ceo)
    return '\n'.join(lines)


POINTS = {0: 15, 1: 10, 2: 5}


def rider_stats(races, rider):
    pts, places = 0, [0, 0, 0]
    for race in races:
        for pos, r in enumerate(race):
            if r == rider:
                pts += POINTS.get(pos, 0)
                if pos < 3: places[pos] += 1
    return pts, places


def ref_rpw1(races):
    riders = sorted({r for race in races for r in race})
    best = None
    for r in riders:
        pts, _ = rider_stats(races, r)
        if best is None or pts > best[0]: best = (pts, r)
    return best[1]


def ref_rpw2(races):
    left = sorted({r for race in races for r in race})
    out = []
    while left:
        best = None
        for r in left:
            pts, pl = rider_stats(races, r)
            key = [pts] + pl
            if best is None or key > best[0]: best = (key, r)  # strict: earlier (smaller) name wins ties
        out.append(best[1]); left.remove(best[1])
    return out


def ref_rsp(pref):
    m = len(pref[0])
    left, out = list(range(m)), []

    def row(s): return [sum(1 for p in pref if p[pos] == s) for pos in range(m)]
    while left:
        best = left[0]
        for s in left[1:]:
            if row(s) > row(best): best = s
        out.append(best); left.remove(best)
    return out


def ref_rvc(events):
    vehicles = sorted({e[0] for e in events if e[0] != 'server'} | {e[2] for e in events})
    score = {v: sum(len(e[1].split(' ')) for e in events if e[0] == v) for v in vehicles}
    out = []
    while vehicles:
        best = vehicles[0]
        for v in vehicles[1:]:
            if score[v] > score[best]: best = v
        out.append(best); vehicles.remove(best)
    return out


def rhn_feasible(sizes, counts):
    """Backtracking: can the counts be spread over neighborhoods of the given sizes with no repeat inside one?"""
    values = sorted(counts)
    sizes = list(sizes)

    def place(vi, remaining):
        if vi == len(values): return all(s == 0 for s in remaining)
        c = counts[values[vi]]
        for pick in combinations([i for i, s in enumerate(remaining) if s > 0], c):
            for i in pick: remaining[i] -= 1
            ok = place(vi + 1, remaining)
            for i in pick: remaining[i] += 1
            if ok: return True
        return False
    return place(0, sizes)


def ref_rhn(houses):
    counts = {}
    for row in houses:
        for v in row: counts[v] = counts.get(v, 0) + 1
    feasible = rhn_feasible([len(r) for r in houses], dict(counts))
    out = []
    for row in houses:
        order = sorted((v for v in counts if counts[v] > 0), key=lambda v: (-counts[v], v))
        if len(order) < len(row): out = None; break
        take = order[:len(row)]
        for v in take: counts[v] -= 1
        out.append(sorted(take))
    if out is not None:  # validity of the canonical filling, checked independently
        assert all(len(set(r)) == len(r) and r == sorted(r) for r in out)
        assert sorted(v for r in out for v in r) == sorted(v for r in houses for v in r)
    if (out is not None) != feasible: raise AssertionError('canonical filling disagrees with exhaustive feasibility')
    return out if out is not None else []


def ref_rmk(nums, k, m):
    work = list(nums)
    for _ in range(k):
        i = work.index(max(work))
        work[i] = (work[i] - work[i] % 2) // 2
    return sum(work) % m


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid == NCP:
        budget(args[0] <= 80 and len(args[1]) <= 200); return ref_ncp(*args)
    if uid == OPB:
        budget(len(args[0]) <= 200); return ref_opb(args[0])
    if uid == OOV:
        calls = trace(OOV, args, 200001); budget(len(calls) <= 300); return ref_oov(calls)
    if uid == OSP:
        budget(len(args[0]) <= 12); return ref_osp(args[0])
    if uid == OTS:
        budget(len(args[0]) <= 12); return ref_ots(*args)
    if uid == OBS:
        budget(args[0] * len(args[1]) <= 20000); return ref_obs(*args)
    if uid == PCI:
        budget(len(args[1]) <= 2000); return ref_pci(*args)
    if uid == PST:
        calls = trace(PST, args, 200001); budget(len(calls) <= 300); return ref_pst(calls)
    if uid in PBC:
        budget(len(args[0]) <= 40); return (ref_pbc1 if uid == PBC1 else ref_pbc2)(*args)
    if uid == PSS: return ref_pss(args[0])
    if uid == PEO:
        budget(len(args[0]) <= 80); return ref_peo(args[0])
    if uid in RPW:
        budget(sum(map(len, args[0])) <= 300); return (ref_rpw1 if uid == RPW1 else ref_rpw2)(args[0])
    if uid == RSP:
        budget(len(args[0]) * len(args[0][0]) <= 300); return ref_rsp(args[0])
    if uid == RVC:
        budget(len(args[0]) <= 100); return ref_rvc(args[0])
    if uid == RHN:
        budget(sum(map(len, args[0])) <= 12); return ref_rhn(args[0])
    budget(args[1] <= 200 and len(args[0]) <= 200); return ref_rmk(*args)
