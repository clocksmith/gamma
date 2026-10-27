"""Fixed batch D definition oracles; no candidate loader or execution route.

Full-domain validity is independent of enumeration and transport budgets.
Constructive and analytic large shapes remain explicitly categorized.
"""
from __future__ import annotations

import ast
from itertools import combinations, permutations, product
import json
import random
import re

from . import imported_qualification as q

IDS = (3513, 3522, 3527, 3546, 3572)
PARAMETERS = {3513: ('nums',), 3522: ('instructions', 'values'),
              3527: ('responses',), 3546: ('grid',), 3572: ('x', 'y')}
STATEMENT_SHA256 = {
    3513: '683628dca23a3c4ce7f8b206a25dfeeb117e967b511d3245a919af993e17a887',
    3522: 'c8e8e84bc8ab4ea86e42c07e7a2284e2e2322968ba7920030d3cdd4eb6452efd',
    3527: '3e8a7efc6b15291ecad33bac82bb9062910ecca31076d3e1d586df7e858f741e',
    3546: '603c1ba44d69b02745bf8f0ab71e160e880ebdc6fc1441b878d876f8fe28cfe3',
    3572: '94baa2947c7d52f23afc3ddaafb95872f1948f1805dc7cba3fd4b37b2d3bfc16',
}
EXAMPLE_COUNT = {3513: 2, 3522: 3, 3527: 2, 3546: 2, 3572: 2}
CASE_COUNT = {3513: 209, 3522: 317, 3527: 315, 3546: 339, 3572: 948}
CASES_SHA256 = {
    3513: 'e415b06aeb9445011eea49679160feabf30f221c0b7ae3a1dfc424910340e571',
    3522: '444ef7cd94d3d1eb8f91586d9660123c4baaa829ed2ed024022d4ec54c2cc7fd',
    3527: '26d3db312c2a6844e8923b3b34027b4685c8064e6946518da3c29ba3bd7ab783',
    3546: 'dfef7db59e3927ea886eaddcfa8ac3dd00c6a8cf22ad2ebc5249f0fe5494dbfd',
    3572: 'e27c95e962a1525603c0c43e99a6f25a288811a21daee026123a56aaf0aeaf3b',
}
SEED_BASE = 202610270900
SMALL_BUDGET = {3513: 64, 3522: 64, 3527: 100, 3546: 36, 3572: 18}
OMITTED_MAXIMUM_SHAPES = {
    3513: 'Maximum-length permutations have constructive full-value-span witnesses; arbitrary full-length positional triples are not enumerated.',
    3522: 'Maximum instruction count and fitting large signed scores are included; uniform maximum-magnitude full-length values exceed the unchanged packet cap.',
    3527: 'Even the shortest simultaneous 1000-day by 1000-response matrix exceeds the unchanged packet cap. Separate maxima and a 250000-response fitting shape are retained.',
    3546: 'Maximum-area row, column and rectangle shapes are included; arbitrary maximum-area cut enumeration is not attempted.',
    3572: 'Maximum-length distinctness shapes and boundary values are included; two uniform maximum-value length 100000 arrays exceed the unchanged packet cap.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _ints(values, low, high, minimum=1, maximum=100000):
    return type(values) is list and minimum <= len(values) <= maximum and all(_integer(x, low, high) for x in values)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 3513:
        nums = args[0]
        if type(nums) is not list or not _ints(nums, 1, len(nums)) or len(set(nums)) != len(nums):
            raise ValueError('input must be an exact permutation of 1 through its length')
    elif pid == 3522:
        instructions, values = args
        if (type(instructions) is not list or not 1 <= len(instructions) <= 100000 or
                any(type(x) is not str or x not in ('add', 'jump') for x in instructions) or
                not _ints(values, -100000, 100000, len(instructions), len(instructions))):
            raise ValueError('instruction or value arrays outside pinned domain')
    elif pid == 3527:
        responses = args[0]
        if type(responses) is not list or not 1 <= len(responses) <= 1000:
            raise ValueError('day count outside pinned domain')
        for day in responses:
            if (type(day) is not list or not 1 <= len(day) <= 1000 or
                    any(type(s) is not str or not 1 <= len(s) <= 10 or
                        any(not 'a' <= c <= 'z' for c in s) for s in day)):
                raise ValueError('response count, length or alphabet outside pinned domain')
    elif pid == 3546:
        grid = args[0]
        if type(grid) is not list or not 1 <= len(grid) <= 100000 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 100000:
            raise ValueError('grid dimensions outside pinned domain')
        width = len(grid[0])
        if not 2 <= len(grid) * width <= 100000 or any(not _ints(row, 1, 100000, width, width) for row in grid):
            raise ValueError('grid area, rectangularity or cell domain differs')
    else:
        x, y = args
        if not _ints(x, 1, 1000000, 3, 100000) or not _ints(y, 1, 1000000, len(x), len(x)):
            raise ValueError('paired arrays outside pinned positive integer domain')


def _positional_xor_triples(nums):
    return len({nums[i] ^ nums[j] ^ nums[k] for i in range(len(nums))
                for j in range(i, len(nums)) for k in range(j, len(nums))})


def _successor_path_score(instructions, values):
    edges = [i + 1 if token == 'add' else i + values[i] for i, token in enumerate(instructions)]
    weights = [value if token == 'add' else 0 for token, value in zip(instructions, values)]
    path, index = [], 0
    while 0 <= index < len(edges) and index not in path:
        path.append(index)
        index = edges[index]
    return sum(weights[i] for i in path)


def _day_membership_response(responses):
    vocabulary = {word for day in responses for word in day}
    return min(vocabulary, key=lambda word: (-sum(word in day for day in responses), word))


def _materialized_cuts(grid):
    height, width = len(grid), len(grid[0])
    for cut in range(1, height):
        top = [value for row in grid[:cut] for value in row]
        bottom = [value for row in grid[cut:] for value in row]
        if sum(top) == sum(bottom):
            return True
    for cut in range(1, width):
        left = [value for row in grid for value in row[:cut]]
        right = [value for row in grid for value in row[cut:]]
        if sum(left) == sum(right):
            return True
    return False


def _distinct_index_triples(x, y):
    return max((y[i] + y[j] + y[k] for i, j, k in combinations(range(len(x)), 3)
                if len({x[i], x[j], x[k]}) == 3), default=-1)


def expected(pid, args):
    validate(pid, args)
    size = sum(map(len, args[0])) if pid == 3527 else len(args[0]) * len(args[0][0]) if pid == 3546 else len(args[0])
    if size > SMALL_BUDGET[pid]:
        raise ValueError('independent enumeration budget exceeded')
    if pid == 3513:
        return _positional_xor_triples(args[0])
    if pid == 3522:
        return _successor_path_score(*args)
    if pid == 3527:
        return _day_membership_response(args[0])
    if pid == 3546:
        return _materialized_cuts(args[0])
    return _distinct_index_triples(*args)


def _xor_span_witness_count(n):
    """Construct every attainable value, plus a bit-width upper bound."""
    if not _integer(n, 1, 100000):
        raise ValueError('witness size outside pinned domain')
    if n < 3:
        return _positional_xor_triples(list(range(1, n + 1)))
    power = 1 << (n.bit_length() - 1)
    bound = power * 2
    # All input values are below bound, so no XOR can set a higher bit.
    for value in range(bound):
        if value == 0:
            triple = (1, 2, 3)
        elif value <= n:
            triple = (value, 1, 1)
        else:
            remainder = value ^ power
            a = 2 if remainder == 1 else 1
            triple = (power, a, a ^ remainder)
        if not all(1 <= x <= n for x in triple) or triple[0] ^ triple[1] ^ triple[2] != value:
            raise ValueError('constructive XOR witness failed')
    return bound


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned definition required before example extraction')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*([^\n]+)', raw.decode(), re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(k.arg for k in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned example ordered parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('definition oracle disagrees with public example')
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
        if answer is sentinel:
            answer = expected(pid, args)
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3513:
        for n in range(1, 6):
            for nums in permutations(range(1, n + 1)):
                add([list(nums)], 'exhaustive_permutations_length_1_to_5')
        for _ in range(40):
            n = rng.randrange(6, 21)
            add([rng.sample(range(1, n + 1), n)], 'seeded_positional_xor_triples')
        for n in (7, 8, 9, 15, 16, 17, 31, 32, 33):
            add([list(range(n, 0, -1))], 'bit_boundary_positional_xor_triples')
        for n, order in ((65535, 'ascending'), (65536, 'reverse'), (65537, 'rotate'),
                         (100000, 'shuffle'), (100000, 'reverse')):
            values = list(range(1, n + 1))
            if order == 'reverse':
                values.reverse()
            elif order == 'rotate':
                values = values[1:] + values[:1]
            elif order == 'shuffle':
                rng.shuffle(values)
            add([values], 'constructive_large_full_xor_span', _xor_span_witness_count(n))
    elif pid == 3522:
        alphabet = tuple(product(('add', 'jump'), (-1, 0, 1)))
        for length in range(1, 4):
            for tape in product(alphabet, repeat=length):
                add([[x[0] for x in tape], [x[1] for x in tape]], 'exhaustive_short_successor_graphs')
        for _ in range(50):
            n = rng.randrange(4, 65)
            add([[rng.choice(('add', 'jump')) for _ in range(n)],
                 [rng.choice((-100000, -n, -1, 0, 1, n, 100000)) for _ in range(n)]], 'seeded_boundary_successor_graphs')
        for instructions, values, answer in [
            (['add'] * 100000, [999] * 100000, 99900000),
            (['add'] * 100000, [100000] * 50000 + [0] * 50000, 5000000000),
            (['add'] * 100000, [-100000] * 49000 + [0] * 51000, -4900000000),
            (['jump'] * 100000, [1] * 100000, 0),
            (['jump'] * 100000, [1] * 99999 + [-99999], 0),
            (['jump'] + ['add'] * 99999, [100000] + [0] * 99999, 0),
        ]:
            add([instructions, values], 'analytic_maximum_instruction_shapes', answer)
    elif pid == 3527:
        days = [list(day) for length in (1, 2) for day in product(('a', 'b'), repeat=length)]
        for length in range(1, 4):
            for responses in product(days, repeat=length):
                add([[day.copy() for day in responses]], 'exhaustive_short_day_membership')
        for _ in range(50):
            responses = [[rng.choice(('a', 'aa', 'ab', 'b', 'z', 'abcdefghij')) for _ in range(rng.randrange(1, 9))]
                         for _ in range(rng.randrange(1, 9))]
            add([responses], 'seeded_lexical_membership_ties')
        add([[['a'] * 250 for _ in range(1000)]], 'analytic_fitting_250000_response_matrix', 'a')
        add([[['z'] * 1000] + [['a'] for _ in range(999)]], 'analytic_separate_day_and_row_maxima', 'a')
        add([[['z' * 10, 'a' * 10] for _ in range(1000)]], 'analytic_maximum_word_length_tie', 'a' * 10)
        add([[['abcdefghij'] * 1000]], 'analytic_maximum_single_day_duplicates', 'abcdefghij')
        add([[['aaaaaaaaaa'], ['aaaaaaaaa'], ['aaaaaaaaaa', 'aaaaaaaaa']]], 'explicit_lexical_prefix_tie')
    elif pid == 3546:
        for height, width, alphabet in ((1, 2, (1, 2, 3)), (1, 3, (1, 2, 3)),
                                        (2, 1, (1, 2, 3)), (3, 1, (1, 2, 3)),
                                        (2, 2, (1, 2, 3)), (2, 3, (1, 2)), (3, 2, (1, 2))):
            for values in product(alphabet, repeat=height * width):
                add([ [list(values[i * width:(i + 1) * width]) for i in range(height)] ], 'exhaustive_small_materialized_cuts')
        for _ in range(50):
            height, width = rng.randrange(1, 7), rng.randrange(1, 7)
            if height * width == 1:
                width = 2
            add([[[rng.choice((1, 2, 99999, 100000)) for _ in range(width)] for _ in range(height)]], 'seeded_numeric_materialized_cuts')
        for grid, answer in [
            ([[100000] * 100000], True), ([[100000] for _ in range(100000)], True),
            ([[100000] * 99999], False), ([[100000] for _ in range(99999)], False),
            ([[100000] * 200 for _ in range(500)], True), ([[1] * 99999 + [99999]], True),
        ]:
            add([grid], 'analytic_maximum_area_positive_grid', answer)
    else:
        for x in product((1, 2, 3), repeat=3):
            for y in product((1, 2, 1000000), repeat=3):
                add([list(x), list(y)], 'exhaustive_three_index_distinctness')
        for x in product((1, 2, 3), repeat=4):
            for y in ([1] * 4, [1, 2, 3, 4]):
                add([list(x), y.copy()], 'exhaustive_four_label_two_weight_patterns')
        for _ in range(50):
            n = rng.randrange(5, 19)
            add([[rng.choice((1, 2, 3, 999999, 1000000)) for _ in range(n)],
                 [rng.choice((1, 2, 999999, 1000000)) for _ in range(n)]], 'seeded_numeric_index_triples')
        add([[1] * 100000, [1000000] * 100000], 'analytic_maximum_length_one_label', -1)
        add([[1, 2] * 50000, [1000000] * 100000], 'analytic_maximum_length_two_labels', -1)
        add([[1 + i % 3 for i in range(100000)], [1000000] * 100000], 'analytic_maximum_length_three_labels', 3000000)
        add([list(range(1, 100001)), [1 + i % 1000 for i in range(100000)]], 'analytic_maximum_length_distinct_labels', 3000)
        labels = [999998 + i % 3 for i in range(100000)]
        weights = [1] * 100000
        weights[0:3] = [999998, 999999, 1000000]
        add([labels, weights], 'analytic_maximum_labels_sparse_weight_peaks', 2999997)
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    size = sum(len(q.encoded({'i': i, 'result': c['expected'],
                             'result_type': q.expected_type(c['expected'], language),
                             'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
               for i, c in enumerate(batch))
    return size + len(q.encoded({'done': len(batch)})) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('frozen case population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes']
               for language in ('javascript', 'python')):
            raise ValueError('expected observations exceed unchanged output cap')
    return cases, categories
