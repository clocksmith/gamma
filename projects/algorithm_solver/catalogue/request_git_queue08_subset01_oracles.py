"""Queue 08 subset 01 source-blind specification references, not qualifications.

Only exact gated official definition envelopes are accepted. Full domain validators
are distinct from bounded exhaustive references and analytic maximum-shape probes.
Native callable/export/receiver/helper identities and resource behavior are unknown.
"""
from __future__ import annotations

import ast
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, combinations_with_replacement, product
import json
import random
import re
import string

from . import imported_qualification as q
from .imported_clean_domains import integer, ints, text

IDS = (2981, 2998, 3002, 3006, 3012, 3016)
PARAMETERS = {2981: ('s',), 2998: ('x', 'y'), 3002: ('nums1', 'nums2'),
              3006: ('s', 'a', 'b', 'k'), 3012: ('nums',), 3016: ('word',)}
STATEMENT_SHA256 = {2981: '0b6727432ac65b2b70edf666929d56afc996ad569acbe5958f87b719e739b218', 2998: '6d7dd6e78586e831c03932a7b39421c1e501f5896f40e29b80b05af98e24c90e', 3002: '6ca97c47690816e6b03f39d5823192079c4ab1264577ecff2b8cab6742ed59f6', 3006: '285f86ee15034e182abafd2fa7e3d2bc2f85b1e849e24f93fa8e19b60bfb8e3c', 3012: '1a49f0aa521b69495e7a029e9b04c82f70a2713ef36c763fe680a80a4bc609ff', 3016: '44d6f6d9d8353c80f37fe2728d9134184463e55b729478aea5a25389f60df58c'}
TITLES = {2981: 'Find Longest Special Substring That Occurs Thrice I', 2998: 'Minimum Number of Operations to Make X and Y Equal', 3002: 'Maximum Size of a Set After Removals', 3006: 'Find Beautiful Indices in the Given Array I', 3012: 'Minimize Length of Array Using Operations', 3016: 'Minimum Number of Pushes to Type Word II'}
EXAMPLE_COUNT = {2981: 3, 2998: 3, 3002: 3, 3006: 2, 3012: 3, 3016: 3}
CASE_COUNT = {2981: 570, 2998: 1299, 3002: 338, 3006: 9373, 3012: 515, 3016: 404}
CASES_SHA256 = {2981: '96fa1a499c616b5059fa9a4752d36684229fb59effb22304649ae4beb4d00fcb', 2998: 'f837a783385f94a12bfe2bea46aa3fda4435e63a111a9d47867d34d6c4b4037f', 3002: '42aa8315a2ab13cf59e964d51a573fae8ff7716e3b2715899e3e7afbf6557248', 3006: 'a7dcf5edc4bbf49409d94986d05ac350e7945abc67e839d2ec88b598e49cf928', 3012: '5f4d0c67369afc3fc5fe628d62637ca1e049fc77dcfc12eb5d4d496d42f00258', 3016: '2a41e88ae1219f9a476a3496488f2c1d431b3c3c272dca5b4385f705b30e232a'}
SEED_BASE = 202610272008
OMITTED_MAXIMUM_SHAPES = {
    2981: 'All maximum-length shape probes are finite, not an exhaustive 26^50 population.',
    2998: 'Small interval graph equivalence and finite full-bound probes do not cover all 100000000 ordered pairs.',
    3002: 'Arbitrary maximum arrays are not brute-forced; retained large expectations are analytic.',
    3006: 'Current public I domain permits length 100000. Large probes are analytic, not evidence that arbitrary quadratic matching meets native limits.',
    3012: 'Valid [1000000000]*100000 already has 1100001 compact JSON bytes before an argument envelope, beyond the unchanged 1100000 packet cap. Length maxima use small values; numeric extremes are separate.',
    3016: 'Finite maximum-length frequency profiles are not exhaustive; candidate native interface and performance remain unmeasured.',
}


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported exact identity or ordered argument shape')
    if pid == 2981:
        valid = text(args[0], minimum=3, maximum=50)
    elif pid == 2998:
        valid = all(integer(x, 1, 10000) for x in args)
    elif pid == 3002:
        a, b = args
        valid = ints(a, 1, 10**9, 2, 20000) and len(a) % 2 == 0 and ints(b, 1, 10**9, len(a), len(a))
    elif pid == 3006:
        s, a, b, k = args
        valid = (text(s, maximum=100000) and text(a, maximum=10) and text(b, maximum=10)
                 and integer(k, 1, len(s)))
    elif pid == 3012:
        valid = ints(args[0], 1, 10**9, 1, 100000)
    else:
        valid = text(args[0], maximum=100000)
    if not valid:
        raise ValueError('outside pinned full statement domain')


def _special(s):
    counts = Counter(s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)
                     if len(set(s[i:j])) == 1)
    return max((len(part) for part, count in counts.items() if count >= 3), default=-1)


def _operations(x, y):
    # A direct +/-1 route has length d. Any route with at most d edges cannot
    # exceed x+d: only +1 can increase. A nonpositive excursion cannot help
    # positive endpoints and can be replaced by a shorter positive route.
    bound = x + abs(x-y)
    queue = deque([(x, 0)]); seen = {x}
    while queue:
        value, distance = queue.popleft()
        if value == y:
            return distance
        for nxt in (value-1, value+1, value//5 if value % 5 == 0 else 0,
                    value//11 if value % 11 == 0 else 0):
            if 1 <= nxt <= bound and nxt not in seen:
                seen.add(nxt); queue.append((nxt, distance+1))
    raise AssertionError('direct route must exist')


def _retained_union(a, b):
    size = len(a)//2
    left = [set(a[i] for i in chosen) for chosen in combinations(range(len(a)), size)]
    right = [set(b[i] for i in chosen) for chosen in combinations(range(len(b)), size)]
    return max(len(x | y) for x in left for y in right)


def _beautiful(s, a, b, k):
    left = [i for i in range(len(s)-len(a)+1) if s[i:i+len(a)] == a]
    right = [i for i in range(len(s)-len(b)+1) if s[i:i+len(b)] == b]
    return [i for i in left if any(abs(i-j) <= k for j in right)]


@lru_cache(maxsize=100000)
def _remainders(state):
    best = len(state)
    for i, a in enumerate(state):
        if a == 0:
            continue
        for j, b in enumerate(state):
            if i != j and b:
                nxt = tuple(sorted([x for z, x in enumerate(state) if z not in (i, j)] + [a % b]))
                best = min(best, _remainders(nxt))
    return best


@lru_cache(maxsize=2048)
def _key_assignment(frequencies):
    # Alphabet order, not sorted frequencies. Each state records assigned slot
    # counts at costs 1..4; capacities encode the eight physical keys.
    states = {(0, 0, 0, 0): 0}
    for frequency in frequencies:
        if frequency == 0:
            continue
        nxt = {}
        for used, cost in states.items():
            for tier, cap in enumerate((8, 8, 8, 2)):
                if used[tier] < cap:
                    key = tuple(x + (i == tier) for i, x in enumerate(used))
                    candidate = cost + frequency*(tier+1)
                    nxt[key] = min(nxt.get(key, candidate), candidate)
        states = nxt
    return min(states.values())


def expected(pid, args):
    validate(pid, args)
    if pid == 2981:
        return _special(args[0])
    if pid == 2998:
        return _operations(*args)
    if pid == 3002 and len(args[0]) <= 8:
        return _retained_union(*args)
    if pid == 3006 and len(args[0]) <= 128:
        return _beautiful(*args)
    if pid == 3012 and len(args[0]) <= 7:
        return _remainders(tuple(sorted(args[0])))
    if pid == 3016:
        counts = Counter(args[0])
        return _key_assignment(tuple(counts[c] for c in string.ascii_lowercase))
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
        validate(pid, args)
        result = expected(pid, args) if answer is sentinel else answer
        key = q.encoded(args)
        if key in seen:
            index = seen[key]
            if not q.exact(result, cases[index]['expected']):
                raise ValueError('duplicate argument has conflicting expectation')
            if category not in categories[index].split('|'):
                categories[index] += '|'+category
            return
        seen[key] = len(cases)
        cases.append({'args': args, 'expected': result, 'compare': 'return'}); categories.append(category)
    for case in public_examples(pid, statement):
        add(case['args'], 'pinned_public_example', case['expected'])
    if pid == 2981:
        for n in range(3, 9):
            for word in product('ab', repeat=n):
                add([''.join(word)], 'exhaustive_binary_substring_enumeration')
        for _ in range(60):
            add([''.join(rng.choices(string.ascii_lowercase, k=rng.randrange(3, 51)))], 'seeded_full_alphabet')
        for word in ('a'*50, 'ab'*25, 'a'*16+'b'+'a'*16+'b'+'a'*16, (string.ascii_lowercase*2)[:50]):
            add([word], 'maximum_length_literal_reference')
    elif pid == 2998:
        for x in range(1, 36):
            for y in range(1, 36):
                add([x, y], 'exhaustive_small_directed_graph')
        for _ in range(60):
            add([rng.randrange(1, 10001), rng.randrange(1, 10001)], 'seeded_full_domain_bfs')
        for x in (1, 5, 10, 11, 12, 9999, 10000):
            for y in (1, 5, 11, 10000):
                add([x, y], 'numeric_boundary_bfs')
    elif pid == 3002:
        for n in (2, 4):
            arrays = list(product((1, 2), repeat=n))
            for a in arrays:
                for b in arrays:
                    add([list(a), list(b)], 'exhaustive_binary_half_index_subsets')
        for _ in range(60):
            n = rng.choice((2, 4, 6, 8))
            add([[rng.randrange(1, 9) for _ in range(n)] for _ in range(2)], 'seeded_half_index_subsets')
        add([[1]*20000, [10**9]*20000], 'analytic_maximum_distinct_uniform_inputs', 2)
        add([list(range(1, 20001)), list(range(20001, 40001))], 'analytic_maximum_disjoint_unique', 20000)
        add([list(range(1, 20001)), list(range(1, 20001))], 'analytic_maximum_equal_unique_disjoint_retention', 20000)
        add([[1]*20000, [1]*20000], 'analytic_maximum_common_uniform', 1)
    elif pid == 3006:
        patterns = [''.join(v) for n in (1, 2) for v in product('ab', repeat=n)]
        for n in range(1, 6):
            for chars in product('ab', repeat=n):
                s = ''.join(chars)
                for a in patterns:
                    for b in patterns:
                        for k in range(1, n+1):
                            add([s, a, b, k], 'exhaustive_binary_literal_matches')
        for _ in range(80):
            n = rng.randrange(1, 100)
            add([''.join(rng.choices('abcxyz', k=n)), ''.join(rng.choices('abcxyz', k=rng.randrange(1, 11))),
                 ''.join(rng.choices('abcxyz', k=rng.randrange(1, 11))), rng.randrange(1, n+1)], 'seeded_patterns_longer_than_string_allowed')
        add(['a'*100000, 'a', 'a', 1], 'analytic_maximum_all_starts', list(range(100000)))
        add(['a'*100000, 'a'*10, 'a'*10, 100000], 'analytic_maximum_overlapping_ten_characters', list(range(99991)))
        add(['a'*100000, 'a', 'b', 100000], 'analytic_maximum_absent_witness', [])
    elif pid == 3012:
        for n in range(1, 7):
            for values in combinations_with_replacement(range(1, 6), n):
                add([list(values)], 'exhaustive_small_multiset_reachability')
        for _ in range(50):
            add([[rng.randrange(1, 31) for _ in range(rng.randrange(1, 7))]], 'seeded_ordered_remainder_reachability')
        add([[1]*100000], 'analytic_maximum_uniform_pairing', 50000)
        add([[1]+[10]*99999], 'analytic_maximum_unique_minimum', 1)
        add([[2]*50000+[4]*50000], 'analytic_maximum_even_minimum_count_all_multiples', 25000)
        add([[2]*50001+[4]*49999], 'analytic_maximum_odd_minimum_count_all_multiples', 25001)
        add([[2]*99999+[3]], 'analytic_maximum_nonmultiple_creates_unique_smaller_remainder', 1)
        add([[10**9]*7], 'separate_maximum_numeric_value', 4)
    else:
        for n in range(1, 6):
            for chars in product('abc', repeat=n):
                add([''.join(chars)], 'exhaustive_small_alphabet_slot_assignment')
        for count in (8, 9, 16, 17, 24, 25, 26):
            for _ in range(5):
                add([''.join(c*rng.randrange(1, 20) for c in string.ascii_lowercase[:count])], 'seeded_press_tier_capacity_assignment')
        add(['a'*100000], 'analytic_maximum_single_letter', 100000)
        add([(string.ascii_lowercase*3846)+'abcd'], 'analytic_maximum_balanced_alphabet', 215380)
        add(['a'*99975+string.ascii_lowercase[1:]], 'analytic_maximum_skewed_alphabet', 100030)
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
