"""Independent exposed-development Git queue 01 reference contracts.

Only pinned official definitions inform these oracles. No candidate loading or
execution occurs here. Full-domain admission is separate from bounded reference
work; explicitly justified analytic probes cover selected large boundaries.
"""
from __future__ import annotations

import ast
from collections import Counter
from functools import lru_cache
from itertools import combinations, product
import json
import random
import re

from . import imported_qualification as q

IDS = (1957, 1971, 2017, 2048)
PARAMETERS = {1957: ('s',), 1971: ('n', 'edges', 'source', 'destination'),
              2017: ('grid',), 2048: ('n',)}
TITLES = {1957: 'Delete Characters to Make Fancy String', 1971: 'Find if Path Exists in Graph',
          2017: 'Grid Game', 2048: 'Next Greater Numerically Balanced Number'}
SLUGS = {1957: 'delete-characters-to-make-fancy-string', 1971: 'find-if-path-exists-in-graph',
         2017: 'grid-game', 2048: 'next-greater-numerically-balanced-number'}
STATEMENT_SHA256 = {
    1957: '8e84233c909da868fb60aa9f9b2644a4eae6c030fdb01635c8b8a45f6600f3ca',
    1971: 'a79f9261c2e2697f2ee27d6268a2135adaf14ae8d36f8feb91e0641ca01d9c38',
    2017: '47f4d24e86cf39ba4b45558ad53663a5cd049e8618c33b88cbbb131b70036bdd',
    2048: 'aef8e178b2661339fe4c3a0be5a313a75fb3daa1c3db93c69f3549d64aaa5541',
}
EXAMPLE_COUNT = {1957: 3, 1971: 2, 2017: 3, 2048: 3}
SEED_BASE = 202610271834
CONTRACTS = {
    1957: dict(domain='1..100000 lowercase ASCII characters', result='unique longest subsequence with no equal triple',
               reference='Enumerate all subsequences for length <= 12; maximize valid length, assert uniqueness.',
               complexity='Candidate review target O(n) time, O(n) output; no complexity qualification from finite probes.'),
    1971: dict(domain='1..200000 vertices; 0..200000 unique undirected non-self edges; in-range source/destination',
               result='boolean reachability, including zero-length path',
               reference='Floyd-Warshall Boolean transitive closure on at most 10 vertices.',
               complexity='Candidate review target O(n+m) time/space or union-find bound; no timing result yet.'),
    2017: dict(domain='2 by n grid; 1<=n<=50000; integer cells 1..100000', result='integer minimax second-path points',
               reference='Enumerate every first path, zero its cells, enumerate and sum every second path; n<=24.',
               complexity='Candidate review target O(n) time; no complexity qualification from finite probes.'),
    2048: dict(domain='integer n in 0..1000000', result='least balanced integer strictly greater than n',
               reference='Enumerate every integer 1..1224444 and count decimal digits, then select the next.',
               complexity='Reference is fixed full-domain enumeration; candidate complexity must be reviewed separately.'),
}
COMMON_CONTRACT = {
    'exposure': 'Exposed development only; never fresh confirmation.',
    'adapter': 'Existing imported_qualification packet/batches/observer, compare=return, policy=exact.',
    'candidate_interface': 'Unknown until independently reviewed oracle freeze and later authorized exact source read; ordered arguments come from official examples only.',
    'helpers': 'All candidate helpers and source dependencies must be charged in later source review; none inferred here.',
    'operations': 'Pure single-call value interface; no stateful constructor operations.',
    'mutation': 'Qualification observer requires arguments unchanged; this is an explicit conservative service contract, not a claim that the official statement prohibits local input mutation.',
    'alias': 'Scalar results have no return/input alias; exact observer expects no alias edges.',
    'numeric': 'Exact integers and booleans; reject bool as an integer. Maximum grid score <= 5e9, exactly representable in JavaScript Number.',
    'unicode': '1957 permits lowercase English ASCII only; no Unicode normalization assumptions.',
    'expected_values': 'Host only; never included in sandbox packets.',
    'limits': 'q.MAX_FILE, q.MAX_PACKET and q.LIMITS remain unchanged.',
}
OMITTED_MAXIMUM_SHAPES = {
    1957: 'No maximum length omitted; arbitrary maximum-length subsequence enumeration is not claimed.',
    1971: 'Maximum n is tested with sparse graphs. A 200000-edge explicit graph exceeds the unchanged packet cap in available constructions; 40000-node chains are retained. No maximum-edge execution claim.',
    2017: 'Maximum n and maximum cell values tested together; arbitrary maximum-size path enumeration is not claimed.',
    2048: 'All normative n are admitted. Complete output-changing intervals are probed at both endpoints; candidate is not run on every n.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def validate(pid, args):
    """Full normative domain, not a small-test-domain filter."""
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    valid = False
    if pid == 1957:
        s = args[0]
        valid = type(s) is str and 1 <= len(s) <= 100000 and set(s) <= set('abcdefghijklmnopqrstuvwxyz')
    elif pid == 1971:
        n, edges, start, end = args
        valid = (_integer(n, 1, 200000) and _integer(start, 0, n-1) and _integer(end, 0, n-1)
                 and type(edges) is list and len(edges) <= 200000
                 and all(type(e) is list and len(e) == 2 and _integer(e[0], 0, n-1)
                         and _integer(e[1], 0, n-1) and e[0] != e[1] for e in edges))
        if valid:
            valid = len({tuple(sorted(e)) for e in edges}) == len(edges)
    elif pid == 2017:
        grid = args[0]
        valid = (type(grid) is list and len(grid) == 2 and type(grid[0]) is list
                 and 1 <= len(grid[0]) <= 50000 and all(type(row) is list and len(row) == len(grid[0])
                 and all(_integer(value, 1, 100000) for value in row) for row in grid))
    else:
        valid = _integer(args[0], 0, 1000000)
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _fancy_subsequences(s):
    best = set(); longest = -1
    for mask in range(1 << len(s)):
        selected = ''.join(char for i, char in enumerate(s) if mask >> i & 1)
        if len(selected) < longest or any(selected[i] == selected[i+1] == selected[i+2] for i in range(len(selected)-2)):
            continue
        if len(selected) > longest:
            longest = len(selected); best.clear()
        best.add(selected)
    if len(best) != 1:
        raise AssertionError('definition uniqueness not witnessed')
    return best.pop()


def _closure(n, edges, start, end):
    reachable = [[i == j for j in range(n)] for i in range(n)]
    for a, b in edges:
        reachable[a][b] = reachable[b][a] = True
    for via in range(n):
        for a in range(n):
            for b in range(n):
                reachable[a][b] = reachable[a][b] or (reachable[a][via] and reachable[via][b])
    return reachable[start][end]


def _grid_paths(grid):
    n = len(grid[0]); scores = []
    for first_down in range(n):
        residual = [list(row) for row in grid]
        for c in range(first_down+1):
            residual[0][c] = 0
        for c in range(first_down, n):
            residual[1][c] = 0
        responses = []
        for second_down in range(n):
            responses.append(sum(residual[0][:second_down+1]) + sum(residual[1][second_down:]))
        scores.append(max(responses))
    return min(scores)


@lru_cache(maxsize=1)
def balanced_numbers():
    """Complete integer enumeration; upper witness 1224444 covers n<=1e6."""
    numbers = []
    for value in range(1, 1224445):
        digits = str(value)
        if '0' in digits:
            continue
        counts = Counter(digits)
        if all(count == int(digit) for digit, count in counts.items()):
            numbers.append(value)
    assert numbers[-1] == 1224444
    return tuple(numbers)


def expected(pid, args):
    validate(pid, args)
    if pid == 1957:
        if len(args[0]) > 12:
            raise ValueError('bounded subsequence reference budget exceeded')
        return _fancy_subsequences(args[0])
    if pid == 1971:
        if args[0] > 10:
            raise ValueError('bounded graph closure budget exceeded')
        return _closure(*args)
    if pid == 2017:
        if len(args[0][0]) > 24:
            raise ValueError('bounded path enumeration budget exceeded')
        return _grid_paths(args[0])
    return next(value for value in balanced_numbers() if value > args[0])


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned official definition bytes required')
    statement = re.sub(r'(?m)^L\d+: ?', '', raw.decode())
    if f'{pid}. {TITLES[pid]}' not in statement or f'https://leetcode.com/problems/{SLUGS[pid]}/' not in statement:
        raise ValueError('numeric/title/slug identity mismatch')
    cases = []
    for match in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)', statement):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(item.arg for item in call.keywords) != PARAMETERS[pid]:
            raise ValueError('ordered public-example parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('reference disagrees with official example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, raw):
    cases = public_examples(pid, raw)
    categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid); sentinel = object()

    def add(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 1957:
        for alphabet, lengths in [('ab', range(1, 9)), ('abc', range(1, 5))]:
            for n in lengths:
                for letters in product(alphabet, repeat=n):
                    add([''.join(letters)], 'exhaustive_strings_and_subsequences')
        for _ in range(50):
            add([''.join(rng.choice('aaabbccxyz') for _ in range(rng.randint(5, 12)))], 'seeded_subsequence_search')
        for value, answer in [('a'*100000, 'aa'), ('ab'*50000, 'ab'*50000),
                              ('a'*50000+'z'*50000, 'aazz'), ('abc'*33333+'a', 'abc'*33333+'a'),
                              ('aaa'*16666+'bbb'*16666+'zzzz', 'aabbzz')]:
            add([value], 'analytic_maximum_run_structure', answer)
    elif pid == 1971:
        for n in range(1, 5):
            possible = list(combinations(range(n), 2))
            for mask in range(1 << len(possible)):
                edges = [list(edge) for i, edge in enumerate(possible) if mask >> i & 1]
                for start in range(n):
                    for end in range(n):
                        add([n, edges, start, end], 'exhaustive_simple_graphs_and_endpoint_pairs')
        for _ in range(60):
            n = rng.randint(5, 10)
            edges = [list(edge) for edge in combinations(range(n), 2) if rng.randrange(4) == 0]
            rng.shuffle(edges)
            edges = [edge[::-1] if rng.randrange(2) else edge for edge in edges]
            add([n, edges, rng.randrange(n), rng.randrange(n)], 'seeded_edge_order_orientation')
        for args, answer in [([200000, [], 0, 199999], False), ([200000, [], 199999, 199999], True),
                             ([200000, [[199999, 0]], 0, 199999], True),
                             ([40000, [[i, i+1] for i in range(39999)], 0, 39999], True),
                             ([40000, [[i, i+1] for i in range(39998)], 0, 39999], False)]:
            add(args, 'analytic_large_graph_boundaries', answer)
    elif pid == 2017:
        for n in range(1, 5):
            for cells in product((1, 3), repeat=2*n):
                add([[list(cells[:n]), list(cells[n:])]], 'exhaustive_grid_path_pairs')
        for _ in range(70):
            n = rng.randint(2, 24)
            add([[[rng.choice((1, 2, 99999, 100000)) for _ in range(n)] for _ in range(2)]], 'seeded_path_pairs_numeric_extremes')
        for n, value in [(1, 100000), (49999, 100000), (50000, 100000), (50000, 1)]:
            add([[[value]*n, [value]*n]], 'analytic_uniform_balanced_split', (n//2)*value)
        add([[[100000]*50000, [1]*50000]], 'analytic_asymmetric_rows', 49999)
        add([[[1]*50000, [100000]*50000]], 'analytic_asymmetric_rows', 49999)
    else:
        for n in range(501):
            add([n], 'exhaustive_small_input_integers')
        for value in balanced_numbers():
            for n in (value-1, value, value+1):
                if 0 <= n <= 1000000:
                    add([n], 'balanced_transition_neighbors')
        for _ in range(100):
            add([rng.randrange(1000001)], 'seeded_full_domain_integers')
        add([1000000], 'maximum_input_upper_witness')
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    records = [{'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []} for i, c in enumerate(batch)]
    return sum(len(q.encoded(record)) for record in records) + len(q.encoded({'done': len(batch)})) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case artifact exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('projected successful output exceeds unchanged observer cap')
    return cases, categories
