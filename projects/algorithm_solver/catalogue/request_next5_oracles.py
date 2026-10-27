"""Fixed next-five pure definition oracles; no candidate, runner or file loader.

Small cases enumerate definition-level choices. Large analytic shapes are named
separately; domain validity does not imply transport or execution qualification.
"""
from __future__ import annotations

import ast
from itertools import combinations, product
import json
from math import comb, prod
import random
import re

from . import imported_qualification as q

IDS = (3514, 3528, 3566, 3578, 3607)
PARAMETERS = {3514: ('nums',), 3528: ('conversions',), 3566: ('nums', 'target'),
              3578: ('nums', 'k'), 3607: ('c', 'connections', 'queries')}
MOD = 1000000007
STATEMENT_SHA256 = {
    3514: '3c24ea865f6199653709c9ae84f29e8f519ca05284e4cfb6ba2f718b84a704bf',
    3528: '5a0aed7c4df854c1f0c82a9c8c39faa2f64c64d412f25d5d7638377aa5acf0b8',
    3566: '2bb3739809f6f21986fc09678c4bade1b63192d0241f94b3d84955ee23a38b9b',
    3578: 'b51f8779bd18d4bbcf1c019e9cbf5f5c5addadc613860560b0a46a4c5ed1c924',
    3607: 'bcfdff6534ff0b69793c9214b1d98fabff876dba2fce93680a1d300f7293f46c',
}
CASE_COUNT = {3514: 231, 3528: 112, 3566: 353, 3578: 400, 3607: 440}
CASES_SHA256 = {
    3514: '0041ee315fb8e3b0f3c266e86baca98e2176710e3ad36c709bd90061a8b32239',
    3528: '26eb4f9cd98d6bacd2eae1b988cbcca5fd3c9175f318ddc853744f89f31c364e',
    3566: 'b9c8121cdb367a4ab459edc57ca5234272905b2481f8e02232921a5a304a9a87',
    3578: '87df1cd51af294ba725db70537eaa8c64dc0b6f6fde67ee763e394cbea654de5',
    3607: 'a9d9c9548235fcac6ea9c8a7d49d25b28ab3c9fe4e9e75265ba52c93fd031ea1',
}
SEED_BASE = 202610270500
SMALL_BUDGET = {3514: 14, 3528: 10, 3566: 12, 3578: 12, 3607: 8}
OMITTED_MAXIMUM_SHAPES = {
    3514: 'Full-size analytic value spans are tested; arbitrary 1500-element triple enumeration is not attempted.',
    3528: 'Even the shortest full 100000-unit conversion tree exceeds the unchanged packet cap; analytic star reaches 90000 units and chain 60000.',
    3566: 'The complete declared length up to 12 is within the enumeration budget; finite inputs do not exhaust all distinct sets and targets.',
    3578: 'Full-length analytic arrays are retained; arbitrary 50000-element cut-mask enumeration is not attempted.',
    3607: 'The minimum 200000-query packet exceeds the unchanged cap. Analytic query probe reaches 50000; station/edge limits are separately represented.',
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered argument shape')
    if pid in (3514, 3566, 3578):
        values = args[0]
        lo, hi, bound = {3514: (1, 1500, 1500), 3566: (3, 12, 100), 3578: (2, 50000, 10**9)}[pid]
        if type(values) is not list or not lo <= len(values) <= hi or any(not _integer(x, 1, bound) for x in values):
            raise ValueError('array outside pinned integer domain')
        if pid == 3566 and (len(set(values)) != len(values) or not _integer(args[1], 1, 10**15)):
            raise ValueError('distinct array or target outside pinned domain')
        if pid == 3578 and not _integer(args[1], 0, 10**9):
            raise ValueError('threshold outside pinned domain')
        return
    if pid == 3528:
        edges = args[0]
        if type(edges) is not list or not 1 <= len(edges) <= 99999:
            raise ValueError('conversion count outside pinned domain')
        n = len(edges) + 1
        incoming = [0] * n
        children = [[] for _ in range(n)]
        for row in edges:
            if (type(row) is not list or len(row) != 3 or
                    not all(_integer(x, 0, n - 1) for x in row[:2]) or not _integer(row[2], 1, 10**9)):
                raise ValueError('conversion row outside pinned domain')
            source, target, _ = row
            incoming[target] += 1
            children[source].append(target)
        if incoming != [0] + [1] * (n - 1):
            raise ValueError('conversions are not a directed root-zero arborescence')
        seen, stack = {0}, [0]
        while stack:
            for target in children[stack.pop()]:
                if target in seen:
                    raise ValueError('conversion cycle')
                seen.add(target)
                stack.append(target)
        if len(seen) != n:
            raise ValueError('conversion target unreachable from zero')
        return
    c, edges, queries = args
    if (not _integer(c, 1, 100000) or type(edges) is not list or
            len(edges) > min(100000, c * (c - 1) // 2) or
            type(queries) is not list or not 1 <= len(queries) <= 200000):
        raise ValueError('station, cable or query count outside pinned domain')
    for edge in edges:
        if (type(edge) is not list or len(edge) != 2 or
                any(not _integer(x, 1, c) for x in edge) or edge[0] == edge[1]):
            raise ValueError('invalid cable endpoints')
    # Parallel cables are not excluded by the pinned statement.
    for query in queries:
        if (type(query) is not list or len(query) != 2 or
                not _integer(query[0], 1, 2) or not _integer(query[1], 1, c)):
            raise ValueError('invalid maintenance query')


def _xor_triples(values):
    return len({values[i] ^ values[j] ^ values[k] for i in range(len(values))
                for j in range(i, len(values)) for k in range(j, len(values))})


def _directed_path_products(edges):
    answers = []
    for target in range(len(edges) + 1):
        found = []
        stack = [(0, 1)]
        while stack:
            node, amount = stack.pop()
            if node == target:
                found.append(amount)
            for source, child, factor in edges:
                if source == node:
                    stack.append((child, amount * factor))
        if len(found) != 1:
            raise ValueError('definition requires one directed conversion path')
        answers.append(found[0] % MOD)
    return answers


def _complementary_products(values, target):
    # Fix the last element on the right to remove complementary duplicates.
    for mask in range(1, 1 << (len(values) - 1)):
        left, right = 1, 1
        for i, value in enumerate(values):
            if mask >> i & 1:
                left *= value
            else:
                right *= value
        if left == right == target:
            return True
    return False


def _cut_partitions(values, threshold):
    answer = 0
    for mask in range(1 << (len(values) - 1)):
        start, valid = 0, True
        for stop in range(1, len(values) + 1):
            if stop == len(values) or mask >> (stop - 1) & 1:
                segment = values[start:stop]
                if max(segment) - min(segment) > threshold:
                    valid = False
                    break
                start = stop
        answer += valid
    return answer % MOD


def _search_each_maintenance(c, edges, queries):
    online, answers = set(range(1, c + 1)), []
    for kind, station in queries:
        if kind == 2:
            online.discard(station)
        elif station in online:
            answers.append(station)
        else:
            reached, stack = {station}, [station]
            while stack:
                node = stack.pop()
                for a, b in edges:
                    neighbor = b if a == node else a if b == node else None
                    if neighbor is not None and neighbor not in reached:
                        reached.add(neighbor)
                        stack.append(neighbor)
            answers.append(min(reached & online, default=-1))
    return answers


def expected(pid, args):
    validate(pid, args)
    size = len(args[0]) + 1 if pid == 3528 else args[0] if pid == 3607 else len(args[0])
    if size > SMALL_BUDGET[pid] or (pid == 3607 and len(args[2]) > 16):
        raise ValueError('independent enumeration budget exceeded')
    if pid == 3514:
        return _xor_triples(args[0])
    if pid == 3528:
        return _directed_path_products(args[0])
    if pid == 3566:
        return _complementary_products(*args)
    if pid == 3578:
        return _cut_partitions(*args)
    return _search_each_maintenance(*args)


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
            raise ValueError('oracle disagrees with pinned example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != 2:
        raise ValueError('both pinned examples are required')
    return cases


def build_cases(pid, statement):
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

    if pid == 3514:
        for n in range(1, 5):
            for values in product((1, 2, 3), repeat=n):
                add([list(values)], 'exhaustive_short_index_triples')
        for _ in range(40):
            add([[rng.randrange(1, 1501) for _ in range(rng.randrange(5, 15))]], 'seeded_index_triples')
        for values in product((1, 511, 1024, 1500), repeat=3):
            add([list(values)], 'high_bit_index_triples')
        for values, answer in [([1500] * 1500, 1), ([1, 1500] * 750, 2),
                               (list(range(1, 1024)), 1024), (list(range(1, 1501)), 2048),
                               ([1024] * 1499 + [1500], 2)]:
            add([values], 'analytic_full_size_xor_span', answer)
    elif pid == 3528:
        for n in range(2, 6):
            for parents in product(*(range(i) for i in range(1, n))):
                labels = [0, *range(n - 1, 0, -1)]
                for factors in ((2, 3, 5), (10**9, 10**9 - 1, 999999937)):
                    edges = [[labels[p], labels[i], factors[(i - 1) % 3]] for i, p in enumerate(parents, 1)]
                    add([edges[::-1]], 'exhaustive_small_shuffled_root_trees')
        for _ in range(40):
            n = rng.randrange(6, 11)
            labels = [0, *rng.sample(range(1, n), n - 1)]
            edges = [[labels[rng.randrange(i)], labels[i], rng.choice((1, 2, 7, 10**9, 999999937))] for i in range(1, n)]
            rng.shuffle(edges)
            add([edges], 'seeded_exact_path_products')
        add([[[0, i, 1] for i in range(1, 90000)]], 'analytic_large_star', [1] * 90000)
        add([[[i - 1, i, 1] for i in range(1, 60000)]], 'analytic_deep_chain', [1] * 60000)
        add([[[i - 1, i, 10**9] for i in range(1, 101)]], 'analytic_high_factor_chain', [pow(10**9, i, MOD) for i in range(101)])
        add([[[0, i, 10**9] for i in range(1, 1000)]], 'analytic_high_factor_star', [1] + [10**9] * 999)
    elif pid == 3566:
        for n in range(3, 7):
            for values in combinations(range(1, 7), n):
                for target in (1, 2, 3, 6, 12, 24, 36):
                    add([list(values), target], 'exhaustive_small_distinct_subset_products')
        for i in range(40):
            values = rng.sample(range(1, 101), rng.randrange(7, 13))
            target = prod(values[:len(values) // 2]) if i % 2 else rng.randrange(1, 10**15 + 1)
            add([values, target], 'seeded_exact_complement_products')
        high = [99, 80, 90, 88, 96, 63, 84, 72, 77, 60, 70, 66]
        target = 221298739200
        for _ in range(4):
            rng.shuffle(high)
            for value in (target - 1, target, target + 1, 10**15):
                add([high.copy(), value], 'high_product_above_safe_number')
        add([[68, 76, 78, 80, 84, 85, 88, 90, 91, 95, 98, 99], 391091500800],
            'targeted_exact_product_vs_float_rounding')
    elif pid == 3578:
        for n in range(2, 5):
            for values in product((1, 2, 3), repeat=n):
                for threshold in (0, 1, 2):
                    add([list(values), threshold], 'exhaustive_short_cut_masks')
        for _ in range(40):
            values = [rng.choice((1, 2, 10**9 - 1, 10**9)) for _ in range(rng.randrange(5, 13))]
            add([values, rng.choice((0, 1, 10**9 - 2, 10**9 - 1, 10**9))], 'seeded_boundary_cut_masks')
        for values, k, answer in [([1] * 50000, 0, pow(2, 49999, MOD)),
                                  ([1, 10**9] * 25000, 0, 1),
                                  ([1, 10**9] * 25000, 10**9 - 1, pow(2, 49999, MOD)),
                                  ([1] * 25000 + [10**9] * 25000, 0, pow(2, 49998, MOD)),
                                  (list(range(1, 50001)), 0, 1),
                                  ([10**9] * 50000, 10**9, pow(2, 49999, MOD)),
                                  (list(range(1, 61)), 1, sum(comb(60 - j, j) for j in range(31)) % MOD)]:
            add([values, k], 'analytic_partition_shape', answer)
    else:
        for c in (1, 2, 3):
            pairs = list(combinations(range(1, c + 1), 2))
            tokens = [(kind, x) for kind in (1, 2) for x in range(1, c + 1)]
            for mask in range(1 << len(pairs)):
                edges = [list(pair) for i, pair in enumerate(pairs) if mask >> i & 1]
                for length in range(1, 4 if c == 1 else 3):
                    for queries in product(tokens, repeat=length):
                        add([c, edges, [list(query) for query in queries]], 'exhaustive_small_graph_query_traces')
        for _ in range(40):
            c = rng.randrange(4, 9)
            pairs = list(combinations(range(1, c + 1), 2))
            edges = [list(rng.choice(pairs)) for _ in range(rng.randrange(len(pairs) + 1))]
            queries = [[rng.randrange(1, 3), rng.randrange(1, c + 1)] for _ in range(rng.randrange(3, 17))]
            add([c, edges, queries], 'seeded_repeated_cable_traces')
        special = [
            [3, [[1, 2], [2, 3]], [[2, 2], [2, 1], [1, 1], [2, 3], [1, 2]]],
            [3, [[1, 2], [1, 2], [2, 1]], [[2, 1], [2, 1], [1, 1], [1, 3]]],
            [3, [[1, 2], [2, 3]], [[1, 3], [2, 2], [1, 3]]],
            [1, [], [[2, 1], [2, 1]]],
        ]
        for args in special:
            add(args, 'explicit_offline_bridge_and_idempotence')
        add([100000, [], [[1, 100000], [2, 100000], [1, 100000]]], 'analytic_maximum_station_count', [100000, -1])
        add([100000, [[1, i] for i in range(2, 100001)] + [[1, 2]], [[2, 1], [1, 1], [2, 2], [1, 1]]], 'analytic_maximum_edge_multigraph', [2, 3])
        add([40000, [[i, i + 1] for i in range(1, 40000)], [[2, 20000], [2, 1], [1, 1], [1, 20000]]], 'analytic_deep_offline_bridge', [2, 2])
        add([1, [], [[2, 1]] + [[1, 1]] * 49999], 'analytic_long_query_trace', [-1] * 49999)
    if len(cases) != CASE_COUNT[pid] or q.sha(q.encoded(cases)) != CASES_SHA256[pid]:
        raise ValueError('frozen case population or bytes changed')
    list(q.batches(cases))  # Never silently drop a valid but oversized probe.
    return cases, categories
