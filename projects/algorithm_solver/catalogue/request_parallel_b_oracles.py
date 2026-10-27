"""Fixed batch B definition oracles, without candidate or historical case access.

Full-domain validation is separate from bounded enumeration and transport. Large
analytic shapes are explicitly labeled, not represented as exhaustive proofs.
"""
from __future__ import annotations

import ast
from itertools import combinations, permutations, product
import json
from math import isqrt
import random
import re

from . import imported_qualification as q

IDS = (3517, 3531, 3567, 3598, 3618)
PARAMETERS = {3517: ('s',), 3531: ('n', 'buildings'), 3567: ('grid', 'k'),
              3598: ('words',), 3618: ('nums',)}
STATEMENT_SHA256 = {
    3517: '5621a0c20dd093d920f66ada7892aad1dd34fd178046b2e51a90af16fc29de0a',
    3531: '6e0d48d4112d343c2d33c8cf48bc73cbc236b1204c44d2b4d7c12fd480706e90',
    3567: '84d479a733b7889d8c27604952ccc16c05760e09722becca444fcc9412eeb790',
    3598: 'cf0aa501339690c096342b6fd5290ae57da2b5c3361befe782b13a6a4d7cd162',
    3618: 'f071002ef434a81ee95a0747d0f9ea2472ceaef92327a5433621492176386cbf',
}
CASE_COUNT = {3517: 206, 3531: 583, 3567: 483, 3598: 397, 3618: 436}
CASES_SHA256 = {
    3517: '3cbee371fc6bfd06f5b11887a48a53560e9eed828300a7ecc38d5f1d0ee550e8',
    3531: '70550479fda55d357d9d29334d859d1586d256911c1a10abbda7f3ad4266fd1c',
    3567: '723c5a7ebc26ca35e1690f9b6699302f73826cae70ed6b2775e5acb3f5b64077',
    3598: '27046f7fe5d0409343167b4565f025291e6c8aa2f269b16e8a9b5d68c9a823ed',
    3618: 'b1c586e92f0878f5d90829627e29c5103ac5da3209754ecdc14a17bc685ff0e1',
}
SEED_BASE = 202610270700
SMALL_BUDGET = {3517: 8, 3531: 64, 3567: 36, 3598: 16, 3618: 100000}
OMITTED_MAXIMUM_SHAPES = {
    3517: 'Maximum-length block shapes are retained; arbitrary full-length positional permutations are not enumerated.',
    3531: 'Maximum building count is represented by rectangles and lines; full-size high-coordinate sets can exceed the unchanged packet cap.',
    3567: 'Full 30 by 30 analytic grids are retained; arbitrary full-size pair-enumerated matrices are not generated.',
    3598: 'Maximum word count, individual length and total length have analytic probes; arbitrary full-size removal traces are not enumerated.',
    3618: 'Full length is represented, but uniform maximum-magnitude arrays exceed the unchanged packet cap; exact boundary values appear in fitting shapes.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _lower(value, low, high):
    return type(value) is str and low <= len(value) <= high and all('a' <= c <= 'z' for c in value)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 3517:
        if not _lower(args[0], 1, 100000) or args[0] != args[0][::-1]:
            raise ValueError('input must be a lowercase ASCII palindrome of declared length')
    elif pid == 3531:
        n, buildings = args
        if not _integer(n, 2, 100000) or type(buildings) is not list or not 1 <= len(buildings) <= 100000:
            raise ValueError('city or building count outside pinned domain')
        occupied = set()
        for point in buildings:
            if type(point) is not list or len(point) != 2 or any(not _integer(x, 1, n) for x in point):
                raise ValueError('building coordinates outside pinned domain')
            if tuple(point) in occupied:
                raise ValueError('building coordinates must be unique')
            occupied.add(tuple(point))
    elif pid == 3567:
        grid, k = args
        if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
            raise ValueError('matrix dimensions outside pinned domain')
        width = len(grid[0])
        if any(type(row) is not list or len(row) != width or
               any(not _integer(x, -100000, 100000) for x in row) for row in grid):
            raise ValueError('matrix must be rectangular with bounded exact integer cells')
        if not _integer(k, 1, min(len(grid), width)):
            raise ValueError('window width outside pinned domain')
    elif pid == 3598:
        words = args[0]
        if (type(words) is not list or not 1 <= len(words) <= 100000 or
                any(not _lower(word, 1, 10000) for word in words) or
                sum(map(len, words)) > 100000):
            raise ValueError('word count, alphabet, individual or total length outside pinned domain')
    else:
        values = args[0]
        if type(values) is not list or not 1 <= len(values) <= 100000 or any(not _integer(x, -10**9, 10**9) for x in values):
            raise ValueError('array outside pinned exact integer domain')


def _palindromic_permutations(s):
    return min(''.join(chars) for chars in permutations(s) if chars == chars[::-1])


def _directional_witnesses(buildings):
    return sum(all((any(a == x and b < y for a, b in buildings),
                    any(a == x and b > y for a, b in buildings),
                    any(b == y and a < x for a, b in buildings),
                    any(b == y and a > x for a, b in buildings)))
               for x, y in buildings)


def _window_value_pairs(grid, k):
    answer = []
    for i in range(len(grid) - k + 1):
        row = []
        for j in range(len(grid[0]) - k + 1):
            values = {grid[x][y] for x in range(i, i + k) for y in range(j, j + k)}
            row.append(min((abs(a - b) for a, b in combinations(values, 2)), default=0))
        answer.append(row)
    return answer


def _removal_traces(words):
    answer = []
    for removed in range(len(words)):
        remaining = words[:removed] + words[removed + 1:]
        best = 0
        for left, right in zip(remaining, remaining[1:]):
            common = 0
            for a, b in zip(left, right):
                if a != b:
                    break
                common += 1
            best = max(best, common)
        answer.append(best)
    return answer


def _prime(index):
    return index >= 2 and all(index % d != 0 for d in range(2, isqrt(index) + 1))


def _trial_prime_sums(values):
    prime_sum, other_sum = 0, 0
    for i, value in enumerate(values):
        if _prime(i):
            prime_sum += value
        else:
            other_sum += value
    return abs(prime_sum - other_sum)


def expected(pid, args):
    validate(pid, args)
    size = len(args[1]) if pid == 3531 else len(args[0]) * len(args[0][0]) if pid == 3567 else len(args[0])
    if size > SMALL_BUDGET[pid] or (pid == 3598 and sum(map(len, args[0])) > 1000):
        raise ValueError('independent enumeration budget exceeded')
    if pid == 3517:
        return _palindromic_permutations(args[0])
    if pid == 3531:
        return _directional_witnesses(args[1])
    if pid == 3567:
        return _window_value_pairs(*args)
    if pid == 3598:
        return _removal_traces(args[0])
    return _trial_prime_sums(args[0])


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact definition pin required before example extraction')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*([^\n]+)', raw.decode(), re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(k.arg for k in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('oracle disagrees with pinned public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != (2 if pid in (3598, 3618) else 3):
        raise ValueError('all pinned examples are required')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement)
    categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid)
    sentinel = object()

    def add(args, category, answer=sentinel):
        validate(pid, args)
        if answer is sentinel:
            answer = expected(pid, args)
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3517:
        for half_length in range(4):
            for half in product('abc', repeat=half_length):
                left = ''.join(half)
                for middle in ('', 'a', 'b', 'c'):
                    s = left + middle + left[::-1]
                    if s:
                        add([s], 'exhaustive_short_palindromic_inputs')
        for _ in range(40):
            half = ''.join(rng.choice('abmyz') for _ in range(rng.randrange(1, 5)))
            middle = rng.choice(('', 'a', 'z')) if len(half) < 4 else ''
            add([half + middle + half[::-1]], 'seeded_positional_permutations')
        for s, answer in [
            ('a' * 100000, 'a' * 100000),
            ('z' * 25000 + 'a' * 50000 + 'z' * 25000, 'a' * 25000 + 'z' * 50000 + 'a' * 25000),
            ('z' * 24999 + 'a' * 50001 + 'z' * 24999, 'a' * 25000 + 'z' * 24999 + 'a' + 'z' * 24999 + 'a' * 25000),
        ]:
            add([s], 'analytic_maximum_length_blocks', answer)
        left = ''.join(c * 1000 for c in 'zyxwvutsrqponmlkjihgfedcba')
        least = left[::-1]
        add([left + left[::-1]], 'analytic_all_alphabet_blocks', least + least[::-1])
    elif pid == 3531:
        for n in (2, 3):
            points = list(product(range(1, n + 1), repeat=2))
            for mask in range(1, 1 << len(points)):
                buildings = [list(p) for i, p in enumerate(points) if mask >> i & 1]
                add([n, buildings[::-1]], 'exhaustive_small_coordinate_subsets')
        for _ in range(50):
            n = rng.randrange(4, 10)
            points = list(product(range(1, n + 1), repeat=2))
            add([n, [list(p) for p in rng.sample(points, rng.randrange(1, min(50, len(points)) + 1))]], 'seeded_directional_witnesses')
        add([100000, [[1, i] for i in range(1, 100001)]], 'analytic_maximum_count_line', 0)
        add([100000, [[i, 1] for i in range(1, 100001)]], 'analytic_maximum_count_line', 0)
        add([100000, [[i, j] for i in range(1, 251) for j in range(1, 401)]], 'analytic_maximum_count_rectangle', 248 * 398)
        add([100000, [[1, 50000], [100000, 50000], [50000, 1], [50000, 100000], [50000, 50000]]], 'extreme_coordinate_cross')
    elif pid == 3567:
        for height, width, alphabet in ((1, 1, (-1, 0, 1)), (2, 2, (-1, 0, 1)), (2, 3, (-1, 1)), (3, 2, (-1, 1))):
            for values in product(alphabet, repeat=height * width):
                grid = [list(values[i * width:(i + 1) * width]) for i in range(height)]
                for k in range(1, min(height, width) + 1):
                    add([grid, k], 'exhaustive_small_window_value_pairs')
        for _ in range(50):
            height, width = rng.randrange(1, 7), rng.randrange(1, 7)
            grid = [[rng.choice((-100000, -99999, -1, 0, 1, 99999, 100000)) for _ in range(width)] for _ in range(height)]
            add([grid, rng.randrange(1, min(height, width) + 1)], 'seeded_numeric_window_pairs')
        for k in (1, 15, 30):
            add([[[100000] * 30 for _ in range(30)], k], 'analytic_maximum_constant_grid', [[0] * (31 - k) for _ in range(31 - k)])
        for k in (2, 16, 30):
            add([[[-100000 if (i + j) % 2 else 100000 for j in range(30)] for i in range(30)], k], 'analytic_maximum_checkerboard', [[200000] * (31 - k) for _ in range(31 - k)])
        for k in (2, 15, 30):
            add([[[222 * (30 * i + j) - 100000 for j in range(30)] for i in range(30)], k], 'analytic_maximum_distinct_grid', [[222] * (31 - k) for _ in range(31 - k)])
    elif pid == 3598:
        for length in range(1, 5):
            for words in product(('a', 'ab', 'aba', 'b'), repeat=length):
                add([list(words)], 'exhaustive_short_removal_traces')
        for _ in range(50):
            words = [''.join(rng.choice('abz') for _ in range(rng.randrange(1, 21))) for _ in range(rng.randrange(1, 17))]
            add([words], 'seeded_full_removal_traces')
        add([['a'] * 100000], 'analytic_maximum_word_count_equal', [1] * 100000)
        add([['a', 'b'] * 50000], 'analytic_maximum_word_count_alternating', [0] + [1] * 99998 + [0])
        add([['a' * 9999 + c for c in 'abcdefghij']], 'analytic_maximum_word_and_total_lengths', [9999] * 10)
        add([['a' * 10000, 'b' * 10000] * 5], 'analytic_maximum_word_length_bridge', [0] + [10000] * 8 + [0])
        add([['z' * 10000]], 'analytic_single_maximum_word', [0])
    else:
        for length in range(1, 6):
            for values in product((-1, 0, 1), repeat=length):
                add([list(values)], 'exhaustive_short_trial_prime_sums')
        for _ in range(64):
            add([[rng.choice((-10**9, -1, 0, 1, 10**9)) for _ in range(rng.randrange(6, 1001))]], 'seeded_numeric_trial_prime_sums')
        for values in ([0] * 100000, [999999999] * 100000, [-99999999] * 100000,
                       [10**9] * 90000 + [0] * 10000, [-10**9] * 90000,
                       [(-1 if i % 2 else 1) * 99999999 for i in range(100000)],
                       list(range(100000))):
            add([values], 'full_size_or_numeric_trial_prime_sums')
    return cases, categories


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(cases)) != CASES_SHA256[pid]:
        raise ValueError('frozen case population or bytes changed')
    list(q.batches(cases))  # Valid but oversized probes fail; no silent dropping.
    return cases, categories
