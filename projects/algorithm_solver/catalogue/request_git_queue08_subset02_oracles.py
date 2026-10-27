"""Queue 08 subset 02 source-blind bounded references; no candidate qualification.

The current official definitions, domains and frozen finite cases are separate
from unknown native source interfaces, resource behavior and full-domain proof.
"""
from __future__ import annotations
import ast
from collections import Counter
from itertools import combinations_with_replacement, product
import json
import random
import re
import string
from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (3020, 3039, 3048, 3070, 3080)
PARAMETERS = {3020: ('nums',), 3039: ('s',), 3048: ('nums', 'changeIndices'), 3070: ('grid', 'k'), 3080: ('nums', 'queries')}
STATEMENT_SHA256 = {3020: '878f1e0ab7ea715f14416c9329448c4b2f9c9847cf2abb7e81538057ea2f67e6', 3039: '00feabffb53072b4b3e04dea998beff8066982921c78ac1c1e9c774a331f6673', 3048: '99d828033d82e591af479bce678ac331da62b1564e625c2c44a05c3a52d49045', 3070: '043f1fe04bfee108d34013344977b1c4d6425ef5833c2c16ec1467ba24c37305', 3080: 'f76151ea51d496561f3fc7f31586c831f66d5b7b65bd393c4da5bb03f99acf60'}
TITLES = {3020: 'Find the Maximum Number of Elements in Subset', 3039: 'Apply Operations to Make String Empty', 3048: 'Earliest Second to Mark Indices I', 3070: 'Count Submatrices with Top-Left Element and Sum Less Than k', 3080: 'Mark Elements on Array by Performing Queries'}
EXAMPLE_COUNT = {3020: 2, 3039: 2, 3048: 3, 3070: 2, 3080: 2}
CASE_COUNT = {3020: 555, 3039: 3344, 3048: 1680, 3070: 2058, 3080: 5219}
CASES_SHA256 = {3020: 'ef9d555d0644cab6d7af573ccb46a0a1a78e0a8ae0b277bcef6df310fa9e26bf', 3039: '1bda52a70c0dba6af3d3ac8539aea74dcc28e4611193f5215ec5ac2cb24f10f8', 3048: '212b6034ca165d37fdb88e480bbd67f44a854237ec6ba38fe8195bcebda327a7', 3070: '17c6809b0aa2f37478de1b6e5c6e615fc437127a507742d292ff3be5cac1bf16', 3080: '427597d728a805fa2a26deb637c09d1959913320bce66a73c1aaa6e1a2a1dcf8'}
SEED_BASE = 202610272015
OMITTED_MAXIMUM_SHAPES = {
3020: 'Combined maximum [1000000000]*100000 exceeds unchanged packet cap; length and numeric maxima are separate.',
3039: 'Length 500000 probes are analytic; no exhaustive full string domain. Prior unsolicited global development snippet exposure remains explicit.',
3048: 'Only bounded state graphs and analytic large schedules; no universal candidate scheduling/performance claim.',
3070: 'A 1000 by 1000 zero grid already needs 2002001 compact JSON bytes before envelope, beyond unchanged 1100000 cap. Maximum area omitted, full validator unchanged.',
3080: 'Simultaneous maximum query/array shapes can exceed packet/output caps. Retained length/count probes fit; full-domain transport is not established.'}


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported exact identity or ordered argument shape')
    if pid == 3020:
        valid = ints(args[0], 1, 10**9, 2, 100000)
    elif pid == 3039:
        valid = text(args[0], maximum=500000)
    elif pid == 3048:
        a, b = args
        valid = ints(a, 0, 10**9, 1, 2000) and ints(b, 1, len(a), 1, 2000)
    elif pid == 3070:
        grid, k = args
        valid = (type(grid) is list and 1 <= len(grid) <= 1000 and type(grid[0]) is list
                 and 1 <= len(grid[0]) <= 1000 and all(ints(row, 0, 1000, len(grid[0]), len(grid[0])) for row in grid)
                 and integer(k, 1, 10**9))
    else:
        a, queries = args
        valid = (ints(a, 1, 100000, 1, 100000) and type(queries) is list and 1 <= len(queries) <= len(a)
                 and all(ints(row, 0, len(a)-1, 2, 2) for row in queries))
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _square_subsets(nums):
    best = 1
    for mask in range(1, 1 << len(nums)):
        size = mask.bit_count()
        if size <= best or size % 2 == 0:
            continue
        selected = Counter(x for i, x in enumerate(nums) if mask >> i & 1)
        for root in selected:
            required = Counter(); value = root
            for _ in range(size//2):
                required[value] += 2; value *= value
            required[value] += 1
            if required == selected:
                best = size; break
    return best


def _rounds(s):
    previous = s
    while s:
        previous = s; removed = set(); retained = []
        for c in s:
            if c not in removed:
                removed.add(c)
            else:
                retained.append(c)
        s = ''.join(retained)
    return previous


def _mark_states(nums, changes):
    # Decrementing below zero cannot help future marking at zero and may be
    # replaced by no-op. Every useful state has 0 <= remaining <= original.
    states = {(tuple(nums), 0)}; full = (1 << len(nums))-1
    for second, current in enumerate(changes, 1):
        following = set(states)
        for remaining, marked in states:
            if remaining[current-1] == 0:
                new = marked | (1 << (current-1))
                if new == full:
                    return second
                following.add((remaining, new))
            for i, x in enumerate(remaining):
                if x > 0:
                    nxt = list(remaining); nxt[i] -= 1
                    following.add((tuple(nxt), marked))
        states = following
    return -1


def _anchored(grid, k):
    return sum(sum(grid[i][j] for i in range(r+1) for j in range(c+1)) <= k
               for r in range(len(grid)) for c in range(len(grid[0])))


def _queries(nums, queries):
    marked = [False]*len(nums); answer = []
    for index, count in queries:
        marked[index] = True
        for _ in range(count):
            candidates = [i for i in range(len(nums)) if not marked[i]]
            if not candidates:
                break
            marked[min(candidates, key=lambda i: (nums[i], i))] = True
        answer.append(sum(x for i, x in enumerate(nums) if not marked[i]))
    return answer


def expected(pid, args):
    validate(pid, args)
    if pid == 3020 and len(args[0]) <= 12:
        return _square_subsets(args[0])
    if pid == 3039 and len(args[0]) <= 80:
        return _rounds(args[0])
    if pid == 3048 and len(args[0]) <= 4 and len(args[1]) <= 9 and max(args[0]) <= 4:
        return _mark_states(*args)
    if pid == 3070 and len(args[0])*len(args[0][0]) <= 100:
        return _anchored(*args)
    if pid == 3080 and len(args[0]) <= 32:
        return _queries(*args)
    raise ValueError('bounded independent reference budget exceeded')


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    envelope = json.loads(raw)
    if type(envelope) is not dict or envelope.get('problem_id') != pid or type(envelope.get('web_result')) is not str:
        raise ValueError('invalid definition envelope')
    body = re.sub(r'^L\d+: ?', '', envelope['web_result'], flags=re.M)
    if f'{pid}. {TITLES[pid]}' not in body:
        raise ValueError('numeric identity/title mismatch')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', body, re.S):
        call = ast.parse('f('+match[1].strip()+')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(x.arg for x in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(x.value) for x in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, statement):
    cases = []; categories = []; seen = {}; rng = random.Random(SEED_BASE+pid); sentinel = object()
    def add(args, category, answer=sentinel):
        validate(pid, args); result = expected(pid, args) if answer is sentinel else answer; key = q.encoded(args)
        if key in seen:
            index = seen[key]
            if not q.exact(result, cases[index]['expected']): raise ValueError('conflicting duplicate expectation')
            if category not in categories[index].split('|'): categories[index] += '|'+category
            return
        seen[key] = len(cases); cases.append({'args': args, 'expected': result, 'compare': 'return'}); categories.append(category)
    for case in public_examples(pid, statement): add(case['args'], 'pinned_public_example', case['expected'])
    if pid == 3020:
        for n in range(2, 9):
            for values in combinations_with_replacement((1, 2, 4, 16), n):
                add([list(values)], 'exhaustive_small_multisets_index_subsets')
        for _ in range(60):
            add([[rng.choice((1, 2, 3, 4, 9, 16, 81, 256, 65536, 10**9)) for _ in range(rng.randrange(2, 11))]], 'seeded_missing_square_chain_links')
        add([[1]*100000], 'analytic_maximum_even_ones', 99999)
        add([[1]*99999+[2]], 'analytic_maximum_odd_ones', 99999)
        add([[2]*99992+[4, 4, 16, 16, 256, 256, 65536, 65536]], 'analytic_maximum_complete_square_chain', 9)
        add([[10**9]*10], 'analytic_separate_numeric_maximum', 1)
    elif pid == 3039:
        for n in range(1, 8):
            for chars in product('abc', repeat=n): add([''.join(chars)], 'exhaustive_small_literal_rounds')
        for _ in range(60): add([''.join(rng.choices('abcxyz', k=rng.randrange(1, 81)))], 'seeded_round_ties_order')
        add(['a'*500000], 'analytic_maximum_uniform', 'a')
        add(['ab'*250000], 'analytic_maximum_equal_frequency', 'ab')
        add(['a'*250000+'b'*250000], 'analytic_maximum_separated_equal_frequency', 'ab')
        add(['ab'*249999+'ba'], 'analytic_maximum_last_occurrence_order', 'ba')
    elif pid == 3048:
        for n in range(1, 4):
            for nums in product(range(3), repeat=n):
                for m in range(1, (5 if n <= 2 else 3)+1):
                    for changes in product(range(1, n+1), repeat=m):
                        add([list(nums), list(changes)], 'exhaustive_bounded_schedule_state_graphs')
        for _ in range(60):
            n = rng.randrange(1, 5)
            add([[rng.randrange(5) for _ in range(n)], [rng.randrange(1, n+1) for _ in range(rng.randrange(1, 10))]], 'seeded_schedule_state_graphs')
        add([[0]*2000, list(range(1, 2001))], 'analytic_maximum_mark_every_zero_once', 2000)
        add([[1]*2000, list(range(1, 2001))], 'analytic_maximum_insufficient_total_seconds', -1)
        add([[0]*2000, [1]*2000], 'analytic_maximum_missing_indices', -1)
        add([[10**9], [1]*2000], 'analytic_numeric_work_exceeds_seconds', -1)
        add([[1999], [1]*2000], 'analytic_last_second_mark_after_decrements', 2000)
    elif pid == 3070:
        for rows in range(1, 4):
            for cols in range(1, 4):
                for values in product((0, 1), repeat=rows*cols):
                    grid = [list(values[r*cols:(r+1)*cols]) for r in range(rows)]
                    for k in sorted({1, max(1, sum(values)), sum(values)+1}):
                        add([grid, k], 'exhaustive_small_binary_anchored_rectangles_inclusive_thresholds')
        for _ in range(60):
            rows, cols = rng.randrange(1, 11), rng.randrange(1, 11)
            grid = [[rng.randrange(1001) for _ in range(cols)] for _ in range(rows)]
            add([grid, rng.randrange(1, rows*cols*1000+1)], 'seeded_asymmetric_rectangles')
        add([[[0]*600 for _ in range(600)], 1], 'analytic_fitting_large_zero_square', 360000)
        add([[[1000]*400 for _ in range(400)], 10**9], 'analytic_fitting_large_numeric_square', 160000)
        add([[[1000]*1000], 1000000], 'analytic_maximum_column_count_exact_threshold', 1000)
        add([[[1000] for _ in range(1000)], 999999], 'analytic_maximum_row_count_below_total', 999)
    else:
        for n in range(1, 5):
            queries = list(product(range(n), repeat=2))
            for values in product((1, 2), repeat=n):
                for m in range(1, min(n, 2)+1):
                    for history in product(queries, repeat=m):
                        add([list(values), [list(x) for x in history]], 'exhaustive_small_value_index_query_histories')
        for _ in range(60):
            n = rng.randrange(1, 33)
            add([[rng.randrange(1, 100001) for _ in range(n)], [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randrange(1, n+1))]], 'seeded_ties_repeated_marks_exhaustion')
        add([[100000]*100000, [[0, 0]]], 'analytic_maximum_sum_above_32_bit', [9999900000])
        add([[1]*100000, [[0, 0]]*100000], 'analytic_maximum_query_count_repeated_mark', [99999]*100000)
        add([[1]*100000, [[99999, 99999]]], 'analytic_maximum_query_exhaustion', [0])
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    return (sum(len(q.encoded({'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                              'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
                for i, c in enumerate(batch)) + len(q.encoded({'done': len(batch)})) + (language == 'python'))


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('frozen case population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('expected observations exceed unchanged output cap')
    return cases, categories
