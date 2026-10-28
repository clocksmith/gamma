"""Source-blind bounded references; never imports candidate programs."""
from collections import deque
from functools import lru_cache
from itertools import combinations
from math import isqrt
import random

IDS = (3623, 3625, 3627, 3628, 3629, 3634, 3635, 3638, 3644, 3645)
MOD = 1000000007


def integer(v, lo, hi):
    return type(v) is int and lo <= v <= hi


def array(a, lo, hi, minimum, maximum):
    return type(a) is list and minimum <= len(a) <= maximum and all(integer(v, lo, hi) for v in a)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:
        raise ValueError('exact identity and ordered argument list required')
    arity = 2 if pid in (3634, 3645) else 4 if pid == 3635 else 1
    if len(args) != arity:
        raise ValueError('argument count')
    a = args[0]
    if pid in (3623, 3625):
        bound, maximum = (10**8, 100000) if pid == 3623 else (1000, 500)
        good = (type(a) is list and 4 <= len(a) <= maximum and
                all(array(p, -bound, bound, 2, 2) for p in a))
        if good:
            good = len(set(map(tuple, a))) == len(a)
    elif pid == 3627:
        good = array(a, 1, 10**9, 3, 500000) and len(a) % 3 == 0
    elif pid == 3628:
        good = type(a) is str and 1 <= len(a) <= 100000 and all('A' <= c <= 'Z' for c in a)
    elif pid == 3629:
        good = array(a, 1, 10**6, 1, 100000)
    elif pid == 3634:
        good = array(a, 1, 10**9, 1, 100000) and integer(args[1], 1, 100000)
    elif pid == 3635:
        good = all(array(v, 1, 100000, 1, 50000) for v in args) and len(a) == len(args[1]) and len(args[2]) == len(args[3])
    elif pid == 3638:
        good = array(a, 1, 10**9, 2, 100000)
    elif pid == 3644:
        good = array(a, 0, 99999, 1, 100000) and set(a) == set(range(len(a)))
    else:
        good = array(a, 1, 100000, 1, 100000) and array(args[1], 1, len(a), len(a), len(a))
    if not good:
        raise ValueError('outside exact official domain')


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def hull(points):
    points = sorted(points)
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def prime(v):
    return v >= 2 and all(v % d for d in range(2, isqrt(v)+1))


def expected(pid, args):
    validate(pid, args)
    a = args[0]
    if pid in (3623, 3625):
        if len(a) > 12:
            raise ValueError('quadruple reference bound')
        total = 0
        for four in combinations(a, 4):
            poly = hull(four)
            if len(poly) != 4:
                continue
            edges = [(poly[(i+1) % 4][0]-poly[i][0], poly[(i+1) % 4][1]-poly[i][1]) for i in range(4)]
            if pid == 3623:
                total += any(edges[i][1] == edges[i+2][1] == 0 for i in (0, 1))
            else:
                total += any(edges[i][0]*edges[i+2][1] == edges[i][1]*edges[i+2][0] for i in (0, 1))
        return total % MOD if pid == 3623 else total
    if pid == 3627:
        if len(a) > 12:
            raise ValueError('triple partition bound')
        @lru_cache(None)
        def visit(left):
            if not left:
                return 0
            first = left[0]
            return max(sorted((a[first], a[i], a[j]))[1]+visit(tuple(k for k in left if k not in (first, i, j))) for i, j in combinations(left[1:], 2))
        return visit(tuple(range(len(a))))
    if pid == 3628:
        if len(a) > 12:
            raise ValueError('insertion enumeration bound')
        def count(s):
            return sum(s[i]+s[j]+s[k] == 'LCT' for i, j, k in combinations(range(len(s)), 3))
        return max(count(a[:i]+c+a[i:]) for i in range(len(a)+1) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if pid == 3629:
        if len(a) > 30:
            raise ValueError('explicit directed graph bound')
        distance = [-1]*len(a); distance[0] = 0; todo = deque([0])
        while todo:
            i = todo.popleft()
            for j in range(len(a)):
                if distance[j] < 0 and (abs(i-j) == 1 or (prime(a[i]) and a[j] % a[i] == 0)):
                    distance[j] = distance[i]+1; todo.append(j)
        return distance[-1]
    if pid == 3634:
        if len(a) > 16:
            raise ValueError('all subsets bound')
        best = 1
        for mask in range(1, 1 << len(a)):
            kept = [x for i, x in enumerate(a) if mask >> i & 1]
            if max(kept) <= min(kept)*args[1]:
                best = max(best, len(kept))
        return len(a)-best
    if pid == 3635:
        if len(a)*len(args[2]) > 400:
            raise ValueError('ride pair enumeration bound')
        ls, ld, ws, wd = args
        return min(min(max(ls[i]+ld[i], ws[j])+wd[j], max(ws[j]+wd[j], ls[i])+ld[i]) for i in range(len(ls)) for j in range(len(ws)))
    if pid == 3638:
        if len(a) > 18:
            raise ValueError('interval scheduling bound')
        dp = [0]*(len(a)+1)
        for end in range(1, len(a)+1):
            dp[end] = dp[end-1]
            for start in range(end):
                if a[end-1] < max(a[start:end]):
                    dp[end] = max(dp[end], dp[start]+1)
        return dp[-1]
    if pid == 3644:
        if len(a) > 10:
            raise ValueError('value-swap graph bound')
        if a == list(range(len(a))):
            return 0
        for k in range(len(a)-1, -1, -1):
            parent = list(range(len(a)))
            def find(x):
                while parent[x] != x:
                    x = parent[x]
                return x
            for i, j in combinations(range(len(a)), 2):
                if i & j == k:
                    parent[find(i)] = find(j)
            if all(find(i) == find(v) for i, v in enumerate(a)):
                return k
        raise AssertionError('zero connects all values')
    if len(a) > 10:
        raise ValueError('complete activation-state bound')
    limits = args[1]
    @lru_cache(None)
    def visit(used, active, dead):
        best = 0
        for i, value in enumerate(a):
            if (used | dead) >> i & 1 or active.bit_count() >= limits[i]:
                continue
            after = active | (1 << i); count = after.bit_count()
            retired = dead | sum(1 << j for j, limit in enumerate(limits) if limit <= count)
            best = max(best, value+visit(used | (1 << i), after & ~retired, retired))
        return best
    return visit(0, 0, 0)


def synthetic_cases():
    rng = random.Random(20261028)
    result = []
    for _ in range(20):
        points = [list(p) for p in rng.sample([(x, y) for x in range(-2, 3) for y in range(-2, 3)], 7)]
        result.extend([(3623, [points]), (3625, [points]), (3627, [[rng.randrange(1, 9) for _ in range(6)]]),
                       (3628, [''.join(rng.choices('LCTX', k=7))]), (3629, [[rng.randrange(1, 40) for _ in range(8)]]),
                       (3634, [[rng.randrange(1, 15) for _ in range(7)], rng.randrange(1, 5)]),
                       (3635, [[rng.randrange(1, 10) for _ in range(3)] for _ in range(4)]),
                       (3638, [[rng.randrange(1, 10) for _ in range(8)]]),
                       (3644, [rng.sample(range(7), 7)]),
                       (3645, [[rng.randrange(1, 10) for _ in range(7)], [rng.randrange(1, 8) for _ in range(7)]])])
    return result
