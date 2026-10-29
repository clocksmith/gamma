"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (regex token splits,
flat entry lists with linear search and backup replay, list removal from the front, eager array
rewriting, all-pairs prefix enumeration, full re-sorting, scans of the print history, reverse
first-wins passes, minute-by-minute week walks, sorted-window comparison, per-start set growth,
recursive searches over rebuilt child lists, per-piece seat sums, sorting of accumulated nets,
length-4 window enumeration and whole-list rewriting) and refuse inputs above a small budget.
"""
import re

H = 'hack2hire:'
FST = H + '68d8465eae12841706c1fc6e'
IMD1 = H + '689505e73a1d9e6d6042d51a'
IMD2 = H + '68961c873a1d9e6d6042d57a'
IMD3 = H + '689641c83a1d9e6d6042d585'
IMD4 = H + '689bb2061126a03aace65e39'
IQR = H + '677df76b052a260e0165706c'
LZA = H + '68539b6bd3dbd4fb8b026e9f'
DWC = H + '697460b3a0697bac5fdca97e'
ESC = H + '681bc967a73bd75b806cb994'
ELR = H + '68edc9c15abdefad4f6693fc'
FVS = H + '6a987edf0ca9cc4e1c78a9a5'
FMI = H + '6782d18f3cd890ccd3798fc5'
FAS = H + '68c8719bdf5a6365aa774b15'
FKD = H + '69f131b096981f58ae1f7654'
FPT1 = H + '6772e2e1dd9437f8aa275b01'
FPT2 = H + '6772e85ddd9437f8aa275b02'
FRI = H + '6833f407c7e9643eccb00bf5'
KHD = H + '688e62068cf2da976a9c6903'
FIR = H + '680d8976286d3dbf97693ad5'
GTR = H + '67a26ae89056d103b4aafc72'

IDS = (FST, IMD1, IMD2, IMD3, IMD4, IQR, LZA, DWC, ESC, ELR, FVS, FMI, FAS, FKD, FPT1, FPT2, FRI, KHD, FIR, GTR)
IMD = (IMD1, IMD2, IMD3, IMD4)
FPT = (FPT1, FPT2)

_L1 = {'setData': 3, 'getData': 2, 'deleteData': 2}
_L2 = dict(_L1, scanData=1, scanDataByPrefix=2)
_L3 = {'setDataAt': 4, 'setDataAtWithTtl': 5, 'deleteDataAt': 3, 'getDataAt': 3, 'scanDataAt': 2, 'scanDataByPrefixAt': 3}
_L4 = dict(_L3, backup=1, restore=2)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    IMD1: ('InMemoryDB', 0, _L1, ('setData',)),
    IMD2: ('InMemoryDB', 0, _L2, ('setData',)),
    IMD3: ('InMemoryDB', 0, _L3, ('setDataAt', 'setDataAtWithTtl')),
    IMD4: ('InMemoryDB', 0, _L4, ('setDataAt', 'setDataAtWithTtl', 'restore')),
    IQR: ('InfiniteQueue', 0, {'add': 1, 'poll': 0, 'getRandom': 1}, ('add',)),
    LZA: ('LazyArray', 1, {'map': 2, 'indexOf': 1}, ('map',)),
    ESC: ('EscapeRoom', 2, {'advance': 1, 'countInRoom': 1, 'topPlayers': 1}, ('advance',)),
    ELR: ('EventLogger', 1, {'logEvent': 2}, ()),
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


def fst_domain(files, word):
    sized(files, 0, 1000); text(word, r'[A-Za-z0-9]{1,30}', 30)
    names, lines, chars = set(), 0, 0
    for f in files:
        sized(f, 2, 2); text(f[0], r'[A-Za-z0-9._-]{1,30}', 30); sized(f[1], 0, 100000)
        if f[0] in names: raise ValueError('duplicate file name')
        names.add(f[0])
        for line in f[1]:
            text(line, r'[ -~]*', 200); lines += 1; chars += len(line)
    if lines > 100000 or chars > 1000000: raise ValueError('text budget')


KEY, FIELD, VALUE = r'[a-z0-9]{1,4}', r'[a-z0-9]{1,8}', r'[a-z0-9]{0,8}'


def imd_domain(uid, args):
    calls = trace(uid, args)
    last, backups = 0, []
    for op, row in calls:
        if op in ('setData', 'setDataAt', 'setDataAtWithTtl'): text(row[0], KEY); text(row[1], FIELD); text(row[2], VALUE)
        elif op in ('getData', 'deleteData', 'getDataAt', 'deleteDataAt'): text(row[0], KEY); text(row[1], FIELD)
        elif op in ('scanData', 'scanDataAt'): text(row[0], KEY)
        elif op in ('scanDataByPrefix', 'scanDataByPrefixAt'): text(row[0], KEY); text(row[1], VALUE)
        if uid in (IMD3, IMD4):
            stamp = row[0] if op in ('backup', 'restore') else row[-2] if op == 'setDataAtWithTtl' else row[-1]
            integer(stamp, 1, 10**9)
            if stamp <= last: raise ValueError('timestamps must increase')
            last = stamp
            if op == 'setDataAtWithTtl': integer(row[-1], 1, 10**9)
            if op == 'backup': backups.append(stamp)
            if op == 'restore':
                integer(row[1], 1, 10**9)
                if not row[1] < stamp or not backups or backups[0] > row[1]: raise ValueError('restore target needs an earlier backup')


def iqr_domain(args):
    for op, row in trace(IQR, args):
        if op == 'add': integer(row[0], 0, 10**9)
        if op == 'getRandom': integer(row[0], 0, 10**15)


def lza_domain(args):
    calls = trace(LZA, args)
    arr = args[1][0][0]; intlist(arr, -10**6, 10**6)
    big = max((abs(x) for x in arr), default=0)
    a, b = 1, 0
    for op, row in calls:
        if op == 'map':
            if row[0] == 'add': integer(row[1], -10**6, 10**6); b += row[1]
            elif row[0] == 'multiply': integer(row[1], -1000, 1000); a *= row[1]; b *= row[1]
            else: raise ValueError('operation')
            if abs(a) * big + abs(b) > 10**15 or abs(a) > 10**15 or abs(b) > 10**15: raise ValueError('composed map out of exact range')
        else: integer(row[0], -2 * 10**15, 2 * 10**15)


def dwc_domain(energy, positions, costs):
    integer(energy, 0, 10**15); intlist(positions, -10**9, 10**9); intlist(costs, 1, 10**9)
    if len(positions) != len(costs) or 0 in positions or len(set(positions)) != len(positions): raise ValueError('walls')


def esc_domain(args):
    calls = trace(ESC, args)
    n, m = args[1][0]; integer(n, 1, 10**5); integer(m, 1, 10**5)
    for op, row in calls:
        if op == 'advance': integer(row[0], 0, m - 1)
        elif op == 'countInRoom': integer(row[0], 0, n - 1)
        else: integer(row[0], 1, 1000)


def elr_domain(args):
    calls = trace(ELR, args); integer(args[1][0][0], 1, 10**9); last = 0
    for _, row in calls:
        text(row[0], r'[a-z]{1,10}'); integer(row[1], 0, 10**9)
        if row[1] < last: raise ValueError('timestamps must not decrease')
        last = row[1]


def fvs_domain(sources):
    sized(sources, 0, 1000); width = None; total = 0
    for row in sources:
        sized(row, 0, 1000)
        if width is None: width = len(row)
        if len(row) != width: raise ValueError('not rectangular')
        total += len(row)
        for e in row: text(e, r'[a-z0-9_]{1,10}:[a-z0-9_:]{0,10}', 21)
    if total > 200000: raise ValueError('entry budget')


DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
TIME = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (1[0-2]|[1-9]):[0-5][0-9] (AM|PM)'


def fas_domain(words, s):
    sized(words, 1, 1000); text(s, r'[a-z]*', 10000)
    for w in words: text(w, r'[a-z]{1,50}', 50)
    if len(set(words)) != len(words): raise ValueError('words must be distinct')


def tree_children(tree):
    """Parse the level-order N-ary serialization; return (values, children lists)."""
    sized(tree, 1, 20000)
    if tree[0] is None: raise ValueError('root required')
    if len(tree) > 1 and tree[1] is not None: raise ValueError('null after root required')
    if tree[-1] is None and len(tree) > 1: raise ValueError('trailing null')
    values, kids = [tree[0]], [[]]
    parent, i = -1, 1
    while i < len(tree):
        v = tree[i]
        if v is None:
            parent += 1
            if parent >= len(values): raise ValueError('more groups than nodes')
        else:
            integer(v, 1, 100000)
            if parent < 0: raise ValueError('group before root')
            kids[parent].append(len(values)); values.append(v); kids.append([])
        i += 1
    if len(values) > 10000: raise ValueError('node budget')
    return values, kids


def fri_domain(open_, close, capacity, reservations, party):
    integer(open_, 0, 10**9); integer(close, open_ + 1, 10**9); integer(capacity, 1, 10**9); integer(party, 1, capacity)
    sized(reservations, 0, 100000); prev = None; events = []
    for r in reservations:
        sized(r, 3, 3); integer(r[0], open_, close); integer(r[1], r[0] + 1, close); integer(r[2], 1, capacity)
        if prev is not None and r[0] < prev: raise ValueError('reservations not sorted by start')
        prev = r[0]; events.append((r[0], r[2])); events.append((r[1], -r[2]))
    used = 0
    for _, d in sorted(events, key=lambda e: (e[0], e[1])):
        used += d
        if used > capacity: raise ValueError('over capacity')


def khd_domain(loans, k):
    sized(loans, 0, 100000); integer(k, 1, 100000)
    for loan in loans:
        sized(loan, 3, 3); text(loan[0], r'[a-z]{1,10}'); text(loan[1], r'[a-z]{1,10}'); text(loan[2], r'0|[1-9][0-9]{0,8}', 9)
        if loan[0] == loan[1]: raise ValueError('self loan')


def fir_domain(board, move, player):
    sized(board, 1, 300); sized(board[0], 1, 300)
    for row in board:
        sized(row, len(board[0]), len(board[0]))
        for c in row:
            if c not in ('a', 'b', '') or type(c) is not str: raise ValueError('cell')
    sized(move, 2, 2); integer(move[0], 0, len(board) - 1); integer(move[1], 0, len(board[0]) - 1)
    if board[move[0]][move[1]] != '': raise ValueError('occupied cell')
    if player not in ('a', 'b') or type(player) is not str: raise ValueError('player')


def validate_domain(uid, args):
    if uid == FST: envelope(args, 2); fst_domain(*args)
    elif uid in IMD: imd_domain(uid, args)
    elif uid == IQR: iqr_domain(args)
    elif uid == LZA: lza_domain(args)
    elif uid == DWC: envelope(args, 3); dwc_domain(*args)
    elif uid == ESC: esc_domain(args)
    elif uid == ELR: elr_domain(args)
    elif uid == FVS: envelope(args, 1); fvs_domain(args[0])
    elif uid == FMI: envelope(args, 2); text(args[0], TIME, 20); text(args[1], TIME, 20)
    elif uid == FAS: envelope(args, 2); fas_domain(*args)
    elif uid == FKD:
        envelope(args, 2); intlist(args[0], 1, 100000, 1); integer(args[1], 1, len(args[0]))
    elif uid in FPT: envelope(args, 2); tree_children(args[0]); intlist(args[1], 1, 100000, 1, 1000)
    elif uid == FRI: envelope(args, 5); fri_domain(*args)
    elif uid == KHD: envelope(args, 2); khd_domain(*args)
    elif uid == FIR: envelope(args, 3); fir_domain(*args)
    elif uid == GTR:
        envelope(args, 3); intlist(args[0], 1, 10**9, 1); intlist(args[1], 1, 10**9); intlist(args[2], 1, 10**9)
        if len(args[1]) != len(args[2]): raise ValueError('day lists differ')
    else: raise ValueError('unknown uid')


# ---------------------------------------------------------------- references
def ref_fst(files, word):
    out = []
    for name, lines in files:
        count, hits = 0, []
        for line in lines:
            c = [t.lower() for t in re.split(r'[^A-Za-z0-9]+', line)].count(word.lower())
            if c: count += c; hits.append(line)
        if count: out.append([name, str(count)] + hits)
    return out


def ref_imd(uid, calls):
    entries, backups, out = [], [], [None]   # entries: [key, field, value, expiry or None]

    def live(e, t): return t is None or e[3] is None or t < e[3]

    def find(k, f):
        for e in entries:
            if e[0] == k and e[1] == f: return e
        return None

    def scan(k, prefix, t):
        got = sorted((e[1], e[2]) for e in entries if e[0] == k and e[1].startswith(prefix) and live(e, t))
        return [f + '(' + v + ')' for f, v in got]
    for op, row in calls:
        if op in ('setData', 'setDataAt', 'setDataAtWithTtl'):
            e = find(row[0], row[1])
            if e is not None: entries.remove(e)
            expiry = row[3] + row[4] if op == 'setDataAtWithTtl' else None
            entries.append([row[0], row[1], row[2], expiry]); out.append(None)
        elif op in ('getData', 'getDataAt'):
            e = find(row[0], row[1]); t = row[2] if op == 'getDataAt' else None
            out.append(e[2] if e is not None and live(e, t) else '')
        elif op in ('deleteData', 'deleteDataAt'):
            e = find(row[0], row[1]); t = row[2] if op == 'deleteDataAt' else None
            ok = e is not None and live(e, t)
            if e is not None: entries.remove(e)
            out.append(ok)
        elif op == 'scanData': out.append(scan(row[0], '', None))
        elif op == 'scanDataByPrefix': out.append(scan(row[0], row[1], None))
        elif op == 'scanDataAt': out.append(scan(row[0], '', row[1]))
        elif op == 'scanDataByPrefixAt': out.append(scan(row[0], row[1], row[2]))
        elif op == 'backup':
            t = row[0]
            snap = [(e[0], e[1], e[2], None if e[3] is None else e[3] - t) for e in entries if live(e, t)]
            backups.append((t, snap)); out.append(len({e[0] for e in snap}))
        else:
            t, target = row
            chosen = None
            for when, snap in backups:
                if when <= target: chosen = snap
            entries = [[k, f, v, None if r is None else t + r] for k, f, v, r in chosen]
            out.append(None)
    return out


def ref_iqr(calls):
    q, out = [], [None]
    for op, row in calls:
        if op == 'add': q.append(row[0]); out.append(None)
        elif op == 'poll': out.append(q.pop(0) if q else -1)
        else: out.append(q[row[0] % len(q)] if q else -1)
    return out


def ref_lza(arr, calls):
    cur, out = list(arr), [None]
    for op, row in calls:
        if op == 'map':
            cur = [x + row[1] for x in cur] if row[0] == 'add' else [x * row[1] for x in cur]
            out.append(None)
        else: out.append(cur.index(row[0]) if row[0] in cur else -1)
    return out


def ref_dwc(energy, positions, costs):
    right = [c for p, c in sorted(zip(positions, costs)) if p > 0]
    left = [c for p, c in sorted(zip(positions, costs), reverse=True) if p < 0]
    best = 0
    for i in range(len(right) + 1):
        for j in range(len(left) + 1):
            r, l = sum(right[:i]), sum(left[:j])
            if min(2 * r + l, r + 2 * l) <= energy: best = max(best, i + j)
    return best


def ref_esc(n, m, calls):
    room, stamp, clock, out = [0] * m, list(range(m)), m, [None]
    for op, row in calls:
        if op == 'advance':
            p = row[0]
            if room[p] < n - 1: room[p] += 1; stamp[p] = clock; clock += 1
            out.append(None)
        elif op == 'countInRoom': out.append(room.count(row[0]))
        else: out.append(sorted(range(m), key=lambda p: (-room[p], stamp[p]))[:row[0]])
    return out


def ref_elr(window, calls):
    printed, out = [], [None]
    for _, (name, t) in calls:
        blocked = any(n == name and t - s < window for n, s in printed)
        if not blocked: printed.append((name, t))
        out.append(not blocked)
    return out


def ref_fvs(sources):
    final = {}
    for row in reversed(sources):
        for e in reversed(row):
            k, v = e.split(':', 1)
            if k not in final: final[k] = v
    return [k + ':' + final[k] for k in sorted(final)]


def week_minute(s):
    day, clock, half = s.split(' ')
    h, mm = clock.split(':')
    hour = int(h) % 12 + (12 if half == 'PM' else 0)
    return DAYS.index(day) * 1440 + hour * 60 + int(mm)


_LABELS = []


def ref_fmi(start, end):
    if not _LABELS:
        for d in DAYS:
            for half in ('AM', 'PM'):
                for h in [12] + list(range(1, 12)):
                    for mm in range(60): _LABELS.append('%s %d:%02d %s' % (d, h, mm, half))
    labels = _LABELS
    a, b = week_minute(start), week_minute(end)
    out, t = [], a
    while True:
        if t % 5 == 0: out.append(labels[t % 10080])
        if t % 10080 == b: break
        t += 1
    return out


def ref_fas(words, s):
    for w in words:
        key = sorted(w)
        for i in range(len(s) - len(w) + 1):
            if sorted(s[i:i + len(w)]) == key: return w
    return ''


def ref_fkd(arr, k):
    best = -1
    for i in range(len(arr)):
        seen = set()
        for j in range(i, len(arr)):
            seen.add(arr[j])
            if len(seen) >= k:
                if best < 0 or j - i + 1 < best: best = j - i + 1
                break
    return best


def ref_fpt(uid, tree, path):
    values, kids = tree_children(tree)

    def down(v, i):
        if values[v] != path[i]: return False
        if i == len(path) - 1: return True
        return any(down(c, i + 1) for c in kids[v])
    starts = [0] if uid == FPT1 else range(len(values))
    return any(down(v, 0) for v in starts)


def ref_fri(open_, close, capacity, reservations, party):
    cuts = sorted({open_, close} | {r[0] for r in reservations} | {r[1] for r in reservations})
    out = []
    for a, b in zip(cuts, cuts[1:]):
        used = sum(r[2] for r in reservations if r[0] <= a < r[1])
        if capacity - used >= party:
            if out and out[-1][1] == a: out[-1][1] = b
            else: out.append([a, b])
    return out


def ref_khd(loans, k):
    people = sorted({x for loan in loans for x in loan[:2]})
    nets = []
    for p in people:
        net = sum(int(l[2]) for l in loans if l[0] == p) - sum(int(l[2]) for l in loans if l[1] == p)
        if net > 0: nets.append((-net, p))
    nets.sort()
    return nets[k - 1][1] if k <= len(nets) else ''


def ref_fir(board, move, player):
    grid = [list(r) for r in board]; x, y = move; grid[x][y] = player
    R, Cn = len(grid), len(grid[0])
    for dx, dy in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for back in range(4):
            sx, sy = x - back * dx, y - back * dy
            cells = [(sx + i * dx, sy + i * dy) for i in range(4)]
            if all(0 <= a < R and 0 <= b < Cn and grid[a][b] == player for a, b in cells): return True
    return False


def ref_gtr(server, replaced, new):
    cur, out = list(server), []
    for old, nid in zip(replaced, new):
        cur = [nid if s == old else s for s in cur]
        out.append(sum(cur))
    return out


def budget(ok):
    if not ok: raise ValueError('reference budget')


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        calls = trace(uid, args)
        budget(len(calls) <= 400)
        if uid in IMD: return ref_imd(uid, calls)
        if uid == IQR: return ref_iqr(calls)
        if uid == LZA:
            budget(len(args[1][0][0]) <= 300); return ref_lza(args[1][0][0], calls)
        if uid == ESC:
            budget(args[1][0][1] <= 300); return ref_esc(*args[1][0], calls)
        return ref_elr(args[1][0][0], calls)
    if uid == FST:
        budget(sum(len(f[1]) for f in args[0]) <= 400); return ref_fst(*args)
    if uid == DWC:
        budget(len(args[1]) <= 60); return ref_dwc(*args)
    if uid == FVS:
        budget(len(args[0]) * len(args[0][0] if args[0] else []) <= 2000); return ref_fvs(args[0])
    if uid == FMI: return ref_fmi(*args)
    if uid == FAS:
        budget(len(args[0]) * len(args[1]) <= 20000); return ref_fas(*args)
    if uid == FKD:
        budget(len(args[0]) <= 400); return ref_fkd(*args)
    if uid in FPT:
        budget(len(args[0]) <= 400 and len(args[1]) <= 400); return ref_fpt(uid, *args)
    if uid == FRI:
        budget(len(args[3]) <= 200); return ref_fri(*args)
    if uid == KHD:
        budget(len(args[0]) <= 300); return ref_khd(*args)
    if uid == FIR:
        budget(len(args[0]) * len(args[0][0]) <= 2500); return ref_fir(*args)
    budget(len(args[0]) * len(args[1]) <= 40000); return ref_gtr(*args)
