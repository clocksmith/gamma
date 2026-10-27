"""Fixed batch C pure definition oracles and deterministic development cases.

No candidate loader, execution route or admission registry. Full domain validity
is separate from bounded reference cost and unchanged packet transport limits.
"""
from __future__ import annotations

import ast
from collections import deque
from functools import lru_cache
from itertools import combinations, permutations, product
import json
import random
import re

from . import imported_qualification as q

IDS = (3524, 3551, 3587, 3608, 3619)
PARAMETERS = {3524: ('nums', 'k'), 3551: ('nums',), 3587: ('nums',),
              3608: ('n', 'edges', 'k'), 3619: ('grid', 'k')}
STATEMENT_SHA256 = {
    3524: '14284e99e81807e658fd74cf988decd56113511e8e26a26689597479a5222416',
    3551: '277f00697e77ed708c6b1e8e9d77524168babd637abecfd3b5f3a931325ba38f',
    3587: 'd830b374e4d2338a90c9bee462709e7ba23ae89e8b6fe433da86ac32ff0e208c',
    3608: 'fd237dc0e186bdd6822f385245f622b23a25b736b7e1626e2f4e75296dba32cc',
    3619: 'c4b8be7c74f1eb244ad0251845a0ed6d2e13c5f5b0874c0683670f1f55fd2373',
}
EXAMPLE_COUNT = {3524: 3, 3551: 3, 3587: 4, 3608: 3, 3619: 2}
SMALL_BUDGET = {3524: 12, 3551: 7, 3587: 10, 3608: 7, 3619: 25}
SEED_BASE = 202610270700
CASE_COUNT = {3524: 648, 3551: 223, 3587: 302, 3608: 159, 3619: 353}
CASES_SHA256 = {3524: 'd90506a34201f23934ebfa2cad3336cf046e07c2773b6610875968c84401e1a2', 3551: 'b638e730dcd207bd83afa2d0b11149729f82a71664f23cbc9829b9165e9b6f4c', 3587: '891103be36936547272ad53e7f11549534ec818bc82d409fe7a1672686ccef5a', 3608: '52b07dde56afc06aa1fc55cd86b314a4d46ea231a16e7096447e14de66a964d0', 3619: '9610a99c750325c766ff445f7f5bc40dbafe24e5990de9eb20b63aaed7ce93e3'}
OMITTED_MAXIMUM_SHAPES = {
    3524: 'Full-length low-width analytic arrays are included. Maximum-length ten-digit constant arrays exceed the unchanged packet cap; high-value analytic arrays use 99000 elements. Arbitrary full-length interval enumeration is not attempted.',
    3551: 'Full-length sorted, reversed and rotated analytic permutations are included; arbitrary 100000-element swap-graph enumeration is not attempted.',
    3587: 'Full-length analytic parity shapes are included; arbitrary 100000-element adjacent-swap state enumeration is not attempted.',
    3608: 'The full 100000-node same-time star packet exceeds the unchanged cap. Maximum node count is separately represented with zero or one edge; included star and chain have 65000 and 50000 nodes. No maximum-edge or arbitrary large-graph oracle claim.',
    3619: 'Full 100000-cell analytic grids are included, including each dimension limit separately; arbitrary large-grid transitive-closure enumeration is not attempted.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered arguments')
    if pid in (3524, 3551, 3587):
        nums = args[0]
        if (type(nums) is not list or not 1 <= len(nums) <= 100000 or
                any(not _integer(x, 1, 10**9) for x in nums)):
            raise ValueError('array outside pinned positive integer domain')
        if pid in (3551, 3587) and len(set(nums)) != len(nums):
            raise ValueError('distinct values required')
        if pid == 3524 and not _integer(args[1], 1, 5):
            raise ValueError('remainder modulus outside pinned domain')
        return
    if pid == 3608:
        n, edges, k = args
        if (not _integer(n, 1, 100000) or type(edges) is not list or len(edges) > 100000 or
                not _integer(k, 1, n)):
            raise ValueError('graph dimensions or target outside pinned domain')
        seen = set()
        for edge in edges:
            if (type(edge) is not list or len(edge) != 3 or
                    not _integer(edge[0], 0, n - 1) or not _integer(edge[1], 0, n - 1) or
                    edge[0] == edge[1] or not _integer(edge[2], 1, 10**9)):
                raise ValueError('edge outside pinned endpoint/time domain')
            pair = tuple(sorted(edge[:2]))
            if pair in seen:
                raise ValueError('duplicate undirected edge')
            seen.add(pair)
        return
    grid, k = args
    if (type(grid) is not list or not 1 <= len(grid) <= 1000 or type(grid[0]) is not list or
            not 1 <= len(grid[0]) <= 1000 or len(grid) * len(grid[0]) > 100000 or
            not _integer(k, 1, 10**6)):
        raise ValueError('grid dimensions or divisor outside pinned domain')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(not _integer(x, 0, 10**6) for x in row) for row in grid):
        raise ValueError('rectangular nonnegative integer grid required')


def _digit_sum(value):
    total = 0
    while value:
        value, digit = divmod(value, 10)
        total += digit
    return total


@lru_cache(maxsize=7)
def _swap_distances(n):
    """Derive all small permutation distances from legal swaps, not a formula."""
    start = tuple(range(n)); distances = {start: 0}; queue = deque([start])
    while queue:
        state = queue.popleft()
        for i in range(n):
            for j in range(i + 1, n):
                changed = list(state); changed[i], changed[j] = changed[j], changed[i]
                target = tuple(changed)
                if target not in distances:
                    distances[target] = distances[state] + 1; queue.append(target)
    return distances


@lru_cache(maxsize=10)
def _parity_distances(n):
    starts = {tuple((i + first) % 2 for i in range(n)) for first in (0, 1)}
    distances = dict.fromkeys(starts, 0); queue = deque(sorted(starts))
    while queue:
        state = queue.popleft()
        for i in range(n - 1):
            if state[i] == state[i + 1]:
                continue
            changed = list(state); changed[i], changed[i + 1] = changed[i + 1], changed[i]
            target = tuple(changed)
            if target not in distances:
                distances[target] = distances[state] + 1; queue.append(target)
    return distances


def _closure(reach):
    n = len(reach)
    for via in range(n):
        for source in range(n):
            if reach[source][via]:
                for target in range(n):
                    reach[source][target] |= reach[via][target]
    return reach


def expected(pid, args):
    validate(pid, args)
    size = len(args[0]) if pid in (3524, 3551, 3587) else args[0] if pid == 3608 else len(args[0]) * len(args[0][0])
    if size > SMALL_BUDGET[pid]:
        raise ValueError('valid input exceeds the declared small reference budget')
    if pid == 3524:
        nums, k = args; answer = [0] * k
        for begin in range(len(nums)):
            value = 1
            for end in range(begin, len(nums)):
                value *= nums[end]; answer[value % k] += 1
        return answer
    if pid == 3551:
        nums = args[0]; ordered = sorted(nums, key=lambda x: (_digit_sum(x), x))
        ranks = {x: i for i, x in enumerate(ordered)}
        return _swap_distances(len(nums))[tuple(ranks[x] for x in nums)]
    if pid == 3587:
        return _parity_distances(len(args[0])).get(tuple(x % 2 for x in args[0]), -1)
    if pid == 3608:
        n, edges, k = args
        for time in sorted({0, *(row[2] for row in edges)}):
            reach = [[i == j for j in range(n)] for i in range(n)]
            for left, right, removed in edges:
                if removed > time:
                    reach[left][right] = reach[right][left] = True
            _closure(reach); remaining = set(range(n)); count = 0
            while remaining:
                start = min(remaining); remaining -= {j for j in range(n) if reach[start][j]}; count += 1
            if count >= k:
                return time
        raise AssertionError('all edges removed must meet any valid target')
    grid, k = args
    cells = [(i, j) for i, row in enumerate(grid) for j, value in enumerate(row) if value > 0]
    reach = [[abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1 for b in cells] for a in cells]
    _closure(reach); remaining = set(range(len(cells))); answer = 0
    while remaining:
        start = min(remaining); component = {j for j in range(len(cells)) if reach[start][j]}
        remaining -= component
        total = sum(grid[cells[j][0]][cells[j][1]] for j in component)
        answer += total % k == 0
    return answer


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact fixed statement bytes required')
    cases = []
    for args_text, answer_text in re.findall(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', raw.decode(), re.S):
        call = ast.parse('f(' + args_text.strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or [kw.arg for kw in call.keywords] != list(PARAMETERS[pid]):
            raise ValueError('ordered literal public example arguments required')
        args = [ast.literal_eval(kw.value) for kw in call.keywords]
        answer = json.loads(answer_text.strip())
        if not q.exact(expected(pid, args), answer):
            raise ValueError('definition oracle disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('all fixed public examples required')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement); categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid); sentinel = object()
    def add(args, category, answer=sentinel):
        validate(pid, args)
        if answer is sentinel:
            answer = expected(pid, args)
        cases.append({'args': args, 'expected': answer, 'compare': 'return'}); categories.append(category)
    if pid == 3524:
        for n in range(1, 5):
            for nums in product((1, 2, 3), repeat=n):
                for k in range(1, 6):
                    add([list(nums), k], 'exhaustive_short_interval_products')
        for _ in range(40):
            add([[rng.choice((1, 2, 5, 999999999, 10**9)) for _ in range(rng.randrange(5, 13))], rng.randrange(1, 6)], 'seeded_exact_large_products')
        n = 100000; total = n * (n + 1) // 2
        for args, answer in [([[1] * n, 5], [0, total, 0, 0, 0]),
                             ([[10**9] * 99000, 5], [99000 * 99001 // 2, 0, 0, 0, 0]),
                             ([[1] * n, 1], [total]),
                             ([[10**9] * 99000, 3], [0, 99000 * 99001 // 2, 0]),
                             ([[1, 2] * (n // 2), 2], [total - n // 2, n // 2])]:
            add(args, 'analytic_maximum_length' if len(args[0]) == n else 'analytic_near_maximum_high_values', answer)
    elif pid == 3551:
        basis = (1, 10, 2, 20, 11)
        for n in range(1, 6):
            for nums in permutations(basis[:n]):
                add([list(nums)], 'exhaustive_fixed_tie_set_permutations')
        for _ in range(40):
            add([rng.sample(range(1, 10**9 + 1), rng.randrange(6, 8))], 'seeded_arbitrary_swap_graph')
        for nums in permutations((10**9, 999999999, 100000001, 99999998)):
            add([list(nums)], 'high_digit_sum_order')
        nums = sorted(range(1, 100001), key=lambda x: (_digit_sum(x), x))
        add([nums], 'analytic_maximum_sorted', 0)
        add([nums[::-1]], 'analytic_maximum_reversal', len(nums) // 2)
        add([nums[1:] + nums[:1]], 'analytic_maximum_single_cycle', len(nums) - 1)
    elif pid == 3587:
        for n in range(1, 8):
            for bits in product((0, 1), repeat=n):
                add([[2 * (i + 1) + bit for i, bit in enumerate(bits)]], 'exhaustive_short_parity_words')
        for _ in range(40):
            bits = [rng.randrange(2) for _ in range(rng.randrange(8, 11))]
            add([[10**9 - 2 * (i + 1) + bit for i, bit in enumerate(bits)]], 'seeded_high_value_parity_words')
        n = 100000; m = n // 2
        add([list(range(1, n + 1))], 'analytic_maximum_alternating', 0)
        add([list(range(2, 2 * n + 1, 2))], 'analytic_maximum_impossible', -1)
        add([list(range(2, 2 * m + 1, 2)) + list(range(1, 2 * m, 2))], 'analytic_maximum_balanced_blocks', m * (m - 1) // 2)
        add([list(range(1, 2 * m, 2)) + list(range(2, 2 * m + 1, 2))], 'analytic_maximum_reversed_blocks', m * (m - 1) // 2)
    elif pid == 3608:
        for n in range(1, 4):
            pairs = list(combinations(range(n), 2))
            for states in product((0, 1, 2), repeat=len(pairs)):
                edges = [[a, b, t] for (a, b), t in zip(pairs, states) if t]
                for k in range(1, n + 1):
                    add([n, edges, k], 'exhaustive_tiny_timed_simple_graphs')
        for _ in range(60):
            n = rng.randrange(4, 8); pairs = list(combinations(range(n), 2)); rng.shuffle(pairs)
            edges = [[a, b, rng.choice((1, 2, 3, 10**9 - 1, 10**9))] for a, b in pairs[:rng.randrange(len(pairs) + 1)]]
            add([n, edges, rng.randrange(1, n + 1)], 'seeded_removal_thresholds')
        for args in ([4, [[0, 1, 7], [1, 2, 7], [2, 3, 7]], 3],
                     [4, [[0, 1, 10**9], [2, 3, 1]], 3],
                     [5, [[4, 0, 10**9]], 4],
                     [3, [[0, 1, 1], [1, 2, 2], [2, 0, 3]], 2]):
            add(args, 'explicit_ties_cycles_and_disconnection')
        add([100000, [], 100000], 'analytic_maximum_node_count', 0)
        add([100000, [[0, 1, 10**9]], 100000], 'analytic_maximum_time', 10**9)
        add([65000, [[0, i, 1] for i in range(1, 65000)], 65000], 'analytic_large_star', 1)
        add([50000, [[i, i + 1, 1] for i in range(49999)], 50000], 'analytic_large_chain', 1)
    else:
        for height, width in ((1, 1), (1, 2), (2, 1), (2, 2)):
            for values in product((0, 1, 2), repeat=height * width):
                grid = [list(values[i * width:(i + 1) * width]) for i in range(height)]
                for k in (1, 2, 3):
                    add([grid, k], 'exhaustive_tiny_island_grids')
        for _ in range(40):
            height, width = rng.choice(((3, 3), (3, 4), (4, 5), (5, 5)))
            grid = [[rng.choice((0, 0, 1, 2, 999999, 10**6)) for _ in range(width)] for _ in range(height)]
            add([grid, rng.choice((1, 2, 3, 999983, 10**6))], 'seeded_component_closure')
        add([[[0] * 1000 for _ in range(100)], 1], 'analytic_maximum_water', 0)
        add([[[10**6] * 1000 for _ in range(100)], 10**6], 'analytic_maximum_exact_sum', 1)
        add([[[10**6 if (i + j) % 2 == 0 else 0 for j in range(1000)] for i in range(100)], 10**6], 'analytic_maximum_isolated_cells', 50000)
        add([[[1] * 100 for _ in range(1000)], 100000], 'analytic_maximum_height', 1)
        add([[[1 if i % 2 == 0 else 0] * 1000 for i in range(100)], 1000], 'analytic_separated_land_rows', 50)
    list(q.batches(cases))
    return cases, categories


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(cases)) != CASES_SHA256[pid]:
        raise ValueError('frozen batch C population or case bytes changed')
    return cases, categories
