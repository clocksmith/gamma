"""Fixed source-blind batch E definition oracles and full input domains.

Finite small references and separately justified analytic probes remain distinct.
This owner loads no candidate source and grants no execution or qualification.
"""
from __future__ import annotations

import ast
from functools import lru_cache
from itertools import combinations, permutations, product
import json
from math import factorial, isqrt
import random
import re

from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (3227, 3234, 3556, 3577, 3584)
PARAMETERS = {3227: ('s',), 3234: ('s',), 3556: ('s',), 3577: ('complexity',), 3584: ('nums', 'm')}
STATEMENT_SHA256 = {
    3227: '82d857c840929888d69c7b0a3a882bf5ebe538f42e3aa7a714712dd5df98a30c',
    3234: '2e5589b2e736873269c8e78349e07df754614aa48b42643550dddac1f5a36060',
    3556: '5b57e2a04aa064536fe08cdbf980055e592b93a45cb2581ffa2569f2452fdf5c',
    3577: 'feddd3388c77afbdca5fab660dc9cefa881d00b646ea1dc5d6faaeb0d39bd3c8',
    3584: '4eaa07fbc64538d2e420ba3d94b5075a6d453c83ac1467dcff23fce17276e828',
}
EXAMPLE_COUNT = {3227: 2, 3234: 2, 3556: 2, 3577: 2, 3584: 3}
CASE_COUNT = {3227: 558, 3234: 1071, 3556: 844, 3577: 409, 3584: 488}
CASES_SHA256 = {
    3227: 'f2b47e12022991061799250b26d01d101b56256b506f1859e977d633d1378f62',
    3234: '2c08c07588951925f6c95137ced50b19cc86df04fbe6789e5bd6e03c778a4392',
    3556: 'bc6c71d56def27960e2eef66fccf1378c45d223df1a9781c9423b6ba0bb7f21b',
    3577: '192041023b91860dcaead7f38366a0e308bec4b51b46c937350ca1ac69ae17d0',
    3584: 'c65c933e92015d947ae18c492362f439bb047b36989065dbdc2fd3d7ae323a7a',
}
SMALL_BUDGET = {3227: 12, 3234: 64, 3556: 10, 3577: 8, 3584: 12}
SEED_BASE = 202610271510
MOD = 1000000007
OMITTED_MAXIMUM_SHAPES = {
    3227: 'Maximum-length game shapes included; arbitrary full-length minimax is not attempted.',
    3234: 'Maximum-length analytic strings retained; arbitrary full-length substring enumeration is not attempted. Resource outcomes remain unmeasured.',
    3556: 'Full input-length and numeric-boundary strings included; the finite set does not enumerate every possible digit string.',
    3577: 'Length-100000 arrays of ten-digit complexities can exceed the unchanged packet cap. Fitting maximum-count and separate maximum-value probes are retained.',
    3584: 'Maximum-length endpoint shapes included; arbitrary full-length subsequence enumeration is not attempted.',
}


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 3227:
        valid = text(args[0], maximum=100000)
    elif pid == 3234:
        valid = text(args[0], '01', 1, 40000)
    elif pid == 3556:
        valid = text(args[0], '0123456789', 1, 10)
    elif pid == 3577:
        valid = ints(args[0], 1, 10**9, 2, 100000)
    else:
        valid = ints(args[0], -100000, 100000, 1, 100000) and integer(args[1], 1, len(args[0]))
    if not valid:
        raise ValueError('outside pinned full statement domain')


@lru_cache(maxsize=16384)
def _game_win(bits, player):
    required = 1 if player == 0 else 0
    for left in range(len(bits)):
        for right in range(left + 1, len(bits) + 1):
            if bits[left:right].count('1') % 2 == required:
                if not _game_win(bits[:left] + bits[right:], 1 - player):
                    return True
    return False


def _dominant_intervals(s):
    return sum(s[left:right].count('1') >= s[left:right].count('0')**2
               for left in range(len(s)) for right in range(left + 1, len(s) + 1))


@lru_cache(maxsize=32768)
def _trial_prime(value):
    return value >= 2 and all(value % divisor for divisor in range(2, isqrt(value) + 1))


def _prime_substrings(s):
    values = {int(s[left:right]) for left in range(len(s)) for right in range(left + 1, len(s) + 1)}
    return sum(sorted((value for value in values if _trial_prime(value)), reverse=True)[:3])


def _unlock_orders(complexity):
    count = 0
    for order in permutations(range(1, len(complexity))):
        unlocked = {0}
        for target in order:
            if not any(witness < target and complexity[witness] < complexity[target] for witness in unlocked):
                break
            unlocked.add(target)
        else:
            count += 1
    return count % MOD


def _subsequence_endpoints(values, length):
    return max(values[indices[0]] * values[indices[-1]] for indices in combinations(range(len(values)), length))


def expected(pid, args):
    validate(pid, args)
    if len(args[0]) > SMALL_BUDGET[pid]:
        raise ValueError('bounded independent reference budget exceeded')
    if pid == 3227:
        return _game_win(''.join('1' if char in 'aeiou' else '0' for char in args[0]), 0)
    if pid == 3234:
        return _dominant_intervals(args[0])
    if pid == 3556:
        return _prime_substrings(args[0])
    if pid == 3577:
        return _unlock_orders(args[0])
    return _subsequence_endpoints(*args)


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

    if pid == 3227:
        for length in range(1, 9):
            for letters in product('ab', repeat=length):
                add([''.join(letters)], 'exhaustive_binary_game_states_length_1_to_8')
        for _ in range(40):
            add([''.join(rng.choice('aeioubyz') for _ in range(rng.randrange(9, 13)))], 'seeded_minimax_game_states')
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for value, answer in [('b' * 100000, False), ('a' + 'b' * 99999, True),
                              ('a' * 100000, True), ('ab' * 50000, True),
                              (alphabet * 3846 + alphabet[:4], True), ('y' * 100000, False)]:
            add([value], 'analytic_maximum_length_game', answer)
    elif pid == 3234:
        for length in range(1, 10):
            for digits in product('01', repeat=length):
                add([''.join(digits)], 'exhaustive_binary_intervals_length_1_to_9')
        for _ in range(40):
            add([''.join(rng.choice('01') for _ in range(rng.randrange(10, 65)))], 'seeded_direct_interval_counts')
        n = 40000
        t = n - 2
        block_count = 20000 * 20001 // 2 + sum(20000 - z*z + 1 for z in range(1, isqrt(20000) + 1))
        for value, answer in [('1' * n, n * (n + 1) // 2), ('0' * n, 0),
                              ('0' + '1' * (n - 1), n * (n + 1) // 2 - 1),
                              ('1' * (n - 1) + '0', n * (n + 1) // 2 - 1),
                              ('00' + '1' * t, t * (t + 1) // 2 + 2*t - 3),
                              ('0' * 20000 + '1' * 20000, block_count),
                              ('1' * 20000 + '0' * 20000, block_count)]:
            add([value], 'analytic_length_40000_interval_shape', answer)
    elif pid == 3556:
        for length in range(1, 5):
            for digits in product('01237', repeat=length):
                add([''.join(digits)], 'exhaustive_small_prime_substring_values')
        for _ in range(50):
            add([''.join(rng.choice('0123456789') for _ in range(rng.randrange(5, 11)))], 'seeded_full_length_prime_trials')
        for value in ('0000000000', '2222222222', '9999999967', '4294967291',
                      '2147483647', '9999999999', '0000000011', '0101010101',
                      '1000000007', '1000000000', '9999800001', '9998000099'):
            add([value], 'full_length_numeric_prime_trials')
    elif pid == 3577:
        for length in range(2, 6):
            for values in product((1, 2, 3), repeat=length):
                add([list(values)], 'exhaustive_small_unlock_orders')
        for _ in range(40):
            add([[rng.choice((1, 2, 3, 999999999, 1000000000)) for _ in range(rng.randrange(6, 9))]],
                'seeded_explicit_unlock_permutations')
        fact = factorial(99999) % MOD
        for values, answer in [([1] + [2] * 99999, fact), (list(range(1, 100001)), fact),
                               ([2, 1] + [3] * 99998, 0), ([1] * 100000, 0),
                               ([1] + [999999999] * 99999, fact), ([1] + [2] * 99998 + [1], 0),
                               ([1] + [1000000000] * 89999, factorial(89999) % MOD)]:
            add([values], 'analytic_large_root_order_shapes', answer)
    else:
        for length in range(1, 5):
            for values in product((-1, 0, 1), repeat=length):
                for size in range(1, length + 1):
                    add([list(values), size], 'exhaustive_small_index_subsequences')
        for _ in range(50):
            length = rng.randrange(5, 13)
            values = [rng.choice((-100000, -99999, -1, 0, 1, 99999, 100000)) for _ in range(length)]
            add([values, rng.randrange(1, length + 1)], 'seeded_numeric_index_subsequences')
        for args, answer in [([[-100000] * 100000, 1], 10**10),
                             ([[-100000] * 100000, 100000], 10**10),
                             ([[100000] * 100000, 50000], 10**10),
                             ([[0] * 100000, 50000], 0),
                             ([[100000] + [0] * 99998 + [-100000], 100000], -10**10),
                             ([[-100000] + [0] * 99998 + [-100000], 100000], 10**10),
                             ([[-100000, 100000] * 50000, 99999], 10**10),
                             ([list(range(-50000, 50000)), 100000], -2499950000),
                             ([list(range(-50000, 50000)), 1], 2500000000)]:
            add(args, 'analytic_maximum_length_endpoint_shapes', answer)
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
        raise ValueError('frozen batch E population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('projected successful observation exceeds unchanged output cap')
    return cases, categories
