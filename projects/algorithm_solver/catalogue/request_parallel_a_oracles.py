"""Fixed batch A pure public-definition oracles; no source loader or runner.

Small references enumerate legal states, explicit choices, graph closure or
index tuples. Large analytic probes remain separately categorized and charged.
"""
from __future__ import annotations

import ast
from functools import lru_cache
from itertools import combinations, combinations_with_replacement, product
import json
from math import comb
import random
import re

from . import imported_qualification as q
from .imported_clean_domains import integer, ints, rows, text

IDS = (3223, 3232, 3532, 3583, 3612)
PARAMETERS = {3223: ('s',), 3232: ('nums',), 3532: ('n', 'nums', 'maxDiff', 'queries'),
              3583: ('nums',), 3612: ('s',)}
STATEMENT_SHA256 = {
    3223: '352de890dc133abb40b87841a5d86f794380207a72ffd51c88ab4d1671fdb30e',
    3232: '175b45d35b8485e3cec17e2521ce5af17ddebfb27e81d25cb8e8afd3847294b4',
    3532: '3ee04fd2c1a603aa29c15c669d472a297dbdeb4ea3427b3629a72bd1efedddc0',
    3583: 'b7fb74bbf34c0d874768332b250b43ecd33b88c1a0a3f75f19a065bddae08efb',
    3612: '68a781e4845c55ce84027e87c619db43b815a1287be4326c2d297b2c0469597d',
}
EXAMPLE_COUNT = {3223: 2, 3232: 3, 3532: 2, 3583: 3, 3612: 2}
CASE_COUNT = {3223: 558, 3232: 387, 3532: 380, 3583: 400, 3612: 828}
CASES_SHA256 = {
    3223: '028004ce3dd7f16f588e52d1148d6974f1db16fcb206dad947d6a48b0cbf2f5a',
    3232: '4785f0260ba85c123872734324ec4a8245c722296e0978b81ff8105a2a904bca',
    3532: '0c95e8f644f2cdb1665b6ce819ca359621f9f91894a45a892ec038beb53aeecd',
    3583: '45d6ce3bf83f11ad93245deebc4f9529ce37ccb9e31561d2c742e65824d7fbd2',
    3612: '6a363040c91bd48d79d946fd41df8b78108a3eaa7547157a71d66747fb842529',
}
SEED_BASE = 202610271400
MOD = 1000000007
SMALL_BUDGET = {3223: 12, 3232: 100, 3532: 12, 3583: 12, 3612: 12}
OMITTED_MAXIMUM_SHAPES = {
    3223: 'Full-length analytic strings are included; arbitrary length-200000 state enumeration is not attempted.',
    3232: 'The full length-100 domain is tractable per input, but the finite set does not enumerate all arrays.',
    3532: 'Combined maximum-size six-digit arrays and six-digit query endpoints exceed the unchanged packet cap. Full node count, full query count, and a fitting simultaneous maximum with low labels are retained.',
    3583: 'Full-length analytic arrays are retained; arbitrary length-100000 index-triple enumeration is not attempted.',
    3612: 'Maximum-length and maximum-output analytic strings are retained; general reverse-index enumeration is capped at input length12. No full-domain performance claim.',
}


def validate(pid, args):
    """Pinned full domain, separate from the smaller reference computation budget."""
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered argument shape')
    if pid == 3223:
        good = text(args[0], maximum=200000)
    elif pid == 3232:
        good = ints(args[0], 1, 99, 1, 100)
    elif pid == 3583:
        good = ints(args[0], 0, 100000, 3, 100000)
    elif pid == 3612:
        good = text(args[0], 'abcdefghijklmnopqrstuvwxyz*#%', 1, 20)
    else:
        n, values, difference, queries = args
        good = (integer(n, 1, 100000) and ints(values, 0, 100000, n, n) and
                all(a <= b for a, b in zip(values, values[1:])) and
                integer(difference, 0, 100000) and rows(queries, 2, 0, n - 1, 1, 100000))
    if not good:
        raise ValueError('input outside pinned full statement domain')


@lru_cache(maxsize=16384)
def _minimum_remaining(s):
    best = len(s)
    for center, letter in enumerate(s):
        left, right = s.rfind(letter, 0, center), s.find(letter, center + 1)
        if left >= 0 and right >= 0:
            successor = s[:left] + s[left + 1:right] + s[right + 1:]
            best = min(best, _minimum_remaining(successor))
    return best


def _allowed_digit_choices(values):
    for width in (1, 2):
        alice = [i for i, value in enumerate(values) if len(str(value)) == width]
        selected = set(alice)
        if sum(values[i] for i in alice) > sum(value for i, value in enumerate(values) if i not in selected):
            return True
    return False


def _pairwise_closure(n, values, difference, queries):
    reachable = [[abs(values[i] - values[j]) <= difference for j in range(n)] for i in range(n)]
    for middle in range(n):
        for start in range(n):
            if reachable[start][middle]:
                reachable[start] = [a or b for a, b in zip(reachable[start], reachable[middle])]
    return [reachable[a][b] for a, b in queries]


def _special_triples(values):
    return sum(values[i] == 2 * values[j] == values[k]
               for i, j, k in combinations(range(len(values)), 3)) % MOD


def _reverse_index_string(s):
    lengths = [0]
    for token in s:
        before = lengths[-1]
        lengths.append(max(0, before - 1) if token == '*' else
                       2 * before if token == '#' else before if token == '%' else before + 1)
    output = []
    for final_index in range(lengths[-1]):
        index = final_index
        for position in range(len(s) - 1, -1, -1):
            token, before = s[position], lengths[position]
            if token == '%':
                index = before - 1 - index
            elif token == '#':
                if before == 0:
                    raise ValueError('impossible nonempty trace through empty duplication')
                index %= before
            elif token == '*':
                pass  # Every surviving position has the same earlier index.
            elif index == before:
                output.append(token)
                break
        else:
            raise ValueError('output position did not reach an appended letter')
    return ''.join(output)


def expected(pid, args):
    validate(pid, args)
    size = args[0] if pid == 3532 else len(args[0])
    if size > SMALL_BUDGET[pid] or (pid == 3532 and len(args[3]) > 144):
        raise ValueError('bounded independent oracle budget exceeded')
    if pid == 3223:
        return _minimum_remaining(args[0])
    if pid == 3232:
        return _allowed_digit_choices(args[0])
    if pid == 3532:
        return _pairwise_closure(*args)
    if pid == 3583:
        return _special_triples(args[0])
    return _reverse_index_string(args[0])


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact pinned statement bytes required')
    cases = []
    pattern = r'Input:\s*(.*?)\n\s*Output:\s*(.*?)(?=\n\s*(?:Explanation:|Constraints:)|$)'
    for match in re.finditer(pattern, raw.decode(), re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if (not isinstance(call, ast.Call) or call.args or
                tuple(item.arg for item in call.keywords) != PARAMETERS[pid]):
            raise ValueError('pinned example ordered parameters differ')
        args = [ast.literal_eval(item.value) for item in call.keywords]
        answer = json.loads(match[2].strip())
        if not q.exact(expected(pid, args), answer):
            raise ValueError('independent oracle disagrees with public example')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('complete pinned public examples required')
    return cases


def _generate_cases(pid, statement_bytes):
    cases = public_examples(pid, statement_bytes)
    categories = ['pinned_public_example'] * len(cases)
    rng = random.Random(SEED_BASE + pid)

    def add(args, category, answer=None):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is None else answer, 'compare': 'return'})
        categories.append(category)

    if pid == 3223:
        for length in range(1, 9):
            for letters in product('ab', repeat=length):
                add([''.join(letters)], 'exhaustive_binary_length_1_to_8')
        for _ in range(40):
            add([''.join(rng.choice('abc') for _ in range(rng.randrange(9, 13)))], 'seeded_ternary_length_9_to_12')
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for s, answer in [('a' * 200000, 2), ('a' * 199999, 1), ('ab' * 100000, 4),
                          ('abc' * 66666 + 'ab', 4), (alphabet * 7692 + alphabet[:8], 44),
                          ('z' * 199999 + 'a', 2)]:
            add([s], 'analytic_full_length_parity_shape', answer)
    elif pid == 3232:
        for length in range(1, 5):
            for values in product((1, 9, 10, 99), repeat=length):
                add([list(values)], 'exhaustive_digit_boundary_arrays_length_1_to_4')
        for _ in range(40):
            add([[rng.randrange(1, 100) for _ in range(rng.randrange(5, 101))]], 'seeded_full_domain_digit_choices')
        for values, answer in [([99] * 100, True), ([9] * 100, True),
                               ([2] * 90 + [18] * 10, False), ([2] * 89 + [18] * 11, True)]:
            add([values], 'analytic_length_100_choice', answer)
    elif pid == 3532:
        for n in range(1, 7):
            queries = [list(pair) for pair in product(range(n), repeat=2)]
            for values in combinations_with_replacement((0, 1, 3), n):
                for difference in (0, 1, 2, 3):
                    add([n, list(values), difference, queries], 'exhaustive_sorted_ternary_graphs_length_1_to_6')
        for _ in range(40):
            n = rng.randrange(7, 13)
            values = sorted(rng.choice((0, 1, 2, 99999, 100000)) for _ in range(n))
            queries = [[rng.randrange(n), rng.randrange(n)] for _ in range(40)]
            add([n, values, rng.choice((0, 1, 2, 99998, 99999, 100000)), queries], 'seeded_pairwise_threshold_graphs')
        endpoints = [[0, 99999], [99999, 0], [50000, 50000]]
        for args, answer in [([100000, [0] * 100000, 0, endpoints], [True] * 3),
                             ([100000, list(range(100000)), 1, endpoints], [True] * 3),
                             ([100000, list(range(100000)), 0, endpoints], [False, False, True]),
                             ([100000, [0] * 50000 + [100000] * 50000, 99999,
                               [[0, 49999], [49999, 50000], [99999, 50000], [0, 99999]]], [True, False, True, False]),
                             ([1, [100000], 100000, [[0, 0]] * 100000], [True] * 100000),
                             ([100000, [0] * 100000, 0, [[0, 0]] * 100000], [True] * 100000)]:
            add(args, 'analytic_maximum_graph_shape', answer)
    elif pid == 3583:
        for length in range(3, 6):
            for values in product((0, 1, 2), repeat=length):
                add([list(values)], 'exhaustive_ternary_index_triples_length_3_to_5')
        for _ in range(40):
            add([[rng.choice((0, 1, 2, 50000, 99999, 100000)) for _ in range(rng.randrange(6, 13))]],
                'seeded_numeric_boundary_index_triples')
        for values, answer in [([0] * 100000, comb(100000, 3) % MOD), ([1] * 100000, 0),
                               ([100000] * 33333 + [50000] * 33334 + [100000] * 33333, (33333**2 * 33334) % MOD),
                               ([2] * 25000 + [1] * 50000 + [2] * 25000, (25000**2 * 50000) % MOD),
                               (list(range(100000)), 0), ([0] * 99999 + [100000], comb(99999, 3) % MOD)]:
            add([values], 'analytic_length_100000_triplet_shape', answer)
    else:
        for length in range(1, 5):
            for tokens in product('ab*#%', repeat=length):
                add([''.join(tokens)], 'exhaustive_operation_strings_length_1_to_4')
        for _ in range(40):
            add([''.join(rng.choice('abc*#%') for _ in range(rng.randrange(5, 13)))], 'seeded_reverse_index_strings')
        for s, answer in [('a' + '#' * 19, 'a' * 524288), ('ab' + '#' * 18, 'ab' * 262144),
                          ('ab' + '#' * 17 + '%', 'ba' * 131072), ('ab' + '#' * 17 + '*', ('ab' * 131072)[:-1]),
                          ('*#%' * 6 + '*#', ''), ('abc' + '#' * 15 + '%*', ('cba' * 32768)[:-1])]:
            add([s], 'analytic_length_20_expansion_shape', answer)
    return cases, categories


def expected_observation_bytes(batch, language):
    """Exact successful observer JSON size projection, not candidate execution."""
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    records = [{'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], language),
                'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []} for i, c in enumerate(batch)]
    # The Python observer uses default separators for its final done record.
    return (sum(len(q.encoded(record)) for record in records) +
            len(q.encoded({'done': len(batch)})) + (language == 'python'))


def build_cases(pid, statement_bytes):
    cases, categories = _generate_cases(pid, statement_bytes)
    if len(cases) != CASE_COUNT.get(pid) or q.sha(q.encoded(cases)) != CASES_SHA256.get(pid):
        raise ValueError('frozen batch A population or case bytes changed')
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('case file exceeds unchanged reader cap')
    for _, batch in q.batches(cases):
        for language in ('javascript', 'python'):
            if expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes']:
                raise ValueError('expected observation exceeds unchanged output cap')
    return cases, categories
