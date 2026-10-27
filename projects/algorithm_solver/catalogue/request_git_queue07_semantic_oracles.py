"""Source-blind 2900/2901 witness oracles and host-only optimum bindings.

This is not a runner or a comparator registry. Existing result-contract owners
retain acceptance authority. No candidate sources are imported or executed.
Cases retain one legal optimal list solely for transport type and projection;
acceptance must not require equality with that chosen witness. The separately
hashed optimum artifact must be checked before any future preparation.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random

IDS = (2900, 2901)
PARAMETERS = {pid: ('words', 'groups') for pid in IDS}
DEFINITIONS = {
    2900: ('Longest Unequal Adjacent Groups Subsequence I',
           '07a54a8f4ccd1602e3fc8437b860f7e9b54a297bdc9fd0403386cf8c83c4561d'),
    2901: ('Longest Unequal Adjacent Groups Subsequence II',
           'cca27a10f4e16f31d144fcde7fa1a658c2881718bed0e08935da281cde2932e7'),
}
OPTIMUM_SCHEMA = 'gamma.queue07.semantic-optimum-lengths.v1'


def encoded(value):
    """Existing canonical case JSON format; no alternative execution protocol."""
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require_policy(pid, policy):
    if type(pid) is not int or pid not in IDS or type(policy) is not str or policy != f'problem:{pid}':
        raise ValueError('unregistered queue07 semantic identity or policy')


def validate(pid, args):
    require_policy(pid, f'problem:{pid}')
    if type(args) is not list or len(args) != 2:
        raise ValueError('exact current positional words, groups interface required')
    words, groups = args
    limit = 100 if pid == 2900 else 1000
    if (type(words) is not list or not 1 <= len(words) <= limit
            or type(groups) is not list or len(groups) != len(words)
            or any(type(w) is not str or not 1 <= len(w) <= 10
                   or any(not 'a' <= c <= 'z' for c in w) for w in words)
            or len(set(words)) != len(words)):
        raise ValueError('outside pinned word array domain')
    low, high = (0, 1) if pid == 2900 else (1, len(words))
    if any(type(g) is not int or not low <= g <= high for g in groups):
        raise ValueError('outside pinned exact integer group domain')


def _adjacent(pid, words, groups, i, j):
    if groups[i] == groups[j]:
        return False
    return (pid == 2900 or (len(words[i]) == len(words[j])
            and sum(a != b for a, b in zip(words[i], words[j])) == 1))


def legal_witness(pid, args, answer):
    """Legality only, deliberately separate from the optimum calculation."""
    validate(pid, args)
    if type(answer) is not list or not answer or any(type(w) is not str for w in answer):
        return False
    words, groups = args
    positions = {word: i for i, word in enumerate(words)}
    previous = None
    for word in answer:
        current = positions.get(word)
        if current is None or (previous is not None and
                (current <= previous or not _adjacent(pid, words, groups, previous, current))):
            return False
        previous = current
    return True


def exhaustive_optimum(pid, args):
    """Independent bounded subset enumeration, never used beyond n=12."""
    validate(pid, args)
    words, groups = args
    if len(words) > 12:
        raise ValueError('bounded exhaustive oracle only')
    best = 0
    for mask in range(1, 1 << len(words)):
        if mask.bit_count() <= best:
            continue
        selected = [i for i in range(len(words)) if mask & (1 << i)]
        admissible = True
        for i, j in zip(selected, selected[1:]):
            if groups[i] == groups[j]:
                admissible = False
                break
            if pid == 2901:
                if len(words[i]) != len(words[j]):
                    admissible = False
                    break
                differences = [k for k in range(len(words[i])) if words[i][k] != words[j][k]]
                if len(differences) != 1:
                    admissible = False
                    break
        if admissible:
            best = len(selected)
    return best


def optimum_length(pid, args):
    """Scalar optimum: exhaustive small cases; run count or suffix DAG otherwise."""
    validate(pid, args)
    words, groups = args
    if len(words) <= 12:
        return exhaustive_optimum(pid, args)
    if pid == 2900:
        return 1 + sum(a != b for a, b in zip(groups, groups[1:]))
    suffix = [1] * len(words)
    for i in range(len(words) - 1, -1, -1):
        for j in range(i + 1, len(words)):
            if _adjacent(pid, words, groups, i, j):
                suffix[i] = max(suffix[i], 1 + suffix[j])
    return max(suffix)


def reference(pid, args):
    """Construct one witness with forward paths, independent of scalar ties."""
    validate(pid, args)
    words, groups = args
    if pid == 2900:
        return [word for i, word in enumerate(words) if i == 0 or groups[i] != groups[i - 1]]
    distance, parent = [1] * len(words), [-1] * len(words)
    for end in range(len(words)):
        for previous in range(end):
            if _adjacent(pid, words, groups, previous, end) and distance[previous] + 1 > distance[end]:
                distance[end], parent[end] = distance[previous] + 1, previous
    current = max(range(len(words)), key=distance.__getitem__)
    answer = []
    while current >= 0:
        answer.append(words[current])
        current = parent[current]
    return answer[::-1]


def gray_words(size):
    """Distinct length-ten words, adjacent entries at Hamming distance one."""
    if type(size) is not int or not 1 <= size <= 1000:
        raise ValueError('bounded Gray prefix required')
    return [''.join('b' if (i ^ (i >> 1)) & (1 << bit) else 'a'
                    for bit in range(10)) for i in range(size)]


def case_design(pid):
    require_policy(pid, f'problem:{pid}')
    cases, categories, seen = [], [], set()
    def add(args, category):
        key = encoded(args)
        if key in seen:
            return
        seen.add(key)
        cases.append({'args': args, 'expected': reference(pid, args)})
        categories.append(category)
    rng = random.Random(729000 + pid)
    if pid == 2900:
        for n in range(1, 9):
            for groups in itertools.product((0, 1), repeat=n):
                add([list('abcdefgh'[:n]), list(groups)], 'exhaustive-binary-group-patterns')
        for args in ([['e', 'a', 'b'], [0, 0, 1]], [['a', 'b', 'c', 'd'], [1, 0, 1, 1]],
                     [['z', 'abc', 'yy', 'a'], [0, 1, 0, 1]]):
            add(args, 'official-or-no-hamming-restriction')
        words = gray_words(100)
        for groups in ([0] * 100, [1] * 100, [i % 2 for i in range(100)],
                       [0] * 50 + [1] * 50, [(i // 9) % 2 for i in range(100)]):
            add([words[:], groups], 'maximum-length-runs-and-ties')
    else:
        universe = ('a', 'b', 'aa', 'ab', 'ba')
        for n in range(1, 5):
            for words in itertools.permutations(universe, n):
                for groups in itertools.product(range(1, min(2, n) + 1), repeat=n):
                    add([list(words), list(groups)], 'exhaustive-small-word-orders-and-groups')
        for n in range(2, 9):
            for groups in itertools.product((1, 2), repeat=n):
                add([gray_words(n), list(groups)], 'small-gray-path-and-group-cuts')
        for args in ([['bab', 'dab', 'cab'], [1, 2, 2]],
                     [['a', 'b', 'c', 'd'], [1, 2, 3, 4]],
                     [['aa', 'ba', 'bb', 'a', 'b'], [1, 2, 3, 4, 5]],
                     [['zz', 'aa', 'ab', 'zy', 'zb'], [5, 4, 3, 2, 1]]):
            add(args, 'official-or-disconnected-mixed-length-classes')
        words = gray_words(1000)
        for group in ([1] * 1000, [1 + i % 2 for i in range(1000)], list(range(1, 1001))):
            add([words[:], group], 'maximum-length-gray-chain-or-singleton-optimum')
        add([words[::-1], [1000 - i % 2 for i in range(1000)]], 'maximum-reversed-gray-chain')
    for _ in range(48):
        n = rng.randint(1, 12)
        words = set()
        while len(words) < n:
            words.add(''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rng.randint(1, 10))))
        ordered = sorted(words)
        rng.shuffle(ordered)
        groups = [rng.randrange(2) if pid == 2900 else rng.randint(1, n) for _ in range(n)]
        add([ordered, groups], 'seeded-full-alphabet-small-exhaustive-optimum')
    return cases, categories


def build_cases(pid, statement):
    require_policy(pid, f'problem:{pid}')
    if type(statement) is not bytes or sha(statement) != DEFINITIONS[pid][1]:
        raise ValueError('pinned official definition bytes required')
    if f'{pid}. {DEFINITIONS[pid][0]}' not in statement.decode('utf-8'):
        raise ValueError('official numeric identity and title required')
    return case_design(pid)


def build_optimum_artifact(pid, cases, policy):
    """Only admitted inputs determine optimum; expected is checked, never trusted."""
    require_policy(pid, policy)
    if type(cases) is not list or not cases:
        raise ValueError('nonempty frozen cases required')
    rows = []
    for index, case in enumerate(cases):
        if type(case) is not dict or set(case) != {'args', 'expected'}:
            raise ValueError('exact existing case schema required')
        optimum = optimum_length(pid, case['args'])
        if not legal_witness(pid, case['args'], case['expected']) or len(case['expected']) != optimum:
            raise ValueError('frozen witness is not legal and optimal')
        rows.append({'index': index, 'args_sha256': sha(encoded(case['args'])), 'optimal_length': optimum})
    return {'schema': OPTIMUM_SCHEMA, 'problem_id': pid, 'comparison_policy': policy,
            'definition_sha256': DEFINITIONS[pid][1], 'cases_sha256': sha(encoded(cases)),
            'case_count': len(cases), 'rows': rows}


def validate_optimum_artifact(pid, policy, case_bytes, optimum_bytes, *, cases_sha256, optimum_sha256):
    """Fail closed on exact trusted artifact pins and recompute every optimum.

    This host-only primitive is not currently wired into a qualification lane.
    A future assigned preparer must bind these trusted hashes in its reviewed
    manifest and call this before source access or preparation; no new lane is
    authorized by importing this module.
    """
    require_policy(pid, policy)
    for raw, digest in ((case_bytes, cases_sha256), (optimum_bytes, optimum_sha256)):
        if type(raw) is not bytes or type(digest) is not str or sha(raw) != digest:
            raise ValueError('frozen artifact hash mismatch')
    cases, optimum = json.loads(case_bytes), json.loads(optimum_bytes)
    if encoded(cases) != case_bytes or encoded(optimum) != optimum_bytes:
        raise ValueError('exact canonical artifact encoding required')
    recomputed = build_optimum_artifact(pid, cases, policy)
    # Comparing bytes rather than Python objects also rejects bool/int equality.
    if encoded(recomputed) != optimum_bytes:
        raise ValueError('optimum artifact identity, schema or recomputation mismatch')
    return cases
