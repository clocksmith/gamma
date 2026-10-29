"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (binary-string rebuilding,
quadratic DP, relaxation sweeps, list-based snake simulation, all-pairs matching with calendar.timegm,
set tests, str.replace, linear parameter scans, subset enumeration, per-element startswith, regex
substitution to a fixpoint, row-by-row fall simulation, exhaustive colouring, whole-board scans,
area sums and in-order replay).
"""
import calendar
from datetime import datetime
from functools import lru_cache
from itertools import combinations, product
import re

H = 'hack2hire:'
PARITY = H + '67cf4b1faca6a2fa74a72cfd'
HIKE = H + '681aa38c0a6e86cbf10c58f9'
SPATH = H + '680aa01ecbb5948f87732bc0'
SNAKE = H + '68c48c55e558bc07a7541e31'
SPAM = H + '6842720b61bdd61d17676953'
BEE = H + '68dc5d69dd5418be11109b00'
REPL = H + '688bd40e3867670cfb894186'
READ = H + '67801e4c6fee41e51af73dda'
SUB1 = H + '677c8aba5cbaff553b53b06e'
SUB2 = H + '677c90795cbaff553b53b06f'
SUB3 = H + '677c923c5cbaff553b53b070'
WRAP = H + '67882811e20f8f324213c2a0'
TPL1 = H + '69d18c8717b72775cc49c0c2'
TPL2 = H + '69d18cdd17b72775cc49c0c6'
TET1 = H + '6aa861838c97c56cdbdc93e2'
TET2 = H + '6aa8623b8c97c56cdbdc93eb'
COLOR = H + '67ff11d2a19f45c95d40567f'
TTT = H + '684cd590cab8e9bb7ea93b11'
TRI = H + '6a95ede5cddc54478ddf6b5b'
FLIGHT = H + '69f3a12f42791c82ab992d99'

IDS = (PARITY, HIKE, SPATH, SNAKE, SPAM, BEE, REPL, READ, SUB1, SUB2, SUB3, WRAP, TPL1, TPL2, TET1, TET2, COLOR, TTT, TRI, FLIGHT)
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    SNAKE: ('SnakeGame', 2, {'move': 1}, ()),
    TTT: ('TicTacToe', 3, {'move': 3}, ()),
}
MOD = 1000000007
NAME = r'[A-Za-z0-9_]{1,20}'
PLACEHOLDER = re.compile(r'\{([A-Za-z0-9_]{1,20})\}')
TETS = (TET1, TET2)
SUBS = (SUB1, SUB2, SUB3)
TPLS = (TPL1, TPL2)


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def binary_grid(g, max_rows, max_cols):
    if type(g) is not list or not 1 <= len(g) <= max_rows or type(g[0]) is not list or not 1 <= len(g[0]) <= max_cols: raise ValueError('grid shape')
    for row in g:
        if type(row) is not list or len(row) != len(g[0]): raise ValueError('ragged grid')
        for v in row:
            if type(v) is not int or v not in (0, 1): raise ValueError('cell domain')


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


@lru_cache(maxsize=None)
def stamp(v, seconds):
    """Validate a fixed-width timestamp string; return its UTC epoch seconds (calendar.timegm)."""
    pattern = r'(19[7-9][0-9]|20[0-9][0-9])-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}' + (':[0-9]{2}' if seconds else '')
    if type(v) is not str or re.fullmatch(pattern, v) is None: raise ValueError('timestamp format')
    parts = (int(v[0:4]), int(v[5:7]), int(v[8:10]), int(v[11:13]), int(v[14:16]), int(v[17:19]) if seconds else 0)
    datetime(*parts)  # raises ValueError for an impossible date or time
    return calendar.timegm(parts + (0, 0, 0))


def placeholders(s, keys):
    """Check well-formed {name} placeholders whose names are keys; return the names in order."""
    names, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == '}': raise ValueError('stray closing brace')
        if ch == '{':
            m = PLACEHOLDER.match(s, i)
            if m is None: raise ValueError('malformed placeholder')
            if m.group(1) not in keys: raise ValueError('undefined placeholder')
            names.append(m.group(1)); i = m.end()
        else: i += 1
    return names


def tpl_lengths(keys, values):
    """Expanded length per key (dependency order, iterative); raises on a cycle."""
    refs = {k: placeholders(v, set(keys)) for k, v in zip(keys, values)}
    raw = {k: len(v) - sum(len(n) + 2 for n in refs[k]) for k, v in zip(keys, values)}
    length, state = {}, {}
    for root in keys:
        if root in length: continue
        stack = [(root, 0)]
        while stack:
            k, i = stack.pop()
            if i == 0:
                if state.get(k) == 'open': raise ValueError('cyclic references')
                state[k] = 'open'
            if i < len(refs[k]):
                stack.append((k, i + 1)); child = refs[k][i]
                if child not in length:
                    if state.get(child) == 'open': raise ValueError('cyclic references')
                    stack.append((child, 0))
            else:
                length[k] = raw[k] + sum(length[c] for c in refs[k]); state[k] = 'done'
    return length


def fall(background, block, offset):
    """Row-by-row fall from fully above the grid; returns the resting top row of the block."""
    rows, h = len(background), len(block)
    cells = [(r, c) for r in range(h) for c in range(len(block[0])) if block[r][c]]
    top = -h
    while True:
        nxt = top + 1
        if any(nxt + r >= rows or (nxt + r >= 0 and background[nxt + r][offset + c]) for r, c in cells): return top
        top = nxt


def subset_count_capped(nums, k, cap):
    """Number of distinct value multisets summing to k, capped at cap + 1."""
    counts = {}
    for v in nums: counts[v] = counts.get(v, 0) + 1
    ways = [1] + [0] * k
    for v, m in counts.items():
        new = ways[:]
        for s in range(k + 1):
            if ways[s]:
                for j in range(1, m + 1):
                    t = s + j * v
                    if t > k: break
                    new[t] = min(cap + 1, new[t] + ways[s])
        ways = new
    return ways[k]


def validate_domain(uid, args):
    if uid == PARITY:
        envelope(args, 1); integer(args[0], 0, 255)
    elif uid == HIKE:
        envelope(args, 2); t, k = args; array(t, 0, 10**9, 1, 100000); integer(k, 0, 100000)
        if t[0] != 0 or any(t[i] > t[i + 1] for i in range(len(t) - 1)): raise ValueError('t must start at 0 and be non-decreasing')
    elif uid == SPATH:
        envelope(args, 4); n, edges, s, t = args; integer(n, 1, 100000)
        if type(edges) is not list or len(edges) > 200000: raise ValueError('edge count')
        for e in edges:
            if type(e) is not list or len(e) != 2: raise ValueError('edge shape')
            integer(e[0], 0, n - 1); integer(e[1], 0, n - 1)
        integer(s, 0, n - 1); integer(t, 0, n - 1)
    elif uid == SNAKE:
        ops, rows = trace(uid, args, 100001); r, c = rows[0]
        integer(r, 1, 100000); integer(c, 1, 100000)
        if r * c > 10**9: raise ValueError('board size')
        for row in rows[1:]: text(row[0], r'[UDLR]', 1)
    elif uid == SPAM:
        envelope(args, 3); calls, reports, window = args
        if type(calls) is not list or len(calls) > 100000 or type(reports) is not list or len(reports) > 100000: raise ValueError('log size')
        for c in calls:
            if type(c) is not list or len(c) != 3: raise ValueError('call shape')
            text(c[0], r'[A-Za-z0-9+-]{1,15}', 15); text(c[1], r'[A-Za-z0-9+-]{1,15}', 15); stamp(c[2], True)
        for r in reports:
            if type(r) is not list or len(r) != 2: raise ValueError('report shape')
            text(r[0], r'[A-Za-z0-9+-]{1,15}', 15); stamp(r[1], True)
        integer(window, 0, 10**9)
    elif uid == BEE:
        envelope(args, 3); req, opt, words = args; text(req, r'[a-z]', 1)
        if type(opt) is not list or len(opt) > 26: raise ValueError('optional letters')
        for ch in opt: text(ch, r'[a-z]', 1)
        if type(words) is not list or len(words) > 100000: raise ValueError('dictionary size')
        for w in words: text(w, r'[a-z]{1,20}', 20)
    elif uid == REPL:
        envelope(args, 3); src, tgt, rep = args
        text(src, r'[ -~]*', 100000); text(tgt, r'[ -~]+', 100000); text(rep, r'[ -~]*', 1000)
        if len(src) + src.count(tgt) * (len(rep) - len(tgt)) > 2000000: raise ValueError('output size')
    elif uid == READ:
        envelope(args, 2); array(args[0], 1, 10**9, 1, 100000); integer(args[1], 1, 10**9)
    elif uid in SUBS:
        envelope(args, 2); nums, k = args
        if uid == SUB3:
            array(nums, 1, 10**6, 1, 100); integer(k, 1, 10000)
            if subset_count_capped(nums, k, 10000) > 10000: raise ValueError('author test cap: too many combinations')
        else:
            array(nums, 1, 10**6, 1, 1000); integer(k, 1, 10**9); total = sum(nums)
            if k < total:
                work = min(k, total - k) * (len(nums) if uid == SUB2 else 1)
                if work > 10**6: raise ValueError('author test cap')
    elif uid == WRAP:
        envelope(args, 2); text(args[0], r'[a-z]+( [a-z]+)*', 100000)
        if type(args[1]) is not list or not 1 <= len(args[1]) <= 1000: raise ValueError('element count')
        for e in args[1]: text(e, r'[a-z]{1,20}', 20)
    elif uid in TPLS:
        envelope(args, 3); txt, keys, values = args; text(txt, r'[ -~]*', 100000)
        if type(keys) is not list or type(values) is not list or len(keys) != len(values) or len(keys) > 2000: raise ValueError('key lists')
        if uid == TPL2 and not keys: raise ValueError('at least one key')
        for k in keys: text(k, NAME, 20)
        if len(set(keys)) != len(keys): raise ValueError('duplicate key')
        for v in values: text(v, r'[ -z|~]*' if uid == TPL1 else r'[ -~]*', 1000)
        if uid == TPL1: lengths = {k: len(v) for k, v in zip(keys, values)}
        else:
            lengths = tpl_lengths(keys, values)
            if any(x > 2000000 for x in lengths.values()): raise ValueError('expanded value size')
        names = placeholders(txt, set(keys))
        if len(txt) - sum(len(n) + 2 for n in names) + sum(lengths[n] for n in names) > 2000000: raise ValueError('output size')
    elif uid in TETS:
        envelope(args, 3); bg, blk, off = args; binary_grid(bg, 300, 300); binary_grid(blk, 10, 10)
        if not any(any(row) for row in blk): raise ValueError('empty block')
        integer(off, 0, len(bg[0]) - len(blk[0]))
        top = fall(bg, blk, off)
        if any(top + r < 0 for r in range(len(blk)) if any(blk[r])): raise ValueError('block does not fit inside the grid (inferred precondition)')
    elif uid == COLOR:
        envelope(args, 2); locs, adj = args
        if type(locs) is not list or not 1 <= len(locs) <= 20: raise ValueError('location count')
        for x in locs: text(x, NAME, 20)
        if len(set(locs)) != len(locs): raise ValueError('duplicate location')
        if type(adj) is not list or len(adj) > 200: raise ValueError('adjacency count')
        for e in adj:
            if type(e) is not list or len(e) != 2 or type(e[0]) is not str or e[0] not in locs or type(e[1]) is not str or e[1] not in locs or e[0] == e[1]:
                raise ValueError('adjacency pair')
    elif uid == TTT:
        ops, rows = trace(uid, args, 20001); n, m, k = rows[0]
        integer(n, 1, 100000); integer(m, 1, 100000); integer(k, 1, max(n, m) if type(n) is int and type(m) is int else 1)
        owner, run, won = {}, [{}, {}, {}, {}], False
        for row in rows[1:]:
            r, c, p = row
            integer(r, 0, n - 1); integer(c, 0, m - 1); integer(p, 1, 2)
            if won: raise ValueError('move after a win')
            if (r, c) in owner: raise ValueError('occupied cell')
            owner[(r, c)] = p
            for d, (dr, dc) in enumerate(((0, 1), (1, 0), (1, 1), (1, -1))):
                a, b = (r - dr, c - dc), (r + dr, c + dc)
                left = run[d][a] if owner.get(a) == p else 0
                right = run[d][b] if owner.get(b) == p else 0
                total = left + right + 1
                run[d][(r - left * dr, c - left * dc)] = total; run[d][(r + right * dr, c + right * dc)] = total
                if total >= k: won = True
    elif uid == TRI:
        envelope(args, 10)
        for v in args: integer(v, -10**7, 10**7)
    elif uid == FLIGHT:
        envelope(args, 3); flights, user, at = args
        if type(flights) is not list or len(flights) > 100000: raise ValueError('flight count')
        per = {}
        for f in flights:
            if type(f) is not list or len(f) != 5: raise ValueError('flight shape')
            text(f[0], r'[A-Z]{3}', 3); text(f[2], r'[A-Z]{3}', 3); text(f[4], NAME, 20)
            if not stamp(f[1], False) < stamp(f[3], False): raise ValueError('departure before arrival required')
            per.setdefault(f[4], []).append((f[1], f[3]))
        for legs in per.values():
            legs.sort()
            if any(legs[i][1] > legs[i + 1][0] for i in range(len(legs) - 1)): raise ValueError('overlapping flights')
        text(user, NAME, 20); stamp(at, False)
    else:
        raise ValueError('unknown uid')


def budget(cost, limit):
    if cost > limit: raise ValueError('reference budget')


def ref_parity(byte):
    bits = format(byte, '08b')
    return int(('1' if bits[1:].count('1') % 2 else '0') + bits[1:], 2)


def ref_hike(t, k):
    n = len(t)
    if n == 1: return 0
    days = min(k + 1, n - 1)
    budget(n * n * days, 3000000)
    inf = float('inf')
    best = [0] + [inf] * (n - 1)          # best[j]: smallest longest day reaching stop j with the current day count
    answer = inf
    for _ in range(days):
        new = [inf] * n
        for j in range(1, n):
            for i in range(j):
                if best[i] < inf: new[j] = min(new[j], max(best[i], t[j] - t[i]))
        best = new; answer = min(answer, best[n - 1])
    return answer


def ref_spath(n, edges, source, target):
    budget((n + 1) * (len(edges) + 1), 3000000)
    dist = [None] * n; dist[source] = 0; changed = True
    while changed:
        changed = False
        for u, v in edges:
            for a, b in ((u, v), (v, u)):
                if dist[a] is not None and (dist[b] is None or dist[a] + 1 < dist[b]): dist[b] = dist[a] + 1; changed = True
    return -1 if dist[target] is None else dist[target]


def ref_snake(ops, rows):
    budget(len(ops) * (len(ops) // 5 + 2), 3000000)
    height, width = rows[0]
    body, out, alive, moves = [(0, 0)], [None], True, 0   # body[0] is the tail, body[-1] the head
    for (d,) in rows[1:]:
        if not alive: out.append(False); continue
        moves += 1
        r, c = body[-1]
        r, c = {'U': (r - 1, c), 'D': (r + 1, c), 'L': (r, c - 1), 'R': (r, c + 1)}[d]
        rest = body if moves % 5 == 0 else body[1:]
        if not (0 <= r < height and 0 <= c < width) or (r, c) in rest: alive = False; out.append(False); continue
        body = rest + [(r, c)]; out.append(True)
    return out


def ref_spam(calls, reports, window):
    budget(len(calls) * len(reports) + 1, 3000000)
    totals = {}
    for caller, receiver, ts in calls:
        t = stamp(ts, True)
        for who, rts in reports:
            if who == receiver and abs(stamp(rts, True) - t) <= window: totals[caller] = totals.get(caller, 0) + 1
    return [[c, n] for c, n in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))]


def ref_bee(req, opt, words):
    allowed = set(opt) | {req}
    return [w for w in words if len(w) >= 4 and req in w and set(w) <= allowed]


def ref_repl(src, tgt, rep):
    return src.replace(tgt, rep)


def ref_read(pages, days):
    if days < len(pages): return -1
    budget(len(pages) * max(pages), 3000000)
    x = 1
    while sum(-(-p // x) for p in pages) > days: x += 1
    return x


def ref_subsets(uid, nums, k):
    n = len(nums)
    budget(2 ** n * n, 2000000)
    hits = [c for size in range(1, n + 1) for c in combinations(range(n), size) if sum(nums[i] for i in c) == k]
    if uid == SUB1: return bool(hits)
    if uid == SUB2: return len(hits) % MOD
    return [list(t) for t in sorted({tuple(sorted(nums[i] for i in c)) for c in hits})]


def ref_wrap(s, elements):
    budget(len(s) * len(elements), 3000000)
    out = []
    for word in s.split(' '):
        done = False
        for i in range(len(word)):
            found = [e for e in elements if word.startswith(e, i)]
            if found:
                e = max(found, key=len)
                out.append(word[:i] + '[' + e + ']' + word[i + len(e):]); done = True; break
        if not done: out.append(word)
    return ' '.join(out)


def ref_tpl(uid, txt, keys, values):
    d = dict(zip(keys, values))
    s = PLACEHOLDER.sub(lambda m: d[m.group(1)], txt)
    if uid == TPL2:
        rounds = 0
        while '{' in s:
            rounds += 1; budget(rounds * len(s), 3000000)
            s = PLACEHOLDER.sub(lambda m: d[m.group(1)], s)
    return s


def ref_tet(uid, bg, blk, off):
    top = fall(bg, blk, off)
    g = [row[:] for row in bg]
    for r in range(len(blk)):
        for c in range(len(blk[0])):
            if blk[r][c]: g[top + r][off + c] = 1
    if uid == TET2:
        while True:
            full = [i for i, row in enumerate(g) if all(row)]
            if not full: break
            del g[full[-1]]; g.insert(0, [0] * len(bg[0]))
    return g


def ref_color(locs, adj):
    n = len(locs)
    budget(3 ** n, 200000)
    idx = {x: i for i, x in enumerate(locs)}
    pairs = [(idx[a], idx[b]) for a, b in adj]
    return any(all(col[a] != col[b] for a, b in pairs) for col in product(range(3), repeat=n))


def ref_ttt(ops, rows):
    n, m, k = rows[0]
    budget(len(ops) * n * m * 4, 3000000)
    board = [[0] * m for _ in range(n)]; out = [None]
    for r, c, p in rows[1:]:
        board[r][c] = p; win = False
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            for sr in range(n):
                for sc in range(m):
                    length = 0
                    while 0 <= sr + length * dr < n and 0 <= sc + length * dc < m and board[sr + length * dr][sc + length * dc] == p: length += 1
                    if length >= k: win = True
        out.append(p if win else 0)
    return out


def ref_tri(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq):
    def area2(ax, ay, bx, by, cx, cy): return abs(ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    whole = area2(x1, y1, x2, y2, x3, y3)
    if whole == 0: return 0

    def inside(px, py):
        return area2(px, py, x2, y2, x3, y3) + area2(x1, y1, px, py, x3, y3) + area2(x1, y1, x2, y2, px, py) == whole
    p, q = inside(xp, yp), inside(xq, yq)
    return 3 if p and q else 1 if p else 2 if q else 4


def ref_flight(flights, user, at):
    legs = sorted((f for f in flights if f[4] == user), key=lambda f: f[1])
    if not legs: return ''
    here = legs[0][0]
    for dep_air, dep, arr_air, arr, _ in legs:
        if at < dep: break
        if at == dep: return dep_air
        if at < arr: return ''
        here = arr_air
    return here


def reference(uid, args):
    validate_domain(uid, args)
    if uid == PARITY: return ref_parity(*args)
    if uid == HIKE: return ref_hike(*args)
    if uid == SPATH: return ref_spath(*args)
    if uid == SNAKE: return ref_snake(*args)
    if uid == SPAM: return ref_spam(*args)
    if uid == BEE: return ref_bee(*args)
    if uid == REPL: return ref_repl(*args)
    if uid == READ: return ref_read(*args)
    if uid in SUBS: return ref_subsets(uid, *args)
    if uid == WRAP: return ref_wrap(*args)
    if uid in TPLS: return ref_tpl(uid, *args)
    if uid in TETS: return ref_tet(uid, *args)
    if uid == COLOR: return ref_color(*args)
    if uid == TTT: return ref_ttt(*args)
    if uid == TRI: return ref_tri(*args)
    return ref_flight(*args)
