"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (per-party rescans,
innermost-call regex rewriting, exhaustive enumeration, literal API emulation, repeated relaxation
sweeps, explicit path enumeration, all-pairs comparison) and refuse inputs above a small budget.
"""
from itertools import product
import re

H = 'hack2hire:'
EOD1 = H + '677b5ef978175fce2ecdfc12'
EOD2 = H + '677b5f4078175fce2ecdfc13'
EVAL = H + '67872240e20f8f324213c297'
FAC1 = H + '6a1a10e2c81f779dc6a23794'
FAC2 = H + '6a1a1112c81f779dc6a23797'
FAC3 = H + '6a2b14eb97d3b4b32966cb00'
FSC = H + '68fbce5f378ce2f46141f920'
FSD = H + '6962cbcef731aa3969ef5176'
FSDS = H + '696442bb3b4797da7459a055'
BOTT = H + '684ba2bf4023c4f502877de9'
MID1 = H + '67e4a80550b60b77022f3848'
MID2 = H + '67e4adbf50b60b77022f384b'
EXIT1 = H + '68f93bebd7ff180d0ab95208'
EXIT2 = H + '68f9a7290fa32e4d82f4fb89'
OFFER = H + '6a5e8727bd09995a83107ec3'
PREFIX = H + '67e4ab3b50b60b77022f384a'
HUB = H + '687e85b47bd121d1f502da90'
DNA = H + '67707837366afdc1233e4ff7'
LOGIN = H + '68acfc391bf7d2097f647f71'
CITY = H + '6781dbee3cd890ccd3798fc0'
PATH = H + '67dcd82499f4f89b276f188a'

IDS = (EOD1, EOD2, EVAL, FAC1, FAC2, FAC3, FSC, FSD, FSDS, BOTT, MID1, MID2, EXIT1, EXIT2, OFFER, PREFIX, HUB, DNA,
       LOGIN, CITY, PATH)

# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    FSC: ('FileSystemStats', 1, {'getTotalSize': 0, 'getCollectionSize': 1, 'getTopCollections': 1, 'setParent': 2, 'getHierarchySize': 1},
          ('setParent',)),
}
DIGITS = r'0|[1-9][0-9]{0,9}'
NAME20 = r'[A-Za-z0-9_]{1,20}'
SEG = r'[A-Za-z0-9_.]{1,10}'
INF = float('inf')


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def decimal(v, hi):
    text(v, DIGITS, 10)
    if int(v) > hi: raise ValueError('decimal range')


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


def grid(g, values):
    if type(g) is not list or not g: raise ValueError('grid rows')
    width = None
    for row in g:
        if type(row) is not list or not row: raise ValueError('grid row')
        if width is None: width = len(row)
        if len(row) != width: raise ValueError('rectangular grid')
        for v in row:
            if type(v) is not int or v not in values: raise ValueError('grid cell')
    if len(g) * width > 100000: raise ValueError('grid size')


def acyclic(n, edges):
    indeg = [0] * n; out = [[] for _ in range(n)]
    for u, v in edges: out[u].append(v); indeg[v] += 1
    todo = [v for v in range(n) if indeg[v] == 0]; seen = 0
    while todo:
        u = todo.pop(); seen += 1
        for v in out[u]:
            indeg[v] -= 1
            if indeg[v] == 0: todo.append(v)
    if seen != n: raise ValueError('cycle')


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
    return ops, rows


EVAL_TOKEN = re.compile(r' *(add|sub|\(|\)|,|-?(?:0|[1-9][0-9]*))')


def eval_check(s):
    """Validate the inferred add/sub grammar with a non-recursive state machine."""
    if type(s) is not str or not 1 <= len(s) <= 100000: raise ValueError('expression size')
    pos, frames, state, pending = 0, [], 'expr', None
    while True:
        m = EVAL_TOKEN.match(s, pos)
        if m is None:
            if s[pos:].strip(' ') == '' and state == 'after' and not frames: return
            raise ValueError('token')
        tok = m.group(1); pos = m.end()
        if pending is not None:
            if tok != '(': raise ValueError('call needs (')
            frames.append([pending, 0]); pending = None; state = 'expr'; continue
        if state == 'expr':
            if tok in ('add', 'sub'): pending = tok
            elif tok[-1].isdigit():
                if tok == '-0' or abs(int(tok)) > 10**9: raise ValueError('literal domain')
                state = 'after'
            else: raise ValueError('expression expected')
        else:
            if not frames or tok not in (',', ')'): raise ValueError('separator expected')
            frames[-1][1] += 1
            if tok == ',': state = 'expr'
            else:
                name, count = frames.pop()
                if (name == 'add' and count < 2) or (name == 'sub' and count != 2): raise ValueError('argument count')
                state = 'after'


def costs_check(costs):
    if type(costs) is not list or not 1 <= len(costs) <= 100000: raise ValueError('costs size')
    total = 0
    for row in costs:
        array(row, 0, 10**6, 1, 200000); total += len(row)
    if total > 200000: raise ValueError('total options')


FSC_FILE = re.compile(r'[A-Za-z0-9_.-]{1,30},(?:[1-9][0-9]{0,6})((?:,[A-Za-z0-9_]{1,20}){0,5})')


def fsc_domain(args):
    ops, rows = trace(FSC, args, 3001)
    files = rows[0][0]
    strlist(files, FSC_FILE.pattern, 0, 10000, 160)
    ids = set()
    for f in files:
        if int(f.split(',')[1]) > 10**6: raise ValueError('size range')
        ids.update(f.split(',')[2:])
    parent = {}
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'getTopCollections': integer(row[0], 1, 100)
        else:
            for v in row: text(v, NAME20, 20)
            ids.update(row)
        if op == 'setParent':
            child, par = row
            if child == par or child in parent: raise ValueError('child already linked')
            a = par
            while a is not None:
                if a == child: raise ValueError('cycle')
                a = parent.get(a)
            parent[child] = par
    if len(ids) > 2000: raise ValueError('collection count')


def fsd_domain(dirs, edges, files, path):
    pat = '(?:/' + SEG + ')+'
    strlist(dirs, pat, 0, 100000, 11000); strlist(files, pat, 0, 100000, 11000); text(path, pat, 11000)
    rows_of(edges, 2, 100000)
    ds, fs = set(dirs), set(files)
    if len(ds) != len(dirs) or len(fs) != len(files) or ds & fs: raise ValueError('unique paths')
    if len(dirs) + len(files) > 100000 or sum(map(len, dirs)) + sum(map(len, files)) > 5000000: raise ValueError('size budget')
    seen = set()
    for p, c in edges:
        if type(p) is not str or type(c) is not str or p not in ds or (c not in ds and c not in fs): raise ValueError('edge endpoints')
        if c in seen or not c.startswith(p + '/') or '/' in c[len(p) + 1:]: raise ValueError('edge shape')
        seen.add(c)
    if not fs <= seen: raise ValueError('every file has a parent')
    for d in dirs:  # a directory whose string parent exists must be linked to it
        if d not in seen and d.rsplit('/', 1)[0] in ds: raise ValueError('missing directory edge')


def fsds_domain(root, limit):
    integer(limit, 0, 10**14)
    if type(root) is not dict or set(root) != {'name', 'children'}: raise ValueError('root must be a directory')
    stack, count = [(root, 0)], 0
    while stack:
        node, depth = stack.pop(); count += 1
        if type(node) is not dict: raise ValueError('entry')
        text(node.get('name'), r'[A-Za-z0-9_.-]{1,20}', 20)
        if set(node) == {'name', 'size'}: integer(node['size'], 0, 10**8)
        elif set(node) == {'name', 'children'}:
            if type(node['children']) is not list or depth > 90: raise ValueError('directory')
            stack.extend((c, depth + 1) for c in node['children'])
        else: raise ValueError('entry keys')
    if count > 100000: raise ValueError('entry count')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid in (EOD1, EOD2):
        envelope(args, 1)
        rows_of(args[0], 3, 100000)
        for a, b, x in args[0]:
            text(a, NAME20, 20); text(b, NAME20, 20); integer(x, 1, 10**9)
            if a == b: raise ValueError('payer != payee')
    elif uid == EVAL:
        envelope(args, 1); eval_check(args[0])
    elif uid in (FAC1, FAC2, FAC3):
        envelope(args, 2 if uid == FAC3 else 1)
        costs_check(args[0])
        if uid == FAC3:
            n = len(args[0]); edges = args[1]
            rows_of(edges, 2, n - 1, n - 1)
            parent = list(range(n))

            def find(x):
                while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
                return x
            for u, v in edges:
                integer(u, 0, n - 1); integer(v, 0, n - 1)
                ru, rv = find(u), find(v)
                if ru == rv: raise ValueError('edges must form a tree')
                parent[ru] = rv
    elif uid == FSC:
        fsc_domain(args)
    elif uid == FSD:
        envelope(args, 4); fsd_domain(*args)
    elif uid == FSDS:
        envelope(args, 2); fsds_domain(*args)
    elif uid == BOTT:
        envelope(args, 2)
        integer(args[0], 1, 100000); n = args[0]
        rows_of(args[1], 2, 200000)
        seen = set()
        for u, v in args[1]:
            integer(u, 0, n - 1); integer(v, 0, n - 1)
            if u == v or (u, v) in seen: raise ValueError('self loop or duplicate edge')
            seen.add((u, v))
        acyclic(n, args[1])
    elif uid == MID1:
        envelope(args, 1)
        pairs = args[0]
        rows_of(pairs, 2, 100000, 2)
        if len(pairs) % 2: raise ValueError('odd course count')
        firsts, seconds = {}, {}
        for a, b in pairs:
            text(a, NAME20, 20); text(b, NAME20, 20)
            if a in firsts or b in seconds or a == b: raise ValueError('chain shape')
            firsts[a] = b; seconds[b] = a
        starts = [a for a in firsts if a not in seconds]
        if len(starts) != 1: raise ValueError('single start')
        cur, steps = starts[0], 0
        while cur in firsts: cur = firsts[cur]; steps += 1
        if steps != len(pairs): raise ValueError('one continuous chain')
    elif uid == MID2:
        envelope(args, 1)
        pairs = args[0]
        rows_of(pairs, 2, 5000, 1)
        names, seen = {}, set()
        for a, b in pairs:
            text(a, NAME20, 20); text(b, NAME20, 20)
            if a == b or (a, b) in seen: raise ValueError('self loop or duplicate pair')
            seen.add((a, b)); names.setdefault(a, len(names)); names.setdefault(b, len(names))
        if len(names) > 1000: raise ValueError('course count')
        acyclic(len(names), [(names[a], names[b]) for a, b in pairs])
    elif uid in (EXIT1, EXIT2):
        envelope(args, 2)
        grid(args[0], (0, 1))
        e = args[1]
        if type(e) is not list or len(e) != 2: raise ValueError('entrance')
        integer(e[0], 0, len(args[0]) - 1); integer(e[1], 0, len(args[0][0]) - 1)
        if args[0][e[0]][e[1]] != 1: raise ValueError('entrance must be open')
    elif uid == OFFER:
        envelope(args, 3)
        offers, events, t = args
        rows_of(offers, 4, 200); rows_of(events, 4, 100000); integer(t, 0, 10**9)
        ids = set()
        for oid, s, e, m in offers:
            text(oid, r'[A-Za-z0-9_]{1,12}', 12); decimal(s, 10**9); decimal(e, 10**9); decimal(m, 10**6)
            if oid in ids or int(s) > int(e): raise ValueError('offer rows')
            ids.add(oid)
        users = set()
        for u, ts, act, oid in events:
            text(u, r'[A-Za-z0-9_]{1,12}', 12); decimal(ts, 10**9); text(act, r'redeem|unredeem', 8); text(oid, r'[A-Za-z0-9_]{1,12}', 12)
            users.add(u)
        if len(users) > 500: raise ValueError('user count')
    elif uid == PREFIX:
        envelope(args, 1)
        strlist(args[0], r'[a-z]{1,100}', 1, 100000, 100)
        if sum(map(len, args[0])) > 300000: raise ValueError('character budget')
        s = sorted(args[0])
        for a, b in zip(s, s[1:]):
            if b.startswith(a): raise ValueError('no word is a prefix of another')
    elif uid == HUB:
        envelope(args, 4)
        caps, ivs, req, task = args
        array(caps, 1, 10**9, 1, 10000); integer(req, 1, 10**9)
        if type(ivs) is not list or len(ivs) != len(caps): raise ValueError('intervals per hub')
        total = 0
        for row in ivs + [[task]]:
            if type(row) is not list: raise ValueError('interval list')
            total += len(row)
            for iv in row:
                text(iv, '(?:' + DIGITS + '):(?:' + DIGITS + ')', 21)
                a, b = map(int, iv.split(':'))
                if not a <= b <= 10**9: raise ValueError('interval range')
        if total > 100001: raise ValueError('interval budget')
    elif uid == DNA:
        envelope(args, 1)
        strlist(args[0], r'[ACGT]{1,100}', 0, 100000, 100)
        if sum(map(len, args[0])) > 300000: raise ValueError('character budget')
    elif uid == LOGIN:
        envelope(args, 2)
        strlist(args[0], NAME20 + ' (?:signin|signout) (?:' + DIGITS + ')', 0, 100000, 50)
        integer(args[1], 0, 10**9)
        last = 0
        for line in args[0]:
            t = int(line.rsplit(' ', 1)[1])
            if t > 10**9 or t < last: raise ValueError('chronological timestamps')
            last = t
    elif uid == CITY:
        envelope(args, 4)
        cities, xs, ys, qs = args
        strlist(cities, r'[a-z0-9]{1,10}', 1, 100000, 10)
        array(xs, 1, 10**9, len(cities), len(cities)); array(ys, 1, 10**9, len(cities), len(cities))
        if len(set(cities)) != len(cities) or len(set(zip(xs, ys))) != len(cities): raise ValueError('distinct names and points')
        strlist(qs, r'[a-z0-9]{1,10}', 1, 100000, 10)
        known = set(cities)
        if any(q not in known for q in qs): raise ValueError('query names a city')
    elif uid == PATH:
        envelope(args, 1)
        grid(args[0], range(10))


# ---------------------------------------------------------------- references (small inputs only)
def balances_literal(rows):
    parties = sorted({r[0] for r in rows} | {r[1] for r in rows})
    out = []
    for p in parties:  # rescan the full list per party
        out.append([p, sum(x for a, b, x in rows if b == p) - sum(x for a, b, x in rows if a == p)])
    return out


def ref_settle(rows):
    bal = {p: v for p, v in balances_literal(rows)}
    out = []
    while any(bal.values()):
        cred = min((p for p in bal if bal[p] > 0), key=lambda p: (-bal[p], p))
        debt = min((p for p in bal if bal[p] < 0), key=lambda p: (bal[p], p))
        amt = min(bal[cred], -bal[debt])
        out.append([debt, cred, amt]); bal[cred] -= amt; bal[debt] += amt
    return out


INNER = re.compile(r'(add|sub)\(([^()]*)\)')


def ref_eval(s):
    s = s.replace(' ', '')
    while True:
        m = INNER.search(s)
        if m is None: return int(s)
        vals = [int(x) for x in m.group(2).split(',')]
        v = sum(vals) if m.group(1) == 'add' else vals[0] - vals[1]
        s = s[:m.start()] + str(v) + s[m.end():]


def ref_fac(uid, costs, edges=None):
    if uid == FAC2: edges = [[i, i + 1] for i in range(len(costs) - 1)]
    elif uid == FAC1: edges = []
    best = None
    for pick in product(*[range(len(r)) for r in costs]):
        if any(pick[u] == pick[v] for u, v in edges): continue
        total = sum(r[j] for r, j in zip(costs, pick))
        if best is None or total < best: best = total
    return -1 if best is None else best


def ref_fsc(ops, rows):
    files = [f.split(',') for f in rows[0][0]]
    parent, out = {}, [None]

    def direct(cid): return sum(int(f[1]) for f in files if cid in set(f[2:]))
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'getTotalSize': out.append(sum(int(f[1]) for f in files))
        elif op == 'getCollectionSize': out.append(direct(row[0]))
        elif op == 'getTopCollections':
            named = {c for f in files for c in f[2:]}
            out.append(sorted(named, key=lambda c: (-direct(c), c))[:row[0]])
        elif op == 'setParent': parent[row[0]] = row[1]; out.append(None)
        else:
            known = {c for f in files for c in f[2:]} | set(parent) | set(parent.values())
            total = 0
            for c in known:  # walk every collection's ancestor chain looking for the queried id
                a = c
                while a is not None and a != row[0]: a = parent.get(a)
                if a == row[0]: total += direct(c)
            out.append(total if known else 0)
    return out


class EmulatedFileSystem:
    """Literal model of the preview's FileSystem API: delete only removes a file or an empty directory."""
    def __init__(self, dirs, edges, files):
        self.dirs, self.files = set(dirs), set(files)
        self.kids = {d: [] for d in dirs}; self.up = {}
        for p, c in edges: self.kids[p].append(c); self.up[c] = p

    def isDirectory(self, p): return p in self.dirs

    def getAllFiles(self, p): return list(self.kids[p])

    def delete(self, p):
        if p in self.files: self.files.discard(p)
        elif p in self.dirs and not self.kids[p]: self.dirs.discard(p)
        else: return False
        if p in self.up: self.kids[self.up[p]].remove(p)
        return True


def ref_fsd(dirs, edges, files, path):
    fs = EmulatedFileSystem(dirs, edges, files)
    if path not in fs.dirs and path not in fs.files: return []
    out = []

    def rec(p):
        if fs.isDirectory(p):
            for c in fs.getAllFiles(p): rec(c)
        if not fs.delete(p): raise AssertionError('emulated delete refused')
        out.append(p)
    rec(path)
    return out


def ref_fsds(root, limit):
    def size(node): return node['size'] if 'size' in node else sum(size(c) for c in node['children'])

    def dirs(node):
        if 'children' in node:
            yield node
            for c in node['children']: yield from dirs(c)
    return sum(t for t in (size(d) for d in dirs(root)) if t <= limit)


def ref_bott(n, edges):
    level = [1] * n
    changed = True
    while changed:
        changed = False
        for u, v in edges:
            if level[u] + 1 > level[v]: level[v] = level[u] + 1; changed = True
    out = []
    for t in sorted(set(level)):
        at = [v for v in range(n) if level[v] == t]
        if len(at) == 1: out.append(at[0])
    return out


def ref_mid1(pairs):
    start = next(a for a, _ in pairs if all(b != a for _, b in pairs))
    chain = [start]
    while len(chain) <= len(pairs):
        chain.append(next(b for a, b in pairs if a == chain[-1]))  # linear search per step
    return chain[len(pairs) // 2]


def ref_mid2(pairs):
    succ = {}
    for a, b in pairs: succ.setdefault(a, []).append(b); succ.setdefault(b, [])
    starts = [c for c in succ if all(b != c for _, b in pairs)]
    mids, stack, paths = set(), [[s] for s in starts], 0
    while stack:
        path = stack.pop()
        nxt = succ[path[-1]]
        if not nxt:
            paths += 1
            if paths > 20000: raise ValueError('reference budget')
            mids.add(path[(len(path) - 1) // 2])
        for b in nxt: stack.append(path + [b])
    return sorted(mids)


def relax_distances(g, sources, moves):
    m, n = len(g), len(g[0])
    d = [[INF] * n for _ in range(m)]
    for r, c in sources: d[r][c] = 0
    changed = True
    while changed:
        changed = False
        for r in range(m):
            for c in range(n):
                if not g[r][c]: continue
                for dr, dc in moves:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < m and 0 <= cc < n and d[rr][cc] + 1 < d[r][c]: d[r][c] = d[rr][cc] + 1; changed = True
    return d


FOUR = ((1, 0), (-1, 0), (0, 1), (0, -1))
EIGHT = FOUR + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def ref_exit(uid, g, e):
    d = relax_distances(g, [tuple(e)], FOUR)
    m, n = len(g), len(g[0])
    exits = [(d[r][c], r, c) for r in range(m) for c in range(n)
             if g[r][c] and (r in (0, m - 1) or c in (0, n - 1)) and [r, c] != e and d[r][c] < INF]
    if uid == EXIT1: return min(exits)[0] if exits else -1
    return [min(exits)[1], min(exits)[2]] if exits else [-1, -1]


def ref_offer(offers, events, t):
    out = []
    for u in sorted({e[0] for e in events}):
        avail = []
        for oid, s, e, m in offers:
            s, e, m, count = int(s), int(e), int(m), 0
            for eu, ts, act, eo in events:  # replay the whole list for this (user, offer)
                ts = int(ts)
                if eu != u or eo != oid or ts > t or ts < s or ts > e: continue
                if act == 'redeem' and count < m: count += 1
                elif act == 'unredeem' and count > 0: count -= 1
            if s <= t <= e and count < m: avail.append(oid)
        out.append([u, avail])
    return out


def ref_prefix(words):
    out = []
    for i, w in enumerate(words):
        for k in range(1, len(w) + 1):
            if not any(j != i and o.startswith(w[:k]) for j, o in enumerate(words)):
                out.append(w[:k]); break
    return out


def ref_hub(caps, ivs, req, task):
    a, b = map(int, task.split(':'))
    ok = [i for i in range(len(caps)) if caps[i] >= req and
          all(int(iv.split(':')[1]) < a or b < int(iv.split(':')[0]) for iv in ivs[i])]
    return min(ok, key=lambda i: (caps[i], i)) if ok else -1


COMP = str.maketrans('ACGT', 'TGCA')


def ref_dna(seqs):
    return sum(1 for i in range(len(seqs)) for j in range(i + 1, len(seqs)) if seqs[j] == seqs[i].translate(COMP)[::-1])


def ref_login(logs, max_time):
    rows = [line.split(' ') for line in logs]
    valid = []
    for u in sorted({r[0] for r in rows}):
        start = None
        for who, act, t in rows:
            if who != u: continue
            if act == 'signin': start = int(t)
            elif start is not None:
                if int(t) - start <= max_time: valid.append(u); break
                start = None
    return valid


def ref_city(cities, xs, ys, qs):
    out = []
    for q in qs:
        i = cities.index(q); best = None
        for j in range(len(cities)):
            if j != i and (xs[j] == xs[i] or ys[j] == ys[i]):
                key = (abs(xs[j] - xs[i]) + abs(ys[j] - ys[i]), cities[j])
                if best is None or key < best: best = key
        out.append(best[1] if best else 'NONE')
    return out


def ref_path(g):
    m, n = len(g), len(g[0])
    if not g[0][0] or not g[m - 1][n - 1]: return -1
    d = relax_distances(g, [(0, 0)], EIGHT)
    return d[m - 1][n - 1] + 1 if d[m - 1][n - 1] < INF else -1


def reference(uid, args):
    validate_domain(uid, args)
    if uid in (EOD1, EOD2):
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return balances_literal(args[0]) if uid == EOD1 else ref_settle(args[0])
    if uid == EVAL:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_eval(args[0])
    if uid in (FAC1, FAC2, FAC3):
        combos = 1
        for r in args[0]: combos *= len(r)
        if combos > 20000: raise ValueError('reference budget')
        return ref_fac(uid, *args)
    if uid == FSC:
        if len(args[0]) > 300 or len(args[1][0][0]) > 300: raise ValueError('reference budget')
        return ref_fsc(*args)
    if uid == FSD:
        if len(args[0]) + len(args[2]) > 400: raise ValueError('reference budget')
        return ref_fsd(*args)
    if uid == FSDS:
        if len(str(args[0])) > 40000: raise ValueError('reference budget')
        return ref_fsds(*args)
    if uid == BOTT:
        if args[0] > 300: raise ValueError('reference budget')
        return ref_bott(*args)
    if uid == MID1:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_mid1(args[0])
    if uid == MID2: return ref_mid2(args[0])
    if uid in (EXIT1, EXIT2):
        if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
        return ref_exit(uid, *args)
    if uid == OFFER:
        if len(args[0]) * len(args[1]) * max(1, len({e[0] for e in args[1]})) > 2000000: raise ValueError('reference budget')
        return ref_offer(*args)
    if uid == PREFIX:
        if len(args[0]) > 100: raise ValueError('reference budget')
        return ref_prefix(args[0])
    if uid == HUB: return ref_hub(*args)
    if uid == DNA:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_dna(args[0])
    if uid == LOGIN:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_login(*args)
    if uid == CITY:
        if len(args[0]) * len(args[3]) > 2000000: raise ValueError('reference budget')
        return ref_city(*args)
    if len(args[0]) * len(args[0][0]) > 400: raise ValueError('reference budget')
    return ref_path(args[0])


# ---------------------------------------------------------------- closed forms used by analytic maximum rows
def serpentine_exit(rows, cols):
    """EXIT maze: border walls; odd rows 1..rows-2 are corridors over columns 1..cols-2; even interior rows are walls with one gap
    (column cols-2 when row % 4 == 2, else column 1); the only border opening is (rows-1, end column of the last corridor)."""
    g = [[0] * cols for _ in range(rows)]
    for r in range(1, rows - 1):
        if r % 2: g[r][1:cols - 1] = [1] * (cols - 2)
        else: g[r][cols - 2 if r % 4 == 2 else 1] = 1
    k = (rows - 2 + 1) // 2  # corridors
    end = cols - 2 if (k - 1) % 2 == 0 else 1
    g[rows - 1][end] = 1
    moves = k * (cols - 3) + (k - 1) * 2 + 1
    return g, [1, 1], moves, [rows - 1, end]


def serpentine_path(rows, cols):
    """PATH maze (rows odd): even rows are corridors; odd rows are walls with a gap at column cols-1 (row % 4 == 1) or 0; rows odd, cols >= 3."""
    g = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        if r % 2 == 0: g[r] = [1 + (r + c) % 9 for c in range(cols)]
        else: g[r][cols - 1 if r % 4 == 1 else 0] = 5
    k = (rows + 1) // 2
    if k == 1: return g, cols
    moves = (cols - 2) + (k - 1) * 2 + max(0, k - 2) * (cols - 3) + (0 if (k - 1) % 2 else cols - 2)
    return g, moves + 1
