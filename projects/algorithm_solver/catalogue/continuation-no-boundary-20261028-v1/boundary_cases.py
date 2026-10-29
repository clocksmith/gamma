"""Original N/O cases plus boundary cases for the thirteen review gaps.

Each new expected value comes from a method different from the cohort oracle,
except 3937, whose final-integer enumeration matches the O oracle's (its
independent check is circular_residue in test_boundary.py):
enumeration of the few maximum peak sets (3891), Miller-Rabin primes with
bisection (3896), an exchange-order string sort (3897), block gcds with an
explicit prefix-gcd witness (3901), a separable two-stage L1 distance transform
(3905), arrays built to designed side sums (3909), a value segment tree or
closed forms (3915), Dijkstra on the move graph (3919), split-based tokenizing
(3926), closed forms or base enumeration (3932), a suffix automaton or a
periodic closed form (3934), per-element final-integer windows with a top-two
minimisation (3937) and breadth-first search over dihedral transforms (3942).
Rows whose arguments repeat an earlier row are dropped. Nothing here reads a
candidate source.
"""
from __future__ import annotations
from bisect import bisect_left
from collections import Counter
from functools import cmp_to_key
import heapq
import importlib.util
from math import gcd, isqrt
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]/'authored'
IDS = {'n': (3891, 3896, 3897, 3901, 3905), 'o': (3909, 3915, 3919, 3926, 3932, 3934, 3937, 3942)}
COHORT = {pid: key for key, ids in IDS.items() for pid in ids}
MOD = 10**9+7


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


N_ORACLES = _load(ROOT/'continuation-n-20261028-v1'/'oracles.py', 'no_boundary_n_oracles')
O_ORACLES = _load(ROOT/'continuation-o-20261028-v1'/'oracles.py', 'no_boundary_o_oracles')
N_CASES = _load(ROOT/'continuation-n-20261028-v1'/'cases.py', 'no_boundary_n_cases')
O_CASES = _load(ROOT/'continuation-o-20261028-v1'/'cases.py', 'no_boundary_o_cases')
ORACLES = {'n': N_ORACLES, 'o': O_ORACLES}
CASES = {'n': N_CASES, 'o': O_CASES}


def validate(pid, args):
    ORACLES[COHORT[pid]].validate_domain(pid, args)


def cohort_reference(pid, args):
    return ORACLES[COHORT[pid]].reference(pid, args)


# 3891: peaks cost max(0, max(neighbours)+1-value) independently, and peaks cannot be adjacent.
# Odd n has one maximum set (every odd index). Even n has (n-2)/2 peaks among n-2 interior
# indices, so a maximum set is odd indices 1..2j-1 followed by even indices 2j+2..n-2.

def min_increase(nums):
    n = len(nums)
    cost = [0]+[max(0, max(nums[i-1], nums[i+1])+1-nums[i]) for i in range(1, n-1)]+[0]
    if n % 2:
        return sum(cost[1:n-1:2])
    half = (n-2)//2
    odd = [0]
    for j in range(half):
        odd.append(odd[-1]+cost[2*j+1])
    even = [0]*(half+1)
    for j in range(half-1, -1, -1):
        even[j] = even[j+1]+cost[2*j+2]
    return min(odd[j]+even[j] for j in range(half+1))


# 3896: deterministic Miller-Rabin (bases 2, 3, 5, 7 are exact below 3.2e9) and a bisected prime list.

def is_prime_mr(v):
    if v < 2:
        return False
    for p in (2, 3, 5, 7):
        if v % p == 0:
            return v == p
    d, s = v-1, 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in (2, 3, 5, 7):
        x = pow(a, d, v)
        if x in (1, v-1):
            continue
        for _ in range(s-1):
            x = x*x % v
            if x == v-1:
                break
        else:
            return False
    return True


PRIMES = [v for v in range(2, 100200) if is_prime_mr(v)]


def alternating_prime_ops(nums):
    total = 0
    for i, v in enumerate(nums):
        if i % 2 == 0:
            total += PRIMES[bisect_left(PRIMES, v)]-v
        elif is_prime_mr(v):
            total += 2 if v == 2 else 1
    return total


# 3897: exchange order A before B iff A+B >= B+A as strings, then the exact binary integer.

def concatenated_max(ones, zeros):
    counts = Counter(zip(ones, zeros))
    order = sorted(('1'*a+'0'*b for a, b in counts), key=cmp_to_key(lambda x, y: (y+x > x+y)-(y+x < x+y)))
    text = ''.join(segment*counts[(segment.count('1'), segment.count('0'))] for segment in order)
    return int(text, 2) % MOD


# 3901: only multiples of p can join a gcd-p subsequence. Block gcds give the gcd of those.
# If some element is not a multiple, that gcd being p is a proper witness. Otherwise the indices
# where the running prefix gcd drops form a witness; it is proper unless it is every index, in
# which case dropping each index in turn is checked directly.

def good_subsequence_queries(nums, p, queries):
    a = nums[:]; n = len(a); size = max(1, isqrt(n)); blocks = (n+size-1)//size
    def block_gcd(b):
        return gcd(*[v for v in a[b*size:(b+1)*size] if v % p == 0])
    gcds = [block_gcd(b) for b in range(blocks)]; eligible = sum(v % p == 0 for v in a); answer = 0
    for index, value in queries:
        eligible += (value % p == 0)-(a[index] % p == 0)
        a[index] = value; gcds[index//size] = block_gcd(index//size)
        if gcd(*gcds) != p:
            continue
        if eligible < n:
            answer += 1; continue
        running = 0; drops = []
        for b in range(blocks):
            if running and gcd(running, gcds[b]) == running:
                continue
            for i in range(b*size, min(n, (b+1)*size)):
                if running == 0 or a[i] % running:
                    running = gcd(running, a[i]); drops.append(i)
                    if running == p:
                        break
            if running == p:
                break
        if len(drops) < n:
            answer += 1
        elif any(gcd(*(a[:i]+a[i+1:])) == p for i in range(n)):
            answer += 1
    return answer


# 3905: separable L1 transform. Keys order by distance, then larger colour; distance steps add STEP.
STEP = 1 << 21


def _sweep(keys):
    for i in range(1, len(keys)):
        if keys[i-1]+STEP < keys[i]:
            keys[i] = keys[i-1]+STEP
    for i in range(len(keys)-2, -1, -1):
        if keys[i+1]+STEP < keys[i]:
            keys[i] = keys[i+1]+STEP
    return keys


def flood_fill(n, m, sources):
    far = STEP*(n+m+5)
    rows = [[far]*m for _ in range(n)]
    for r, c, color in sources:
        rows[r][c] = (1 << 20)-color
    for row in rows:
        _sweep(row)
    for c in range(m):
        column = _sweep([rows[r][c] for r in range(n)])
        for r in range(n):
            rows[r][c] = column[r]
    return [[(1 << 20)-(key % STEP) for key in row] for row in rows]


# 3909: arrays are built to designed side sums; the answer follows from the design, not a sum.

def increasing_with_sum(length, total, below):
    """Strictly increasing positive values below `below` whose sum is exactly `total`."""
    base, extra = divmod(total-length*(length-1)//2, length)
    values = [base+i+(i >= length-extra) for i in range(length)]
    if length and (values[0] < 1 or values[-1] >= below):
        raise ValueError('designed side sum is not realizable')
    return values


def bitonic(left_total, left_length, peak, right_total, right_length):
    left = increasing_with_sum(left_length, left_total, peak) if left_length else []
    right = increasing_with_sum(right_length, right_total, peak)[::-1] if right_length else []
    expected = 0 if left_total > right_total else 1 if right_total > left_total else -1
    return [left+[peak]+right], expected


# 3915: value segment tree for range maxima; predecessor j becomes usable at i = j+k.

def max_alternating_sum(nums, k):
    size = 1
    while size < max(nums)+2:
        size *= 2
    trees = {'up': [0]*(2*size), 'down': [0]*(2*size)}
    def update(tree, position, value):
        position += size
        while position and tree[position] < value:
            tree[position] = value; position //= 2
    def query(tree, low, high):  # maximum over values in [low, high)
        best = 0; low += size; high += size
        while low < high:
            if low & 1:
                best = max(best, tree[low]); low += 1
            if high & 1:
                high -= 1; best = max(best, tree[high])
            low //= 2; high //= 2
        return best
    up = [0]*len(nums); down = [0]*len(nums); best = 0
    for i, v in enumerate(nums):
        j = i-k
        if j >= 0:
            update(trees['up'], nums[j], up[j]); update(trees['down'], nums[j], down[j])
        up[i] = v+query(trees['down'], 0, v); down[i] = v+query(trees['up'], v+1, size)
        best = max(best, up[i], down[i])
    return best


def alternating_quadratic(nums, k):
    up = [0]*len(nums); down = [0]*len(nums)
    for i, v in enumerate(nums):
        up[i] = v+max([down[j] for j in range(i-k+1) if nums[j] < v] or [0])
        down[i] = v+max([up[j] for j in range(i-k+1) if nums[j] > v] or [0])
    return max(up+down)


# 3919: Dijkstra from each query source over adjacent moves and closest-index moves.
# Any longer move costs the sum of the adjacent gaps it spans, so adjacent moves dominate it.

def move_costs(nums, queries):
    n = len(nums)
    closest = [1]+[i-1 if nums[i]-nums[i-1] <= nums[i+1]-nums[i] else i+1 for i in range(1, n-1)]+[n-2]
    def edges(i):
        for j in (i-1, i+1):
            if 0 <= j < n:
                yield j, (1 if closest[i] == j else abs(nums[i]-nums[j]))
    found = {}
    for source in sorted({q[0] for q in queries}):
        dist = [None]*n; heap = [(0, source)]
        while heap:
            d, i = heapq.heappop(heap)
            if dist[i] is not None:
                continue
            dist[i] = d
            for j, w in edges(i):
                if dist[j] is None:
                    heapq.heappush(heap, (d+w, j))
        found[source] = dist
    return [found[i][j] for i, j in queries]


# 3926: split on spaces, then on runs of two or more hyphens; strip edge hyphens.

def word_counts(chunks, queries):
    words = Counter()
    for token in ''.join(chunks).split(' '):
        for piece in re.split('-{2,}', token):
            piece = piece.strip('-')
            if piece:
                words[piece] += 1
    return [words[q] for q in queries]


# 3932: k = 1 counts every integer; otherwise enumerate bases until the power passes r.

def kth_roots(left, right, k):
    if k == 1:
        return right-left+1
    count = 0; base = 0
    while base**k <= right:
        count += base**k >= left; base += 1
    return count


# 3934: suffix automaton. A state whose end-position set has one element holds unique
# substrings; its shortest member has length len(link)+1.

def smallest_unique_sam(nums):
    length = [0]; link = [-1]; nxt = [{}]; count = [0]; last = 0
    for v in nums:
        cur = len(length); length.append(length[last]+1); link.append(-1); nxt.append({}); count.append(1)
        p = last
        while p != -1 and v not in nxt[p]:
            nxt[p][v] = cur; p = link[p]
        if p == -1:
            link[cur] = 0
        else:
            q = nxt[p][v]
            if length[p]+1 == length[q]:
                link[cur] = q
            else:
                clone = len(length); length.append(length[p]+1); link.append(link[q]); nxt.append(dict(nxt[q])); count.append(0)
                while p != -1 and nxt[p].get(v) == q:
                    nxt[p][v] = clone; p = link[p]
                link[q] = clone; link[cur] = clone
        last = cur
    for state in sorted(range(1, len(length)), key=length.__getitem__, reverse=True):
        count[link[state]] += count[state]
    return min(length[link[state]]+1 for state in range(1, len(length)) if count[state] == 1)


def periodic_unique(n, period):
    # Distinct symbols repeating with this period: a window is fixed by its start residue, and
    # some residue has exactly one start once at most 2*period-1 starts remain.
    return max(1, n-2*period+2)


# 3937: each element's final integers lie in [v-k, v+k] (negative finals allowed, mathematical
# residue); best y differs from x, so the two cheapest odd residues suffice.

def residue_alternating(nums, k):
    totals = [[0]*k, [0]*k]
    for index, v in enumerate(nums):
        best = [None]*k
        for final in range(v-k, v+k+1):
            residue = final % k; cost = abs(final-v)
            if best[residue] is None or cost < best[residue]:
                best[residue] = cost
        row = totals[index % 2]
        for residue in range(k):
            row[residue] += best[residue]
    even, odd = totals
    ranked = sorted(range(k), key=lambda y: (odd[y], y))
    return min(even[x]+odd[ranked[0] if ranked[0] != x else ranked[1]] for x in range(k))


def circular_residue(nums, k):
    total = [[sum(min((t-v) % k, (v-t) % k) for v in nums[parity::2]) for t in range(k)] for parity in (0, 1)]
    return min(total[0][x]+total[1][y] for x in range(k) for y in range(k) if x != y)


# 3942: breadth-first search over (reflected, shift) transforms; the state is a[(s+i) % n] or a[(s-i) % n].

def dihedral_sort(nums):
    n = len(nums); zero = nums.index(0)
    targets = set()
    for reflected in (0, 1):
        if all(nums[(zero-i if reflected else zero+i) % n] == i for i in range(n)):
            targets.add((reflected, zero))
    if not targets:
        return -1
    start = (0, 0); seen = {start: 0}; frontier = [start]
    while frontier:
        following = []
        for reflected, shift in frontier:
            if (reflected, shift) in targets:
                return seen[(reflected, shift)]
            rotate = (reflected, (shift+(-1 if reflected else 1)) % n)
            reverse = (1-reflected, (shift+(1-n if reflected else n-1)) % n)
            for state in (rotate, reverse):
                if state not in seen:
                    seen[state] = seen[(reflected, shift)]+1; following.append(state)
        frontier = following
    return -1


def boundary_rows(pid):
    rng = random.Random(20261028*7+pid); rows = []
    def add(args, expected, isolate=False):
        validate(pid, args)
        row = {'args': args, 'expected': expected, 'category': 'boundary-independent-reference'}
        if isolate:
            row['isolate'] = True
        rows.append(row)
    top = 10**9
    if pid == 3891:
        for n in (100000, 99999):
            add([[rng.randint(1, top) for _ in range(n)]], None, True)
            add([[rng.randint(top-1000, top) for _ in range(n)]], None, True)
        add([[top-i for i in range(100000)]], None, True)
        add([[top, 1]*49999+[top]], None, True)  # forced odd peaks, each costs 10**9: 49999*10**9
        add([[1, top]*50000], None, True)
        add([[top]*100000], None, True)
        for n in list(range(6, 21))+[31, 50, 64, 101, 1000, 5000]:
            add([[rng.randint(1, 10) for _ in range(n)]], None)
            add([[rng.randint(top-5, top) for _ in range(n)]], None)
    elif pid == 3896:
        upper = 100000
        add([[rng.randint(99000, upper) for _ in range(100000)]], None, True)
        add([[upper]*100000], None, True)
        add([[99991]*100000], None, True)   # largest prime below 10**5
        add([[2]*100000], None, True)
        add([[31398, 31397]*50000], None, True)  # gap 31397..31469 is the widest below 10**5
        add([[rng.randint(1, upper) for _ in range(100000)]], None, True)
        add([[upper, upper-1, 99989, 99991, 99992]], None)
        for _ in range(12):
            add([[rng.randint(upper-200, upper) for _ in range(rng.randint(1, 300))]], None)
    elif pid == 3897:
        cap = 10000
        def pairs_case(pairs, isolate=False):
            add([[a for a, b in pairs], [b for a, b in pairs]], None, isolate)
        pairs_case([rng.choice(((1, 0), (0, 1), (1, 1))) for _ in range(100000)], True)
        pairs_case([(1, 1)]*100000, True)
        pairs_case([rng.choice(((1, 0), (0, 1))) for _ in range(100000)], True)
        pairs_case([rng.choice(((2, 1), (1, 2), (1, 1), (3, 0), (0, 3))) for _ in range(66666)], True)
        pairs_case([(rng.randint(0, 100), rng.randint(1, 100)) for _ in range(1000)], True)
        pairs_case([(rng.randint(1, cap), rng.randint(0, cap)) for _ in range(20)])
        pairs_case([(rng.randint(1, 4000), rng.randint(0, 1000)) for _ in range(40)])
        pairs_case([(5000, rng.randint(0, 5)) for _ in range(30)])
        pairs_case([(rng.randint(0, 3), 5000) for _ in range(30)])
        pairs_case([(cap, 0)]*10+[(0, cap)]*10)
        pairs_case([(rng.randint(1, 3), rng.randint(0, 3)) if rng.random() < 0.7 else (0, rng.randint(1, 3)) for _ in range(5000)], True)
        for n in range(8, 41):
            pairs_case([(rng.randint(1, 20), rng.randint(0, 20)) if rng.random() < 0.8 else (0, rng.randint(1, 20)) for _ in range(n)])
    elif pid == 3901:
        limit = 50000
        def query_case(nums, p, queries, isolate=False):
            add([nums, p, queries], None, isolate)
        # Multiples of 2p hold the eligible gcd at 2p; odd multiples of p bring it down to p. The
        # odd multiples only ever land on a few hot indices, and later queries often overwrite them,
        # so the answer changes many times. Without other values every element is eligible.
        def toggling(p, n, q, others):
            hot = rng.sample(range(n), 4)
            def even():
                return 2*p*rng.randint(1, limit//(2*p))
            def odd():
                return p*(2*rng.randint(0, (limit//p-1)//2)+1)
            def other():
                while True:
                    value = rng.randint(1, limit)
                    if value % p:
                        return value
            nums = [other() if others and rng.random() < 0.4 else even() for _ in range(n)]
            queries = []
            for _ in range(q):
                if rng.random() < 0.3:
                    queries.append([rng.choice(hot), odd() if rng.random() < 0.3 else even()])
                else:
                    index = rng.randrange(n)
                    queries.append([index, other() if others and index not in hot and rng.random() < 0.4 else even()])
            return nums, queries
        for p, n, q, others in ((6, 50000, 50000, True), (210, 30000, 50000, True), (25000, 50000, 50000, True),
                                (1, 50000, 50000, False), (7, 20000, 20000, False), (2, 18, 3000, False), (3, 300, 3000, True)):
            nums, queries = toggling(p, n, q, others); query_case(nums, p, queries, n*q > 10**6)
        # All-eligible arrays where only the whole array reaches the gcd: products of all but one prime.
        for primes, p in (((2, 3, 5), 1), ((2, 3, 5, 7), 1), ((2, 3, 5, 7, 11), 1), ((2, 3, 5, 7, 11, 13), 1), ((2, 3, 5, 7), 2)):
            full = 1
            for prime in primes:
                full *= prime
            nums = [p*full//prime for prime in primes]
            if max(nums) > limit:
                continue
            queries = [[i, nums[i]] for i in range(len(nums))]+[[rng.randrange(len(nums)), p*rng.choice(primes)] for _ in range(6)]
            queries += [[i, nums[i]] for i in range(len(nums))]+[[0, p]]
            query_case(nums, p, queries)
        for n in (13, 16, 17, 18, 40, 500):
            for p in (1, 2, 3, 30):
                nums = [p*rng.choice((6, 10, 15, 21, 35, 14, 22, 33)) for _ in range(n)]
                queries = [[rng.randrange(n), p*rng.choice((6, 10, 15, 21, 2, 3, 12, 1))] for _ in range(200)]
                query_case(nums, p, queries)
    elif pid == 3905:
        color = 10**6
        def grid_case(n, m, sources, isolate=True):
            add([n, m, sources], None, isolate)
        def random_sources(n, m, count, colors):
            return [[cell//m, cell % m, rng.choice(colors)] for cell in rng.sample(range(n*m), count)]
        grid_case(316, 316, random_sources(316, 316, 1500, (1, 2, 3)))
        grid_case(316, 316, random_sources(316, 316, 40, list(range(color-50, color+1))))
        grid_case(250, 400, [[r, c, 1+(r*7+c*3) % 5] for r in range(0, 250, 10) for c in range(0, 400, 10)])  # even spacing: many ties
        grid_case(400, 250, [[r, c, color-((r+c) % 3)] for r in range(0, 400, 9) for c in range(0, 250, 9)])
        grid_case(1, 100000, random_sources(1, 100000, 300, (5, 6)))
        grid_case(100000, 1, random_sources(100000, 1, 300, (5, 6)))
        grid_case(2, 50000, [[0, 0, 1], [1, 49999, 1], [0, 25000, 2], [1, 24999, 3]])
        grid_case(50000, 2, [[0, 0, 3], [49999, 1, 3], [25000, 0, 2]])
        grid_case(316, 316, [[r, c, (r*316+c) % color+1] for r in range(316) for c in range(316)])  # every cell a source
        grid_case(316, 316, [[0, 0, 7]])
        grid_case(316, 316, [[0, 0, 7], [315, 315, 7], [0, 315, 9], [315, 0, 8]])
        grid_case(100, 1000, random_sources(100, 1000, 5000, (1, color)))
        for n, m in ((9, 11), (12, 12), (20, 30)):
            for count in (2, 5, 20):
                grid_case(n, m, random_sources(n, m, count, (1, 2, 3)), False)
    elif pid == 3909:
        peak = top
        big = 40000*(peak-30000)
        designs = [
            (big, 40000, peak, big, 59999),           # equal sums, different lengths
            (big+1, 40000, peak, big, 59999),
            (big, 40000, peak, big+1, 59999),
            (big+2**32, 49999, peak, big, 50000),     # differ by 2**32: equal under 32-bit wraparound
            (2**31+5, 3, peak-1, 2**31-10, 3),        # sides just across the signed 32-bit limit
            (2**31-10, 3, peak-1, 2**31+5, 3),
            (2**32+7, 5, peak, 7, 2),
            (3*10**13, 50000, peak, 3*10**13, 49999),
            (10, 4, 100, 10, 1),
            (6, 3, 10, 6, 3),
        ]
        for left_total, left_length, height, right_total, right_length in designs:
            add(*bitonic(left_total, left_length, height, right_total, right_length), left_length+right_length > 1000)
        mirror = [peak-50000+i for i in range(1, 50000)]
        add([mirror+[peak]+mirror[::-1]], -1, True)  # a palindrome: sides equal by symmetry
        add([[peak-i for i in range(100000)]], 1, True)   # peak at index 0: right side is the rest
        add([[peak-99999+i for i in range(100000)]], 0, True)   # peak at index n-1
        add([[3, 2, 1]], 1); add([[1, 2, 3]], 0); add([[1, 2, 1]], -1); add([[1, 4, 5, 3, 2]], -1)
        add([[peak-1, peak, peak-2]], 0); add([[peak-2, peak, peak-1]], 1)
        for _ in range(20):
            left_length = rng.randint(0, 30); right_length = rng.randint(max(0, 2-left_length), 30)
            height = rng.randint(10**8, peak)
            def span(length):
                return (length*(length+1)//2, length*(height-1)-length*(length-1)//2)
            lo_l, hi_l = span(left_length); lo_r, hi_r = span(right_length)
            if left_length and right_length and max(lo_l, lo_r) <= min(hi_l, hi_r) and rng.random() < 0.5:
                total = rng.randint(max(lo_l, lo_r), min(hi_l, hi_r)); add(*bitonic(total, left_length, height, total, right_length))
            else:
                add(*bitonic(rng.randint(lo_l, hi_l) if left_length else 0, left_length, height,
                             rng.randint(lo_r, hi_r) if right_length else 0, right_length))
    elif pid == 3915:
        n = 100000
        for k in (1, 2, 50000, 99999, 100000):
            add([list(range(1, n+1)), k], n+(n-k) if k <= n-1 else n, True)   # at most one step up
            add([list(range(n, 0, -1)), k], n+(n-k) if k <= n-1 else n, True)
        add([[n]*n, 1], n, True)
        add([[n, 1]*(n//2), 1], (n//2)*(n+1), True)
        for k in (1, 2, 3, 17, 1000, 50000):
            nums = [rng.randint(1, n) for _ in range(n)]; add([nums, k], max_alternating_sum(nums, k), True)
        for k in (1, 2, 5):
            nums = [rng.randint(1, 3) for _ in range(n)]; add([nums, k], max_alternating_sum(nums, k), True)
        for size in (19, 25, 40, 100, 400):
            for _ in range(3):
                nums = [rng.randint(1, 6) if rng.random() < 0.5 else rng.randint(1, n) for _ in range(size)]
                k = rng.randint(1, size); add([nums, k], max_alternating_sum(nums, k))
    elif pid == 3919:
        bound = 10**9
        def query_case(nums, sources, per_source, isolate=True):
            n = len(nums)
            queries = [[s, rng.randrange(n)] for s in sources for _ in range(per_source)]
            queries += [[s, t] for s in sources for t in (0, n-1, s)]
            add([nums, queries], None, isolate)
        n = 100000
        progression = [-bound+20000*i for i in range(n)]   # every interior index ties and moves left cheaply
        query_case(progression, [0, 1, 50000, 99998, 99999], 19000)
        gaps = [rng.choice((1, 2, 3, 3, 3, 10000, 19999)) for _ in range(n-1)]
        values = [-bound]
        for gap in gaps:
            values.append(values[-1]+gap)
        query_case(values, sorted(rng.sample(range(n), 6)), 16000)
        steep = sorted(rng.sample(range(-bound, bound+1), n))
        query_case(steep, sorted(rng.sample(range(n), 6)), 16000)
        twin = []
        for i in range(n//2):
            twin += [-bound+40000*i, -bound+40000*i+20000]   # equal gaps everywhere: all interior ties
        query_case(twin, [3, 49999, 77777], 30000)
        for size in (16, 31, 200, 2000):
            values = sorted(rng.sample(range(-50, 51), size) if size < 100 else rng.sample(range(-bound, bound), size))
            sources = sorted(rng.sample(range(size), min(size, 8)))
            query_case(values, sources, 40, False)
    elif pid == 3926:
        def text_case(chunks, queries, isolate=True):
            add([chunks, queries], word_counts(chunks, queries), isolate)
        def cut(text, pieces):
            cuts = sorted(set([0, len(text)]+rng.sample(range(1, len(text)), pieces)))
            return [text[a:b] for a, b in zip(cuts, cuts[1:])]
        text = ''.join(rng.choice('ab -') for _ in range(100000))
        words = sorted({piece.strip('-') for token in text.split(' ') for piece in re.split('-{2,}', token) if piece.strip('-')})
        queries = words[:3000]+['ab-ab-ab-ab-ab-ab', 'zzz', 'a-b-a-b-a-b-a-b-a-b-a-b']
        text_case(cut(text, 2000), queries)
        text_case([c for c in text], queries)   # one character per chunk
        text = ''.join(rng.choice('a-') for _ in range(100000))
        words = sorted({piece.strip('-') for piece in re.split('-{2,}', text) if piece.strip('-')}, key=lambda word: (len(word), word))
        text_case(cut(text, 5000), words[:2000]+words[-50:])
        long_word = 'a-'*49999+'a'
        text_case(cut(long_word, 1000), [long_word, 'a'])
        text_case([long_word[:50000], long_word[50000:]], [long_word[:49999], long_word[50000:], 'a'])
        vocabulary = [''.join(rng.choice('xyz') for _ in range(rng.randint(1, 4)))+('-'+rng.choice('pq') if rng.random() < 0.3 else '') for _ in range(400)]
        text = ''
        while len(text) < 99000:
            text += rng.choice(vocabulary)+rng.choice((' ', ' ', '  ', '--', '-- ', ' -'))
        text_case(cut(text, 3000), [rng.choice(vocabulary) for _ in range(12000)])
        text_case(['-'*50000, 'b'*50000], ['b'*50000, 'b'])
        text_case([' '*99999+'q'], ['q', 'q-q'])
        for _ in range(20):
            text = ''.join(rng.choice('xy- ') for _ in range(rng.randint(100, 3000)))
            text_case(cut(text, 20), ['x', 'y', 'x-y', 'xy', 'y-x-y', 'xx-yy'], False)
    elif pid == 3932:
        for k in range(1, 31):
            root = top if k == 1 else 0
            while (root+1)**k <= top:
                root += 1
            power = root**k; below = (root-1)**k
            for l, r in ((0, top), (top, top), (power, power), (power, top), (power+1, top), (max(0, power-1), max(0, power-1)),
                         (below, power), (below+1, power-1), (rng.randint(0, top//2), rng.randint(top//2, top)),
                         (rng.randint(10**6, 10**8), rng.randint(10**8, top))):
                if l <= r:
                    add([l, r, k], kth_roots(l, r, k))
        add([999950884, 999950884, 2], kth_roots(999950884, 999950884, 2))   # 31622**2
        add([999950883, 999950885, 2], kth_roots(999950883, 999950885, 2))
    elif pid == 3934:
        n = 100000; high = 100000
        for alphabet in ((1, 2), (1, 2, 3), (high-3, high-2, high-1, high)):
            nums = [rng.choice(alphabet) for _ in range(n)]; add([nums], smallest_unique_sam(nums), True)
        previous, word = [1], [1, 2]
        while len(word) < n:
            previous, word = word, word+previous
        word = [high if v == 1 else 1 for v in word[:n]]
        add([word], smallest_unique_sam(word), True)   # Fibonacci word
        thue = [1+bin(i).count('1') % 2 for i in range(n)]
        add([thue], smallest_unique_sam(thue), True)
        for period in (3, 1000, 49999, 50000, 50001, 33334):
            add([[high-(i % period) for i in range(n)]], periodic_unique(n, period), True)
        nums = [1+(i % 7) for i in range(n)]; nums[n//2] = 8
        add([nums], smallest_unique_sam(nums), True)
        for size in (100, 500, 3000):
            for alphabet in ((1, 2), (1, 2, 3)):
                nums = [rng.choice(alphabet) for _ in range(size)]; add([nums], smallest_unique_sam(nums))
        for size, period in ((200, 7), (1001, 13), (2048, 1024)):
            add([[1+(i % period) for i in range(size)]], periodic_unique(size, period))
    elif pid == 3937:
        for k in range(2, 101):
            for nums in ([rng.randint(1, top) for _ in range(rng.randint(2, 100))],
                         [rng.randint(1, 2*k) for _ in range(rng.randint(2, 100))],
                         [rng.randint(top-2*k, top) for _ in range(100)],
                         [rng.randint(1, top)],
                         [1]*100 if k % 2 else [k]*99):
                add([nums, k], residue_alternating(nums, k))
        for nums, k in (([1, 1], 100), ([1, 99], 100), ([1]*100, 100), ([2, 1]*50, 100), ([99, 1]*50, 100), ([50, 1, 51], 100)):
            add([nums, k], residue_alternating(nums, k))
    elif pid == 3942:
        for n in (100000, 99999):
            identity = list(range(n))
            for t in (1, 2, n//2, n//2+1, n-2, n-1):
                add([identity[t:]+identity[:t]], dihedral_sort(identity[t:]+identity[:t]), True)
            backward = identity[::-1]
            for u in (0, 1, n//2, n-1):
                add([backward[u:]+backward[:u]], dihedral_sort(backward[u:]+backward[:u]), True)
            swapped = identity[:]; swapped[10], swapped[11] = swapped[11], swapped[10]
            add([swapped], -1, True)
            shuffled = identity[:]; rng.shuffle(shuffled)
            add([shuffled], dihedral_sort(shuffled), True)
        for n in (7, 8, 9, 10, 31, 1000):
            identity = list(range(n))
            for _ in range(6):
                t = rng.randrange(n); base = identity if rng.random() < 0.5 else identity[::-1]
                add([base[t:]+base[:t]], dihedral_sort(base[t:]+base[:t]))
    if pid in (3891, 3896, 3897, 3901, 3905, 3919):
        compute = {3891: lambda a: min_increase(a[0]), 3896: lambda a: alternating_prime_ops(a[0]),
                   3897: lambda a: concatenated_max(*a), 3901: lambda a: good_subsequence_queries(*a),
                   3905: lambda a: flood_fill(*a), 3919: lambda a: move_costs(*a)}[pid]
        for row in rows:
            if row['expected'] is None:
                row['expected'] = compute(row['args'])
    return rows


def build_cases(pid):
    original = CASES[COHORT[pid]].build_cases(pid, include_maximum=True)
    rows = []; seen = set()
    for row in original+boundary_rows(pid):
        key = repr(row['args'])
        if key not in seen:
            seen.add(key); rows.append(dict(row))
    return rows
