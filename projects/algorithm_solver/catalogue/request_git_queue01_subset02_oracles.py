"""Queue01 immutable second-subset source-blind reference preparation.

Full statement domains are admitted independently of bounded brute-force budgets.
No candidate sources, historic cases, execution or promotion are loaded here.
"""
from __future__ import annotations

import ast
from itertools import combinations, product
from math import prod
import random
import re
import json

from . import imported_qualification as q

IDS = (1943, 1959, 1977, 1997, 2049, 2056)
PARAMETERS = {1943: ('segments',), 1959: ('nums', 'k'), 1977: ('num',),
              1997: ('nextVisit',), 2049: ('parents',), 2056: ('pieces', 'positions')}
TITLES = {1943: 'Describe the Painting', 1959: 'Minimum Total Space Wasted With K Resizing Operations',
          1977: 'Number of Ways to Separate Numbers', 1997: 'First Day Where You Have Been in All the Rooms',
          2049: 'Count Nodes With the Highest Score', 2056: 'Number of Valid Move Combinations On Chessboard'}
SLUGS = {1943: 'describe-the-painting', 1959: 'minimum-total-space-wasted-with-k-resizing-operations',
         1977: 'number-of-ways-to-separate-numbers', 1997: 'first-day-where-you-have-been-in-all-the-rooms',
         2049: 'count-nodes-with-the-highest-score', 2056: 'number-of-valid-move-combinations-on-chessboard'}
STATEMENT_SHA256 = {
    1943: '50e19746099dee2c61900733bb0084109eca5d90a382ab60e68223a9acaf76e2',
    1959: '690d5b23cc0a83d4060bc0e2aed8deb803f291ecb6d1d1e454bf2ad2acd3c62a',
    1977: '940741373698e34d60afb07aefaa35b926d0f8a2adf8dacd3ef8aa91e54073b9',
    1997: '37a9643de76f485a5958f8da6a6c5967508b109c868effaa1c88b6e4384aa14e',
    2049: '61bb299b7c1d02a4e2fbc71a0aaf390dca093f4da331e5eb7f47d8e4127d2cca',
    2056: '7cdbc667949079835e4000cc286878b042b62582adb028bb3b4653e0d9435591',
}
EXAMPLE_COUNT = {1943: 3, 1959: 3, 1977: 3, 1997: 3, 2049: 2, 2056: 3}
SEED_BASE = 202610271841
MOD = 1000000007
CONTRACTS = {
    1943: dict(domain='1..20000 segments [start,end,color], 1<=start<end<=100000, unique colors in1..1e9',
               result='Minimal positive-area mixed-COLOR-SET runs; return each [left,right,sum], arbitrary row order.',
               reference='At every elementary endpoint interval, explicitly collect the active color set; merge only equal sets, never just equal sums. <=20 input segments.',
               complexity='Candidate review target O(n log n) time and O(n) space; finite tests are not a complexity proof.',
               comparison='Host compare_observation canonicalizes only outer row order, then delegates unchanged q.compare exact types/mutation/aliases.'),
    1959: dict(domain='1..200 lengths in1..1e6; 0<=k<len(nums)', result='Nonnegative integer minimum waste with at most k cuts.',
               reference='Enumerate every subset of at most k gaps; capacity of each block is its maximum; <=14 lengths.',
               complexity='Candidate review target O(n^2*k) or better; no candidate performance claim.'),
    1977: dict(domain='1..3500 ASCII decimal digits, including leading zeros', result='Count positive nondecreasing token partitions with no leading zeros, modulo1e9+7.',
               reference='Enumerate every cut mask; compare exact Python integers for <=16 digits.',
               complexity='Candidate review target O(n^2) or justified equivalent; large uniform-string oracle uses integer partitions, not candidate agreement.'),
    1997: dict(domain='2..100000 integers; nextVisit[i] in0..i', result='First all-rooms-visited day label modulo1e9+7, starting day0.',
               reference='Literal day-by-day simulation with visit counts, <=14 rooms.',
               complexity='Candidate review target O(n) time and O(n) space; no timing qualification yet.'),
    2049: dict(domain='2..100000 parent entries, root0 parent-1, other parents in0..n-1; valid binary rooted tree, arbitrary labeling.',
               result='Count vertices maximizing product of sizes of nonempty components after deletion.',
               reference='For each deleted vertex, rebuild connectivity components and multiply their sizes; <=100 vertices.',
               complexity='Candidate review target O(n) time/space. Three component product <=(n-1)^3/27<2^53; exact JS Number is sufficient, 32bit is not.'),
    2056: dict(domain='1..4 distinct positions in1..8 squared, rook/bishop/queen pieces, at most one queen.',
               result='Integer valid simultaneous destination combinations; instant steps may swap adjacent positions.',
               reference='Enumerate every legal destination for every piece, then every Cartesian combination, compare positions at integer times0..7. Complete full domain per input.',
               complexity='At most28*15^3 motion combinations; all reference calculations outside sandboxes.'),
}
COMMON_CONTRACT = {
    'exposure': 'Exposed development only; never fresh confirmation.',
    'adapter': 'Reuse existing q.packet/q.batches and bounded observer; pure value calls only, no new engine or variant registry.',
    'candidate_interface': 'Not read; exact export and ordered source parameters need later separately authorized source review. PARAMETERS follow pinned public examples.',
    'helpers': 'All candidate helpers/dependencies/operations must be counted at later source review; none inferred.',
    'mutation': 'Conservative service contract requires unchanged input arguments; not a claim that LeetCode itself bans internal mutation.',
    'alias': 'Independent returned values; no return/input identity aliases allowed by service observer.',
    'numeric': 'All inputs/outputs exact bounded integers; reject bool masquerading as integer. Color sums<=2e13 and tree products<2^53; modulo outputs exact.',
    'unicode': 'ASCII digits for1977, exact lowercase enum piece names for2056.',
    'expected_values': 'Host only, never sent in sandbox packets.',
    'limits': 'q.MAX_FILE/q.MAX_PACKET/q.LIMITS unchanged.',
}
OMITTED_MAXIMUM_SHAPES = {
    1943: 'Maximum count, endpoint and color values fit in explicit overlap/disjoint probes. Arbitrary maximum-size color-set enumeration is not attempted.',
    1959: 'Maximum length, values and resize count included in analytic probes; arbitrary maximum cut-set enumeration is not attempted.',
    1977: 'Maximum length includes zero-leading, one-positive-token and uniform-digit partition families; not every maximum string is brute-force enumerated.',
    1997: 'Maximum length and index values included; arbitrary exponential-length room trajectories are not explicitly simulated.',
    2049: 'Maximum length chains and large complete binary trees fit packet caps; no exhaustive maximum-tree topology claim.',
    2056: 'All64 starting squares for each singleton piece, selected collision geometries and maximum4-piece inputs retained; not every input placement is enumerated.',
}


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def ints(values, low, high, minimum, maximum):
    return type(values) is list and minimum <= len(values) <= maximum and all(integer(v, low, high) for v in values)


def binary_tree(parents):
    if not ints(parents, -1, 99999, 2, 100000) or parents[0] != -1:
        return False
    n = len(parents); children = [[] for _ in range(n)]
    for node in range(1, n):
        parent = parents[node]
        if not integer(parent, 0, n-1) or parent == node:
            return False
        children[parent].append(node)
        if len(children[parent]) > 2:
            return False
    pending = [0]; seen = set()
    while pending:
        node = pending.pop()
        if node in seen:
            return False
        seen.add(node); pending.extend(children[node])
    return len(seen) == n


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid == 1943:
        segments = args[0]
        valid = (type(segments) is list and 1 <= len(segments) <= 20000
                 and all(type(s) is list and len(s) == 3 and integer(s[0], 1, 99999)
                         and integer(s[1], s[0]+1, 100000) and integer(s[2], 1, 10**9) for s in segments))
        if valid:
            valid = len({s[2] for s in segments}) == len(segments)
    elif pid == 1959:
        valid = ints(args[0], 1, 10**6, 1, 200) and integer(args[1], 0, len(args[0])-1)
    elif pid == 1977:
        valid = type(args[0]) is str and 1 <= len(args[0]) <= 3500 and set(args[0]) <= set('0123456789')
    elif pid == 1997:
        values = args[0]
        valid = type(values) is list and 2 <= len(values) <= 100000 and all(integer(v, 0, i) for i, v in enumerate(values))
    elif pid == 2049:
        valid = binary_tree(args[0])
    else:
        pieces, positions = args
        valid = (type(pieces) is list and 1 <= len(pieces) <= 4
                 and all(type(piece) is str and piece in ('rook', 'queen', 'bishop') for piece in pieces)
                 and pieces.count('queen') <= 1 and type(positions) is list and len(positions) == len(pieces)
                 and all(ints(position, 1, 8, 2, 2) for position in positions))
        if valid:
            valid = len({tuple(position) for position in positions}) == len(positions)
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _paint_sets(segments):
    endpoints = sorted({x for segment in segments for x in segment[:2]})
    runs = []
    for left, right in zip(endpoints, endpoints[1:]):
        colors = frozenset(color for start, end, color in segments if start <= left and right <= end)
        if not colors:
            continue
        if runs and runs[-1][1] == left and runs[-1][2] == colors:
            runs[-1][1] = right
        else:
            runs.append([left, right, colors])
    return [[left, right, sum(colors)] for left, right, colors in runs]


def _resize_cuts(nums, k):
    best = None
    for count in range(k+1):
        for cuts in combinations(range(1, len(nums)), count):
            boundaries = (0,) + cuts + (len(nums),)
            waste = sum(max(nums[left:right])*(right-left)-sum(nums[left:right]) for left, right in zip(boundaries, boundaries[1:]))
            best = waste if best is None else min(best, waste)
    return best


def _number_cuts(num):
    answer = 0
    for mask in range(1 << (len(num)-1)):
        cuts = [0] + [i+1 for i in range(len(num)-1) if mask >> i & 1] + [len(num)]
        tokens = [num[left:right] for left, right in zip(cuts, cuts[1:])]
        if any(token[0] == '0' for token in tokens):
            continue
        values = [int(token) for token in tokens]
        answer += all(a <= b for a, b in zip(values, values[1:]))
    return answer % MOD


def _room_days(next_visit):
    visits = [0]*len(next_visit); visited = set(); room = 0; day = 0
    while True:
        visits[room] += 1; visited.add(room)
        if len(visited) == len(next_visit):
            return day % MOD
        room = next_visit[room] if visits[room] % 2 else (room+1) % len(next_visit)
        day += 1
        if day > 1 << 15:
            raise AssertionError('declared room simulation bound exceeded')


def _deleted_components(parents):
    n = len(parents); adjacency = [[] for _ in range(n)]
    for node in range(1, n):
        adjacency[node].append(parents[node]); adjacency[parents[node]].append(node)
    scores = []
    for removed in range(n):
        seen = {removed}; sizes = []
        for start in range(n):
            if start in seen:
                continue
            pending = [start]; seen.add(start); size = 0
            while pending:
                node = pending.pop(); size += 1
                for neighbor in adjacency[node]:
                    if neighbor not in seen:
                        seen.add(neighbor); pending.append(neighbor)
            sizes.append(size)
        scores.append(prod(sizes))
    return scores.count(max(scores))


def _motions(piece, start):
    r, c = start; moves = []
    for target_r in range(1, 9):
        for target_c in range(1, 9):
            dr, dc = target_r-r, target_c-c
            straight = dr == 0 or dc == 0
            diagonal = abs(dr) == abs(dc)
            if not ((piece in ('rook', 'queen') and straight) or (piece in ('bishop', 'queen') and diagonal)):
                continue
            duration = max(abs(dr), abs(dc)); vr = (dr > 0)-(dr < 0); vc = (dc > 0)-(dc < 0)
            moves.append(tuple((r+vr*min(t, duration), c+vc*min(t, duration)) for t in range(8)))
    return moves


def valid_motion_combination(motions):
    return all(len({motion[t] for motion in motions}) == len(motions) for t in range(8))


def _chess_destinations(pieces, positions):
    choices = [_motions(piece, position) for piece, position in zip(pieces, positions)]
    return sum(valid_motion_combination(motions) for motions in product(*choices))


def expected(pid, args):
    validate(pid, args)
    bounded = ((pid == 1943 and len(args[0]) <= 20) or (pid == 1959 and len(args[0]) <= 14)
               or (pid == 1977 and len(args[0]) <= 16) or (pid == 1997 and len(args[0]) <= 14)
               or (pid == 2049 and len(args[0]) <= 100) or pid == 2056)
    if not bounded:
        raise ValueError('bounded independent reference budget exceeded')
    return {1943: _paint_sets, 1959: _resize_cuts, 1977: _number_cuts,
            1997: _room_days, 2049: _deleted_components, 2056: _chess_destinations}[pid](*args)


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned official definition bytes required')
    statement = re.sub(r'(?m)^L\d+: ?', '', raw.decode())
    if f'{pid}. {TITLES[pid]}' not in statement or f'https://leetcode.com/problems/{SLUGS[pid]}/' not in statement:
        raise ValueError('numeric/title/slug mismatch')
    cases = []
    for match in re.finditer(r'Input:\s*([^\n]+)\n\s*Output:\s*([^\n]+)', statement):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(call, ast.Call) or call.args or tuple(item.arg for item in call.keywords) != PARAMETERS[pid]:
            raise ValueError('ordered public-example parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]; answer = json.loads(match[2])
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent reference disagrees with official example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete official examples required')
    return cases


def integer_partition_count(n):
    """Uniform nonzero decimal token strings correspond exactly to integer partitions."""
    counts = [1] + [0]*n
    for part in range(1, n+1):
        for total in range(part, n+1):
            counts[total] = (counts[total]+counts[total-part]) % MOD
    return counts[n]


def _generate_cases(pid, raw):
    cases = public_examples(pid, raw); categories = ['pinned_public_example']*len(cases)
    rng = random.Random(SEED_BASE+pid); sentinel = object()

    def add(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 1943:
        intervals = list(combinations(range(1, 5), 2))
        for n in range(1, 4):
            for choices in product(intervals, repeat=n):
                add([[[left, right, color] for (left, right), color in zip(choices, (1, 2, 3))]], 'exhaustive_small_endpoint_arrangements')
        for _ in range(80):
            n = rng.randint(1, 20); colors = rng.sample(range(1, 1000000001), n)
            segments = []
            for color in colors:
                left, right = sorted(rng.sample(range(1, 100001), 2)); segments.append([left, right, color])
            rng.shuffle(segments); add([segments], 'seeded_interval_color_sets_numeric_extremes')
        add([[[1, 3, 1], [1, 3, 4], [3, 5, 2], [3, 5, 3]]], 'equal_sum_distinct_color_sets')
        segments = [[1, 100000, 1000000000-i] for i in range(20000)]
        add([segments], 'analytic_maximum_overlap_and_color_sum', [[1, 100000, 20000*1000000000-19999*20000//2]])
        segments = [[i*2+1, i*2+2, i+1] for i in range(20000)]
        add([segments], 'analytic_maximum_disjoint_count', [list(row) for row in segments])
    elif pid == 1959:
        for n in range(1, 6):
            for values in product((1, 2, 4), repeat=n):
                for k in range(n):
                    add([list(values), k], 'exhaustive_array_and_cut_masks')
        for _ in range(80):
            n = rng.randint(6, 14)
            add([[rng.choice((1, 2, 999999, 1000000)) for _ in range(n)], rng.randrange(n)], 'seeded_resize_cut_sets')
        for value in (1, 1000000):
            for k in (0, 1, 99, 199):
                add([[value]*200, k], 'analytic_maximum_constant_capacity', 0)
        values = [1, 1000000]*100
        add([values, 0], 'analytic_no_resize_maximum_variation', 100*999999)
        add([values, 199], 'analytic_resize_every_gap', 0)
    elif pid == 1977:
        for n in range(1, 7):
            for digits in product('012', repeat=n):
                add([''.join(digits)], 'exhaustive_digit_strings_and_cut_masks')
        for _ in range(80):
            add([''.join(rng.choice('001239') for _ in range(rng.randint(7, 16)))], 'seeded_exact_numeric_token_partitions')
        for value, answer in [('0'*3500, 0), ('0'+'9'*3499, 0), ('1'+'0'*3499, 1),
                              ('1'*3500, integer_partition_count(3500)), ('9'*3500, integer_partition_count(3500))]:
            add([value], 'analytic_maximum_length_integer_partition_or_zero', answer)
    elif pid == 1997:
        for n in range(2, 7):
            for values in product(*(range(i+1) for i in range(n))):
                add([list(values)], 'exhaustive_room_transition_arrays')
        for _ in range(100):
            n = rng.randint(7, 14)
            add([[rng.randrange(i+1) for i in range(n)]], 'seeded_literal_day_simulation')
        n = 100000
        add([[0]*n], 'analytic_maximum_all_return_to_zero', (pow(2, n, MOD)-2) % MOD)
        add([list(range(n))], 'analytic_maximum_self_return', 2*(n-1))
        add([[max(0, i-1) for i in range(n)]], 'analytic_maximum_previous_room_return', n*(n-1) % MOD)
        values = list(range(n)); values[-1] = 0
        add([values], 'analytic_final_entry_does_not_change_first_visit', 2*(n-1))
    elif pid == 2049:
        for n in range(2, 7):
            for parents in product(range(n), repeat=n-1):
                values = [-1]+list(parents)
                if binary_tree(values):
                    add([values], 'exhaustive_arbitrarily_labeled_small_binary_trees')
        for _ in range(100):
            n = rng.randint(7, 100); parents = [-1]; available = [0]; child_count = [0]*n
            for node in range(1, n):
                parent = rng.choice(available); parents.append(parent); child_count[parent] += 1
                if child_count[parent] == 2:
                    available.remove(parent)
                available.append(node)
            labels = [0]+rng.sample(range(1, n), n-1); shuffled = [-1]*n
            for node in range(1, n):
                shuffled[labels[node]] = labels[parents[node]]
            add([shuffled], 'seeded_binary_trees_with_label_permutations')
        for n in (99999, 100000):
            add([[-1]+list(range(n-1))], 'analytic_maximum_chain_midpoint_scores', 1 if n % 2 else 2)
        add([[-1]+[(i-1)//2 for i in range(1, 65535)]], 'analytic_complete_binary_tree_two_maximizers', 2)
    else:
        for piece in ('rook', 'bishop', 'queen'):
            for r in range(1, 9):
                for c in range(1, 9):
                    add([[piece], [[r, c]]], 'exhaustive_single_piece_positions_and_destinations')
        positions = [[1, 1], [1, 2], [2, 1], [2, 2], [4, 4], [4, 5], [7, 7], [8, 8]]
        for first, second in combinations(positions, 2):
            for pieces in product(('rook', 'bishop', 'queen'), repeat=2):
                if pieces.count('queen') <= 1:
                    add([list(pieces), [first, second]], 'pair_collision_crossing_swaps_and_stops')
        for n in (3, 4):
            for _ in range(12):
                spots = rng.sample([(r, c) for r in range(1, 9) for c in range(1, 9)], n)
                pieces = [rng.choice(('rook', 'bishop')) for _ in range(n)]
                if rng.randrange(2):
                    pieces[0] = 'queen'
                add([pieces, [list(spot) for spot in spots]], 'seeded_maximum_piece_count_full_destination_product')
    return cases, categories


def compare_observation(pid, case, record, language):
    """Host-only row-order equivalence; unchanged observer and exact effect checks."""
    if pid not in IDS:
        raise ValueError('unsupported identity')
    if pid != 1943:
        return q.compare(case, record, language)
    if 'error' in record:
        return 'candidate_error'
    result = record.get('result')
    if type(result) is not list or any(type(row) is not list or len(row) != 3
                                     or any(type(value) is not int for value in row) for row in result):
        return 'result_value'
    normalized = dict(record, result=sorted(result))
    return q.compare(dict(case, expected=sorted(case['expected'])), normalized, language)


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
        if any(expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes'] for language in ('python', 'javascript')):
            raise ValueError('projected successful output exceeds unchanged observer cap')
    return cases, categories
