"""Fixed F definition oracles, independent of candidate sources and runners.

Full pinned-domain validation is separate from bounded reference computation.
Large analytic probes retain their narrower evidence class.
"""
from __future__ import annotations

import ast
from collections import deque
from functools import lru_cache
from itertools import combinations, product
import json
import random
import re

from . import imported_qualification as q

IDS = (3537, 3542, 3573, 3576, 3614)
PARAMETERS = {3537: ('n',), 3542: ('nums',), 3573: ('prices', 'k'),
              3576: ('nums', 'k'), 3614: ('s', 'k')}
STATEMENT_SHA256 = {3537: '0935007843c7aca28426f0510314cc638087afac1273dc2f380f0b547cc155ec', 3542: '955923a08604eada992449ce1e7919f7fc86e128c1fdae4a72b845cffbc98139', 3573: '26a211f1c7035a3c164a774187d02e38cea421eff304c999dee62d6bddbd9866', 3576: '4596d34b39ff6b90c2f9da49374f1294a59db3899a1af195acc4dd23df3925dd', 3614: '6e3daa4c0b0a2bdac63f3ecf7dc268957a4e50d142b4949ff1ab3bb0492e9224'}
EXAMPLE_COUNT = {3537: 3, 3542: 3, 3573: 2, 3576: 2, 3614: 3}
CASE_COUNT = {3537: 13, 3542: 472, 3573: 792, 3576: 1646, 3614: 2639}
CASES_SHA256 = {3537: 'e6f15bbab4c50368df48b70509379e9fd860ba190d97cb44c6ea5ac289ff3f7b', 3542: 'ff76ff5ca5cc7d8b6b4f288c3102f9ab93eb5d8b0d7f6e59ac39c57f3f4f543c', 3573: 'be080bdc9bbdb59114dc0ab4dd3f0441329a3855982597e94c466c00284f8eb4', 3576: 'e2f799539598493c82ea1b328d7c3ec8a246dd627e937e87d8dae43a2edaf5a5', 3614: '9e8773d19cd9e05cf6597bfd0fcddce6b84ef784aa4786ad3bbd2c10f190e06a'}
SEED_BASE = 202610271640
MAX_RESULT_LENGTH = 10**15
SMALL_BUDGET = {3537: 10, 3542: 9, 3573: 12, 3576: 10, 3614: 20}
OMITTED_MAXIMUM_SHAPES = {
    3537: 'Maximum n10 is retained. Valid n9 is omitted from executable cases because the complete n0..10 population exceeds unchanged aggregate case-file and observer ceilings; its exact expectation and size are separately retained.',
    3542: 'Maximum-length analytic shapes are included; arbitrary maximum-length state search is not attempted.',
    3573: 'Maximum n1000, k500 and price bounds are included as analytic shapes; arbitrary maximum-size endpoint subsets are not enumerated.',
    3576: 'Maximum-length parity and budget-boundary shapes are included; arbitrary maximum-length sign-state BFS is not attempted.',
    3614: 'Maximum source length, final length and index are included analytically; arbitrary huge strings are not materialized. Valid temporary length above the final cap is permitted.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _ints(values, low, high, minimum, maximum):
    return type(values) is list and minimum <= len(values) <= maximum and all(_integer(x, low, high) for x in values)


def processed_length(s):
    """Exact final length; early rejection uses a lower bound on final length."""
    length = 0
    for i, token in enumerate(s):
        if token == '*':
            length = max(0, length - 1)
        elif token == '#':
            length *= 2
        elif token != '%':
            length += 1
        # Each remaining character can remove at most one symbol. This is not
        # a prefix cap: a temporary overshoot that later shrinks is accepted.
        if length > MAX_RESULT_LENGTH + len(s) - i - 1:
            raise ValueError('final result necessarily exceeds pinned length bound')
    return length


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid == 3537:
        if not _integer(args[0], 0, 10):
            raise ValueError('grid exponent outside pinned domain')
    elif pid == 3542:
        if not _ints(args[0], 0, 100000, 1, 100000):
            raise ValueError('nonnegative array outside pinned domain')
    elif pid == 3573:
        prices, k = args
        if not _ints(prices, 1, 10**9, 2, 1000) or not _integer(k, 1, len(prices) // 2):
            raise ValueError('price or transaction budget outside pinned domain')
    elif pid == 3576:
        nums, k = args
        if (not _ints(nums, -1, 1, 1, 100000) or 0 in nums or not _integer(k, 1, len(nums))):
            raise ValueError('sign array or operation budget outside pinned domain')
    else:
        s, k = args
        if (type(s) is not str or not 1 <= len(s) <= 100000 or
                any(not ('a' <= c <= 'z' or c in '*#%') for c in s) or
                not _integer(k, 0, MAX_RESULT_LENGTH)):
            raise ValueError('program or zero-based index outside pinned domain')
        if processed_length(s) > MAX_RESULT_LENGTH:
            raise ValueError('final result length outside pinned domain')


def _coordinate_grid(n):
    side = 1 << n
    grid = []
    for row in range(side):
        result_row = []
        for col in range(side):
            value = 0
            for shift in range(n - 1, -1, -1):
                lower, right = (row >> shift) & 1, (col >> shift) & 1
                digit = (1 if lower else 0) if right else (2 if lower else 3)
                value = value * 4 + digit
            result_row.append(value)
        grid.append(result_row)
    return grid


@lru_cache(maxsize=16384)
def _zero_state_distance(state):
    if not any(state):
        return 0
    best = sum(value != 0 for value in state)
    for left in range(len(state)):
        for right in range(left, len(state)):
            minimum = min(state[left:right + 1])
            if minimum == 0:
                continue
            following = tuple(0 if left <= i <= right and value == minimum else value
                              for i, value in enumerate(state))
            best = min(best, 1 + _zero_state_distance(following))
    return best


def _endpoint_subsets(prices, k):
    best = 0
    for transactions in range(1, k + 1):
        for days in combinations(range(len(prices)), 2 * transactions):
            best = max(best, sum(abs(prices[days[i + 1]] - prices[days[i]])
                                 for i in range(0, len(days), 2)))
    return best


@lru_cache(maxsize=4096)
def _sign_state_distance(initial):
    todo, seen = deque([(initial, 0)]), {initial}
    while todo:
        state, distance = todo.popleft()
        if len(set(state)) == 1:
            return distance
        for i in range(len(state) - 1):
            following = state[:i] + (-state[i], -state[i + 1]) + state[i + 2:]
            if following not in seen:
                seen.add(following)
                todo.append((following, distance + 1))
    return None


def _literal_result(s):
    result = ''
    for token in s:
        if token == '*':
            result = result[:-1]
        elif token == '#':
            result += result
        elif token == '%':
            result = result[::-1]
        else:
            result += token
        if len(result) > 262144:
            raise ValueError('literal materialization budget exceeded')
    return result


def expected(pid, args):
    validate(pid, args)
    size = args[0] if pid == 3537 else len(args[0])
    if size > SMALL_BUDGET[pid]:
        raise ValueError('independent reference budget exceeded')
    if pid == 3537:
        return _coordinate_grid(args[0])
    if pid == 3542:
        return _zero_state_distance(tuple(args[0]))
    if pid == 3573:
        return _endpoint_subsets(*args)
    if pid == 3576:
        distance = _sign_state_distance(tuple(args[0]))
        return distance is not None and distance <= args[1]
    result = _literal_result(args[0])
    return result[args[1]] if args[1] < len(result) else '.'


def _homogeneous_program(length):
    if not _integer(length, 1, MAX_RESULT_LENGTH + 1):
        raise ValueError('constructive length outside declared range')
    return 'a' + ''.join('#' + ('a' if bit == '1' else '') for bit in bin(length)[3:])


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

    if pid == 3537:
        for n in (*range(9), 10):
            add([n], 'coordinate_rank_grid_maximum_included_n9_omitted')
    elif pid == 3542:
        for n in range(1, 6):
            for values in product(range(3), repeat=n):
                add([list(values)], 'exhaustive_short_nonnegative_states')
        for _ in range(100):
            n = rng.randrange(6, 10)
            add([[rng.choice((0, 1, 2, 99999, 100000)) for _ in range(n)]], 'seeded_exact_operation_search')
        for values, answer in (([0] * 100000, 0), ([100000] * 100000, 1),
                               (list(range(1, 100001)), 100000), (list(range(100000, 0, -1)), 100000),
                               ([1, 2] * 50000, 50001), ([0, 100000] * 50000, 50000)):
            add([values], 'analytic_maximum_length_operation_shapes', answer)
    elif pid == 3573:
        for n in range(2, 6):
            for values in product((1, 2, 3), repeat=n):
                for k in range(1, n // 2 + 1):
                    add([list(values), k], 'exhaustive_short_disjoint_transaction_endpoints')
        for _ in range(100):
            n = rng.randrange(6, 13)
            add([[rng.choice((1, 2, 500000000, 999999999, 1000000000)) for _ in range(n)], rng.randrange(1, n // 2 + 1)], 'seeded_endpoint_subsets_numeric_limits')
        for values, k, answer in (([10**9] * 1000, 500, 0),
                                  ([1 + i * 1000000 for i in range(1000)], 500, 999000000),
                                  ([1 + i * 1000000 for i in reversed(range(1000))], 1, 999000000),
                                  ([1, 10**9] * 500, 500, 500 * (10**9 - 1)),
                                  ([1, 10**9] * 500, 499, 499 * (10**9 - 1)),
                                  ([1] * 500 + [10**9] + [1] * 499, 500, 10**9 - 1)):
            add([values, k], 'analytic_maximum_transaction_and_numeric_shapes', answer)
    elif pid == 3576:
        for n in range(1, 8):
            for values in product((-1, 1), repeat=n):
                for k in range(1, n + 1):
                    add([list(values), k], 'exhaustive_short_sign_states_and_budgets')
        for _ in range(100):
            n = rng.randrange(8, 11)
            add([[rng.choice((-1, 1)) for _ in range(n)], rng.randrange(1, n + 1)], 'seeded_concrete_sign_bfs')
        for values, k, answer in (([1] * 100000, 1, True), ([-1] * 100000, 100000, True),
                                  ([-1] + [1] * 99999, 100000, False),
                                  ([-1, -1] + [1] * 99998, 1, True),
                                  ([-1, 1] * 50000, 49999, False),
                                  ([-1, 1] * 50000, 50000, True)):
            add([values, k], 'analytic_maximum_sign_parity_and_budget_shapes', answer)
    else:
        for n in range(1, 5):
            for tokens in product('ab*#%', repeat=n):
                s = ''.join(tokens)
                length = len(_literal_result(s))
                for k in sorted({0, max(0, length - 1), length, length + 1}):
                    add([s, k], 'exhaustive_short_literal_programs_and_indices')
        for _ in range(100):
            s = ''.join(rng.choice('az*#%') for _ in range(rng.randrange(5, 21)))
            length = len(_literal_result(s))
            add([s, rng.choice((0, max(0, length - 1), length, 10**15))], 'seeded_literal_program_boundaries')
        max_program = _homogeneous_program(10**15)
        for s, k, answer in ((max_program, 10**15 - 1, 'a'), (max_program, 10**15, '.'),
                             (_homogeneous_program(10**15 + 1) + '*', 10**15 - 1, 'a'),
                             ('a' * 100000, 99999, 'a'), ('a' * 100000, 100000, '.'),
                             ('*#%' * 33333 + '*', 0, '.'),
                             ('a' + '%' * 99999, 0, 'a'),
                             ('a' * 50000 + '*' * 50000, 0, '.')):
            add([s, k], 'analytic_maximum_input_output_length_and_index', answer)
        periodic = 'ab' + '#' * 48
        length = 2**49
        for suffix in ('', '%', '*', '%*', '*%', '%%'):
            final_length = length - suffix.count('*')
            for k in (0, 1, final_length - 1, final_length, 10**15):
                if k >= final_length:
                    answer = '.'
                elif suffix in ('%', '%*'):
                    answer = 'ba'[k % 2]
                elif suffix == '*%':
                    answer = 'ab'[(final_length - 1 - k) % 2]
                else:
                    answer = 'ab'[k % 2]
                add([periodic + suffix, k], 'analytic_large_periodic_index_and_reversal', answer)
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
