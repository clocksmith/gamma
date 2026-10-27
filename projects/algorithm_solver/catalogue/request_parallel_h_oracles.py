"""Source-blind fixed batch H graph/state oracles; no candidate loading.

Full normative input domains remain distinct from bounded exhaustive references.
Large probes have separate analytic justifications, not full-domain proof.
"""
from __future__ import annotations

import ast
from collections import deque
from itertools import combinations, product
import json
import random
import re

from . import imported_qualification as q
from .imported_clean_domains import integer, ints

IDS = (3534, 3568, 3600, 3613, 3620)
PARAMETERS = {3534: ('n', 'nums', 'maxDiff', 'queries'), 3568: ('classroom', 'energy'),
              3600: ('n', 'edges', 'k'), 3613: ('n', 'edges', 'k'), 3620: ('edges', 'online', 'k')}
STATEMENT_SHA256 = {
    3534: 'f1af9540dbf70ae0c35cbbcdf302e00a6e51136e3ea81875285b7cc17a0caaed',
    3568: 'eeecee49ad430279fa5cedeecb7d84a2a6ddf1a6d79932664d773cb32395f605',
    3600: '6e76ebe5b6a3f6cf37293a54f11b1ae0c05467a81beb596e540385eeaf857639',
    3613: 'ea378cfb3ee496cff718043f3d6091f25139278bded2a34a9108ef75568b5bd6',
    3620: '7a5eb127b96aec744b4f297596f59f8a42df8208211266fbd1353c183bf95bf3',
}
EXAMPLE_COUNT = {3534: 3, 3568: 3, 3600: 3, 3613: 2, 3620: 2}
CASE_COUNT = {3534: 428, 3568: 850, 3600: 351, 3613: 188, 3620: 828}
CASES_SHA256 = {3534: '2452898707934a571b06247d6c2054293a186218e6b3525b08ff70b881015260', 3568: '139fbda56d5c427c74cdd1865fd3e838cf7c39cd9b80896683d2994983db4b31', 3600: 'eec2b379a8baa1337dfe230a56b2791cdaf619a51a2540d4275137bc978303a0', 3613: '4c1e410f29096e0823d95b455c3df8616727a3dcbfa691304d607d99d8ea0577', 3620: 'f73437a3122ec01d119f60512f6ac52fd97bd36065aaddd70d6a14f7e096940a'}
SEED_BASE = 202610271640
OMITTED_MAXIMUM_SHAPES = {
    3534: 'Maximum node and query counts are separate probes; their simultaneous largest decimal-valued shape exceeds the unchanged packet cap.',
    3568: 'Maximum grid dimensions, energy and litter count are retained analytically. Not every full Cartesian state-space shape is enumerated.',
    3600: 'A 100000-node connected explicit tree exceeds the unchanged packet cap. Maximum n is tested disconnected; smaller connected trees and dense small graphs are retained.',
    3613: 'Maximum node count, edge multiplicity and weight are tested in separate shapes. A 100000-edge population of long decimal endpoints and weights exceeds the packet cap; not every simultaneous maximum is transported.',
    3620: 'Maximum vertex count is tested with a direct route and a zero-cost chain when the exact packet fits. Simultaneous maximum large-cost edge population is not transported.',
}


def _components(n, edges):
    adjacency = [[] for _ in range(n)]
    for edge in edges:
        a, b = edge[:2]
        adjacency[a].append(b); adjacency[b].append(a)
    seen = set(); count = 0
    for start in range(n):
        if start in seen:
            continue
        count += 1; seen.add(start); stack = [start]
        while stack:
            for target in adjacency[stack.pop()]:
                if target not in seen:
                    seen.add(target); stack.append(target)
    return count


def _dag(n, edges):
    adjacency = [[] for _ in range(n)]; indegree = [0] * n
    for a, b, _ in edges:
        adjacency[a].append(b); indegree[b] += 1
    ready = deque(i for i, degree in enumerate(indegree) if degree == 0); visited = 0
    while ready:
        node = ready.popleft(); visited += 1
        for target in adjacency[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return visited == n


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    valid = False
    if pid == 3534:
        n, nums, difference, queries = args
        valid = (integer(n, 1, 100000) and ints(nums, 0, 100000, n, n) and integer(difference, 0, 100000)
                 and type(queries) is list and 1 <= len(queries) <= 100000
                 and all(ints(pair, 0, n - 1, 2, 2) for pair in queries))
    elif pid == 3568:
        grid, energy = args
        valid = (type(grid) is list and 1 <= len(grid) <= 20 and type(grid[0]) is str and 1 <= len(grid[0]) <= 20
                 and all(type(row) is str and len(row) == len(grid[0]) and set(row) <= set('SLRX.') for row in grid)
                 and sum(row.count('S') for row in grid) == 1 and sum(row.count('L') for row in grid) <= 10
                 and integer(energy, 1, 50))
    elif pid in (3600, 3613):
        n, edges, k = args
        width = 4 if pid == 3600 else 3
        valid = (integer(n, 2 if pid == 3600 else 1, 100000 if pid == 3600 else 50000)
                 and integer(k, 0 if pid == 3600 else 1, n) and type(edges) is list
                 and (1 if pid == 3600 else 0) <= len(edges) <= 100000
                 and all(type(e) is list and len(e) == width and integer(e[0], 0, n - 1)
                         and integer(e[1], 0, n - 1) and integer(e[2], 1, 100000 if pid == 3600 else 1000000)
                         and (pid != 3600 or (e[0] != e[1] and integer(e[3], 0, 1))) for e in edges))
        if valid:
            if pid == 3600:
                valid = len({tuple(sorted(e[:2])) for e in edges}) == len(edges)
            else:
                valid = _components(n, edges) == 1
    else:
        edges, online, budget = args
        valid = (type(online) is list and 2 <= len(online) <= 50000 and all(type(v) is bool for v in online)
                 and online[0] and online[-1] and integer(budget, 0, 5 * 10**13) and type(edges) is list
                 and len(edges) <= min(100000, len(online) * (len(online) - 1) // 2)
                 and all(type(e) is list and len(e) == 3 and integer(e[0], 0, len(online) - 1)
                         and integer(e[1], 0, len(online) - 1) and e[0] != e[1]
                         and integer(e[2], 0, 10**9) for e in edges))
        if valid:
            valid = _dag(len(online), edges)
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _threshold_distances(n, nums, difference, queries):
    adjacency = [[j for j in range(n) if j != i and abs(nums[i] - nums[j]) <= difference] for i in range(n)]
    answers = []
    for start, target in queries:
        distances = [-1] * n; distances[start] = 0; ready = deque([start])
        while ready:
            node = ready.popleft()
            for neighbor in adjacency[node]:
                if distances[neighbor] == -1:
                    distances[neighbor] = distances[node] + 1; ready.append(neighbor)
        answers.append(distances[target])
    return answers


def _classroom_states(grid, capacity):
    rows, columns = len(grid), len(grid[0]); litter = {}; start = None
    for r in range(rows):
        for c in range(columns):
            if grid[r][c] == 'L':
                litter[r, c] = len(litter)
            elif grid[r][c] == 'S':
                start = (r, c)
    target = (1 << len(litter)) - 1
    first = (*start, 0, capacity); ready = deque([(first, 0)]); seen = {first}
    while ready:
        (r, c, mask, energy), distance = ready.popleft()
        if mask == target:
            return distance
        if energy == 0:
            continue
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < columns and grid[nr][nc] != 'X':
                remaining = capacity if grid[nr][nc] == 'R' else energy - 1
                collected = mask | (1 << litter[nr, nc] if (nr, nc) in litter else 0)
                state = (nr, nc, collected, remaining)
                if state not in seen:
                    seen.add(state); ready.append((state, distance + 1))
    return -1


def _spanning_subsets(n, edges, k):
    best = -1; mandatory = {i for i, edge in enumerate(edges) if edge[3]}
    for chosen in combinations(range(len(edges)), n - 1):
        if not mandatory.issubset(chosen):
            continue
        selected = [edges[i] for i in chosen]
        if _components(n, selected) != 1:
            continue
        optional = [i for i in chosen if not edges[i][3]]
        for count in range(min(k, len(optional)) + 1):
            for upgraded in combinations(optional, count):
                best = max(best, min(edges[i][2] * (2 if i in upgraded else 1) for i in chosen))
    return best


def _retained_subsets(n, edges, k):
    best = max((e[2] for e in edges), default=0)
    for mask in range(1 << len(edges)):
        kept = [edge for i, edge in enumerate(edges) if mask >> i & 1]
        if _components(n, kept) <= k:
            best = min(best, max((edge[2] for edge in kept), default=0))
    return best


def _all_paths(edges, online, budget):
    adjacency = [[] for _ in online]
    for a, b, weight in edges:
        adjacency[a].append((b, weight))
    best = -1; stack = [(0, 0, None)]
    while stack:
        node, cost, minimum = stack.pop()
        if node == len(online) - 1:
            best = max(best, minimum)
            continue
        for neighbor, weight in adjacency[node]:
            if online[neighbor] and cost + weight <= budget:
                stack.append((neighbor, cost + weight, weight if minimum is None else min(minimum, weight)))
    return best


def expected(pid, args):
    validate(pid, args)
    if pid == 3534:
        bounded = args[0] <= 12 and len(args[3]) <= 144
    elif pid == 3568:
        bounded = len(args[0]) * len(args[0][0]) <= 16 and sum(row.count('L') for row in args[0]) <= 5 and args[1] <= 8
    elif pid in (3600, 3613):
        bounded = args[0] <= 7 and len(args[1]) <= 12
    else:
        bounded = len(args[1]) <= 10 and len(args[0]) <= 16
    if not bounded:
        raise ValueError('bounded independent reference budget exceeded')
    if pid == 3534:
        return _threshold_distances(*args)
    if pid == 3568:
        return _classroom_states(*args)
    if pid == 3600:
        return _spanning_subsets(*args)
    if pid == 3613:
        return _retained_subsets(*args)
    return _all_paths(*args)


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\n\s*Output:\s*([^\n]+)', raw.decode(), re.S):
        call = ast.parse('f(' + match[1].strip().replace('true', 'True').replace('false', 'False') + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(item.arg for item in call.keywords) != PARAMETERS[pid]:
            raise ValueError('pinned ordered example parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement); categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid); sentinel = object()

    def add(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3534:
        for n in range(1, 5):
            for values in product((0, 1, 3), repeat=n):
                for difference in (0, 1, 2):
                    add([n, list(values), difference, [[a, b] for a in range(n) for b in range(n)]], 'exhaustive_small_threshold_graphs')
        for _ in range(60):
            n = rng.randrange(5, 13); values = [rng.choice((0, 1, 7, 99999, 100000)) for _ in range(n)]
            add([n, values, rng.choice((0, 1, 6, 99999, 100000)), [[rng.randrange(n), rng.randrange(n)] for _ in range(20)]], 'seeded_explicit_graph_distances')
        for args, answer in [([100000, [0] * 100000, 0, [[0, 99999], [123, 123]]], [1, 0]),
                             ([100000, list(range(100000)), 1, [[0, 99999], [111, 444]]], [99999, 333]),
                             ([100000, list(range(99999, -1, -1)), 1, [[0, 99999], [444, 111]]], [99999, 333]),
                             ([2, [0, 100000], 99999, [[0, 1]]], [-1]),
                             ([1, [100000], 100000, [[0, 0]] * 100000], [0] * 100000)]:
            add(args, 'analytic_maximum_threshold_shapes', answer)
    elif pid == 3568:
        for start in range(4):
            for others in product('.LRX', repeat=3):
                cells = list(others); cells.insert(start, 'S'); grid = [''.join(cells[:2]), ''.join(cells[2:])]
                for energy in (1, 2, 3):
                    add([grid, energy], 'exhaustive_two_by_two_energy_states')
        for _ in range(70):
            cells = [rng.choice('.LRX') for _ in range(9)]
            while cells.count('L') > 5:
                cells[cells.index('L')] = '.'
            cells[rng.randrange(9)] = 'S'
            add([[''.join(cells[i:i + 3]) for i in range(0, 9, 3)], rng.randrange(1, 9)], 'seeded_explicit_litter_states')
        for args, answer in [([['SL'], 1], 1), ([['SRL'], 1], 2), ([['S.L'], 1], -1),
                             ([['S' + '.' * 19] + ['.' * 20] * 19, 50], 0),
                             ([['S' + 'L' * 10 + '.' * 9] + ['.' * 20] * 19, 50], 10),
                             ([['S' + '.' * 19] + ['.' * 20] * 18 + ['.' * 19 + 'L'], 38], 38),
                             ([['S' + '.' * 19] + ['.' * 20] * 18 + ['.' * 19 + 'L'], 37], -1),
                             ([['S' + 'R' * 18 + 'L'] + ['X' * 20] * 19, 1], 19),
                             ([['S' + 'X' * 19] + ['X' * 20] * 18 + ['X' * 19 + 'L'], 50], -1)]:
            add(args, 'analytic_energy_boundaries_and_maximum_grid', answer)
    elif pid == 3600:
        pairs = ((0, 1), (0, 2), (1, 2))
        for states in product(range(4), repeat=3):
            edges = [[a, b, 1 if state == 1 else 3, int(state == 3)] for (a, b), state in zip(pairs, states) if state]
            if not edges:
                continue
            for k in range(4):
                add([3, edges, k], 'exhaustive_three_node_mandatory_upgrade_states')
        for _ in range(90):
            n = rng.randrange(2, 7); pairs = list(combinations(range(n), 2)); rng.shuffle(pairs)
            edges = [[a, b, rng.choice((1, 2, 7, 100000)), rng.randrange(2)] for a, b in pairs[:rng.randrange(1, min(10, len(pairs)) + 1)]]
            add([n, edges, rng.randrange(n + 1)], 'seeded_explicit_spanning_and_upgrade_subsets')
        for args, answer in [([100000, [[0, 1, 100000, 0]], 100000], -1),
                             ([10000, [[i, i + 1, 100000, 0] for i in range(9999)], 9999], 200000),
                             ([10000, [[i, i + 1, 7, 0] for i in range(9999)], 9998], 7),
                             ([10000, [[i, i + 1, 7, 1] for i in range(9999)], 10000], 7),
                             ([3, [[0, 1, 100000, 1], [1, 2, 100000, 1], [2, 0, 100000, 1]], 3], -1),
                             ([100, [[a, b, 3, 0] for a, b in combinations(range(100), 2)], 99], 6)]:
            add(args, 'analytic_large_spanning_shapes', answer)
    elif pid == 3613:
        for states in product((0, 1, 7), repeat=3):
            edges = [[a, b, weight] for (a, b), weight in zip(((0, 1), (0, 2), (1, 2)), states) if weight]
            if _components(3, edges) != 1:
                continue
            for k in range(1, 4):
                add([3, edges, k], 'exhaustive_connected_three_node_removal_subsets')
        for _ in range(120):
            n = rng.randrange(1, 7); edges = [[i, i + 1, rng.choice((1, 3, 1000000))] for i in range(n - 1)]
            for _ in range(rng.randrange(7)):
                edges.append([rng.randrange(n), rng.randrange(n), rng.choice((1, 3, 1000000))])
            add([n, edges, rng.randrange(1, n + 1)], 'seeded_multigraph_and_self_loop_removal_subsets')
        for args, answer in [([1, [], 1], 0), ([1, [[0, 0, 1000000]], 1], 0),
                             ([2, [[0, 1, 1]] * 100000, 1], 1),
                             ([10000, [[i, i + 1, 1000000] for i in range(9999)], 1], 1000000),
                             ([10000, [[i, i + 1, 1000000] for i in range(9999)], 10000], 0),
                             ([50000, [[i, i + 1, 1] for i in range(49999)], 49999], 1)]:
            add(args, 'analytic_maximum_counts_and_connected_shapes', answer)
    else:
        pairs = list(combinations(range(4), 2))
        for states in product((None, 0, 2), repeat=6):
            edges = [[a, b, weight] for (a, b), weight in zip(pairs, states) if weight is not None]
            online = [True, rng.choice((True, False)), rng.choice((True, False)), True]
            add([edges, online, rng.choice((0, 1, 2, 4, 6))], 'exhaustive_four_node_dag_edge_shapes_seeded_status_budget')
        for _ in range(90):
            n = rng.randrange(3, 9); middle = list(range(1, n - 1)); rng.shuffle(middle); order = [0] + middle + [n - 1]
            pairs = list(combinations(order, 2)); rng.shuffle(pairs)
            edges = [[a, b, rng.choice((0, 1, 10**9))] for a, b in pairs[:rng.randrange(min(len(pairs), 16) + 1)]]
            online = [True] + [rng.choice((True, False)) for _ in range(n - 2)] + [True]
            add([edges, online, rng.choice((0, 1, 10**9, 2 * 10**9, 5 * 10**13))], 'seeded_permuted_dags_and_exact_numeric_paths')
        for args, answer in [([[[0, 2, 0], [0, 2, 9]], [True, False, True], 9], 9),
                             ([[[0, 2, 9], [2, 1, 8], [1, 3, 7]], [True] * 4, 24], 7),
                             ([[[0, 49999, 10**9]], [True] * 50000, 5 * 10**13], 10**9),
                             ([[[i, i + 1, 0] for i in range(49999)], [True] * 50000, 0], 0),
                             ([[[i, i + 1, 10**9] for i in range(9999)], [True] * 10000, 9999 * 10**9], 10**9),
                             ([[[i, i + 1, 10**9] for i in range(9999)], [True] * 10000, 9999 * 10**9 - 1], -1),
                             ([[], [True] * 50000, 5 * 10**13], -1)]:
            add(args, 'analytic_large_dag_and_budget_shapes', answer)
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
        raise ValueError('frozen batch H population or bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('javascript', 'python')):
            raise ValueError('projected successful observation exceeds unchanged output cap')
    return cases, categories
