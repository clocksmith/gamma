"""Original L/M cases plus boundary cases for the eleven review gaps.

Each new expected value comes from a method different from the cohorts'
references: a block-concatenation doubling recurrence (3855), a left-end sweep
over first and m-th occurrences (3859), construction plus a right-to-left exact
scan that stops once the suffix product passes the total (3862), inclusion-
exclusion digit-sum counts plus explicit monotone enumeration (3869), a
two-pointer window feasibility check (3872), bipartite row/column components
(3873), a parity closed form (3876), meet-in-the-middle subset tables (3877),
leftmost-maximum submask spans (3878), an exact binomial (3881) and a segment
tree over event ids (3885). Boundary rows that repeat an original row are
dropped. Nothing here reads a candidate source.
"""
from __future__ import annotations
import importlib.util
from collections import deque
from math import comb
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]/'authored'
IDS = {'l': (3855, 3859, 3862, 3869), 'm': (3872, 3873, 3876, 3877, 3878, 3881, 3885)}
MOD = 10**9+7


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


L_ORACLES = _load(ROOT/'continuation-l-20261028-v1'/'oracles.py', 'boundary_l_oracles')
M_ORACLES = _load(ROOT/'continuation-m-20261028-v1'/'oracles.py', 'boundary_m_oracles')
_previous = sys.modules.get('oracles'); sys.modules['oracles'] = L_ORACLES
try:
    L_CASES = _load(ROOT/'continuation-l-20261028-v1'/'cases.py', 'boundary_l_cases')
finally:
    if _previous is None:
        sys.modules.pop('oracles', None)
    else:
        sys.modules['oracles'] = _previous


def validate(pid, args):
    if pid in IDS['l']:
        L_ORACLES.validate_domain(pid, args)
    else:
        M_ORACLES.validate(pid, args)


# 3855: a block of length a followed by a block of length b has total T(a)*10^b*N(b) + T(b)*N(a).

def digit_tuple_total(l, r, k):
    choices = r-l+1; digit_sum = (l+r)*choices//2

    def join(high, low):
        t1, n1, p1 = high; t2, n2, p2 = low
        return ((t1*p2 % MOD*n2+t2*n1) % MOD, n1*n2 % MOD, p1*p2 % MOD)
    total, block = (0, 1, 1), (digit_sum % MOD, choices % MOD, 10)
    while k:
        if k & 1:
            total = join(total, block)
        block = join(block, block); k >>= 1
    return total[0]


# 3859: from a left end, the first k distinct values fix the window; it must end before the (k+1)-th
# distinct value's first position and at or after every one of the k values' m-th occurrence.

def count_k_distinct_m(nums, k, m):
    n = len(nums); size = 1
    while size < n:
        size *= 2
    count = [0]*(2*size); high = [-1]*(2*size); infinity = n+1
    positions = {}
    for i, v in enumerate(nums):
        positions.setdefault(v, []).append(i)
    pointer = {v: len(p) for v, p in positions.items()}

    def put(p, marked, value):
        p += size; count[p] = marked; high[p] = value; p //= 2
        while p:
            count[p] = count[2*p]+count[2*p+1]; high[p] = max(high[2*p], high[2*p+1]); p //= 2

    def kth(rank):  # position of the rank-th marked leaf, or n if there are fewer
        if count[1] < rank:
            return n
        p = 1
        while p < size:
            if count[2*p] >= rank:
                p = 2*p
            else:
                rank -= count[2*p]; p = 2*p+1
        return p-size

    def prefix_high(right):  # max over leaves 0..right
        lo, hi, best = size, right+size+1, -1
        while lo < hi:
            if lo & 1:
                best = max(best, high[lo]); lo += 1
            if hi & 1:
                hi -= 1; best = max(best, high[hi])
            lo //= 2; hi //= 2
        return best
    total = 0
    for left in range(n-1, -1, -1):
        v = nums[left]; occ = positions[v]; old = pointer[v]
        if old < len(occ):
            put(occ[old], 0, -1)
        pointer[v] = old-1; mth = occ[old-1+m-1] if old-1+m-1 < len(occ) else infinity
        put(left, 1, mth)
        if count[1] < k:
            continue
        end_first_k = kth(k); stop = kth(k+1); need = prefix_high(end_first_k)
        if need < stop:
            total += stop-need
    return total


# 3862: left sums strictly increase and suffix products never increase, so at most one index balances.

def balanced_scan(nums):
    total = sum(nums); n = len(nums); product = 1; left = total; found = []
    for i in range(n-1, -1, -1):
        left -= nums[i]
        if left == product:
            found.append(i)
        product *= nums[i]
        if product > total:
            break
    return min(found) if found else -1


# 3869: numbers whose digit sum is good, counted by inclusion-exclusion, plus monotone numbers that are not.

def _monotone(number):
    digits = str(number)
    return all(a < b for a, b in zip(digits, digits[1:])) or all(a > b for a, b in zip(digits, digits[1:]))


def _strings_with_sum(length, target):
    if target < 0:
        return 0
    if length == 0:
        return int(target == 0)
    return sum((-1)**j*comb(length, j)*comb(target-10*j+length-1, length-1) for j in range(length+1) if target-10*j >= 0)


def _sum_counts_to(bound, target):  # integers 0..bound with digit sum target
    digits = list(map(int, str(bound))); total = 0; prefix = 0
    for i, top in enumerate(digits):
        rest = len(digits)-i-1
        for d in range(top):
            total += _strings_with_sum(rest, target-prefix-d)
        prefix += top
    return total+int(prefix == target)


def _monotone_numbers():
    found = set(range(10))
    pending = deque(range(1, 10))
    while pending:  # strictly increasing: append a larger digit
        x = pending.popleft()
        for d in range(x % 10+1, 10):
            found.add(x*10+d); pending.append(x*10+d)
    pending = deque(range(1, 10))
    while pending:  # strictly decreasing: append a smaller digit
        x = pending.popleft()
        for d in range(0, x % 10):
            found.add(x*10+d); pending.append(x*10+d)
    return sorted(found)


MONOTONE = _monotone_numbers()
GOOD_SUMS = [s for s in range(0, 9*16+1) if _monotone(s)]


def fancy_to(bound):  # integers 1..bound
    if bound <= 0:
        return 0
    by_sum = sum(_sum_counts_to(bound, s) for s in GOOD_SUMS)-1  # 0 has digit sum 0
    extra = sum(1 for x in MONOTONE if 1 <= x <= bound and not _monotone(sum(map(int, str(x)))))
    return by_sum+extra


def count_fancy(l, r):
    return fancy_to(r)-fancy_to(l-1)


# 3872: a window can be fixed by one change iff its non-constant difference changes sit next to one
# position; feasible windows are closed under shrinking, so two pointers find the longest.

def longest_one_change(a):
    n = len(a); diff = [a[i+1]-a[i] for i in range(n-1)]
    change = [diff[j] != diff[j+1] for j in range(n-2)]
    prefix = [0]
    for flag in change:
        prefix.append(prefix[-1]+flag)
    following = [n]*(n+1); preceding = [-1]*(n+1)
    for j in range(n-3, -1, -1):
        following[j] = j if change[j] else following[j+1]
    last = -1
    for j in range(n-2):
        if change[j]:
            last = j
        preceding[j] = last

    def constant(x, y):  # diffs x..y inclusive share one value (empty or single is constant)
        return y-x < 1 or prefix[y]-prefix[x] == 0

    def fixable(c, l, r):
        if c == l:
            return constant(l+1, r-1)
        if c == r:
            return constant(l, r-2)
        step = None
        if c-1 > l:
            if not constant(l, c-2):
                return False
            step = diff[c-2]
        if c+1 < r:
            if not constant(c+1, r-1) or (step is not None and diff[c+1] != step):
                return False
            step = diff[c+1]
        gap = a[c+1]-a[c-1]
        return gap % 2 == 0 if step is None else gap == 2*step

    def feasible(l, r):
        if r-l < 2 or constant(l, r-1):
            return True
        first = following[l]; final = preceding[r-2]
        return any(fixable(c, l, r) for c in range(max(l, final), min(r, first+2)+1))
    best = left = 0
    for right in range(n):
        while not feasible(left, right):
            left += 1
        best = max(best, right-left+1)
    return best


# 3873: components of the bipartite row/column graph; an added point joins the two largest.

def activation_by_components(points):
    rows, cols = {}, {}
    for x, y in points:
        rows.setdefault(x, []).append(y); cols.setdefault(y, []).append(x)
    seen_x, seen_y, sizes = set(), set(), []
    for x0 in rows:
        if x0 in seen_x:
            continue
        seen_x.add(x0); queue = [('x', x0)]; size = 0
        while queue:
            side, key = queue.pop()
            if side == 'x':
                size += len(rows[key])
                for y in rows[key]:
                    if y not in seen_y:
                        seen_y.add(y); queue.append(('y', y))
            else:
                for x in cols[key]:
                    if x not in seen_x:
                        seen_x.add(x); queue.append(('x', x))
        sizes.append(size)
    sizes.sort(reverse=True)
    return 1+sum(sizes[:2])


# 3876: all even succeeds unchanged; otherwise every even needs a smaller odd, i.e. the minimum is odd.

def uniform_parity(nums):
    return all(x % 2 == 0 for x in nums) or min(nums) % 2 == 1


# 3877: meet in the middle over explicit subset enumerations of each half.

def _half_table(values):
    xors, kept = [0], [0]
    for v in values:
        xors = xors+[x ^ v for x in xors]; kept = kept+[c+1 for c in kept]
    best = {}
    for x, c in zip(xors, kept):
        if best.get(x, -1) < c:
            best[x] = c
    return best


def min_removals_xor(nums, target):
    half = len(nums)//2; first = _half_table(nums[:half]); second = _half_table(nums[half:])
    kept = max((c+second[x ^ target] for x, c in first.items() if x ^ target in second), default=-1)
    return -1 if kept < 0 else len(nums)-kept


# 3878: a window's OR equals one of its values iff every value is a submask of its maximum; count each
# window at its leftmost maximum.

def count_or_member(nums):
    n = len(nums); left_ge = [-1]*n; stack = []
    for j, v in enumerate(nums):
        while stack and nums[stack[-1]] < v:
            stack.pop()
        left_ge[j] = stack[-1] if stack else -1; stack.append(j)
    last = [-1]*31; left_bad = [-1]*n
    for j, v in enumerate(nums):
        left_bad[j] = max((last[b] for b in range(31) if not v >> b & 1), default=-1)
        for b in range(31):
            if v >> b & 1:
                last[b] = j
    first = [n]*31; right_bad = [n]*n
    for j in range(n-1, -1, -1):
        v = nums[j]
        right_bad[j] = min((first[b] for b in range(31) if not v >> b & 1), default=n)
        for b in range(31):
            if v >> b & 1:
                first[b] = j
    return sum((j-max(left_ge[j], left_bad[j]))*(right_bad[j]-j) for j in range(n))


# 3881: the person at pos may face either way; exactly k of the other n-1 are visible.

def visible_assignments(n, pos, k):
    return 2*comb(n-1, k) % MOD


# 3885: a max segment tree over compressed ids holds (priority, -id) for each active event.

class EventTree:
    def __init__(self, events, extra_ids=()):
        ids = sorted({i for i, _ in events} | set(extra_ids)); self.index = {v: j for j, v in enumerate(ids)}
        self.size = 1
        while self.size < len(ids):
            self.size *= 2
        self.tree = [None]*(2*self.size); self.priority = {}
        for i, p in events:
            self.priority[i] = p; self.tree[self.size+self.index[i]] = (p, -i)
        for j in range(self.size-1, 0, -1):
            self.tree[j] = self._better(self.tree[2*j], self.tree[2*j+1])

    @staticmethod
    def _better(a, b):
        if a is None:
            return b
        if b is None:
            return a
        return a if a > b else b

    def _set(self, event, value):
        j = self.size+self.index[event]; self.tree[j] = value; j //= 2
        while j:
            self.tree[j] = self._better(self.tree[2*j], self.tree[2*j+1]); j //= 2

    def update(self, event, priority):
        self.priority[event] = priority; self._set(event, (priority, -event))

    def poll(self):
        top = self.tree[1]
        if top is None:
            return -1
        event = -top[1]; del self.priority[event]; self._set(event, None)
        return event


def event_trace(args):
    operations, params = args; tree = EventTree(params[0][0]); out = [None]
    for name, row in zip(operations[1:], params[1:]):
        if name == 'updatePriority':
            tree.update(*row); out.append(None)
        else:
            out.append(tree.poll())
    return out


def independent(pid, args):
    validate(pid, args)
    if pid == 3855:
        return digit_tuple_total(*args)
    if pid == 3859:
        return count_k_distinct_m(*args)
    if pid == 3862:
        return balanced_scan(args[0])
    if pid == 3869:
        return count_fancy(*args)
    if pid == 3872:
        return longest_one_change(args[0])
    if pid == 3873:
        return activation_by_components(args[0])
    if pid == 3876:
        return uniform_parity(args[0])
    if pid == 3877:
        return min_removals_xor(*args)
    if pid == 3878:
        return count_or_member(args[0])
    if pid == 3881:
        return visible_assignments(*args)
    return event_trace(args)


def matches(pid, args, result):
    """M owner check kept from the L/M lane: recompute with the cohort reference, or this module's
    independent reference where the cohort reference declines the input as over budget."""
    try:
        wanted = M_ORACLES.expected(pid, args)
    except ValueError:
        wanted = independent(pid, args)
    return M_ORACLES.exact(result, wanted)


# Generators for the boundary rows.

def _event_trace_case(rng, events, calls, priority_range, update_share, reuse_share=0.3, distinct_ids=True):
    ids = rng.sample(range(1, 10**9+1), events) if distinct_ids else list(range(1, events+1))
    low, high = priority_range
    rows = [[i, rng.randint(low, high)] for i in ids]
    active = [i for i, _ in rows]; where = {i: j for j, i in enumerate(active)}
    history = {i: [p] for i, p in rows}; tree = EventTree(rows); operations = ['EventManager']; params = [[rows]]
    for _ in range(calls):
        if active and rng.random() < update_share:
            event = active[rng.randrange(len(active))]; roll = rng.random()
            if roll < reuse_share/3:
                priority = tree.priority[event]  # same priority again
            elif roll < 2*reuse_share/3:
                priority = rng.choice(history[event])  # an earlier priority
            elif roll < reuse_share and tree.tree[1] is not None:
                priority = tree.tree[1][0]  # tie with the current top
            else:
                priority = rng.randint(low, high)
            history[event].append(priority); tree.update(event, priority)
            operations.append('updatePriority'); params.append([event, priority])
        else:
            polled = tree.poll(); operations.append('pollHighest'); params.append([])
            if polled != -1:
                j = where.pop(polled); tail = active.pop()
                if tail != polled:
                    active[j] = tail; where[tail] = j
    return [operations, params]


def _points_component(rng, size, x_base, y_base, spread):
    """A connected point set: each new point shares a row or a column with an earlier one."""
    points = [(x_base, y_base)]; seen = set(points); xs = [x_base]; ys = [y_base]
    while len(points) < size:
        if rng.random() < 0.5:
            x = rng.choice(xs); y = y_base+rng.randrange(spread)
        else:
            y = rng.choice(ys); x = x_base+rng.randrange(spread)
        if (x, y) not in seen:
            seen.add((x, y)); points.append((x, y)); xs.append(x); ys.append(y)
    return points


def _components_case(rng, sizes, spread_factor=3):
    points = []; offset = -10**9
    for size in sizes:
        spread = max(2, size*spread_factor//2+2)
        points += _points_component(rng, size, offset, offset, spread)
        offset += spread+1+rng.randrange(1000)
        if offset > 10**9:
            raise ValueError('component layout exceeds coordinate domain')
    rng.shuffle(points)
    expected = 1+sum(sorted(sizes, reverse=True)[:2])
    return [[list(p) for p in points]], expected


def _arith_blocks(rng, n, block_range, step_range, noise=0.0):
    a = []; value = rng.randint(40000, 60000)
    while len(a) < n:
        length = rng.randint(*block_range); step = rng.randint(*step_range)
        for _ in range(length):
            if len(a) == n:
                break
            if not 1 <= value <= 100000:
                step = -step; value = min(100000, max(1, value))
            a.append(value); value += step
        if rng.random() < noise and a:
            a[-1] = rng.randint(1, 100000)
    return a


def boundary_rows(pid):
    rng = random.Random(20261028*11+pid); rows = []

    def add(args, expected, isolate=False):
        validate(pid, args)
        row = {'args': args, 'expected': expected, 'category': 'boundary-independent-reference'}
        if isolate:
            row['isolate'] = True
        rows.append(row)
    if pid == 3855:
        for l in range(10):
            for r in range(l, 10):
                ks = {5, 10, 10**9, rng.randint(5, 60), rng.randint(61, 10**9)}
                for k in sorted(ks):
                    add([l, r, k], digit_tuple_total(l, r, k))
        special = [6, 7, 8, 9, 11, 15, 16, 17, 18, 19, 20, 21, 31, 32, 33, 52, 53, 54, 63, 64, 65, 100, 1000, 12345,
                   10**5, 10**6+3, 2**29, 2**29+1, 999999937, 10**9-1, 500000003]
        for l, r in ((0, 9), (1, 9), (3, 7), (9, 9), (0, 1), (2, 8), (4, 5)):
            for k in special:
                add([l, r, k], digit_tuple_total(l, r, k))
    elif pid == 3859:
        n = 100000
        labels = rng.sample(range(1, n+1), n//2); pairs = [v for v in labels for _ in range(2)]
        for k, m in ((1000, 2), (50000, 2), (1, 2), (25000, 1), (777, 3)):
            # Every value appears twice: m=2 counts windows of whole pairs (D-k+1), m=3 never holds, m=1 is general.
            add([pairs, k, m], count_k_distinct_m(pairs, k, m), isolate=True)
        perm = rng.sample(range(1, n+1), n)
        for k, m in ((n, 1), (50000, 1), (99999, 1), (3, 2)):
            add([perm, k, m], count_k_distinct_m(perm, k, m), isolate=True)
        for top, k, m in ((30000, 5000, 1), (1000, 200, 2), (100000, 10, 1), (50, 25, 100), (20000, 15000, 1), (5000, 2500, 3)):
            nums = [rng.randint(1, top) for _ in range(n)]
            add([nums, k, m], count_k_distinct_m(nums, k, m), isolate=True)
        base = rng.sample(range(1, 10**5+1), 20000); periodic = base*5
        for k, m in ((20000, 3), (20000, 5), (19999, 1), (5000, 1)):
            add([periodic, k, m], count_k_distinct_m(periodic, k, m), isolate=True)
        for _ in range(40):
            size = rng.randint(200, 2000); top = rng.choice((5, 50, size//2, size))
            nums = [rng.randint(1, top) for _ in range(size)]
            add([nums, rng.randint(1, min(size, top)), rng.randint(1, 4)], None)
            rows[-1]['expected'] = count_k_distinct_m(*rows[-1]['args'])
    elif pid == 3862:
        big = 10**9

        def planted(prefix, middle, suffix, isolate=False):
            # Left sum equals suffix product at len(prefix); monotonicity makes it the only balanced index.
            nums = prefix+[middle]+suffix
            if sum(prefix) != _product(suffix):
                raise AssertionError('not a planted balance')
            expected = balanced_scan(nums)
            if expected != len(prefix):
                raise AssertionError('scan disagrees with the planted index')
            add([nums], expected, isolate)

        def missed(nums, isolate=False):
            add([nums], balanced_scan(nums), isolate)
        planted([big]*50000, 7, [50000, big], True)  # left sum 5*10**13
        planted([big]*99997, 3, [99997, big], True)  # n = 100000, left sum near 10**14
        planted([big, big, 147483648], 9, [2**16, 2**15])  # left sum exactly 2**31
        planted([big, big], 5, [big, 2])  # product 2*10**9 above 2**31
        planted([1]*99990, 4, [2, 9, 5, 11, 101], True)  # left sum of ones equals 99990
        planted([big]*1000, big, [125, 8, big], True)
        missed([big]*4+[294967302, 5, 2, 3])  # left sum 2**32+6 against product 6: int32 wrap would match
        missed([big]*4+[294967302, 5, 2, 3]+[1]*99990, True)
        missed([big]*50000+[1, 7, 50000, big], True)  # left sum one above the product
        missed([big]*49999+[big-1, 7, 50000, big], True)  # left sum one below the product
        missed([3]+[big]*99999, True)  # huge suffix products throughout
        missed([big]*99999+[2], True)
        missed([1, big])
        for _ in range(30):
            factors = [rng.choice((1, 2, 3, 7, 10, 999, 65536, 10**6, rng.randint(1, big))) for _ in range(rng.randint(0, 4))]
            total = _product(factors)
            if total > 10**14 or total < 1:
                continue
            length = rng.randint(-(-total//big), min(total, 3000))
            cuts = sorted(rng.sample(range(1, total), length-1)) if length > 1 else []
            prefix = [b-a for a, b in zip([0]+cuts, cuts+[total])]
            if max(prefix) > big:
                continue
            planted(prefix, rng.randint(1, big), factors)
    elif pid == 3869:
        windows = [(1, 10**15), (10**15-1, 10**15), (9876543210, 10**15), (123456789, 9876543210), (1, 9876543210)]
        windows += [(1, 10**k) for k in range(1, 16)]+[(10**k, 10**(k+1)-1) for k in range(0, 15)]
        windows += [(10**k-rng.randint(1, 10**(k-1)), 10**k+rng.randint(1, 10**k)) for k in range(2, 15)]
        long_monotone = [x for x in MONOTONE if x >= 10**5]
        for x in rng.sample(long_monotone, 40):
            width = rng.choice((101, 999, 10**4, 10**6, 10**9))
            windows += [(max(1, x-width), min(10**15, x+width)), (x, x), (x, x+1), (max(1, x-1), x)]
        for _ in range(40):
            a, b = sorted(rng.sample(range(1, 16), 2))
            l = rng.randint(10**(a-1), 10**a); r = rng.randint(max(l, 10**(b-1)), 10**b)
            windows.append((l, min(r, 10**15)))
        for l, r in windows:
            add([l, r], count_fancy(l, r))
    elif pid == 3872:
        n = 100000

        def heavy(a):
            add([a], longest_one_change(a), isolate=True)
        line = list(range(1, n+1)); one = line[:]; one[50000] = 7; heavy(one)
        down = line[::-1]; down[0] = 5; heavy(down)
        two = line[:]; two[30000] = 3; two[70000] = 99999; heavy(two)
        flat = [7]*n; flat[12345] = 8; flat[99998] = 9; heavy(flat)
        odd_join = [1+2*i for i in range(40000)]+[50]+[80002+2*i for i in range(9999)]; heavy(odd_join)
        even_join = [1+2*i for i in range(40000)]+[50]+[80001+2*i for i in range(9999)]+[3]*50000; heavy(even_join)
        heavy([1, 3]*50000)
        heavy([1, 100000]*50000)
        heavy([rng.randint(1, 3) for _ in range(n)])
        for blocks, steps, noise in (((1, 2000), (-50, 50), 0.3), ((2, 40), (-3, 3), 0.5), ((500, 30000), (-2, 2), 0.9), ((3, 9), (0, 1), 0.2)):
            heavy(_arith_blocks(rng, n, blocks, steps, noise))
        for _ in range(30):
            size = rng.randint(4, 3000)
            a = _arith_blocks(rng, size, (1, max(2, size//3)), (-5, 5), 0.5)
            add([a], longest_one_change(a))
    elif pid == 3873:
        def components(sizes):
            args, expected = _components_case(rng, sizes)
            if activation_by_components(args[0]) != expected:
                raise AssertionError('construction and component search disagree')
            add(args, expected, isolate=True)
        components([40000, 30000, 20000, 10000])
        components([50000, 50000])
        components([99999, 1])
        components([2]*50000)
        sizes = []
        while sum(sizes) < 99000:
            sizes.append(rng.randint(1, 500))
        components(sizes)
        components([33333, 33333, 33334])
        stair = [[i, i] for i in range(50000)]+[[i, i+1] for i in range(50000)]; rng.shuffle(stair)
        add([stair], activation_by_components(stair), isolate=True)
        grid = [[x*7919-10**9, y*104729-10**9] for x in range(316) for y in range(316)]
        grid += [[5*10**8+i, 5*10**8+i] for i in range(100000-len(grid))]; rng.shuffle(grid)
        add([grid], activation_by_components(grid), isolate=True)
        for pool in (40000, 60000, 150000, 400000):
            xs = rng.sample(range(-10**9, 10**9+1), pool); ys = rng.sample(range(-10**9, 10**9+1), pool); seen = set()
            while len(seen) < 100000:
                seen.add((rng.choice(xs), rng.choice(ys)))
            points = [list(p) for p in seen]; rng.shuffle(points)
            add([points], activation_by_components(points), isolate=True)
        for _ in range(30):
            g = rng.randint(3, 60); points = rng.sample([(x, y) for x in range(g) for y in range(g)], rng.randint(13, min(g*g, 400)))
            add([[list(p) for p in points]], activation_by_components(points))
    elif pid == 3876:
        n, top = 100000, 10**9

        def evens(count, low):
            return [2*v for v in rng.sample(range(low//2+1, top//2+1), count)]

        def odds(count, low):
            return [2*v+1 for v in rng.sample(range(low//2+1, (top-1)//2+1), count)]

        def heavy(nums):
            rng.shuffle(nums); add([nums], uniform_parity(nums), isolate=True)
        heavy([1]+evens(n-1, 2))  # one odd, the minimum
        heavy([2]+odds(n-1, 3))  # minimum even among odds
        heavy([3]+evens(n-2, 4)+[1000])
        heavy(evens(n-1, 2)+[999999999])  # one odd, not the minimum
        heavy([500000001]+odds(40000, 500000002)+evens(n-40001, 500000002))
        heavy([500000000]+odds(40000, 500000002)+evens(n-40001, 500000002))
        heavy(odds(50000, 2)+evens(50000, 2))
        heavy(rng.sample(range(1, top+1), n))
        heavy(rng.sample(range(2, top+1), n))
        for _ in range(40):
            nums = rng.sample(range(1, rng.choice((40, 1000, top))+1), rng.randint(1, 30))
            add([nums], uniform_parity(nums))
    elif pid == 3877:
        def case(nums, target):
            add([nums, target], min_removals_xor(nums, target))
        for _ in range(8):
            nums = [rng.randint(0, 10000) for _ in range(40)]; case(nums, rng.randint(0, 10000))
        nums = [rng.randint(0, 5000) for _ in range(40)]; whole = 0  # values below 2**13 keep the total XOR in domain
        for v in nums:
            whole ^= v
        case(nums, whole); case(nums, 0)
        case([2*rng.randint(0, 5000) for _ in range(40)], 9999)  # odd target, even values: -1
        case([rng.choice((1024, 2048, 3072, 4096)) for _ in range(40)], 7168)
        case([rng.choice((1024, 2048, 3072, 4096)) for _ in range(40)], 1)
        case([0]*20+[rng.randint(1, 10000) for _ in range(20)], rng.randint(0, 10000))
        case([10000]*39+[1], 1)
        case([1 << rng.randrange(13) for _ in range(40)], 8191)
        case([rng.randint(9000, 10000) for _ in range(40)], 10000)
        for size in (19, 21, 33, 39):
            case([rng.randint(0, 10000) for _ in range(size)], rng.randint(0, 10000))
    elif pid == 3878:
        n = 100000

        def heavy(nums):
            add([nums], count_or_member(nums), isolate=True)
        heavy([rng.randint(0, 10**9) for _ in range(n)])
        heavy([rng.randint(0, 7) for _ in range(n)])
        masks = [rng.randrange(1 << 29) | rng.randrange(1 << 29) for _ in range(5)]
        heavy([rng.choice(masks) & rng.randrange(1 << 30) for _ in range(n)])
        ladder = [(1 << k)-1 for k in range(1, 30)]
        heavy([ladder[i % 29] for i in range(n)])
        heavy([rng.choice(ladder) for _ in range(n)])
        heavy([0 if rng.random() < 0.7 else rng.randint(1, 10**9) for _ in range(n)])
        heavy([1 << rng.randrange(30) for _ in range(n)])
        heavy([2**29+rng.randrange(1 << 20) for _ in range(n)])
        for _ in range(30):
            nums = [rng.choice(masks[:2]) & rng.randrange(1 << 30) if rng.random() < .5 else rng.randint(0, 31) for _ in range(rng.randint(100, 3000))]
            add([nums], count_or_member(nums))
    elif pid == 3881:
        for n in (100000, 99999, 65537, 50001, 1000):
            for k in sorted({2, 3, n//3, n//2-1, n//2, n//2+1, 2*n//3, n-3, n-4}):
                add([n, rng.randrange(n), k], visible_assignments(n, 0, k))
        for _ in range(150):
            n = rng.randint(17, 100000); add([n, rng.randrange(n), rng.randrange(n)], None)
            rows[-1]['expected'] = visible_assignments(*rows[-1]['args'])
    elif pid == 3885:
        def trace(*spec, isolate=True, **options):
            args = _event_trace_case(rng, *spec, **options)
            add(args, event_trace(args), isolate=isolate)
        trace(50000, 50000, (1, 10**9), 0.5)
        trace(100000, 100000, (1, 10**9), 0.5)  # domain maximum: 100,000 events and 100,000 calls
        trace(50000, 50000, (1, 3), 0.5)  # many ties
        trace(20000, 99999, (1, 10**9), 0.97, reuse_share=0.6)  # update-heavy; about 3,000 polls never drain it
        trace(30000, 99999, (1, 1000), 0.4)  # mixed; drains, then empty polls
        trace(60000, 80000, (1, 10**9), 0.0)  # polls only: drains, then 20,000 empty polls
        trace(40000, 80000, (1, 50), 0.6, reuse_share=0.9, distinct_ids=False)  # consecutive ids, reused priorities
        for _ in range(40):
            trace(rng.randint(1, 300), rng.randint(1, 600), (1, rng.choice((2, 10, 10**9))), rng.random(), isolate=False,
                  distinct_ids=rng.random() < .5)
    return rows


def _product(values):
    result = 1
    for v in values:
        result *= v
    return result


def build_cases(pid):
    if pid in IDS['l']:
        original = L_CASES.build_cases(pid, include_maximum=True)
    else:
        original = M_ORACLES.build_cases(pid)
    rows = [dict(row) for row in original]; seen = {repr(row['args']) for row in rows}
    for row in boundary_rows(pid):
        if repr(row['args']) not in seen:
            seen.add(repr(row['args'])); rows.append(row)
    return rows
