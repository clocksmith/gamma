"""Queue07 subset01 source-blind deterministic development oracles.

No candidate implementation is imported or executed. Exact current official
statement bytes and independent plan review precede this code. These references
and finite cases do not establish candidate qualification or full-domain timing.
"""
from __future__ import annotations

import hashlib
import itertools
import random

IDS = (2865, 2899, 2909, 2924, 2957)
PARAMETERS = {2865: ('heights',), 2899: ('nums',), 2909: ('nums',),
              2924: ('n', 'edges'), 2957: ('word',)}
DEFINITIONS = {
    2865: ('Beautiful Towers I', '99f3e6681147cf83c561dc265395f753dacd9dc37b346c68e10514d9e300f817'),
    2899: ('Last Visited Integers', '9064616e9a73399408383b3684a0c203d6be4d34bb1a2f7a8ab90d9b337ca86c'),
    2909: ('Minimum Sum of Mountain Triplets II', '9b079f70b998a2ffa34cdc749e91f6b99bb5906213a4b465cbab6e24cf94e14c'),
    2924: ('Find Champion II', '64b3bae24bb6f397f1d4fddc67288a7af9b1137886f3bcfe8320bab502cfb975'),
    2957: ('Remove Adjacent Almost-Equal Characters', '49e50b93b095f0355ee41e2ffc529cc5335c1e35ae0562eba1f10b984476cc35'),
}


def _integer(x, low, high):
    return type(x) is int and low <= x <= high


def _integer_list(xs, low_length, high_length, low, high):
    return (type(xs) is list and low_length <= len(xs) <= high_length
            and all(_integer(x, low, high) for x in xs))


def _dag(n, edges):
    adjacency = [[] for _ in range(n)]
    incoming = [0] * n
    for u, v in edges:
        adjacency[u].append(v)
        incoming[v] += 1
    ready = [v for v in range(n) if incoming[v] == 0]
    for u in ready:
        for v in adjacency[u]:
            incoming[v] -= 1
            if incoming[v] == 0:
                ready.append(v)
    return len(ready) == n


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:
        raise ValueError('outside fixed queue07 subset01 or malformed arguments')
    if len(args) != len(PARAMETERS[pid]):
        raise ValueError('exact official positional argument count required')
    if pid == 2865:
        valid = _integer_list(args[0], 1, 1000, 1, 10**9)
    elif pid == 2899:
        nums = args[0]
        valid = (type(nums) is list and 1 <= len(nums) <= 100
                 and all(type(x) is int and (x == -1 or 1 <= x <= 100) for x in nums))
    elif pid == 2909:
        valid = _integer_list(args[0], 3, 100000, 1, 10**8)
    elif pid == 2924:
        n, edges = args
        valid = (_integer(n, 1, 100) and type(edges) is list
                 and len(edges) <= n * (n - 1) // 2)
        if valid:
            valid = all(type(e) is list and len(e) == 2
                        and all(_integer(v, 0, n - 1) for v in e)
                        and e[0] != e[1] for e in edges)
        if valid:
            valid = _dag(n, edges)
    else:
        word = args[0]
        valid = (type(word) is str and 1 <= len(word) <= 100
                 and all('a' <= c <= 'z' for c in word))
    if not valid:
        raise ValueError('outside pinned current official domain')


def reference(pid, args):
    validate(pid, args)
    if pid == 2865:
        caps = args[0]
        answer = 0
        for peak in range(len(caps)):
            total = caps[peak]
            height = caps[peak]
            for j in range(peak - 1, -1, -1):
                height = min(height, caps[j])
                total += height
            height = caps[peak]
            for j in range(peak + 1, len(caps)):
                height = min(height, caps[j])
                total += height
            answer = max(answer, total)
        return answer
    if pid == 2899:
        seen, answer, consecutive = [], [], 0
        for value in args[0]:
            if value > 0:
                seen.insert(0, value)
                consecutive = 0
            else:
                consecutive += 1
                answer.append(seen[consecutive - 1] if consecutive <= len(seen) else -1)
        return answer
    if pid == 2909:
        nums = args[0]
        suffix = [0] * len(nums)
        suffix[-1] = nums[-1]
        for j in range(len(nums) - 2, -1, -1):
            suffix[j] = min(nums[j], suffix[j + 1])
        left = nums[0]
        answer = None
        for middle in range(1, len(nums) - 1):
            if left < nums[middle] and suffix[middle + 1] < nums[middle]:
                total = left + nums[middle] + suffix[middle + 1]
                answer = total if answer is None else min(answer, total)
            left = min(left, nums[middle])
        return -1 if answer is None else answer
    if pid == 2924:
        n, edges = args
        adjacency = [[] for _ in range(n)]
        for u, v in edges:
            adjacency[u].append(v)
        reaches_all = []
        for root in range(n):
            seen = {root}
            stack = [root]
            while stack:
                for v in adjacency[stack.pop()]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            if len(seen) == n:
                reaches_all.append(root)
        return reaches_all[0] if len(reaches_all) == 1 else -1
    word = args[0]
    costs = [int(letter != ord(word[0]) - 97) for letter in range(26)]
    for character in word[1:]:
        current = ord(character) - 97
        costs = [int(letter != current) + min(costs[previous] for previous in range(26)
                  if abs(letter - previous) > 1) for letter in range(26)]
    return min(costs)


def _all_small_dags():
    for n in range(1, 5):
        possible = [(u, v) for u in range(n) for v in range(n) if u != v]
        for mask in range(1 << len(possible)):
            if mask.bit_count() > n * (n - 1) // 2:
                continue
            edges = [list(edge) for bit, edge in enumerate(possible) if mask >> bit & 1]
            if _dag(n, edges):
                yield [n, edges]


def case_design(pid):
    """Generate deterministic finite cases; the gated caller binds the definition."""
    if type(pid) is not int or pid not in IDS:
        raise ValueError('outside fixed queue07 subset01')
    cases, categories = [], []
    def add(args, category):
        cases.append({'args': args, 'expected': reference(pid, args)})
        categories.append(category)
    rng = random.Random(710000 + pid)
    if pid == 2865:
        for n in range(1, 6):
            for caps in itertools.product(range(1, 4), repeat=n):
                add([list(caps)], 'exhaustive-small-caps')
        for caps in ([5, 3, 4, 1, 1], [6, 5, 3, 9, 2, 7], [3, 2, 5, 5, 2, 3]):
            add([caps], 'official-example')
        for _ in range(40):
            add([[rng.randint(1, 10**9) for _ in range(rng.randint(1, 40))]], 'seeded-full-value-range')
        large = [[10**9] * 1000, list(range(1, 1001)), list(range(1000, 0, -1)),
                 [10**9 if i % 2 == 0 else 1 for i in range(1000)],
                 [10**9] + [1] * 998 + [10**9], [1] * 500 + [10**9] * 500]
        for caps in large:
            add([caps], 'maximum-length-shape-and-large-total')
    elif pid == 2899:
        for n in range(1, 7):
            for nums in itertools.product((-1, 1, 2), repeat=n):
                add([list(nums)], 'exhaustive-short-operation-stream')
        for nums in ([1, 2, -1, -1, -1], [1, -1, 2, -1, -1]):
            add([nums], 'official-example')
        for _ in range(40):
            add([[-1 if rng.randrange(3) else rng.randint(1, 100)
                  for _ in range(rng.randint(1, 100))]], 'seeded-reset-and-exhaustion')
        for nums in ([100] * 100, [-1] * 100, [100, -1] * 50,
                     [1] * 50 + [-1] * 50, [1] + [-1] * 99,
                     [1] + [-1] * 48 + [100] + [-1] * 50):
            add([nums], 'maximum-length-operation-stream')
    elif pid == 2909:
        for n in range(3, 7):
            for nums in itertools.product(range(1, 4), repeat=n):
                add([list(nums)], 'exhaustive-small-triplets')
        for nums in ([8, 6, 1, 5, 3], [5, 4, 8, 7, 10, 2], [6, 5, 4, 3, 4, 5]):
            add([nums], 'official-example')
        for _ in range(40):
            add([[rng.randint(1, 10**8) for _ in range(rng.randint(3, 50))]], 'seeded-large-values')
        for nums in (list(range(1, 100001)), list(range(10**8, 10**8 - 100000, -1)),
                     [10**8] * 100000, [1, 10**8] * 50000,
                     [10**8 - 1] * 49999 + [10**8] + [10**8 - 1] * 50000):
            add([nums], 'maximum-length-mountain-shape')
    elif pid == 2924:
        for args in _all_small_dags():
            add(args, 'exhaustive-small-directed-acyclic-graphs')
        for args in ([3, [[0, 1], [1, 2]]], [4, [[0, 2], [1, 3], [1, 2]]]):
            add(args, 'official-example')
        for args in ([3, [[0, 1], [0, 1]]], [3, [[0, 1], [0, 1], [1, 2]]],
                     [4, [[3, 1], [3, 2], [1, 0], [2, 0]]]):
            add(args, 'duplicate-edges-or-relabeled-diamond')
        for _ in range(40):
            n = rng.randint(5, 12)
            order = rng.sample(range(n), n)
            edges = [[order[i], order[j]] for i in range(n) for j in range(i + 1, n)
                     if rng.randrange(3) == 0]
            rng.shuffle(edges)
            add([n, edges], 'seeded-relabeled-and-reordered-dag')
        for edges in ([], [[i, i + 1] for i in range(99)],
                      [[99, i] for i in range(99)],
                      [[u, v] for u in range(100) for v in range(u + 1, 100)]):
            add([100, edges], 'maximum-vertex-and-edge-shape')
    else:
        for n in range(1, 6):
            for letters in itertools.product('abcz', repeat=n):
                add([''.join(letters)], 'exhaustive-small-alphabet-words')
        for word in ('aaaaa', 'abddez', 'zyxyxyz'):
            add([word], 'official-example')
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for _ in range(40):
            add([''.join(rng.choice(alphabet) for _ in range(rng.randint(1, 100)))], 'seeded-full-alphabet')
        for word in ('a' * 100, 'z' * 100, 'az' * 50, 'ab' * 50,
                     ('zyx' * 34)[:100], (alphabet * 4)[:100]):
            add([word], 'maximum-length-letter-boundary-shape')
    return cases, categories


def build_cases(pid, statement):
    if type(pid) is not int or pid not in IDS or type(statement) is not bytes:
        raise ValueError('fixed identity and exact statement bytes required')
    title, digest = DEFINITIONS[pid]
    if hashlib.sha256(statement).hexdigest() != digest:
        raise ValueError('pinned official definition changed')
    text = statement.decode('utf-8')
    if f'{pid}. {title}' not in text:
        raise ValueError('official numeric ID/title missing')
    return case_design(pid)


def expected_observation_bytes(batch, language):
    """Existing observer projection, not a new execution/output protocol."""
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported observer language')
    from . import imported_qualification as q
    size = sum(len(q.encoded({'i': i, 'result': c['expected'],
                 'result_type': q.expected_type(c['expected'], language),
                 'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
               for i, c in enumerate(batch))
    return size + len(q.encoded({'done': len(batch)})) + (language == 'python')
