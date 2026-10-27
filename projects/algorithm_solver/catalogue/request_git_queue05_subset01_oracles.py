"""Source-blind exposed-development references from four pinned public definitions.

No candidate source loading, execution, adapters or qualification. Expected
values remain host-side; original imported_qualification caps are unchanged.
"""
from __future__ import annotations

import ast
from itertools import combinations, product
import json
import random
import re

from . import imported_qualification as q

IDS = (2508, 2567, 2640, 2672)
PARAMETERS = {2508: ('n', 'edges'), 2567: ('nums',), 2640: ('nums',), 2672: ('n', 'queries')}
TITLES = {2508: 'Add Edges to Make Degrees of All Nodes Even',
          2567: 'Minimum Score by Changing Two Elements',
          2640: 'Find the Score of All Prefixes of an Array',
          2672: 'Number of Adjacent Elements With the Same Color'}
SLUGS = {2508: 'add-edges-to-make-degrees-of-all-nodes-even',
         2567: 'minimum-score-by-changing-two-elements',
         2640: 'find-the-score-of-all-prefixes-of-an-array',
         2672: 'number-of-adjacent-elements-with-the-same-color'}
STATEMENT_SHA256 = {
    2508: '01d0d48364842b9652fffa94b9b384f94debf8d6cfa33be08b211ac6ed2c489f',
    2567: '523c1641993b2b60edb7e0caba6480ca474868bbc345e78325e84ca1b30a6105',
    2640: '4a6d8d7be67b8ab808c3dcd45b0044eac90a071a8e6da4ca7aba4f3cbeada619',
    2672: '672e5f1550c3e0472e74924ff653bf2a57aef4e3b96158bba8b88a0c26216a64',
}
EXAMPLE_COUNT = {2508: 3, 2567: 2, 2640: 2, 2672: 2}
SEED_BASE = 202610271949
CONTRACTS = {
    2508: dict(domain='3..100000 vertices, 2..100000 distinct undirected non-self edges, endpoints 1..n.',
               result='Strict Boolean: adding zero, one or two distinct missing non-self edges can make every degree even.',
               reference='For n<=10, enumerate every subset of zero through two missing edges and recompute all resulting degrees.',
               complexity='Candidate target O(n+m) time/space or justified equivalent; not a runtime result.'),
    2567: dict(domain='3..100000 exact integers in 1..1000000000.',
               result='Minimum high-plus-low pairwise absolute-difference score after assigning values to two distinct positions.',
               reference='For n<=18, enumerate every pair of changed indices. Remaining range lower-bounds high score; assigning both positions an unchanged value attains that range and low score zero.',
               complexity='Candidate target O(n log n) time/O(n) space or better; no timing qualification.'),
    2640: dict(domain='1..100000 exact integers in 1..1000000000.',
               result='Exact integer list: each prefix score sums value plus maximum of its own prefix.',
               reference='For n<=40, independently recompute each prefix maximum and every complete prefix score from the definition.',
               complexity='Candidate target O(n) time and O(n) output storage; no finite-test complexity proof.'),
    2672: dict(domain='n in 1..100000, 1..100000 [index,color] queries, index 0..n-1 and color 1..100000.',
               result='List of adjacent equal positive-color pair counts after each assignment. Adjacent uncolored zeros do not count.',
               reference='For n<=20 and <=50 queries, assign into a fresh full color array then rescan every adjacent pair after each query.',
               complexity='Candidate target O(n+query_count) time and O(n+query_count) storage; no resource result.'),
}
COMMON_CONTRACT = {
    'exposure': 'Exposed development; no fresh holdout or qualification claim.',
    'interface': 'Pure single-call ordered values from official example parameters. Actual candidate export/name/adapter remains unknown.',
    'effects': 'Conservative service envelope: input values and identities unchanged, no mutable return/input alias, no persistent mutable state or external I/O. This is separate from official mutation permissions.',
    'numeric': 'Exact integers and strict booleans; bool is not an integer input. 2640 scores <=2e14, below 2^53 but above 32-bit. 2567 optimum <=1e9-1; 2672 counts <=99999.',
    'unicode': 'No strings in these numeric input contracts.',
    'helpers': 'Candidate helper/dependency costs and interfaces must be reviewed later; none inferred or inserted here.',
    'expected_values': 'Host-side only; q.packet excludes expected values.',
    'limits': 'Unchanged q.MAX_FILE, q.MAX_PACKET=1100000 and q.LIMITS; use q.batches.',
}
OMITTED_MAXIMUM_SHAPES = {
    2508: 'Maximum n and m are included using a dense even clique plus disjoint cycle. A literal 100000-node cycle exceeds the unchanged packet cap; arbitrary maximum graphs are not exhaustively enumerated.',
    2567: 'Maximum length and maximum value appear together in mixed arrays. The uniform 100000-element all-1e9 packet exceeds the unchanged cap; uniform maximum values are probed at length 50000 instead.',
    2640: 'Maximum length and maximum value appear together with a maximum-valued first entry. Uniform all-1e9 length100000 exceeds the packet cap and is represented at length50000. Arbitrary maximum arrays are not reference-enumerated.',
    2672: 'Maximum n and query count are included together with color1. Uniform maximum color with 100000 two-integer queries exceeds the packet cap; maximum color appears in separate boundary probes. No exhaustive maximum query-stream claim.',
}


def _integer(x, low, high):
    return type(x) is int and low <= x <= high


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid == 2508:
        n, edges = args
        valid = (_integer(n, 3, 100000) and type(edges) is list and 2 <= len(edges) <= 100000
                 and all(type(e) is list and len(e) == 2 and _integer(e[0], 1, n)
                         and _integer(e[1], 1, n) and e[0] != e[1] for e in edges))
        if valid:
            valid = len({tuple(sorted(e)) for e in edges}) == len(edges)
    elif pid in (2567, 2640):
        nums = args[0]
        valid = (type(nums) is list and (3 if pid == 2567 else 1) <= len(nums) <= 100000
                 and all(_integer(x, 1, 1000000000) for x in nums))
    else:
        n, queries = args
        valid = (_integer(n, 1, 100000) and type(queries) is list and 1 <= len(queries) <= 100000
                 and all(type(row) is list and len(row) == 2 and _integer(row[0], 0, n-1)
                         and _integer(row[1], 1, 100000) for row in queries))
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _added_edges(n, edges):
    present = {tuple(sorted(e)) for e in edges}
    missing = [e for e in combinations(range(1, n+1), 2) if e not in present]
    for count in range(3):
        for additions in combinations(missing, count):
            degrees = [0] * (n+1)
            for a, b in list(present) + list(additions):
                degrees[a] += 1
                degrees[b] += 1
            if all(d % 2 == 0 for d in degrees):
                return True
    return False


def _changed_pair(nums):
    scores = []
    for i, j in combinations(range(len(nums)), 2):
        unchanged = [x for k, x in enumerate(nums) if k not in (i, j)]
        scores.append(max(unchanged) - min(unchanged))
    return min(scores)


def _prefix_definition(nums):
    return [sum(nums[j] + max(nums[:j+1]) for j in range(end+1)) for end in range(len(nums))]


def _repaint_rescan(n, queries):
    colors = [0] * n
    results = []
    for index, color in queries:
        colors[index] = color
        results.append(sum(colors[i] != 0 and colors[i] == colors[i+1] for i in range(n-1)))
    return results


def expected(pid, args):
    validate(pid, args)
    if pid == 2508:
        if args[0] > 10:
            raise ValueError('bounded added-edge enumeration budget exceeded')
        return _added_edges(*args)
    if pid == 2567:
        if len(args[0]) > 18:
            raise ValueError('bounded changed-index enumeration budget exceeded')
        return _changed_pair(args[0])
    if pid == 2640:
        if len(args[0]) > 40:
            raise ValueError('bounded repeated-prefix reference budget exceeded')
        return _prefix_definition(args[0])
    if args[0] > 20 or len(args[1]) > 50:
        raise ValueError('bounded full-array repaint reference budget exceeded')
    return _repaint_rescan(*args)


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned official definition bytes required')
    statement = json.loads(raw)
    if type(statement) is not str:
        raise ValueError('official rendered-extraction envelope must contain text')
    statement = re.sub(r'(?m)^L\d+: ?', '', statement)
    if f'{pid}. {TITLES[pid]}' not in statement or f'https://leetcode.com/problems/{SLUGS[pid]}/description/' not in statement:
        raise ValueError('numeric/title/slug identity mismatch')
    cases = []
    for found in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)', statement):
        call = ast.parse('f(' + found[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(k.arg for k in call.keywords) != PARAMETERS[pid]:
            raise ValueError('ordered official parameters differ')
        args = [ast.literal_eval(k.value) for k in call.keywords]
        answer = json.loads(found[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with official example')
        cases.append(dict(args=args, expected=answer, compare='return'))
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
        cases.append(dict(args=args, expected=expected(pid, args) if answer is sentinel else answer, compare='return'))
        categories.append(category)

    if pid == 2508:
        for n in range(3, 6):
            pairs = list(combinations(range(1, n+1), 2))
            for mask in range(1 << len(pairs)):
                edges = [list(e) for i, e in enumerate(pairs) if mask >> i & 1]
                if len(edges) >= 2:
                    add([n, edges], 'exhaustive_simple_graphs_missing_edge_subsets')
        for _ in range(80):
            n = rng.randint(6, 10)
            edges = [list(e) for e in combinations(range(1, n+1), 2) if rng.randrange(3) == 0]
            if len(edges) < 2:
                edges = [[1, 2], [2, 3]]
            rng.shuffle(edges)
            edges = [e[::-1] if rng.randrange(2) else e for e in edges]
            add([n, edges], 'seeded_graphs_orientation_and_label_gaps')
        add([100000, [[1, 2], [2, 3]]], 'analytic_maximum_vertices_two_odd_endpoints', True)
        add([100000, [[1, 2], [1, 3], [1, 4]]], 'analytic_four_odd_unavailable_pairings', False)
        dense = [list(e) for e in combinations(range(1, 448), 2)]
        cycle = [[v, v+1] for v in range(448, 766)] + [[766, 448]]
        even = dense + cycle
        assert len(even) == 100000
        add([100000, even], 'analytic_maximum_edges_all_even', True)
        omitted = {(1, 2), (3, 4), (5, 6)}
        many_odd = [e for e in even if tuple(e) not in omitted] + [[90001, 90002], [90003, 90004], [90005, 90006]]
        add([100000, many_odd], 'analytic_maximum_edges_twelve_odd_vertices', False)
    elif pid == 2567:
        for n in range(3, 7):
            for values in product((1, 2, 4), repeat=n):
                add([list(values)], 'exhaustive_changed_index_pairs')
        for _ in range(80):
            nums = [rng.choice((1, 2, 7, 999999999, 1000000000)) for _ in range(rng.randint(7, 18))]
            rng.shuffle(nums)
            add([nums], 'seeded_duplicates_extremes_and_order')
        for nums, answer in [([1]*100000, 0), ([1000000000]*50000, 0),
                             ([1]*99998+[1000000000]*2, 0),
                             ([1]*50000+[1000000000]*50000, 999999999),
                             ([1]*99997+[1000000000]*3, 999999999)]:
            add([nums], 'analytic_maximum_length_or_value', answer)
    elif pid == 2640:
        for n in range(1, 7):
            for values in product((1, 2, 5), repeat=n):
                add([list(values)], 'exhaustive_literal_prefix_definitions')
        for _ in range(80):
            add([[rng.choice((1, 2, 10, 999999999, 1000000000)) for _ in range(rng.randint(7, 40))]], 'seeded_prefix_extremes_and_ties')
        n = 100000
        add([[1]*n], 'analytic_maximum_uniform_minimum', [2*(i+1) for i in range(n)])
        add([[1000000000]+[1]*(n-1)], 'analytic_maximum_prefix_maximum_plateau', [2000000000+i*1000000001 for i in range(n)])
        add([list(range(1, n+1))], 'analytic_maximum_increasing_prefixes', [(i+1)*(i+2) for i in range(n)])
        add([[1000000000]*50000], 'analytic_large_uniform_maximum', [2000000000*(i+1) for i in range(50000)])
    else:
        for n in range(1, 4):
            operations = list(product(range(n), (1, 2)))
            for length in range(1, 5 if n < 3 else 4):
                for stream in product(operations, repeat=length):
                    add([n, [list(row) for row in stream]], 'exhaustive_repaint_streams_full_rescan')
        for _ in range(100):
            n = rng.randint(4, 20)
            add([n, [[rng.randrange(n), rng.choice((1, 2, 99999, 100000))] for _ in range(rng.randint(1, 50))]], 'seeded_recoloring_boundaries')
        add([100000, [[i, 1] for i in range(100000)]], 'analytic_maximum_fill_in_order', list(range(100000)))
        add([100000, [[0, 1] for _ in range(100000)]], 'analytic_maximum_repeated_assignment', [0]*100000)
        add([2, [[i % 2, 99999] for i in range(100000)]], 'analytic_maximum_repeated_two_cell_fill', [0]+[1]*99999)
        add([100000, [[99999, 100000], [99998, 100000], [99999, 1], [99998, 1]]], 'analytic_maximum_index_and_color', [0, 1, 0, 1])
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    records = [dict(i=i, result=c['expected'], result_type=q.expected_type(c['expected'], language),
                    args_before=c['args'], args_after=c['args'], alias_edges=[]) for i, c in enumerate(batch)]
    return sum(len(q.encoded(r)) for r in records) + len(q.encoded(dict(done=len(batch)))) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case artifact exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        for language in ('javascript', 'python'):
            if expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes']:
                raise ValueError('projected successful output exceeds unchanged observer cap')
    return cases, categories
