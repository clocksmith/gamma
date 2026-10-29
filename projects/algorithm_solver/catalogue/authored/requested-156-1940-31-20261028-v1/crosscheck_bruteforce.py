"""Independent brute-force cross-check of requested-156-1940-31 references on random small inputs.

Each brute force restates the problem directly (enumeration, exhaustive search or a different formulation) and
shares no code with oracles.py. Where the public problem allows several answers, the reference answer is checked
for validity instead of equality. Real-valued answers are compared within 1e-6 (1230) or 1e-5 (1924).
Run: python3 crosscheck_bruteforce.py   (prints per-problem counts; exit 1 on any mismatch)
"""
import ast
import importlib.util
import itertools
import json
import math
import random
import sys
from collections import Counter, deque
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('xcheck_oracles_b', HERE / 'oracles.py')
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)
R = random.Random(20261029)
MOD = 10**9 + 7


def tree(vals):
    if not vals or vals[0] is None:
        return None
    nodes = [None if v is None else {'v': v, 'l': None, 'r': None} for v in vals]
    q, i = deque([nodes[0]]), 1
    while q and i < len(nodes):
        n = q.popleft()
        for side in ('l', 'r'):
            if i < len(nodes):
                n[side] = nodes[i]
                if nodes[i]:
                    q.append(nodes[i])
                i += 1
    return nodes[0]


def level(t):
    out, q = [], deque([t])
    while q:
        n = q.popleft()
        out.append(None if n is None else n['v'])
        if n is not None:
            q.extend((n['l'], n['r']))
    while out and out[-1] is None:
        out.pop()
    return out


def all_nodes(t):
    return [] if t is None else [t] + all_nodes(t['l']) + all_nodes(t['r'])


def rand_unique_tree(n):
    vals = R.sample(range(1, 40), n)
    root = {'v': vals[0], 'l': None, 'r': None}
    nodes = [root]
    for v in vals[1:]:
        while True:
            parent, side = R.choice(nodes), R.choice('lr')
            if parent[side] is None:
                parent[side] = {'v': v, 'l': None, 'r': None}
                nodes.append(parent[side])
                break
    return level(root)


def graph(t):
    adj = {}
    for n in all_nodes(t):
        adj.setdefault(n['v'], [])
        for ch in (n['l'], n['r']):
            if ch:
                adj[n['v']].append(ch['v'])
                adj.setdefault(ch['v'], []).append(n['v'])
    return adj


def dists(adj, s):
    d, q = {s: 0}, deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


B = {}


def g156():
    depth = R.randint(0, 5)
    if depth == 0:
        return ([],)
    vals = iter(R.sample(range(1, 11), 10))
    root = cur = {'v': next(vals), 'l': None, 'r': None}
    for _ in range(depth - 1):
        cur['l'] = {'v': next(vals), 'l': None, 'r': None}
        if R.random() < 0.6:
            cur['r'] = {'v': next(vals), 'l': None, 'r': None}
        cur = cur['l']
    return (level(root),)


def b156(vals):
    def flip(n):
        if n is None or n['l'] is None:
            return n
        new_root = flip(n['l'])
        n['l']['l'], n['l']['r'] = n['r'], n
        n['l'] = n['r'] = None
        return new_root
    return level(flip(tree(vals))) if vals else []
B[156] = (g156, b156, None)
B[159] = (lambda: (''.join(R.choice('abcA') for _ in range(R.randint(1, 10))),),
          lambda s: max(j - i for i in range(len(s)) for j in range(i + 1, len(s) + 1) if len(set(s[i:j])) <= 2), None)


def edit(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
    return d[-1]
B[161] = (lambda: (''.join(R.choice('ab') for _ in range(R.randint(0, 4))), ''.join(R.choice('ab') for _ in range(R.randint(0, 4)))),
          lambda s, t: edit(s, t) == 1, None)


def b163(nums, lo, hi):
    miss = [v for v in range(lo, hi + 1) if v not in set(nums)]
    out = []
    for v in miss:
        if out and out[-1][1] == v - 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return out
B[163] = (lambda: (lambda lo, hi: (sorted(R.sample(range(lo, hi + 1), R.randint(0, min(5, hi - lo + 1)))), lo, hi))(*sorted([R.randint(-5, 8), R.randint(-5, 8)])), b163, None)


def check280(nums, got):
    return sorted(got) == sorted(nums) and all((got[i] <= got[i + 1]) if i % 2 == 0 else (got[i] >= got[i + 1]) for i in range(len(got) - 1))
B[280] = (lambda: ([R.randint(0, 4) for _ in range(R.randint(1, 8))],), None, check280)
INF = 2147483647


def b286(g):
    m, n = len(g), len(g[0])
    out = [row[:] for row in g]
    for r in range(m):
        for c in range(n):
            if g[r][c] == INF:
                d, q, best = {(r, c): 0}, deque([(r, c)]), INF
                while q:
                    a, b = q.popleft()
                    if g[a][b] == 0:
                        best = d[(a, b)]
                        break
                    for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= x < m and 0 <= y < n and (x, y) not in d and g[x][y] != -1:
                            d[(x, y)] = d[(a, b)] + 1
                            q.append((x, y))
                out[r][c] = best
    return out
B[286] = (lambda: (lambda m, n: ([[R.choice([INF, INF, -1, 0]) for _ in range(n)] for _ in range(m)],))(R.randint(1, 4), R.randint(1, 4)), b286, None)


@lru_cache(maxsize=None)
def win294(s):
    return any(not win294(s[:i] + '--' + s[i + 2:]) for i in range(len(s) - 1) if s[i:i + 2] == '++')
B[294] = (lambda: (''.join(R.choice('++-') for _ in range(R.randint(1, 12))),), win294, None)


def b737(s1, s2, pairs):
    if len(s1) != len(s2):
        return False
    adj = {}
    for a, b in pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    def reach(a, b):
        seen, q = {a}, deque([a])
        while q:
            u = q.popleft()
            if u == b:
                return True
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return False
    return all(reach(a, b) for a, b in zip(s1, s2))
W = list('abcdef')
B[737] = (lambda: (lambda L: ([R.choice(W) for _ in range(L)], [R.choice(W) for _ in range(L + (R.random() < 0.1))], [[R.choice(W), R.choice(W)] for _ in range(R.randint(0, 5))]))(R.randint(1, 4)), b737, None)


def check742(vals, k, got):
    t = tree(vals)
    leaves = {n['v'] for n in all_nodes(t) if n['l'] is None and n['r'] is None}
    d = dists(graph(t), k)
    return got in leaves and d[got] == min(d[x] for x in leaves)
B[742] = (lambda: (lambda v: (v, R.choice([x for x in v if x is not None])))(rand_unique_tree(R.randint(1, 10))), None, check742)


def check751(ip, n, got):
    a = [int(x) for x in ip.split('.')]
    start = (a[0] << 24) | (a[1] << 16) | (a[2] << 8) | a[3]
    cur = start
    for blk in got:
        addr, p = blk.split('/')
        b = [int(x) for x in addr.split('.')]
        v = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
        size = 1 << (32 - int(p))
        if v != cur or v % size:
            return False
        cur += size

    @lru_cache(maxsize=None)
    def best(c, left):
        if left == 0:
            return 0
        return min(1 + best(c + s, left - s) for s in (1 << e for e in range(33)) if s <= left and c % s == 0)
    return cur == start + n and len(got) == best(start, n)
B[751] = (lambda: ('.'.join(str(x) for x in (R.randint(0, 255), R.randint(0, 255), R.randint(0, 255), R.randint(0, 255))), R.randint(1, 70)), None, check751)


def b755(heights, volume, k):
    h = list(heights)
    n = len(h)
    for _ in range(volume):
        placed = False
        for side in (range(k - 1, -1, -1), range(k + 1, n)):
            reach = []
            prev = k
            for i in side:
                if h[i] > h[prev]:
                    break
                reach.append(i)
                prev = i
            if reach:
                low = min(h[i] for i in reach)
                if low < h[k]:
                    h[min((i for i in reach if h[i] == low), key=lambda i: abs(i - k))] += 1
                    placed = True
                    break
        if not placed:
            h[k] += 1
    return h
B[755] = (lambda: (lambda n: ([R.randint(0, 4) for _ in range(n)], R.randint(0, 8), R.randrange(n)))(R.randint(1, 7)), b755, None)


def b758(words, s):
    bold = [any(s.startswith(w, i - j) for w in words for j in range(len(w)) if 0 <= i - j <= len(s) - len(w)) for i in range(len(s))]
    out = ''
    for i, ch in enumerate(s):
        if bold[i] and (i == 0 or not bold[i - 1]):
            out += '<b>'
        out += ch
        if bold[i] and (i == len(s) - 1 or not bold[i + 1]):
            out += '</b>'
    return out
B[758] = (lambda: ([''.join(R.choice('ab') for _ in range(R.randint(1, 3))) for _ in range(R.randint(0, 3))], ''.join(R.choice('abc') for _ in range(R.randint(1, 10)))), b758, None)


def gen_expr(depth=0):
    if depth > 2 or R.random() < 0.35:
        return str(R.randint(0, 20))
    if R.random() < 0.25:
        return '(' + gen_expr(depth + 1) + ')'
    return gen_expr(depth + 1) + R.choice('+-*/') + gen_expr(depth + 1)


def b772(s):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        a, b = ev(n.left), ev(n.right)
        if isinstance(n.op, ast.Add):
            return a + b
        if isinstance(n.op, ast.Sub):
            return a - b
        if isinstance(n.op, ast.Mult):
            return a * b
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q
    return ev(ast.parse(s, mode='eval'))


def g772():
    while True:
        s = gen_expr()
        try:
            b772(s)
            return (s,)
        except ZeroDivisionError:
            continue
B[772] = (g772, b772, None)


def b774(stations, k):
    gaps = [b - a for a, b in zip(stations, stations[1:])]
    cands = sorted({Fraction(g, m) for g in gaps for m in range(1, k + 2)})
    for D in cands:
        if sum(math.ceil(Fraction(g) / D) - 1 for g in gaps) <= k:
            return round(float(D), 6)
B[774] = (lambda: (sorted(R.sample(range(0, 60), R.randint(2, 7))), R.randint(1, 6)), b774, None)


def b903(s):
    return sum(1 for p in itertools.permutations(range(len(s) + 1))
               if all((p[i] < p[i + 1]) if ch == 'I' else (p[i] > p[i + 1]) for i, ch in enumerate(s))) % MOD
B[903] = (lambda: (''.join(R.choice('DI') for _ in range(R.randint(1, 7))),), b903, None)


def b911(ops, args):
    persons, times = args[0]
    out = [None]
    for (t,) in args[1:]:
        cnt, last = Counter(), {}
        for i, (p, tt) in enumerate(zip(persons, times)):
            if tt <= t:
                cnt[p] += 1
                last[p] = i
        top = max(cnt.values())
        out.append(max((p for p in cnt if cnt[p] == top), key=lambda p: last[p]))
    return out


def g911():
    n = R.randint(1, 8)
    times = sorted(R.sample(range(0, 40), n))
    qs = [[R.randint(times[0], 45)] for _ in range(R.randint(1, 5))]
    return (['TopVotedCandidate'] + ['q'] * len(qs), [[[R.randrange(3) for _ in range(n)], times]] + qs)
B[911] = (g911, b911, None)
B[1213] = (lambda: tuple(sorted(R.sample(range(1, 15), R.randint(1, 8))) for _ in range(3)),
           lambda a, b, c: sorted(set(a) & set(b) & set(c)), None)
B[1214] = (lambda: (rand_unique_tree(R.randint(1, 6)), rand_unique_tree(R.randint(1, 6)), R.randint(2, 70)),
           lambda t1, t2, target: any(x + y == target for x in t1 if x is not None for y in t2 if y is not None), None)


def stepping(v):
    s = str(v)
    return all(abs(int(a) - int(b)) == 1 for a, b in zip(s, s[1:]))
B[1215] = (lambda: tuple(sorted([R.randint(0, 3000), R.randint(0, 3000)])), lambda lo, hi: [v for v in range(lo, hi + 1) if stepping(v)], None)


def b1229(s1, s2, d):
    for t in range(0, 61):
        if any(a <= t and t + d <= b for a, b in s1) and any(a <= t and t + d <= b for a, b in s2):
            return [t, t + d]
    return []


def slots():
    pts = sorted(R.sample(range(0, 60), 2 * R.randint(1, 4)))
    out = [[pts[i], pts[i + 1]] for i in range(0, len(pts), 2)]
    R.shuffle(out)
    return out
B[1229] = (lambda: (slots(), slots(), R.randint(1, 8)), b1229, None)


def b1230(prob, target):
    return sum(math.prod(p if h else 1 - p for p, h in zip(prob, hs)) for hs in itertools.product([0, 1], repeat=len(prob)) if sum(hs) == target)
B[1230] = (lambda: (lambda n: ([R.choice([0.0, 1.0, R.random()]) for _ in range(n)], R.randint(0, n)))(R.randint(1, 9)), b1230, 'close6')
B[1692] = (lambda: (lambda n: (n, R.randint(1, n)))(R.randint(1, 30)),
           lambda n, k: sum((-1) ** i * math.comb(k, i) * (k - i) ** n for i in range(k + 1)) // math.factorial(k) % MOD, None)
B[1714] = (lambda: (lambda n: ([R.randint(0, 10**9) for _ in range(n)], [[R.randrange(n), R.randint(1, n + 2)] for _ in range(R.randint(1, 6))]))(R.randint(1, 30)),
           lambda nums, qs: [sum(nums[j] for j in range(x, len(nums)) if (j - x) % y == 0) % MOD for x, y in qs], None)


def g1740():
    v = rand_unique_tree(R.randint(1, 10))
    vals = [x for x in v if x is not None]
    return (v, R.choice(vals), R.choice(vals))
B[1740] = (g1740, lambda v, p, q: dists(graph(tree(v)), p)[q], None)


def b1820(g):
    m, n = len(g), len(g[0])
    best = 0
    for assign in itertools.product(range(-1, n), repeat=m):
        used = [a for a in assign if a >= 0]
        if len(used) == len(set(used)) and all(a < 0 or g[i][a] for i, a in enumerate(assign)):
            best = max(best, len(used))
    return best
B[1820] = (lambda: (lambda m, n: ([[R.randint(0, 1) for _ in range(n)] for _ in range(m)],))(R.randint(1, 4), R.randint(1, 4)), b1820, None)


def explain(f, c):
    n = len(f)
    return any(f[:i] == c[:i] and f[i:n - 1] == c[i + 1:n] and f[n - 1] != c[i] for i in range(n))


def g1826():
    n = R.randint(1, 6)
    true = [R.randint(1, 3) for _ in range(n)]
    which = R.choice([0, 1, 2])
    s = [true[:], true[:]]
    if which:
        i = R.randrange(n)
        dropped = true[i]
        bad = true[:i] + true[i + 1:] + [R.choice([v for v in range(1, 5) if v != dropped])]
        s[which - 1] = bad
    return (s[0], s[1])


def b1826(s1, s2):
    e1, e2 = explain(s1, s2), explain(s2, s1)
    return 1 if e1 and not e2 else 2 if e2 and not e1 else -1
B[1826] = (g1826, b1826, None)


@lru_cache(maxsize=None)
def nim(piles):
    return any(not nim(tuple(sorted(piles[:i] + (piles[i] - t,) + piles[i + 1:]))) for i in range(len(piles)) for t in range(1, piles[i] + 1))
B[1908] = (lambda: ([R.randint(1, 4) for _ in range(R.randint(1, 4))],), lambda p: nim(tuple(sorted(p))), None)
B[1918] = (lambda: (lambda a: (a, R.randint(1, len(a) * (len(a) + 1) // 2)))([R.randint(1, 9) for _ in range(R.randint(1, 7))]),
           lambda a, k: sorted(sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1))[k - 1], None)


def b1924(trees):
    pts = [tuple(p) for p in trees]
    def encloses(c):
        return all(math.hypot(x - c[0], y - c[1]) <= c[2] + 1e-7 for x, y in pts)
    cands = [(x, y, 0.0) for x, y in pts]
    for a, b in itertools.combinations(pts, 2):
        cands.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, math.hypot(a[0] - b[0], a[1] - b[1]) / 2))
    for a, b, c in itertools.combinations(pts, 3):
        d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        if d:
            ux = ((a[0] ** 2 + a[1] ** 2) * (b[1] - c[1]) + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1]) + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])) / d
            uy = ((a[0] ** 2 + a[1] ** 2) * (c[0] - b[0]) + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0]) + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])) / d
            cands.append((ux, uy, math.hypot(ux - a[0], uy - a[1])))
    return list(min((c for c in cands if encloses(c)), key=lambda c: c[2]))
B[1924] = (lambda: ([[R.randint(0, 9), R.randint(0, 9)] for _ in range(R.randint(1, 7))],), b1924, 'circle')


def b1933(s):
    @lru_cache(maxsize=None)
    def go(i, used2):
        if i == len(s):
            return used2
        ok = False
        if i + 3 <= len(s) and len(set(s[i:i + 3])) == 1:
            ok = go(i + 3, used2)
        if not ok and not used2 and i + 2 <= len(s) and len(set(s[i:i + 2])) == 1:
            ok = go(i + 2, True)
        return ok
    return go(0, False)
B[1933] = (lambda: (''.join(R.choice('0011') * R.randint(1, 3) for _ in range(R.randint(1, 4)))[:R.randint(1, 12)],), b1933, None)
B[1940] = (lambda: ([sorted(R.sample(range(1, 12), R.randint(1, 8))) for _ in range(R.randint(2, 4))],),
           lambda arrs: [x for x in arrs[0] if all(x in a for a in arrs[1:])], None)


def main():
    report, bad = {}, 0
    for pid in O.PROBLEM_IDS:
        gen, brute, mode = B[pid]
        n = mism = 0
        example = None
        for _ in range(150):
            args = gen()
            try:
                O.validate_domain(pid, *json.loads(json.dumps(args)))
            except (ValueError, IndexError, TypeError):
                continue
            got = O.REFERENCES[pid](*json.loads(json.dumps(args)))
            if callable(mode):
                ok = mode(*args, got)
            else:
                want = brute(*args)
                if mode == 'close6':
                    ok = abs(got - want) <= 1e-6
                elif mode == 'circle':
                    ok = abs(got[2] - want[2]) <= 1e-5 and math.hypot(got[0] - want[0], got[1] - want[1]) <= 1e-4
                else:
                    ok = got == want
            n += 1
            if not ok:
                mism += 1
                example = example or {'args': args, 'reference': got, 'brute': None if callable(mode) else brute(*args)}
        report[pid] = {'rows': n, 'mismatches': mism, 'first_mismatch': example}
        bad += mism
    print(json.dumps(report, default=str))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
