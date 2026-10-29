"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (exhaustive grid scans,
event simulation, breadth-first searches, exact Fraction sums over every price, subset enumeration,
per-start displacement sums, list-popping battle replays, descendant searches, per-window rescans,
the built-in sort, frozenset conversion, joined-string line trials, prefix rescans, per-query root walks
and literal digit-queue reductions) and refuse inputs above a small budget.
"""
from collections import deque
from fractions import Fraction
from itertools import combinations
import re

H = 'hack2hire:'
CONVEX = H + '68e9a2a2149617c9114ece06'
BATT = H + '69a4da066e73e4abccc9c43f'
NARY1 = H + '696eb8a4920c39311a3992be'
NARY2 = H + '6976fe265ed12b33b05f1134'
ASSET = H + '696aacf2cc483345efb1b29f'
MENU1 = H + '68b82be483188776facc8f08'
MENU2 = H + '68b830b783188776facc8f09'
MENU3 = H + '68b8f94083188776facc8fc9'
SWAPS = H + '67fc0d33216af53465a721dd'
MTB1 = H + '69a3aa7d6e73e4abccc9c109'
MTB2 = H + '69a3adea6e73e4abccc9c115'
MTB3 = H + '6a56e302665efda9311f8dcb'
MB1 = H + '6779c17edcf91f8e3c1c310f'
MB2 = H + '6779eef9dcf91f8e3c1c3110'
MFS = H + '695c711d68e2c0dd046c4955'
MTS = H + '695ecf112e3ae59d53a81ea7'
NSE = H + '680984a8cbb5948f87732b46'
NEWS = H + '699939266e73e4abccc9a3b1'
OFFSET = H + '67eb157b4c9bb801bfd0ef6f'
PAL = H + '69e92eb7fbaf3da641828669'
PASCAL = H + '67ccdb573363b83a81fc9983'

IDS = (CONVEX, BATT, NARY1, NARY2, ASSET, MENU1, MENU2, MENU3, SWAPS, MTB1, MTB2, MTB3, MB1, MB2, MFS, MTS, NSE, NEWS,
       OFFSET, PAL, PASCAL)
CLASSES = {}  # no native-class variants in this cohort
MTBS = (MTB1, MTB2, MTB3)
NAME = r'[A-Za-z0-9_]{1,12}'
ITEM = r'[a-z]{1,10}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def rows_of(a, width, maximum, minimum=0):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('row list size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


# ---------------------------------------------------------------- domain validators
def tree_nodes(root):
    """Validate a {"val", "children"} tree (depth <= 90 levels, <= 100000 nodes); return (vals, parent map, depth map)."""
    seen, parent, depth = [], {}, {}
    stack = [(root, None, 0)]
    while stack:
        node, par, d = stack.pop()
        if type(node) is not dict or set(node) != {'val', 'children'} or type(node['children']) is not list: raise ValueError('tree node')
        integer(node['val'], -10**9, 10**9)
        if d > 89: raise ValueError('tree depth')
        if node['val'] in parent: raise ValueError('duplicate val')
        parent[node['val']] = par; depth[node['val']] = d; seen.append(node['val'])
        if len(seen) > 100000: raise ValueError('tree size')
        for c in node['children']: stack.append((c, node['val'], d + 1))
    return seen, parent, depth


def menu_check(menu, wants, max_entries, max_wants):
    rows_of(menu, 3, max_entries, 1)
    ids = set()
    for i, price, items in menu:
        text(i, NAME, 12); integer(price, 1, 10**6)
        if type(items) is not str: raise ValueError('items')
        parts = items.split(',')
        if not 1 <= len(parts) <= 10 or len(set(parts)) != len(parts): raise ValueError('item list')
        for x in parts: text(x, ITEM, 10)
        if i in ids: raise ValueError('duplicate id')
        ids.add(i)
    if type(wants) is not list or not 1 <= len(wants) <= max_wants or len(set(wants)) != len(wants): raise ValueError('wants')
    for x in wants: text(x, ITEM, 10)


def monsters_check(team, fields):
    if type(team) is not list or not 1 <= len(team) <= 100: raise ValueError('team size')
    for m in team:
        if type(m) is not dict or set(m) != set(fields): raise ValueError('monster fields')
        text(m['name'], NAME, 12)
        integer(m['health'], 1, 1000); integer(m['attack'], 1, 1000)
        if 'defense' in fields: integer(m['defense'], 0, 1000)
        if 'speed' in fields: integer(m['speed'], 1, 1000)


def hierarchy_check(rows, root, with_cost):
    """Rows [label, (cost,) defeats] forming one tree rooted at root; returns (children, hostile, cost) maps."""
    rows_of(rows, 3 if with_cost else 2, 100000, 1)
    children, hostile, cost, child_of = {}, {}, {}, set()
    for row in rows:
        label, kids = row[0], row[-1]
        if type(label) is not str: raise ValueError('label')
        name = label[:-1] if label.endswith('*') else label
        text(name, NAME, 12)
        if with_cost: integer(row[1], 1, 10**6)
        if type(kids) is not list: raise ValueError('defeats')
        for k in kids: text(k, NAME, 12)
        if name in children: raise ValueError('duplicate monster')
        children[name] = kids; hostile[name] = label.endswith('*'); cost[name] = row[1] if with_cost else 0
        for k in kids:
            if k in child_of: raise ValueError('two parents')
            child_of.add(k)
    text(root, NAME, 12)
    if root not in children or root in child_of: raise ValueError('root')
    if any(k not in children for k in child_of): raise ValueError('child without row')
    count, todo = 0, [root]
    while todo:
        u = todo.pop(); count += 1
        todo.extend(children[u])
    if count != len(children): raise ValueError('not one tree')
    return children, hostile, cost


def nested_check(v, max_depth=190):
    total, stack = 0, [(v, 1)]
    if type(v) is not list: raise ValueError('nested root')
    while stack:
        x, d = stack.pop(); total += 1
        if total > 100001: raise ValueError('nested size')
        if type(x) is str: text(x, r'[a-z0-9]{1,10}', 10)
        elif type(x) is list:
            if d > max_depth: raise ValueError('nested depth')
            stack.extend((y, d + 1) for y in x)
        else: raise ValueError('nested element')
    return total


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == CONVEX:
        envelope(args, 4)
        rows_of(args[0], 2, 2000, 1)
        for s, c in args[0]: integer(s, -10**6, 10**6); integer(c, -10**12, 10**12)
        integer(args[1], -10**9, 10**9); integer(args[2], args[1], 10**9); integer(args[3], 1, 2 * 10**9)
    elif uid == BATT:
        envelope(args, 3)
        array(args[0], 1, 10**9, 1); array(args[1], 0, 10**9, 1)
        if len(args[0]) != len(args[1]): raise ValueError('length mismatch')
        integer(args[2], 1, 10**15)
    elif uid in (NARY1, NARY2):
        envelope(args, 3)
        vals, _, _ = tree_nodes(args[0]); present = set(vals)
        if uid == NARY1:
            integer(args[1], -10**9, 10**9); integer(args[2], -10**9, 10**9)
            if args[1] not in present or args[2] not in present: raise ValueError('value not in tree')
        else:
            for g in args[1:]:
                array(g, -10**9, 10**9, 1)
                if any(x not in present for x in g): raise ValueError('value not in tree')
    elif uid == ASSET:
        envelope(args, 5)
        integer(args[0], 1, 100); integer(args[1], 0, 100); integer(args[2], 0, 1000); integer(args[3], args[2], 1000); integer(args[4], 0, 1000)
    elif uid in (MENU1, MENU2):
        envelope(args, 2); menu_check(args[0], args[1], 300, 12)
    elif uid == MENU3:
        envelope(args, 2); menu_check(args[0], args[1], 40, 10)
    elif uid == SWAPS:
        envelope(args, 1); text(args[0], r'[RW]{1,200000}', 200000)
    elif uid in MTBS:
        envelope(args, 2)
        fields = ['name', 'health', 'attack'] + (['defense'] if uid != MTB1 else []) + (['speed'] if uid == MTB3 else [])
        monsters_check(args[0], fields); monsters_check(args[1], fields)
        names = [m['name'] for m in args[0] + args[1]]
        if len(set(names)) != len(names): raise ValueError('names not unique')
    elif uid in (MB1, MB2):
        envelope(args, 2); hierarchy_check(args[0], args[1], uid == MB2)
    elif uid == MFS:
        envelope(args, 2); text(args[0], r'[a-z]{0,100000}', 100000); integer(args[1], 1, 100)
    elif uid == MTS:
        envelope(args, 2); array(args[0], -10**9, 10**9); integer(args[1], 1, 1000)
    elif uid == NSE:
        envelope(args, 2)
        if nested_check(args[0]) + nested_check(args[1]) > 100002: raise ValueError('nested size')
    elif uid == NEWS:
        envelope(args, 3)
        paras, aligns, width = args
        integer(width, 1, 1000)
        if type(paras) is not list or not 1 <= len(paras) <= 100: raise ValueError('paragraphs')
        if type(aligns) is not list or len(aligns) != len(paras) or any(a not in ('LEFT', 'RIGHT') for a in aligns): raise ValueError('aligns')
        total = 0
        for p in paras:
            if type(p) is not list or not 1 <= len(p) <= 1000: raise ValueError('paragraph size')
            for w in p: text(w, r'[A-Za-z0-9.,!?-]+', width)
            total += len(p)
        if total > 20000: raise ValueError('word total')
    elif uid == OFFSET:
        envelope(args, 1); array(args[0], 0, 10**9, 1, 200000)
        if len(set(args[0])) != len(args[0]): raise ValueError('offsets not distinct')
    elif uid == PAL:
        envelope(args, 4)
        arr, fr, to, qs = args
        if type(arr) is not list or not 1 <= len(arr) <= 100000: raise ValueError('arr')
        for c in arr: text(c, r'[a-z]', 1)
        n = len(arr)
        array(fr, 0, n - 1, n - 1, n - 1); array(to, 0, n - 1, n - 1, n - 1); array(qs, 0, n - 1, 1)
        parent = list(range(n))

        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for u, v in zip(fr, to):
            ru, rv = find(u), find(v)
            if ru == rv: raise ValueError('edges must form a tree')
            parent[ru] = rv
    else:
        envelope(args, 1); text(args[0], r'[0-9]{2,100000}', 100000)


# ---------------------------------------------------------------- references
def ref_convex(lines, a, b, eps):
    best = None
    x = a
    while x <= b:
        f = max(s * x + c for s, c in lines)
        if best is None or f < best[0]: best = (f, x)
        x += eps
    return best[1]


def ref_batt(usage, charge, duration):
    n = len(usage); ready = [0] * n; t = 0; uses = 0; i = 0
    while t < duration:
        if ready[i] > t: return -1
        t += usage[i]; ready[i] = t + charge[i]; uses += 1; i = (i + 1) % n
    return uses


def tree_adjacency(root):
    adj, todo = {}, [root]
    while todo:
        node = todo.pop()
        adj.setdefault(node['val'], [])
        for c in node['children']:
            adj[node['val']].append(c['val']); adj.setdefault(c['val'], []).append(node['val']); todo.append(c)
    return adj


def bfs(adj, start):
    dist = {start: 0}; q = deque([start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist: dist[v] = dist[u] + 1; q.append(v)
    return dist


def ref_nary1(root, p, q): return bfs(tree_adjacency(root), p)[q]


def ref_nary2(root, ga, gb):
    adj = tree_adjacency(root)
    return min(min(d[y] for y in gb) for d in (bfs(adj, x) for x in set(ga)))


def ref_asset(n, k, a, b, p):
    prices = range(a, b + 1); m = b - a + 1
    prev = [Fraction(0)] * (k + 1)
    for _ in range(n):
        cur = []
        for j in range(k + 1):
            total = Fraction(0)
            for x in prices:
                option = x + prev[j]
                if j > 0: option = min(option, p + prev[j - 1])
                total += option
            cur.append(total / m)
        prev = cur
    e = prev[k]
    scaled = e * 10**6 + Fraction(1, 2)
    q = scaled.numerator // scaled.denominator
    return '%d.%06d' % (q // 10**6, q % 10**6)


def ref_menu(menu, wants, mode):
    want = set(wants)
    useful = [(i, price, set(items.split(','))) for i, price, items in menu if want & set(items.split(','))]
    best = None
    for r in range(len(useful) + 1):
        for combo in combinations(useful, r):
            got = set()
            for _, _, items in combo: got |= items
            if want <= got:
                key = (sum(c[1] for c in combo), r)
                if best is None or key < best: best = key
    if mode == 1: return -1 if best is None else best[0]
    return [-1, -1] if best is None else list(best)


def ref_menu3(menu, wants):
    want = set(wants)
    usable = [(i, price, items.split(',')) for i, price, items in menu if set(items.split(',')) <= want]
    found = []
    for r in range(len(usable) + 1):
        for combo in combinations(usable, r):
            got = [x for _, _, items in combo for x in items]
            if len(got) == len(want) and set(got) == want:
                found.append((sum(c[1] for c in combo), sorted(c[0] for c in combo)))
    if not found: return []
    low = min(f[0] for f in found)
    return sorted(ids for cost, ids in found if cost == low)


def ref_swaps(balls):
    reds = [i for i, c in enumerate(balls) if c == 'R']
    r = len(reds)
    if r <= 1: return 0
    return min(sum(abs(p - (s + i)) for i, p in enumerate(reds)) for s in range(len(balls) - r + 1))


def ref_battle(uid, team_a, team_b):
    teams = {'A': [dict(m) for m in team_a], 'B': [dict(m) for m in team_b]}
    other = {'A': 'B', 'B': 'A'}
    log = []

    def hit(side):
        att, dfn = teams[side][0], teams[other[side]][0]
        dmg = att['attack'] if uid == MTB1 else max(1, att['attack'] - dfn['defense'])
        dfn['health'] -= dmg
        log.append('%s attacks %s for %d damage, %s has %d health left' % (att['name'], dfn['name'], dmg, dfn['name'], max(0, dfn['health'])))
        if dfn['health'] <= 0:
            log.append('%s is defeated' % dfn['name'])
            teams[other[side]].pop(0)
            return True
        return False

    turn = 'A'
    while teams['A'] and teams['B']:
        if uid == MTB3:
            order = sorted(['A', 'B'], key=lambda s: (-teams[s][0]['speed'], s))
            if not hit(order[0]): hit(order[1])
        else:
            hit(turn); turn = other[turn]
    log.append('Team %s wins' % ('A' if teams['A'] else 'B'))
    return log


def descendants(children, u):
    out, todo = set(), list(children[u])
    while todo:
        v = todo.pop(); out.add(v); todo.extend(children[v])
    return out


def ref_mb1(rows, root):
    children, hostile, _ = hierarchy_check(rows, root, False)
    bad = {u for u in children if hostile[u]}
    return sorted(u for u in children if not hostile[u] and bad <= descendants(children, u))


def ref_mb2(rows, root):
    children, hostile, cost = hierarchy_check(rows, root, True)
    bad = {u for u in children if hostile[u]}
    friends = [u for u in children if not hostile[u]]
    below = {u: descendants(children, u) for u in friends}
    best = None
    for r in range(len(friends) + 1):
        for combo in combinations(friends, r):
            covered = set()
            for u in combo: covered |= below[u]
            if bad <= covered:
                c = sum(cost[u] for u in combo)
                if best is None or c < best: best = c
    return -1 if best is None else best


def ref_mfs(s, n):
    best = None
    for i in range(len(s) - n + 1):
        w = s[i:i + n]
        count = sum(1 for j in range(len(s) - n + 1) if s[j:j + n] == w)
        if best is None or (-count, w) < best: best = (-count, w)
    return '' if best is None else best[1]


def frozen(v):
    return v if type(v) is str else ('L', frozenset(frozen(x) for x in v))


def ref_news(paras, aligns, width):
    out = ['*' * (width + 2)]
    for words, align in zip(paras, aligns):
        lines, cur = [], []
        for w in words:
            if cur and len(' '.join(cur + [w])) > width: lines.append(' '.join(cur)); cur = []
            cur.append(w)
        lines.append(' '.join(cur))
        for line in lines:
            pad = ' ' * (width - len(line))
            out.append('*' + (line + pad if align == 'LEFT' else pad + line) + '*')
    out.append('*' * (width + 2))
    return out


def ref_offset(offsets):
    done, out, prev = set(), [], -1
    for x in offsets:
        done.add(x)
        c = -1
        while c + 1 in done: c += 1
        out.append(c if c > prev else -1)
        prev = max(prev, c)
    return out


def ref_pal(arr, fr, to, qs):
    n = len(arr); adj = [[] for _ in range(n)]
    for u, v in zip(fr, to): adj[u].append(v); adj[v].append(u)
    parent = [-1] * n; seen = [False] * n; seen[0] = True; q = deque([0])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if not seen[v]: seen[v] = True; parent[v] = u; q.append(v)
    out = []
    for x in qs:
        counts = [0] * 26; total = 0; v = x
        while v != -1:
            counts[ord(arr[v]) - 97] += 1
            if sum(c % 2 for c in counts) <= 1: total += 1
            v = parent[v]
        out.append(total)
    return out


def ref_pascal(digits):
    q = deque(int(c) for c in digits)
    while len(q) > 2:
        nxt = deque(); prev = q.popleft()
        while q:
            cur = q.popleft(); nxt.append((prev + cur) % 10); prev = cur
        q = nxt
    return ''.join(map(str, q))


def reference(uid, args):
    validate_domain(uid, args)
    if uid == CONVEX:
        if (args[2] - args[1]) // args[3] * len(args[0]) > 200000: raise ValueError('reference budget')
        return ref_convex(*args)
    if uid == BATT:
        if args[2] > 200000: raise ValueError('reference budget')
        return ref_batt(*args)
    if uid in (NARY1, NARY2):
        if uid == NARY2 and len(set(args[1])) * len(tree_adjacency(args[0])) > 2000000: raise ValueError('reference budget')
        return ref_nary1(*args) if uid == NARY1 else ref_nary2(*args)
    if uid == ASSET:
        if args[0] * (args[1] + 1) * (args[3] - args[2] + 1) > 30000: raise ValueError('reference budget')
        return ref_asset(*args)
    if uid in (MENU1, MENU2):
        if sum(1 for _, _, items in args[0] if set(items.split(',')) & set(args[1])) > 15: raise ValueError('reference budget')
        return ref_menu(args[0], args[1], 1 if uid == MENU1 else 2)
    if uid == MENU3:
        if sum(1 for _, _, items in args[0] if set(items.split(',')) <= set(args[1])) > 16: raise ValueError('reference budget')
        return ref_menu3(*args)
    if uid == SWAPS:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_swaps(args[0])
    if uid in MTBS: return ref_battle(uid, *args)
    if uid in (MB1, MB2):
        if uid == MB1 and len(args[0]) > 2000: raise ValueError('reference budget')
        if uid == MB2 and sum(1 for r in args[0] if not r[0].endswith('*')) > 14: raise ValueError('reference budget')
        return ref_mb1(*args) if uid == MB1 else ref_mb2(*args)
    if uid == MFS:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_mfs(*args)
    if uid == MTS: return sorted(args[0])
    if uid == NSE: return frozen(args[0]) == frozen(args[1])
    if uid == NEWS:
        if sum(len(p) for p in args[0]) > 2000: raise ValueError('reference budget')
        return ref_news(*args)
    if uid == OFFSET:
        if len(args[0]) > 1000: raise ValueError('reference budget')
        return ref_offset(args[0])
    if uid == PAL:
        if len(args[0]) * len(args[3]) > 400000: raise ValueError('reference budget')
        return ref_pal(*args)
    if len(args[0]) > 800: raise ValueError('reference budget')
    return ref_pascal(args[0])
