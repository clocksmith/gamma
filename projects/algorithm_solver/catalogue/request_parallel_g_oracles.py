"""Source-blind fixed G references, full normative domains and deterministic cases.

No candidate sources, historical cases, execution or qualification are loaded here.
Finite brute-force references are distinct from labeled analytic boundary probes.
"""
from __future__ import annotations

import ast
from functools import reduce
import heapq
from itertools import combinations, product
import json
from math import gcd
from operator import xor
import random
import re

from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (3525, 3552, 3561, 3574, 3599)
PARAMETERS = {3525: ('nums', 'k', 'queries'), 3552: ('matrix',), 3561: ('s',), 3574: ('nums', 'k'), 3599: ('nums', 'k')}
STATEMENT_SHA256 = {
    3525: 'b3e6d221acbb3d8a08ade58e43d755cc06e686bb26c1ba0c613670c7db2e1d2d',
    3552: '5447d0ec76d8479d979d74e9cc2a3c8a942381b4a706a1fcd7e48d9faf734f81',
    3561: 'b8c28407c32ed6528811a3e1d437d6a670b34938b3d3f84ff886151939340682',
    3574: '4a6287d884c16527164d5010550d6802f6cf0310498f710ade10ca4df76205bf',
    3599: '5f134db2a4cb3ca64452176d99ce961b77cd7a81c666b7c2bf71c26d6be8f78e',
}
EXAMPLE_COUNT = {3525: 3, 3552: 2, 3561: 3, 3574: 3, 3599: 3}
CASE_COUNT = {3525: 413, 3552: 838, 3561: 880, 3574: 499, 3599: 666}
CASES_SHA256 = {3525: '906cd2010ff33ad286ca040a07189dfa78663782f3bbece7f995db1bf483dc4e', 3552: 'd7e0c1aff6b287a4d64edf49c374d4148600186b5aaaa41e64e15e458741e888', 3561: 'cfc473f1c2b5aaec885739b650e9d97344d559e85e0ec7906e5eb91fa5d35970', 3574: 'a17c022a4429da9f8cccac2759ede037e483083503c213e4f5090e373b3d2954', 3599: '2434329a7e6fee4ce6d4e62fb055e3bdb02af99d80117269787b8ffa143f4a9d'}
SMALL_BUDGET = {3525: 16, 3552: 36, 3561: 64, 3574: 8, 3599: 12}
SEED_BASE = 202610271645
OMITTED_MAXIMUM_SHAPES = {
    3525: 'Joint maximum-length arrays with all ten-digit values and maximum-count high-coordinate queries can exceed the unchanged packet cap. Fitting maximum n and q, separate high-value probes, and persistent updates are retained.',
    3552: 'Maximum 1000 by 1000 open, all-A and blocked-goal boards are retained. Arbitrary full-size portal-mask search is not attempted by the independent oracle; runtime outcomes remain unmeasured.',
    3561: 'Maximum-length cancellation and unchanged-output shapes are retained; arbitrary maximum-length direct rescanning is not attempted.',
    3574: 'Maximum length and numeric value are retained in analytic uniform shapes; arbitrary full-length doubling-subset enumeration is not attempted.',
    3599: 'Maximum length, numeric values and partition-count boundaries are retained; arbitrary maximum-length cut enumeration is not attempted.',
}


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 3525:
        a, k, queries = args
        valid = (ints(a, 1, 10**9, 1, 100000) and integer(k, 1, 5)
                 and type(queries) is list and 1 <= len(queries) <= 20000
                 and all(type(row) is list and len(row) == 4
                         and integer(row[0], 0, len(a)-1) and integer(row[1], 1, 10**9)
                         and integer(row[2], 0, len(a)-1) and integer(row[3], 0, k-1) for row in queries))
    elif pid == 3552:
        matrix = args[0]
        valid = (type(matrix) is list and 1 <= len(matrix) <= 1000
                 and text(matrix[0], '.#ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1, 1000)
                 and all(text(row, '.#ABCDEFGHIJKLMNOPQRSTUVWXYZ', len(matrix[0]), len(matrix[0])) for row in matrix)
                 and matrix[0][0] != '#')
    elif pid == 3561:
        valid = text(args[0], maximum=100000)
    else:
        valid = ints(args[0], 1, 10**9, 1, 1500 if pid == 3574 else 250) and integer(args[1], 1, len(args[0]))
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _query_products(nums, k, queries):
    current = list(nums)
    out = []
    for index, value, start, residue in queries:
        current[index] = value
        count, full_product = 0, 1
        for end in range(start, len(current)):
            full_product *= current[end]
            count += full_product % k == residue
        out.append(count)
    return out


def _portal_states(matrix):
    rows, cols = len(matrix), len(matrix[0])
    letters = sorted(set(''.join(matrix)) - {'.', '#'})
    bits = {letter: 1 << i for i, letter in enumerate(letters)}
    locations = {letter: [(r, c) for r in range(rows) for c in range(cols) if matrix[r][c] == letter] for letter in letters}
    pending = [(0, 0, 0, 0)]
    distances = {(0, 0, 0): 0}
    while pending:
        cost, r, c, used = heapq.heappop(pending)
        if distances[(r, c, used)] != cost:
            continue
        if (r, c) == (rows-1, cols-1):
            return cost
        moves = [(nr, nc, used, 1) for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                 if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] != '#']
        char = matrix[r][c]
        if char in bits and not used & bits[char]:
            moves += [(nr, nc, used | bits[char], 0) for nr, nc in locations[char] if (nr, nc) != (r, c)]
        for nr, nc, mask, step in moves:
            state = (nr, nc, mask)
            if cost + step < distances.get(state, 10**9):
                distances[state] = cost + step
                heapq.heappush(pending, (cost + step, nr, nc, mask))
    return -1


def _leftmost_removals(s):
    while True:
        for i in range(len(s)-1):
            if abs(ord(s[i])-ord(s[i+1])) in (1, 25):
                s = s[:i] + s[i+2:]
                break
        else:
            return s


def _doubling_masks(nums, k):
    answer = 0
    for mask in range(1 << len(nums)):
        if mask.bit_count() > k:
            continue
        a = [v * (2 if mask >> i & 1 else 1) for i, v in enumerate(nums)]
        for left in range(len(a)):
            value = 0
            for right in range(left, len(a)):
                value = gcd(value, a[right])
                answer = max(answer, (right-left+1)*value)
    return answer


def _xor_cuts(nums, k):
    return min(max(reduce(xor, nums[left:right], 0) for left, right in zip((0,) + cuts, cuts + (len(nums),)))
               for cuts in combinations(range(1, len(nums)), k-1))


def expected(pid, args):
    validate(pid, args)
    if pid == 3552:
        matrix = args[0]
        bounded = len(matrix)*len(matrix[0]) <= SMALL_BUDGET[pid] and len(set(''.join(matrix)) - {'.', '#'}) <= 3
    else:
        bounded = len(args[0]) <= SMALL_BUDGET[pid]
        if pid == 3525:
            bounded = bounded and len(args[2]) <= 160
    if not bounded:
        raise ValueError('bounded independent reference budget exceeded')
    return {3525: _query_products, 3552: _portal_states, 3561: _leftmost_removals,
            3574: _doubling_masks, 3599: _xor_cuts}[pid](*args)


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', raw.decode(), re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(item.arg for item in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement)
    categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid)
    sentinel = object()

    def add(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3525:
        for alphabet, maximum in [((1, 2, 3), 3), ((1, 2), 4)]:
            for n in range(1, maximum+1):
                for values in product(alphabet, repeat=n):
                    for k in range(1, 6):
                        queries = [[index, value, start, residue] for index in range(n) for value in alphabet
                                   for start in range(n) for residue in range(k)]
                        add([list(values), k, queries], 'exhaustive_small_arrays_with_ordered_updates_and_prefixes')
        for _ in range(60):
            n, k = rng.randrange(1, 17), rng.randrange(1, 6)
            values = [rng.choice((1, 2, 3, 4, 5, 999999999, 1000000000)) for _ in range(n)]
            queries = [[rng.randrange(n), rng.choice((1, 2, 3, 5, 1000000000)), rng.randrange(n), rng.randrange(k)]
                       for _ in range(rng.randrange(1, 31))]
            add([values, k, queries], 'seeded_persistent_updates_with_exact_products')
        n = 100000
        queries = [[0, 1, i % n, 0] for i in range(20000)]
        add([[1]*n, 1, queries], 'analytic_joint_maximum_n_and_q_modulus_one', [n-i for i in range(20000)])
        queries = [[i, 1, i, 1] for i in range(20000)]
        add([[1]*n, 5, queries], 'analytic_joint_maximum_n_and_q_ones', [n-i for i in range(20000)])
        add([[1]*n, 5, [[n-1, 5, 0, 0], [n-1, 1, 0, 0], [0, 5, 0, 0], [0, 1, n-1, 1]]],
            'analytic_persistent_endpoint_updates', [1, 0, n, 1])
        add([[1000000000]*90000, 5, [[0, 1000000000, 0, 0], [89999, 1, 89999, 1]]],
            'analytic_high_value_long_array', [90000, 1])
        add([[1], 5, [[0, (i % 5)+1, 0, i % 5] for i in range(20000)]],
            'analytic_maximum_query_count_singleton', [0]*20000)
    elif pid == 3552:
        for rows, cols, alphabet in [(1, 1, '.AZ'), (1, 3, '.#AB'), (2, 2, '.#AB'), (2, 3, '.#A')]:
            for cells in product(alphabet, repeat=rows*cols):
                if cells[0] == '#':
                    continue
                add([[''.join(cells[r*cols:(r+1)*cols]) for r in range(rows)]], 'exhaustive_small_obstacles_and_portal_states')
        for _ in range(100):
            rows, cols = rng.randrange(1, 7), rng.randrange(1, 7)
            cells = [rng.choice('..##ABC') for _ in range(rows*cols)]
            cells[0] = rng.choice('.ABC')
            add([[''.join(cells[r*cols:(r+1)*cols]) for r in range(rows)]], 'seeded_explicit_used_portal_mask_search')
        for matrix, answer in [(['.'*1000]*1000, 1998), (['A'*1000]*1000, 0),
                               (['.'*1000]*999 + ['.'*999+'#'], -1),
                               (['.'*1000], 999), (['.']*1000, 999),
                               (['A'+'#'*998+'A'], 0), (['A']+['#']*998+['A'], 0)]:
            add([matrix], 'analytic_maximum_grid_shapes', answer)
    elif pid == 3561:
        for alphabet, lengths in [('abcz', range(1, 5)), ('az', range(5, 9))]:
            for n in lengths:
                for letters in product(alphabet, repeat=n):
                    add([''.join(letters)], 'exhaustive_leftmost_deletion_strings')
        for _ in range(50):
            add([''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rng.randrange(5, 65)))], 'seeded_literal_leftmost_deletions')
        for value, answer in [('a'*100000, 'a'*100000), ('ab'*50000, ''), ('az'*50000, ''),
                              ('a'*50000+'b'*50000, ''), ('a'*50001+'b'*49999, 'aa'),
                              ('ac'*50000, 'ac'*50000), ('z'*50000+'a'*50000, '')]:
            add([value], 'analytic_maximum_length_deletion_shapes', answer)
    elif pid == 3574:
        for n in range(1, 5):
            for values in product((1, 2, 3), repeat=n):
                for k in range(1, n+1):
                    add([list(values), k], 'exhaustive_doubling_subsets_and_intervals')
        for _ in range(60):
            n = rng.randrange(5, 9)
            add([[rng.choice((1, 2, 3, 4, 8, 999999999, 1000000000)) for _ in range(n)], rng.randrange(1, n+1)],
                'seeded_exact_doubling_masks_with_numeric_boundaries')
        for value in (1, 1000000000):
            for k in (1, 749, 750, 751, 1500):
                add([[value]*1500, k], 'analytic_maximum_uniform_gcd_score', value*max(1500, 2*k))
    else:
        for n in range(1, 5):
            for values in product((1, 2, 3), repeat=n):
                for k in range(1, n+1):
                    add([list(values), k], 'exhaustive_contiguous_cut_positions')
        for values in product((1, 2), repeat=5):
            for k in range(1, 6):
                add([list(values), k], 'exhaustive_binary_length_five_partitions')
        for _ in range(60):
            n = rng.randrange(6, 13)
            add([[rng.choice((1, 2, 3, 2**29, 2**29+1, 1000000000)) for _ in range(n)], rng.randrange(1, n+1)],
                'seeded_numeric_exact_cut_positions')
        for value in (1, 2**29+1, 1000000000):
            for k in (1, 2, 125, 126, 250):
                add([[value]*250, k], 'analytic_maximum_constant_xor_partitions', 0 if 250 >= 2*k else value)
        values = [rng.randrange(1, 1000000001) for _ in range(250)]
        add([values, 1], 'analytic_single_full_length_xor', reduce(xor, values, 0))
        add([values, 250], 'analytic_all_singleton_maximum', max(values))
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    records = [{'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []} for i, c in enumerate(batch)]
    return sum(len(q.encoded(record)) for record in records) + len(q.encoded({'done': len(batch)})) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('fixed generated case count or bytes differ')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('projected successful observation exceeds unchanged output cap')
    return cases, categories
