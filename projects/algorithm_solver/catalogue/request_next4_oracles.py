"""Fixed next-four public-definition oracles; no candidate or case-file access.

All small-case answers come from bounded state/partition/assignment enumeration.
Large analytic probes have separate categories and explicit transport limits.
This module neither executes candidates nor grants qualification or admission.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
from itertools import product
import json
import random
import re

IDS = (3228, 3523, 3558, 3597)
PARAMETERS = {3228: ('s',), 3523: ('nums',), 3558: ('edges',), 3597: ('s',)}
STATEMENT_SHA256 = {
    3228: 'db1aaf0e418d214a790b49059b4a1c38292694d8e8afebaf6d8851cbb83bc7de',
    3523: '5905bd589f27999ecd696c9fb848f554cdaa91dbc70f5c9d29a50245b6d49a84',
    3558: 'c70fa2855b489bf5523b3152f0d10f61c663f2914d422d8210da3ce2968f0c1d',
    3597: '2bc59aac244877addb10ead05b68376c2725fd405f6828f6e63616706a0ed1da',
}
CASE_COUNT = {3228: 1109, 3523: 1179, 3558: 1468, 3597: 1109}
CASES_SHA256 = {
    3228: '6dfd774dcceea7ed5a47d16acc3be74990df8a0c12bac4183d861547a260eb55',
    3523: '766059fd4e5d0a39122b2a59cee847f90a4d75519c2ce3895d202b0a5ed44b8a',
    3558: 'd849f05afcb3e42ea6132181e552466098f2d9877355044e9c788b5a899a8eba',
    3597: 'a0d494e8e7a7124f330ca13fe8bc2148db57a18d9d6e9ea91699e11995ef318d',
}
SEED_BASE = 202610270000
MOD = 1000000007
SMALL_BUDGET = {3228: 12, 3523: 10, 3558: 10, 3597: 12}
OMITTED_MAXIMUM_SHAPES = {
    3228: 'Arbitrary maximum-length state enumeration is not attempted; declared full-size analytic strings are retained.',
    3523: 'Maximum-length arrays filled with six-digit values and fully increasing/decreasing length-200000 arrays exceed the unchanged packet cap and are not executed.',
    3558: 'A 100000-node deep chain and many maximum-node high-label trees exceed the unchanged packet cap. The deepest analytic chain has 50000 nodes; the 100000-node star tests size, not worst depth.',
    3597: 'Only declared maximum-length analytic patterns are executed, not arbitrary-domain string enumeration.',
}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(pid, args):
    """Full pinned input domain, independent of the smaller oracle budget."""
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != 1:
        raise ValueError('unsupported problem or ordered argument shape')
    value = args[0]
    if pid in (3228, 3597):
        alphabet = '01' if pid == 3228 else 'abcdefghijklmnopqrstuvwxyz'
        if type(value) is not str or not 1 <= len(value) <= 100000 or not set(value) <= set(alphabet):
            raise ValueError('string outside pinned ASCII domain')
        return
    if pid == 3523:
        if (type(value) is not list or not 1 <= len(value) <= 200000 or
                any(type(x) is not int or not 1 <= x <= 200000 for x in value)):
            raise ValueError('array outside pinned positive integer domain')
        return
    if type(value) is not list or not 1 <= len(value) <= 99999:
        raise ValueError('tree edge count outside pinned domain')
    n = len(value) + 1
    parents = list(range(n + 1))
    sizes = [1] * (n + 1)

    def find(node):
        while node != parents[node]:
            parents[node] = parents[parents[node]]
            node = parents[node]
        return node

    for edge in value:
        if (type(edge) is not list or len(edge) != 2 or
                any(type(x) is not int or not 1 <= x <= n for x in edge)):
            raise ValueError('invalid tree endpoint shape or label')
        a, b = map(find, edge)
        if a == b:
            raise ValueError('self edge, duplicate edge or cycle is not a tree')
        if sizes[a] < sizes[b]:
            a, b = b, a
        parents[b] = a
        sizes[a] += sizes[b]
    if sizes[find(1)] != n:
        raise ValueError('tree must be connected and contain every label')


@lru_cache(maxsize=8192)
def _maximum_moves(s):
    answers = [0]
    for start in range(len(s) - 1):
        if s[start:start + 2] != '10':
            continue
        end = start + 1
        while end < len(s) and s[end] == '0':
            end += 1
        successor = s[:start] + s[start + 1:end] + '1' + s[end:]
        answers.append(1 + _maximum_moves(successor))
    return max(answers)


def _partition_maxima(values):
    best = 0
    for mask in range(1 << (len(values) - 1)):
        blocks = []
        start = 0
        for stop in range(1, len(values) + 1):
            if stop == len(values) or mask & (1 << (stop - 1)):
                blocks.append(max(values[start:stop]))
                start = stop
        if all(a <= b for a, b in zip(blocks, blocks[1:])):
            best = max(best, len(blocks))
    return best


def _path_weight_assignments(edges):
    n = len(edges) + 1
    neighbors = [[] for _ in range(n + 1)]
    for a, b in edges:
        neighbors[a].append(b)
        neighbors[b].append(a)
    parent, depth, queue = {1: 0}, {1: 0}, [1]
    for node in queue:
        for other in neighbors[node]:
            if other not in parent:
                parent[other] = node
                depth[other] = depth[node] + 1
                queue.append(other)
    deepest = max(depth.values())
    counts = set()
    for node in queue:
        if depth[node] != deepest:
            continue
        path = []
        while node != 1:
            path.append((parent[node], node))
            node = parent[node]
        counts.add(sum(sum(weights) % 2 == 1 for weights in product((1, 2), repeat=len(path))) % MOD)
    if len(counts) != 1:
        raise ValueError('deepest-path assignment counts disagree')
    return counts.pop()


def _valid_cut_partition(s):
    """Enumerate all emitted cuts, then validate the normative prefix rules."""
    solutions = []
    for mask in range(1, 1 << len(s)):
        seen, segments, start = set(), [], 0
        for stop in range(1, len(s) + 1):
            if not mask & (1 << (stop - 1)):
                continue
            segment = s[start:stop]
            if segment in seen or any(s[start:short] not in seen for short in range(start + 1, stop)):
                break
            seen.add(segment)
            segments.append(segment)
            start = stop
        else:
            # Unemitted tail is legal only if no growing prefix becomes unseen.
            if all(s[start:stop] in seen for stop in range(start + 1, len(s) + 1)):
                solutions.append(segments)
    if len(solutions) != 1:
        raise ValueError('normative cut conditions did not select one output')
    return solutions[0]


def expected(pid, args):
    """Pure independent answer oracle, bounded before combinatorial work."""
    validate(pid, args)
    size = len(args[0]) + (pid == 3558)
    if size > SMALL_BUDGET[pid]:
        raise ValueError('small oracle budget exceeded; analytic probes are separate')
    if pid == 3228:
        return _maximum_moves(args[0])
    if pid == 3523:
        return _partition_maxima(args[0])
    if pid == 3558:
        return _path_weight_assignments(args[0])
    return _valid_cut_partition(args[0])


def _public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact new official-tool statement pin required')
    text = raw.decode('utf-8')
    cases = []
    pattern = r'Input:\s*(.*?)\n\s*Output:\s*(.*?)(?=\n\s*(?:Explanation:|Constraints:)|$)'
    for match in re.finditer(pattern, text, re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if (not isinstance(call, ast.Call) or call.args or
                tuple(item.arg for item in call.keywords) != PARAMETERS[pid]):
            raise ValueError('pinned public example argument order differs')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = ast.literal_eval(match[2].strip())
        actual = expected(pid, args)
        if type(actual) is not type(answer) or actual != answer:
            raise ValueError('independent oracle disagrees with pinned public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != 2:
        raise ValueError('both pinned public examples are required')
    return cases


def _prufer_tree(n, sequence):
    degree = [0] + [1] * n
    for node in sequence:
        degree[node] += 1
    edges = []
    for node in sequence:
        leaf = next(i for i in range(1, n + 1) if degree[i] == 1)
        edges.append([leaf, node])
        degree[leaf] -= 1
        degree[node] -= 1
    edges.append([i for i in range(1, n + 1) if degree[i] == 1])
    return edges


def _repeated_letter_segments(letter, length):
    segments, consumed, size = [], 0, 1
    while consumed + size <= length:
        segments.append(letter * size)
        consumed += size
        size += 1
    return segments, length - consumed


def _generate_cases(pid, statement_bytes):
    cases = _public_examples(pid, statement_bytes)
    categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid)

    def add(args, category, answer=None):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is None else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3228:
        for length in range(1, 10):
            for letters in product('01', repeat=length):
                add([''.join(letters)], 'exhaustive_binary_length_1_to_9')
        for _ in range(80):
            add([''.join(rng.choice('01') for _ in range(rng.randrange(10, 13)))], 'seeded_binary_length_10_to_12')
        for value, answer in [('0' * 100000, 0), ('1' * 100000, 0),
                              ('0' * 50000 + '1' * 50000, 0),
                              ('1' * 50000 + '0' * 50000, 50000),
                              ('10' * 50000, 50000 * 50001 // 2)]:
            add([value], 'analytic_shape', answer)
    elif pid == 3523:
        for length in range(1, 7):
            for values in product((1, 2, 3), repeat=length):
                add([list(values)], 'exhaustive_ternary_length_1_to_6')
        for _ in range(80):
            add([[rng.choice((1, 2, 3, 199999, 200000)) for _ in range(rng.randrange(7, 11))]],
                'seeded_partition_length_7_to_10')
        for values, answer in [([1] * 200000, 200000), ([200000] + [1] * 199999, 1),
                               ([1] * 100000 + [200000] * 100000, 200000),
                               (list(range(1, 50001)), 50000), (list(range(50000, 0, -1)), 1)]:
            add([values], 'analytic_shape', answer)
    elif pid == 3558:
        for n in range(2, 7):
            for sequence in product(range(1, n + 1), repeat=n - 2):
                add([_prufer_tree(n, sequence)], 'exhaustive_prufer_nodes_2_to_6')
        for _ in range(20):
            n = rng.randrange(7, 11)
            edges = _prufer_tree(n, [rng.randrange(1, n + 1) for _ in range(n - 2)])
            for edge in edges:
                if rng.randrange(2):
                    edge.reverse()
            rng.shuffle(edges)
            add([edges], 'seeded_prufer_nodes_7_to_10')
        for edges, answer in [([[1, i] for i in range(2, 100001)], 1),
                              ([[i, i + 1] for i in range(1, 50000)], pow(2, 49998, MOD)),
                              ([[i // 2, i] for i in range(2, 65536)], 2**14),
                              ([[2, i] for i in range(1, 10001) if i != 2], 2),
                              ([[2, 1]], 1)]:
            add([edges], 'analytic_tree_shape', answer)
    else:
        for length in range(1, 10):
            for letters in product('ab', repeat=length):
                add([''.join(letters)], 'exhaustive_binary_alphabet_length_1_to_9')
        for _ in range(80):
            add([''.join(rng.choice('abc') for _ in range(rng.randrange(10, 13)))],
                'seeded_ternary_alphabet_length_10_to_12')
        a100000, _ = _repeated_letter_segments('a', 100000)
        a99999, tail = _repeated_letter_segments('a', 99999)
        z100000, _ = _repeated_letter_segments('z', 100000)
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for value, answer in [('a' * 100000, a100000), (alphabet, list(alphabet)),
                              ('a' * 99999 + 'b', a99999 + ['a' * tail + 'b']),
                              ('a' * 99999, a99999), ('z' * 100000, z100000)]:
            add([value], 'analytic_string_shape', answer)
    return cases, categories


def build_cases(pid, statement_bytes):
    """Reproduce the exact pre-source case population or fail closed."""
    cases, categories = _generate_cases(pid, statement_bytes)
    if len(cases) != CASE_COUNT[pid] or sha(encoded(cases)) != CASES_SHA256[pid]:
        raise ValueError('frozen next-four generated cases changed')
    return cases, categories
