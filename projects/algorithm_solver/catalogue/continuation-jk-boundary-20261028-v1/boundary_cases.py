"""Original J/K cases plus boundary cases for the five review gaps.

Each new expected value comes from a method different from the candidates:
closed-form distances on paths and spiders (3820), counting below a bound with
binary search (3821), a Fenwick-tree LIS or an analytic chain (3825), brute
force or closed-form window counts (3835), and per-value net-count combinatorics
(3850). Nothing here reads a candidate source.
"""
from __future__ import annotations
import importlib.util
from math import comb, isqrt
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]/'authored'
IDS = {'j': (3820, 3821, 3825, 3835), 'k': (3850,)}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


J_ORACLES = _load(ROOT/'continuation-j-20261028-v1'/'oracles.py', 'boundary_j_oracles')
K_ORACLES = _load(ROOT/'continuation-k-20261028-v1'/'oracles.py', 'boundary_k_oracles')
_previous = sys.modules.get('oracles'); sys.modules['oracles'] = J_ORACLES
try:
    J_CASES = _load(ROOT/'continuation-j-20261028-v1'/'cases.py', 'boundary_j_cases')
finally:
    if _previous is None:
        sys.modules.pop('oracles', None)
    else:
        sys.modules['oracles'] = _previous


def validate(pid, args):
    if pid in IDS['j']:
        J_ORACLES.validate_domain(pid, args)
    else:
        K_ORACLES.validate(pid, args)


# 3820: distances on a path are index differences; on a spider they add through the center.

def _tree_edges(pairs, rng):
    edges = [[a, b] if rng.random() < 0.5 else [b, a] for a, b in pairs]
    rng.shuffle(edges)
    return edges


def _pythagorean(a, b, c):
    a, b, c = sorted((a, b, c))
    return a*a + b*b == c*c


def path_case(n, rng, positions, shuffle_labels):
    labels = list(range(n))
    if shuffle_labels:
        rng.shuffle(labels)
    x, y, z = (labels[p] for p in positions)
    args = [n, _tree_edges(zip(labels, labels[1:]), rng), x, y, z]
    expected = sum(_pythagorean(abs(i-positions[0]), abs(i-positions[1]), abs(i-positions[2])) for i in range(n))
    return args, expected


def spider_case(legs, rng, targets):
    """legs: leg lengths; targets: three (leg, depth) pairs with depth >= 1."""
    n = 1+sum(legs); labels = list(range(n)); rng.shuffle(labels)
    place = [(None, 0)]; pairs = []; label = 1
    for leg, length in enumerate(legs):
        previous = 0
        for depth in range(1, length+1):
            place.append((leg, depth)); pairs.append((labels[previous], labels[label])); previous = label; label += 1
    index = {spot: i for i, spot in enumerate(place)}
    def dist(u, v):
        (lu, du), (lv, dv) = u, v
        if lu is None or lv is None or lu != lv:
            return du+dv
        return abs(du-dv)
    x, y, z = (labels[index[t]] for t in targets)
    expected = sum(_pythagorean(*(dist(spot, t) for t in targets)) for spot in place)
    return [n, _tree_edges(pairs, rng), x, y, z], expected


# 3821: the n-th number with k ones is the least y with count(<= y) >= n.

def count_below(bound, k):
    total = ones = 0
    for bit in range(bound.bit_length()-1, -1, -1):
        if bound >> bit & 1:
            if 0 <= k-ones <= bit:
                total += comb(bit, k-ones)
            ones += 1
            if ones > k:
                break
    return total


def nth_with_k_ones(n, k):
    low, high = 0, 2**50-1
    while low < high:
        middle = (low+high)//2
        if count_below(middle+1, k) >= n:
            high = middle
        else:
            low = middle+1
    return low


# 3825: per-bit strictly increasing subsequence through a Fenwick prefix maximum.

def longest_and_lis(nums):
    ranks = {v: i+1 for i, v in enumerate(sorted(set(nums)))}; size = len(ranks); best = 0
    for bit in range(30):
        tree = [0]*(size+1)
        for v in nums:
            if v >> bit & 1:
                i = ranks[v]-1; length = 0
                while i > 0:
                    length = max(length, tree[i]); i -= i & -i
                length += 1; best = max(best, length); i = ranks[v]
                while i <= size:
                    if tree[i] < length:
                        tree[i] = length
                    i += i & -i
    return best


# 3835: cost never decreases as a window grows, so each left end has a single cut-off.

def count_windows_brute(nums, k):
    total = 0
    for left in range(len(nums)):
        low = high = nums[left]
        for right in range(left, len(nums)):
            low = min(low, nums[right]); high = max(high, nums[right])
            if (high-low)*(right-left+1) > k:
                break
            total += 1
    return total


def windows_up_to(n, longest):
    return sum(n-length+1 for length in range(1, min(n, longest)+1))


def spike_count(n, spike, k, base=1, peak=10**9):
    left, right = spike, n-1-spike
    longest = k//(peak-base) if peak > base else n
    containing = sum(max(0, min(spike, n-length)-max(0, spike-length+1)+1) for length in range(1, min(n, longest)+1))
    return left*(left+1)//2 + right*(right+1)//2 + containing


# 3850: elements of one value contribute a net count m = pluses - minuses.

VECTORS = {2: (1, 0, 0), 3: (0, 1, 0), 4: (2, 0, 0), 5: (0, 0, 1), 6: (1, 1, 0)}


def net_ways(count, net):
    return sum(comb(count, plus)*comb(count-plus, plus-net) for plus in range(max(0, net), count+1) if 0 <= plus-net <= count-plus)


def count_sequences(nums, k):
    target = []
    for p in (2, 3, 5):
        power = 0
        while k % p == 0:
            power += 1; k //= p
        target.append(power)
    if k != 1:
        return 0
    c = {v: nums.count(v) for v in range(1, 7)}
    e2, e3, e5 = target
    if abs(e5) > c[5]:
        return 0
    total = 0
    for m6 in range(-c[6], c[6]+1):
        m3 = e3-m6
        if abs(m3) > c[3]:
            continue
        for m4 in range(-c[4], c[4]+1):
            m2 = e2-2*m4-m6
            if abs(m2) > c[2]:
                continue
            total += net_ways(c[2], m2)*net_ways(c[3], m3)*net_ways(c[4], m4)*net_ways(c[5], e5)*net_ways(c[6], m6)
    return total*3**c[1]


def _random_reachable_k(nums, rng):
    exponents = [0, 0, 0]
    for x in nums:
        sign = rng.choice((-1, 0, 1))
        for i, d in enumerate(VECTORS.get(x, (0, 0, 0))):
            exponents[i] += sign*d
    if min(exponents) < 0:
        return 1
    k = 2**exponents[0]*3**exponents[1]*5**exponents[2]
    return k if k <= 10**15 else 1


def boundary_rows(pid):
    rng = random.Random(20261028*7+pid); rows = []
    def add(args, expected, isolate=False):
        validate(pid, args)
        row = {'args': args, 'expected': expected, 'category': 'boundary-independent-reference'}
        if isolate:
            row['isolate'] = True
        rows.append(row)
    if pid == 3820:
        n = 100000
        # (46500, 62000, 77500) is a triple whose squares leave the signed 32-bit range unequally.
        for positions, shuffled in (((36000, 48000, 60000), False), ((46500, 62000, 77500), False), ((0, 99999, 50000), True), ((12, 99990, 70001), True)):
            add(*path_case(n, rng, positions, shuffled), isolate=True)
        add(*spider_case([33333, 33333, 33333], rng, [(0, 30000), (1, 20000), (2, 33333)]), isolate=True)
        add(*spider_case([60000, 39999], rng, [(0, 36000), (0, 60000), (1, 39999)]), isolate=True)
        for size in (4, 5, 30, 200, 1500):
            add(*path_case(size, rng, rng.sample(range(size), 3), True))
    elif pid == 3821:
        for k in range(1, 51):
            largest = comb(50, k)
            for n in sorted({1, largest, max(1, comb(49, k)), min(largest, comb(49, k)+1), rng.randint(1, largest)}):
                add([n, k], nth_with_k_ones(n, k))
        for n in (2**31-1, 2**31, 2**32+1, 10**13+7, comb(50, 25)-1):
            add([n, 25], nth_with_k_ones(n, 25))
    elif pid == 3825:
        high = 2**29
        add([[high+1, high+2, high+4, high+8]], 4)
        add([[high+(1 << j) for j in range(29)]], 29)
        add([[high+i for i in range(100000)]], 100000, isolate=True)
        add([[10**9-i for i in range(100000)]], 1, isolate=True)
        add([[939524096+600*i for i in range(100000)]], 100000, isolate=True)
        for _ in range(8):
            nums = [rng.randrange(high, 10**9+1) if rng.random() < 0.4 else rng.randrange(0, 10**9+1) for _ in range(3000)]
            add([nums], longest_and_lis(nums))
    elif pid == 3835:
        n, peak = 100000, 10**9
        for m in (1, 5, 1000):
            nums = [1]*n; nums[n//2] = peak; k = (peak-1)*m
            add([nums, k], spike_count(n, n//2, k), isolate=True)
        for k in ((peak-1)*50000, (peak-1)*50000-1, (peak-1)*2):
            add([[1, peak]*50000, k], 100000+windows_up_to(100000, k//(peak-1))-windows_up_to(100000, 1), isolate=True)
        longest = (1+isqrt(1+4*10**9))//2  # largest length with length*(length-1) <= 10**9
        add([list(range(1, 100001)), 10**9], windows_up_to(100000, longest), isolate=True)
        for size in (200, 600, 1500):
            for _ in range(2):
                nums = [rng.choice((1, 2, 10**9, rng.randrange(1, 10**9+1))) for _ in range(size)]
                k = rng.randrange(0, 10**9*size)
                add([nums, k], count_windows_brute(nums, k))
    elif pid == 3850:
        add([[4]*19, 4**19], count_sequences([4]*19, 4**19))
        add([[6]*19, 6**19], count_sequences([6]*19, 6**19))
        add([[5]*19, 5**19], count_sequences([5]*19, 5**19))
        add([[2]*10+[4]*9, 2**28], count_sequences([2]*10+[4]*9, 2**28))
        add([[4]*8+[5]*11, 10**15], count_sequences([4]*8+[5]*11, 10**15))
        add([[6]*19, 6], count_sequences([6]*19, 6))
        for _ in range(16):
            nums = [rng.randint(1, 6) for _ in range(19)]
            k = _random_reachable_k(nums, rng) if rng.random() < 0.8 else rng.choice((1, 7, 10**15, 2**49))
            add([nums, k], count_sequences(nums, k))
    return rows


def build_cases(pid):
    original = J_CASES.build_cases(pid, include_maximum=True) if pid in IDS['j'] else K_ORACLES.build_cases(pid)
    return [dict(row) for row in original]+boundary_rows(pid)
