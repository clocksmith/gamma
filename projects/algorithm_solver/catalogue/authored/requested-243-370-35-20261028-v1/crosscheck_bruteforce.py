"""Independent brute-force cross-check of requested-243-370-35 references on random small inputs.

Each brute force restates the problem directly (enumeration or exhaustive search) and shares no code with
oracles.py. Order-insensitive problems are compared as multisets where the public problem allows any order.
Run: python3 crosscheck_bruteforce.py   (prints per-problem counts; exit 1 on any mismatch)
"""
import importlib.util
import itertools
import json
import random
import sys
from collections import Counter, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('xcheck_oracles_a', HERE / 'oracles.py')
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)
R = random.Random(20261029)


def tree(vals):
    """Level-order list -> dict node {v, l, r} (independent of oracles._tree_from_level)."""
    if not vals or vals[0] is None:
        return None
    nodes = [None if v is None else {'v': v, 'l': None, 'r': None} for v in vals]
    q = deque([nodes[0]])
    i = 1
    while q and i < len(nodes):
        n = q.popleft()
        if i < len(nodes):
            n['l'] = nodes[i]
            if nodes[i]:
                q.append(nodes[i])
            i += 1
        if i < len(nodes):
            n['r'] = nodes[i]
            if nodes[i]:
                q.append(nodes[i])
            i += 1
    return nodes[0]


def all_nodes(t):
    return [] if t is None else [t] + all_nodes(t['l']) + all_nodes(t['r'])


def inorder(t):
    return [] if t is None else inorder(t['l']) + [t['v']] + inorder(t['r'])


def rand_tree(n, lo=0, hi=5):
    if n == 0:
        return []
    out = [R.randint(lo, hi)]
    while len([v for v in out if v is not None]) < n:
        out.append(R.randint(lo, hi) if R.random() < 0.8 else None)
    while out and out[-1] is None:
        out.pop()
    return out


def bst_from(values):
    root = None
    def ins(t, v):
        if t is None:
            return {'v': v, 'l': None, 'r': None}
        if v < t['v']:
            t['l'] = ins(t['l'], v)
        else:
            t['r'] = ins(t['r'], v)
        return t
    for v in values:
        root = ins(root, v)
    out, q = [], deque([root])
    while q:
        n = q.popleft()
        out.append(None if n is None else n['v'])
        if n is not None:
            q.append(n['l'])
            q.append(n['r'])
    while out and out[-1] is None:
        out.pop()
    return out


ROT = {'0': '0', '1': '1', '6': '9', '8': '8', '9': '6'}


def strobo(s):
    return all(c in ROT for c in s) and ''.join(ROT[c] for c in reversed(s)) == s


def ms(x):
    return Counter(json.dumps(v, sort_keys=True) for v in x)


B = {}


def b243(w, a, b):
    return min(abs(i - j) for i in range(len(w)) for j in range(len(w)) if w[i] == a and w[j] == b and i != j)
def g243():
    w = [R.choice('abcd') for _ in range(R.randint(2, 9))]
    while len(set(w)) < 2:
        w.append(R.choice('abcd'))
    return (w, *R.sample(sorted(set(w)), 2))
B[243] = (g243, b243, None)
def g245():
    while True:
        w = [R.choice('abc') for _ in range(R.randint(2, 9))]
        a, b = R.choice(w), R.choice(w)
        if a != b or w.count(a) >= 2:
            return (w, a, b)
B[245] = (g245, b243, None)
B[246] = (lambda: (''.join(R.choice('0168925') for _ in range(R.randint(1, 6))),), strobo, None)
B[247] = (lambda: (R.randint(1, 6),), lambda n: sorted(s for s in (''.join(p) for p in itertools.product('0123456789', repeat=n)) if strobo(s) and (n == 1 or s[0] != '0')), None)
B[248] = (lambda: tuple(map(str, sorted([R.randint(0, 3000), R.randint(0, 3000)]))), lambda lo, hi: sum(1 for v in range(int(lo), int(hi) + 1) if strobo(str(v))), None)
B[249] = (lambda: ([''.join(R.choice('abz') for _ in range(R.randint(1, 3))) for _ in range(R.randint(1, 8))],), None, None)


def b249(ss):
    canon = lambda s: min(''.join(chr((ord(c) - 97 + k) % 26 + 97) for c in s) for k in range(26))
    groups = {}
    for s in ss:
        groups.setdefault(canon(s), []).append(s)
    return list(groups.values())
B[249] = (B[249][0], b249, 'groups')


def b250(vals):
    t = tree(vals)
    return sum(1 for n in all_nodes(t) if len({m['v'] for m in all_nodes(n)}) == 1)
B[250] = (lambda: (rand_tree(R.randint(0, 9), 1, 2),), b250, None)


def b254(n):
    out = set()
    def rec(rem, start, path):
        for d in range(start, rem + 1):
            if rem % d == 0:
                if d == rem:
                    if path:
                        out.add(tuple(path + [d]))
                else:
                    rec(rem // d, d, path + [d])
    rec(n, 2, [])
    return [list(x) for x in out]
B[254] = (lambda: (R.randint(1, 400),), b254, 'multiset')


def b255(pre):
    def ok(seq, lo, hi):
        if not seq:
            return True
        r = seq[0]
        if not lo < r < hi:
            return False
        i = 1
        while i < len(seq) and seq[i] < r:
            i += 1
        return ok(seq[1:i], lo, r) and ok(seq[i:], r, hi)
    return ok(pre, -10**9, 10**9)
B[255] = (lambda: (R.sample(range(1, 12), R.randint(1, 8)),), b255, None)


def bpaint(costs):
    k = len(costs[0])
    return min(sum(costs[i][c] for i, c in enumerate(cols)) for cols in itertools.product(range(k), repeat=len(costs))
               if all(cols[i] != cols[i + 1] for i in range(len(cols) - 1)))
B[256] = (lambda: ([[R.randint(1, 20) for _ in range(3)] for _ in range(R.randint(1, 6))],), bpaint, None)
B[265] = (lambda: (lambda k: ([[R.randint(1, 20) for _ in range(k)] for _ in range(R.randint(1, 5))],))(R.randint(2, 4)), bpaint, None)
B[259] = (lambda: ([R.randint(-5, 5) for _ in range(R.randint(0, 8))], R.randint(-5, 5)),
          lambda nums, t: sum(1 for a, b, c in itertools.combinations(range(len(nums)), 3) if nums[a] + nums[b] + nums[c] < t), None)
B[267] = (lambda: (''.join(R.choice('aab') for _ in range(R.randint(1, 7))),),
          lambda s: sorted({''.join(p) for p in itertools.permutations(s) if ''.join(p) == ''.join(p)[::-1]}), 'multiset')


def check269(words, got):
    letters = {c for w in words for c in w}
    def less(a, b, order):
        for x, y in zip(a, b):
            if x != y:
                return order.index(x) < order.index(y)
        return len(a) <= len(b)
    if got == '':
        return not any(all(less(words[i], words[i + 1], ''.join(p)) for i in range(len(words) - 1)) for p in itertools.permutations(sorted(letters)))
    return sorted(got) == sorted(letters) and all(less(words[i], words[i + 1], got) for i in range(len(words) - 1))
B[269] = (lambda: ([''.join(R.choice('abcd') for _ in range(R.randint(1, 3))) for _ in range(R.randint(1, 5))],), None, check269)
B[270] = (lambda: (bst_from(R.sample(range(0, 30), R.randint(1, 9))), R.choice([R.randint(-3, 33) + 0.5, float(R.randint(-3, 33))])),
          lambda vals, t: min((v for v in vals if v is not None), key=lambda v: (abs(v - t), v)), None)
B[272] = (lambda: (lambda v: (bst_from(v), R.randint(-3, 33) + 0.25, R.randint(1, len(v))))(R.sample(range(0, 30), R.randint(1, 9))),
          lambda vals, t, k: sorted(sorted((v for v in vals if v is not None), key=lambda v: abs(v - t))[:k]), None)
B[276] = (lambda: (R.randint(1, 6), R.randint(1, 3)),
          lambda n, k: sum(1 for c in itertools.product(range(k), repeat=n) if not any(c[i] == c[i + 1] == c[i + 2] for i in range(n - 2))), None)


def b296(g):
    homes = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == 1]
    return min(sum(abs(r - a) + abs(c - b) for a, b in homes) for r in range(len(g)) for c in range(len(g[0])))
B[296] = (lambda: (lambda m, n: ([[1 if R.random() < 0.4 else 0 for _ in range(n)] for _ in range(m)],))(R.randint(1, 4), R.randint(1, 4)), b296, 'needs2homes')


def b298(vals):
    t = tree(vals)
    def down(n):
        best = 1
        for ch in (n['l'], n['r']):
            if ch and ch['v'] == n['v'] + 1:
                best = max(best, 1 + down(ch))
        return best
    return max([down(n) for n in all_nodes(t)], default=0)
B[298] = (lambda: (rand_tree(R.randint(1, 9), 1, 4),), b298, None)
def g302():
    m, n = R.randint(1, 5), R.randint(1, 5)
    g = [['0'] * n for _ in range(m)]
    r, c = R.randrange(m), R.randrange(n)
    x, y = r, c
    for _ in range(R.randint(1, 10)):
        g[r][c] = '1'
        dr, dc = R.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        if 0 <= r + dr < m and 0 <= c + dc < n:
            r, c = r + dr, c + dc
    return (g, x, y)


def b302(g, x, y):
    seen, q = {(x, y)}, deque([(x, y)])
    while q:
        a, b = q.popleft()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (a + da, b + db)
            if 0 <= p[0] < len(g) and 0 <= p[1] < len(g[0]) and p not in seen and g[p[0]][p[1]] == '1':
                seen.add(p)
                q.append(p)
    rs, cs = [p[0] for p in seen], [p[1] for p in seen]
    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
B[302] = (g302, b302, None)
B[311] = (lambda: (lambda m, k, n: ([[R.choice([0, 0, R.randint(-3, 3)]) for _ in range(k)] for _ in range(m)], [[R.choice([0, R.randint(-3, 3)]) for _ in range(n)] for _ in range(k)]))(R.randint(1, 3), R.randint(1, 3), R.randint(1, 3)),
          lambda a, b: [[sum(a[i][p] * b[p][j] for p in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))], None)


def b314(vals):
    t = tree(vals)
    if t is None:
        return []
    items, q, idx = [], deque([(t, 0, 0)]), 0
    while q:
        n, row, col = q.popleft()
        items.append((col, row, idx, n['v']))
        idx += 1
        if n['l']:
            q.append((n['l'], row + 1, col - 1))
        if n['r']:
            q.append((n['r'], row + 1, col + 1))
    items.sort()
    out = {}
    for col, _, _, v in items:
        out.setdefault(col, []).append(v)
    return [out[c] for c in sorted(out)]
B[314] = (lambda: (rand_tree(R.randint(0, 10), 0, 9),), b314, None)


def b317(g):
    m, n = len(g), len(g[0])
    blds = [(r, c) for r in range(m) for c in range(n) if g[r][c] == 1]
    best = None
    for r in range(m):
        for c in range(n):
            if g[r][c] != 0:
                continue
            dist, q, tot = {(r, c): 0}, deque([(r, c)]), 0
            reached = 0
            while q:
                a, b = q.popleft()
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    x, y = a + da, b + db
                    if 0 <= x < m and 0 <= y < n and (x, y) not in dist:
                        if g[x][y] == 1:
                            dist[(x, y)] = dist[(a, b)] + 1
                            tot += dist[(x, y)]
                            reached += 1
                        elif g[x][y] == 0:
                            dist[(x, y)] = dist[(a, b)] + 1
                            q.append((x, y))
            if reached == len(blds) and (best is None or tot < best):
                best = tot
    return -1 if best is None else best
B[317] = (lambda: (lambda m, n: ([[R.choice([0, 0, 0, 1, 2]) for _ in range(n)] for _ in range(m)],))(R.randint(1, 4), R.randint(1, 4)), b317, 'needsbuilding')


def b320(w):
    out = set()
    for keep in itertools.product([0, 1], repeat=len(w)):
        s, run = '', 0
        for ch, k in zip(w, keep):
            if k:
                run += 1
            else:
                s += (str(run) if run else '') + ch
                run = 0
        out.add(s + (str(run) if run else ''))
    return sorted(out)
B[320] = (lambda: (''.join(R.choice('abc') for _ in range(R.randint(1, 6))),), b320, 'multiset')
B[325] = (lambda: ([R.randint(-3, 3) for _ in range(R.randint(1, 9))], R.randint(-4, 4)),
          lambda a, k: max([j - i for i in range(len(a)) for j in range(i + 1, len(a) + 1) if sum(a[i:j]) == k], default=0), None)


def b333(vals):
    t = tree(vals)
    def is_bst(n, lo, hi):
        return n is None or (lo < n['v'] < hi and is_bst(n['l'], lo, n['v']) and is_bst(n['r'], n['v'], hi))
    return max([len(all_nodes(n)) for n in all_nodes(t) if is_bst(n, -10**9, 10**9)], default=0)
B[333] = (lambda: (rand_tree(R.randint(0, 9), 0, 9),), b333, None)
B[340] = (lambda: (''.join(R.choice('abcd') for _ in range(R.randint(1, 9))), R.randint(0, 4)),
          lambda s, k: max([j - i for i in range(len(s)) for j in range(i + 1, len(s) + 1) if len(set(s[i:j])) <= k], default=0), None)


def b351(m, n):
    pos = {k: ((k - 1) // 3, (k - 1) % 3) for k in range(1, 10)}
    inv = {v: k for k, v in pos.items()}
    def ok(path):
        seen = set()
        for a, b in zip(path, path[1:]):
            seen.add(a)
            (r1, c1), (r2, c2) = pos[a], pos[b]
            if (r1 + r2) % 2 == 0 and (c1 + c2) % 2 == 0:
                mid = inv[((r1 + r2) // 2, (c1 + c2) // 2)]
                if mid not in seen:
                    return False
        return True
    return sum(1 for L in range(m, n + 1) for p in itertools.permutations(range(1, 10), L) if ok(p))
B[351] = (lambda: tuple(sorted([R.randint(1, 4), R.randint(1, 4)])), b351, None)


def b356(pts):
    s = {tuple(p) for p in pts}
    return any(all((cx2 - x, y) in s for x, y in s) for cx2 in range(-20, 21))
B[356] = (lambda: ([[R.randint(-4, 4), R.randint(-2, 2)] for _ in range(R.randint(1, 5))],), b356, None)


def check358(s, k, got):
    def valid(t):
        last = {}
        for i, c in enumerate(t):
            if c in last and i - last[c] < k:
                return False
            last[c] = i
        return True
    if got == '':
        return not any(valid(''.join(p)) for p in set(itertools.permutations(s)))
    return sorted(got) == sorted(s) and valid(got)
B[358] = (lambda: (''.join(R.choice('aab') for _ in range(R.randint(1, 7))), R.randint(0, 3)), None, check358)
B[360] = (lambda: (sorted(R.randint(-6, 6) for _ in range(R.randint(1, 7))), R.randint(-3, 3), R.randint(-3, 3), R.randint(-3, 3)),
          lambda a, x, y, z: sorted(x * v * v + y * v + z for v in a), None)


def b361(g):
    m, n = len(g), len(g[0])
    best = 0
    for r in range(m):
        for c in range(n):
            if g[r][c] != '0':
                continue
            k = 0
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                x, y = r + dr, c + dc
                while 0 <= x < m and 0 <= y < n and g[x][y] != 'W':
                    k += g[x][y] == 'E'
                    x, y = x + dr, y + dc
            best = max(best, k)
    return best
B[361] = (lambda: (lambda m, n: ([[R.choice('0EW0') for _ in range(n)] for _ in range(m)],))(R.randint(1, 4), R.randint(1, 4)), b361, None)


def b366(vals):
    t = tree(vals)
    out = []
    alive = set(id(n) for n in all_nodes(t))
    parent_kids = {id(n): [c for c in (n['l'], n['r']) if c] for n in all_nodes(t)}
    while alive:
        leaves = [n for n in all_nodes(t) if id(n) in alive and not any(id(c) in alive for c in parent_kids[id(n)])]
        out.append([n['v'] for n in leaves])
        alive -= {id(n) for n in leaves}
    return out
B[366] = (lambda: (rand_tree(R.randint(1, 9), 0, 9),), b366, 'levels')
B[369] = (lambda: ([R.randint(1, 9)] + [R.choice([9, 9, R.randint(0, 9)]) for _ in range(R.randint(0, 5))],),
          lambda d: [int(c) for c in str(int(''.join(map(str, d))) + 1)], None)


def b370(n, ups):
    a = [0] * n
    for s, e, inc in ups:
        for i in range(s, e + 1):
            a[i] += inc
    return a
B[370] = (lambda: (lambda n: (n, [sorted([R.randrange(n), R.randrange(n)]) + [R.randint(-3, 3)] for _ in range(R.randint(0, 4))]))(R.randint(1, 6)), b370, None)


def main():
    report, bad = {}, 0
    for pid in O.PROBLEM_IDS:
        gen, brute, mode = B[pid]
        n = mism = 0
        example = None
        for _ in range(150):
            args = gen()
            if mode == 'needs2homes' and sum(map(sum, args[0])) < 2:
                continue
            if mode == 'needsbuilding' and not any(1 in row for row in args[0]):
                continue
            try:
                O.validate_domain(pid, *args)
            except (ValueError, IndexError):
                continue
            got = O.REFERENCES[pid](*json.loads(json.dumps(args)))
            if callable(mode):
                ok = mode(*args, got)
            else:
                want = brute(*args)
                if mode == 'multiset':
                    ok = ms(got) == ms(want)
                elif mode == 'groups':
                    ok = sorted(map(sorted, got)) == sorted(map(sorted, want))
                elif mode == 'levels':
                    ok = [sorted(g) for g in got] == [sorted(g) for g in want]
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
