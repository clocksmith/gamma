"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (recursive rendering
with record rescans, explicit candidate sets, literal server logs, union-find parity, exhaustive
path enumeration, bubble passes, quadratic scans).
"""
import re

H = 'hack2hire:'
FLAT = H + '685b15536d39467927d2f285'
TASK1 = H + '6ad141cb7cb0eaedae659263'
TASK2 = H + '6ad142657cb0eaedae65926e'
TASK3 = H + '6ad143c77cb0eaedae659281'
TASK4 = H + '6ad1440c7cb0eaedae659287'
GAME = H + '68f6f36986f7cb4953d40fbc'
GRID = H + '68edba975abdefad4f6693e3'
MENTION = H + '6a1cc5df8b879849ebc0fc16'
GUESS = H + '68cdc7ec3735a578b6f27eec'
GUESS2 = H + '69c84ccb21f6ab4226966c5a'
DELAY1 = H + '6ab4186ae74ebb7457a3f74a'
DELAY2 = H + '6ab470ffb8a9a175a39ba128'
HIGHLIGHT = H + '68bacaefb5314dcd938cb9fb'
INT1 = H + '6788830e402dc47b67a1494a'
INT2 = H + '678884a8402dc47b67a1494c'
INT3 = H + '67888746402dc47b67a1494d'
JOB = H + '679f09b9e818521cacd22471'
KEYS = H + '677c44295cbaff553b53b06a'
KNIGHT = H + '6907a349e1919109b6df1193'
PARITY = H + '6a73ba2dd713d873ca7a77a1'
LATENCY = H + '696c25586b040fa4d120bc21'
CIRC = H + '688baac33867670cfb894157'

IDS = (FLAT, TASK1, TASK2, TASK3, TASK4, GAME, GRID, MENTION, GUESS, GUESS2, DELAY1, DELAY2, HIGHLIGHT,
       INT1, INT2, INT3, JOB, KEYS, KNIGHT, PARITY, LATENCY, CIRC)
CLASSES = {}  # no native-class variants in this cohort
TASKS = (TASK1, TASK2, TASK3, TASK4)


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


TAG = r'[a-z][a-z0-9]{0,9}'
PRINTABLE = r'[ -~]*'
TID = r'[A-Za-z0-9_]{1,10}'
TNAME = r'[A-Za-z0-9 _-]{1,20}'
TS = r'[0-9]{1,10}'
STRICT_TASK = re.compile(rf'{TS},task,{TID},{TNAME}|{TS},subtask,{TID},{TID},{TNAME}')
LOOSE_TASK = r'[A-Za-z0-9 _,-]{0,80}'
MEMBER = r'id([1-9][0-9]{0,2})'
PHRASE = r'[A-Za-z0-9]+( [A-Za-z0-9]+)*'


def html_shape(root):
    """Iterative shape check (no recursion over input); returns (nodes, levels)."""
    stack, nodes, levels = [(root, 1)], 0, 0
    while stack:
        node, level = stack.pop()
        if type(node) is not dict or set(node) != {'tag', 'children'} or type(node['children']) is not list: raise ValueError('node shape')
        text(node['tag'], TAG, 10)
        nodes += 1; levels = max(levels, level)
        if nodes > 20000 or levels > 90: raise ValueError('tree bound')
        stack.extend((c, level + 1) for c in node['children'])
    return nodes, levels


def task_table(uid, records):
    """Return (definitions in record order as (id, parent or None, name), completed ids) under the level's validity rules."""
    kinds = {'task': 4, 'subtask': 5}
    if uid == TASK4: kinds['complete'] = 3
    defs, seen, done = [], set(), set()
    for r in records:
        f = r.split(',')
        if len(f) < 2 or f[1] not in kinds or len(f) != kinds[f[1]]: continue
        if f[1] == 'complete':
            if f[2] != '': done.add(f[2])
            continue
        if f[1] == 'task': tid, parent, name = f[2], None, f[3]
        else: parent, tid, name = f[2], f[3], f[4]
        if tid == '' or name == '' or parent == '': continue
        if tid in seen: continue
        seen.add(tid); defs.append((tid, parent, name))
    return defs, done


def task_shown(defs):
    """Fixed point: a task is shown when it is a root or its parent is shown (repeated passes)."""
    shown, changed = set(), True
    while changed:
        changed = False
        for tid, parent, _ in defs:
            if tid not in shown and (parent is None or parent in shown):
                shown.add(tid); changed = True
    return shown


def task_depths(defs, shown):
    parent = {t: p for t, p, _ in defs}; out = {}
    for t in shown:
        d, x = 0, t
        while parent[x] is not None: x = parent[x]; d += 1
        out[t] = d
    return out


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == FLAT:
        envelope(args, 1); html_shape(args[0])
    elif uid in TASKS:
        envelope(args, 1); recs = args[0]
        if uid == TASK1:
            strlist(recs, STRICT_TASK.pattern, 0, 20000, 80)
            ids = [r.split(',')[2 if r.split(',')[1] == 'task' else 3] for r in recs]
            if len(set(ids)) != len(ids): raise ValueError('duplicate id')
            known = set(ids)
            for r in recs:
                if r.split(',')[1] == 'subtask' and r.split(',')[2] not in known: raise ValueError('missing parent')
        else:
            strlist(recs, LOOSE_TASK, 0, 20000, 80)
        defs, _ = task_table(uid, recs)
        shown = task_shown(defs)
        if uid == TASK1 and len(shown) != len(defs): raise ValueError('cycle')
        if shown and max(task_depths(defs, shown).values()) > 100: raise ValueError('depth bound')
    elif uid == GAME:
        envelope(args, 3); array(args[0], 0, 10000, 1); array(args[1], -10000, 10000, 1)
        if len(args[0]) != len(args[1]): raise ValueError('length mismatch')
        integer(args[2], 0, 10**9)
    elif uid == GRID:
        envelope(args, 1); g = args[0]
        if type(g) is not list or not g or type(g[0]) is not list or not g[0]: raise ValueError('grid shape')
        n = len(g[0])
        if len(g) * n > 100000: raise ValueError('grid size')
        for row in g:
            if type(row) is not list or len(row) != n: raise ValueError('ragged grid')
            for v in row:
                if type(v) is not int or v not in (1, 0, 9, -1): raise ValueError('cell value')
    elif uid == MENTION:
        envelope(args, 2); strlist(args[0], MEMBER, 0, 1000, 6)
        if len(set(args[0])) != len(args[0]): raise ValueError('duplicate member')
        strlist(args[1], PRINTABLE, 0, 10000, 300)
        for m in args[1]:
            for tok in m.split(' '):
                if tok.startswith('@') and re.fullmatch(rf'@(all|{MEMBER}(,{MEMBER})*)', tok) is None: raise ValueError('malformed mention')
    elif uid == GUESS:
        envelope(args, 1); text(args[0], r'[0-9]{4}', 4)
    elif uid == GUESS2:
        envelope(args, 1); integer(args[0], 0, 999)
    elif uid == DELAY1:
        envelope(args, 2); integer(args[0], 1, 10**9); integer(args[1], 1, args[0])
    elif uid == DELAY2:
        envelope(args, 3); integer(args[0], 1, 10**9); integer(args[1], 1, 20); integer(args[2], 1, args[0])
    elif uid == HIGHLIGHT:
        envelope(args, 2); text(args[0], PRINTABLE, 20000)
        m = args[1]
        if type(m) is not list or len(m) > 500: raise ValueError('mapping size')
        for pair in m:
            if type(pair) is not list or len(pair) != 2: raise ValueError('mapping pair')
            text(pair[0], PHRASE, 40); text(pair[1], r'[A-Za-z0-9_]{1,20}', 20)
    elif uid in (INT1, INT2, INT3):
        envelope(args, 1); integer(args[0], 0, {INT1: 9, INT2: 999, INT3: 2**31 - 1}[uid])
    elif uid == JOB:
        envelope(args, 1); jobs = args[0]
        if type(jobs) is not list or len(jobs) > 100000: raise ValueError('jobs size')
        seen, last = set(), -1
        for j in jobs:
            if type(j) is not list or len(j) != 3: raise ValueError('job shape')
            text(j[0], r'[A-Za-z0-9]{1,10}', 10); text(j[1], r'([01][0-9]|2[0-3])[0-5][0-9]', 4); text(j[2], r'[1-9][0-9]{0,4}', 5)
            if int(j[2]) > 10000 or j[0] in seen: raise ValueError('job domain')
            seen.add(j[0]); start = int(j[1][:2]) * 60 + int(j[1][2:])
            if start < last: raise ValueError('unsorted jobs')
            last = start
    elif uid == KEYS:
        envelope(args, 3); kb = args[0]
        if type(kb) is not list or not 1 <= len(kb) <= 30 or type(kb[0]) is not list or not 1 <= len(kb[0]) <= 30: raise ValueError('keyboard shape')
        for row in kb:
            if type(row) is not list or len(row) != len(kb[0]): raise ValueError('ragged keyboard')
            for ch in row: text(ch, r'[a-z]', 1)
        integer(args[1], 0, 60); text(args[2], r'[a-z]{1,1000}', 1000)
    elif uid == KNIGHT:
        envelope(args, 2); integer(args[0], 0, 9); integer(args[1], 0, 9)
    elif uid == PARITY:
        envelope(args, 1); text(args[0], r'[0-9]{1,100000}', 100000)
    elif uid == LATENCY:
        envelope(args, 3); array(args[0], 1, 10**9)
        if any(a > b for a, b in zip(args[0], args[0][1:])): raise ValueError('unsorted latencies')
        integer(args[1], 1, 10**9); integer(args[2], 1, 100000)
    elif uid == CIRC:
        envelope(args, 2); array(args[0], 0, 1, 1); integer(args[1], 0, len(args[0]))


# ---------------------------------------------------------------- references

def ref_flat(root):
    def render(node): return '<' + node['tag'] + '>' + ''.join(render(c) for c in node['children']) + '</' + node['tag'] + '>'
    return re.findall(r'<[^<]*', render(root))


def ref_task(uid, records):
    if len(records) > 3000: raise ValueError('reference budget')
    defs, done = task_table(uid, records)
    shown = task_shown(defs)
    lines = []

    def kids(p): return [d for d in defs if d[1] == p and d[0] in shown]   # rescan every definition

    def complete(t):
        if t in done: return True
        ks = kids(t)
        return bool(ks) and all(complete(k[0]) for k in ks)

    def show(d, depth, number):
        label = d[2]
        if uid in (TASK3, TASK4): label = number + ' ' + ('[x] ' if complete(d[0]) else '[ ] ') * (uid == TASK4) + d[2]
        lines.append('  ' * depth + label)
        for j, k in enumerate(kids(d[0]), 1): show(k, depth + 1, number + '.' + str(j))
    for i, d in enumerate([d for d in defs if d[1] is None], 1): show(d, 0, str(i))
    return lines


def ref_game(costs, points, energy):
    if len(costs) > 3000: raise ValueError('reference budget')
    totals = []
    for s in range(len(costs)):
        e, total, i = energy, 0, s
        while i < len(costs) and e >= costs[i]:
            e -= costs[i]; total += points[i]; i += 1
        totals.append(total)
    return max(totals)


def ref_grid(g):
    m, n = len(g), len(g[0]); parent = list(range(m * n))

    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for r in range(m):
        for c in range(n):
            if g[r][c] == -1: continue
            for r2, c2 in ((r + 1, c), (r, c + 1)):
                if r2 < m and c2 < n and g[r2][c2] != -1: parent[find(r * n + c)] = find(r2 * n + c2)
    # colour = parity(r + c) xor flip[region]; flip fixed by a pre-coloured cell, else by the region's first cell being black
    flip = {}
    for r in range(m):
        for c in range(n):
            if g[r][c] in (0, 1):
                root, want = find(r * n + c), g[r][c] ^ ((r + c) & 1)
                if flip.setdefault(root, want) != want: return []
    out = []
    for r in range(m):
        row = []
        for c in range(n):
            if g[r][c] == -1: row.append(-1); continue
            root = find(r * n + c)
            if root not in flip: flip[root] = 1 ^ ((r + c) & 1)
            row.append(flip[root] ^ ((r + c) & 1))
        out.append(row)
    return out


def ref_mention(members, messages):
    counts = {m: 0 for m in members}
    for msg in messages:
        hit = set()
        for body in re.findall(r'(?:^|(?<= ))@([^ ]+)', msg):
            hit.update(members if body == 'all' else body.split(','))
        for m in hit:
            if m in counts: counts[m] += 1
    return [counts[m] for m in members]


class _Server:
    def __init__(self, secret): self.secret, self.log = secret, []

    def guessNumber(self, g):
        self.log.append(g); return sum(1 for a, b in zip(g, self.secret) if a == b)


def ref_guess(secret):
    srv = _Server(secret); count = {}
    for d in '0123456789':
        if sum(count.values()) == 4: break
        if d == '9': count['9'] = 4 - sum(count.values()); break
        r = srv.guessNumber(d * 4); count[d] = r
        if r == 4: return srv.log
    filler = min(d for d in '0123456789' if count.get(d, 0) == 0)
    placed = ''
    for p in range(4):
        left = sorted(d for d in count if count[d] > 0)
        digit = left[-1]
        if len(left) > 1:
            for d in left[:-1]:
                if srv.guessNumber(filler * p + d + filler * (3 - p)) == 1: digit = d; break
        placed += digit; count[digit] -= 1
    if srv.log[-1] != placed: srv.guessNumber(placed)
    return srv.log


def ref_guess2(target):
    def answer(g, prev):
        if g == target: return 'Correct'
        if prev is None: return 'First'
        a, b = abs(g - target), abs(prev - target)
        return 'Hotter' if a < b else 'Colder' if a > b else 'Same'
    cand, log = list(range(1000)), []
    while True:
        q = cand[0] if len(cand) == 1 else (min(cand) if len(log) % 2 == 0 else max(cand))
        prev = log[-1] if log else None
        r = answer(q, prev); log.append(q)
        if r == 'Correct': return log
        cand = [t for t in cand if t != q and (r == 'First' or (abs(q - t) < abs(prev - t)) == (r == 'Hotter') and
                                                (abs(q - t) > abs(prev - t)) == (r == 'Colder'))]


def ref_delay(upper, delay, secret):
    log = []

    def check(g):
        log.append(g)
        if len(log) <= delay: return 'PENDING'
        old = log[len(log) - 1 - delay]
        return 'CORRECT' if old == secret else 'TOO_LOW' if old < secret else 'TOO_HIGH'
    lo, hi = 1, upper
    while True:
        mid = (lo + hi) // 2
        for _ in range(delay + 1): r = check(mid)
        if r == 'CORRECT': return [mid, len(log)]
        if r == 'TOO_LOW': lo = mid + 1
        else: hi = mid - 1


def ref_highlight(review, mapping):
    if len(review) * max(1, len(mapping)) > 4000000: raise ValueError('reference budget')
    first = {}
    for phrase, cat in mapping: first.setdefault(phrase.lower(), cat)
    phrases = sorted(first, key=len, reverse=True)
    alnum = lambda ch: ch.isascii() and ch.isalnum()
    out, i, low = [], 0, review.lower()
    while i < len(review):
        if alnum(review[i]) and (i == 0 or not alnum(review[i - 1])):
            for p in phrases:
                j = i + len(p)
                if low[i:j] == p and (j == len(review) or not alnum(review[j])):
                    out.append('[' + first[p] + ']{' + review[i:j] + '}'); i = j; break
            else:
                out.append(review[i]); i += 1
        else:
            out.append(review[i]); i += 1
    return ''.join(out)


_NAMES = [(10**9, 'Billion'), (10**6, 'Million'), (1000, 'Thousand'), (100, 'Hundred'), (90, 'Ninety'), (80, 'Eighty'), (70, 'Seventy'),
          (60, 'Sixty'), (50, 'Fifty'), (40, 'Forty'), (30, 'Thirty'), (20, 'Twenty'), (19, 'Nineteen'), (18, 'Eighteen'), (17, 'Seventeen'),
          (16, 'Sixteen'), (15, 'Fifteen'), (14, 'Fourteen'), (13, 'Thirteen'), (12, 'Twelve'), (11, 'Eleven'), (10, 'Ten'), (9, 'Nine'),
          (8, 'Eight'), (7, 'Seven'), (6, 'Six'), (5, 'Five'), (4, 'Four'), (3, 'Three'), (2, 'Two'), (1, 'One')]


def ref_words(num):
    if num == 0: return 'Zero'

    def words(x):
        for value, name in _NAMES:
            if value <= x:
                if value >= 100: return words(x // value) + [name] + (words(x % value) if x % value else [])
                return [name] + (words(x - value) if x - value else [])
        return []
    return ' '.join(words(num))


def ref_job(jobs):
    if len(jobs) > 3000: raise ValueError('reference budget')
    ends, out = [], []
    for jid, hhmm, dur in jobs:
        start = int(hhmm[:2]) * 60 + int(hhmm[2:])
        for k in range(len(ends) + 1):
            if k == len(ends): ends.append(0)
            if ends[k] <= start: ends[k] = start + int(dur); out.append([jid, 'M' + str(k + 1)]); break
    return out


def ref_keys(kb, dist, word):
    cells = {}
    for r, row in enumerate(kb):
        for c, ch in enumerate(row): cells.setdefault(ch, []).append((r, c))
    if len(word) * len(kb) * len(kb[0]) > 300000 and max(len(v) for v in cells.values()) > 60: raise ValueError('reference budget')
    cur = set(cells.get(word[0], []))
    for ch in word[1:]:
        cur = {(r, c) for r, c in cells.get(ch, []) if any(abs(r - a) + abs(c - b) <= dist for a, b in cur)}
        if not cur: return False
    return bool(cur)


_POS = {'1': (0, 0), '2': (0, 1), '3': (0, 2), '4': (1, 0), '5': (1, 1), '6': (1, 2), '7': (2, 0), '8': (2, 1), '9': (2, 2), '0': (3, 1)}


def _knight_ok(a, b):
    (r1, c1), (r2, c2) = _POS[a], _POS[b]
    return {abs(r1 - r2), abs(c1 - c2)} == {1, 2}


def ref_knight(start, end):
    s, e, paths = str(start), str(end), []

    def dfs(path):
        if path[-1] == e: paths.append(path); return
        for d in _POS:
            if d not in path and _knight_ok(path[-1], d): dfs(path + d)
    dfs(s)
    if not paths: return []
    best = min(map(len, paths))
    return sorted(p for p in paths if len(p) == best)


def ref_parity(num):
    if len(num) > 300: raise ValueError('reference budget')
    s, changed = list(num), True
    while changed:
        changed = False
        for i in range(len(s) - 1):
            if (int(s[i]) - int(s[i + 1])) % 2 == 0 and s[i] < s[i + 1]: s[i], s[i + 1] = s[i + 1], s[i]; changed = True
    return ''.join(s)


def ref_latency(lat, width, buckets):
    if len(lat) * buckets > 3000000: raise ValueError('reference budget')
    out = [0] * buckets
    for x in lat:
        for i in range(buckets):
            if i == buckets - 1 or i * width <= x <= (i + 1) * width - 1: out[i] += 1; break
    return out


def ref_circ(nums, k):
    n = len(nums)
    if n > 400: raise ValueError('reference budget')
    best = 0
    for s in range(n):
        for length in range(1, n + 1):
            if sum(1 for i in range(length) if nums[(s + i) % n] == 0) <= k: best = max(best, length)
    return best


def reference(uid, args):
    validate_domain(uid, args)
    if uid == FLAT: return ref_flat(*args)
    if uid in TASKS: return ref_task(uid, *args)
    if uid == GAME: return ref_game(*args)
    if uid == GRID: return ref_grid(*args)
    if uid == MENTION: return ref_mention(*args)
    if uid == GUESS: return ref_guess(*args)
    if uid == GUESS2: return ref_guess2(*args)
    if uid == DELAY1: return ref_delay(args[0], 1, args[1])
    if uid == DELAY2: return ref_delay(*args)
    if uid == HIGHLIGHT: return ref_highlight(*args)
    if uid in (INT1, INT2, INT3): return ref_words(*args)
    if uid == JOB: return ref_job(*args)
    if uid == KEYS: return ref_keys(*args)
    if uid == KNIGHT: return ref_knight(*args)
    if uid == PARITY: return ref_parity(*args)
    if uid == LATENCY: return ref_latency(*args)
    return ref_circ(*args)
