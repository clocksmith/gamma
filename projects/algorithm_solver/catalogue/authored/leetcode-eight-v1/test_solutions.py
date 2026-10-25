"""Focused developer tests, not Gamma judge qualification or LeetCode submissions.

The two candidate processes receive arguments only. Expected outputs are produced
here by independent small-input oracles; these are not protected corpus cases.
"""
from bisect import bisect_left
from collections import deque
from itertools import combinations, combinations_with_replacement, permutations, product
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
METHODS = {802: 'eventualSafeNodes', 871: 'minRefuelStops', 875: 'minEatingSpeed',
           1438: 'longestSubarray', 1547: 'minCost', 2246: 'longestPath',
           2406: 'minGroups', 2416: 'sumPrefixScores'}
COUNTS = {'python': 0, 'javascript': 0}


def safe_oracle(graph):
    size = len(graph)
    reach = [[False] * size for _ in graph]
    for node, neighbors in enumerate(graph):
        for neighbor in neighbors:
            reach[node][neighbor] = True
    for middle in range(size):
        for left in range(size):
            for right in range(size):
                reach[left][right] |= reach[left][middle] and reach[middle][right]
    return [node for node in range(size)
            if not any(reach[node][other] and reach[other][other] for other in range(size))]


def speed_oracle(piles, hours):
    return next(speed for speed in range(1, max(piles) + 1)
                if sum((pile + speed - 1) // speed for pile in piles) <= hours)


def window_oracle(nums, limit):
    best = 0
    for left in range(len(nums)):
        low = high = nums[left]
        for right in range(left, len(nums)):
            low, high = min(low, nums[right]), max(high, nums[right])
            if high - low <= limit:
                best = max(best, right - left + 1)
    return best


def refuel_oracle(target, start_fuel, stations):
    best = len(stations) + 1
    for mask in range(1 << len(stations)):
        reach = start_fuel
        for index, (position, fuel) in enumerate(stations):
            if mask & (1 << index):
                if position > reach:
                    break
                reach += fuel
        else:
            if reach >= target:
                best = min(best, mask.bit_count())
    return best if best <= len(stations) else -1


def cuts_oracle(length, cuts):
    best = float('inf')
    for order in permutations(cuts):
        boundaries = [0, length]
        total = 0
        for cut in order:
            index = bisect_left(boundaries, cut)
            total += boundaries[index] - boundaries[index - 1]
            boundaries.insert(index, cut)
        best = min(best, total)
    return best


def tree_oracle(parent, labels):
    graph = [[] for _ in parent]
    for node in range(1, len(parent)):
        ancestor = parent[node]
        if labels[node] != labels[ancestor]:
            graph[node].append(ancestor)
            graph[ancestor].append(node)
    best = 1
    for start in range(len(parent)):
        queue = deque([(start, -1, 1)])
        while queue:
            node, previous, distance = queue.popleft()
            best = max(best, distance)
            queue.extend((child, node, distance + 1) for child in graph[node] if child != previous)
    return best


def groups_oracle(intervals):
    # Every maximum overlap is attained at a left endpoint; no sorting/sweep.
    return max(sum(left <= point <= right for left, right in intervals)
               for point, _ in intervals)


def prefix_oracle(words):
    # Sum pairwise longest-common-prefix lengths, not trie visits.
    result = []
    for word in words:
        total = 0
        for other in words:
            for left, right in zip(word, other):
                if left != right:
                    break
                total += 1
        result.append(total)
    return result


class PairedSolutions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('node') is None:
            raise RuntimeError('Node is required; JavaScript checks cannot silently skip')

    def check_cases(self, pid, cases, expected):
        self.assertEqual(len(cases), len(expected))
        payload = json.dumps({'id': pid, 'method': METHODS[pid], 'cases': cases})
        commands = {'python': [sys.executable, str(ROOT / 'python_runner.py')],
                    'javascript': ['node', str(ROOT / 'javascript_runner.cjs')]}
        for language, command in commands.items():
            with self.subTest(problem=pid, language=language):
                run = subprocess.run(command, input=payload, text=True, capture_output=True,
                                     timeout=45, check=False)
                self.assertEqual(run.returncode, 0, run.stderr)
                actual = json.loads(run.stdout)
                self.assertEqual(len(actual), len(expected))
                for index, (observed, wanted) in enumerate(zip(actual, expected)):
                    self.assertEqual(observed, wanted, f'{language} problem {pid} case {index}')
                    if isinstance(wanted, int):
                        self.assertIs(type(observed), int)
                    else:
                        self.assertIsInstance(observed, list)
                        self.assertTrue(all(type(item) is int for item in observed))
                COUNTS[language] += len(cases)

    def test_802_examples_and_exhaustive_graphs(self):
        cases = [[[[1, 2], [2, 3], [5], [0], [5], [], []]],
                 [[[1, 2, 3, 4], [1, 2], [3, 4], [0, 4], []]]]
        expected = [[2, 4, 5, 6], [4]]
        for size in range(1, 4):
            for mask in range(1 << (size * size)):
                graph = [[j for j in range(size) if mask & (1 << (i * size + j))]
                         for i in range(size)]
                cases.append([graph]); expected.append(safe_oracle(graph))
        rng = random.Random(802)
        for _ in range(200):
            size = rng.randint(4, 8)
            graph = [[j for j in range(size) if rng.random() < 0.2] for _ in range(size)]
            cases.append([graph]); expected.append(safe_oracle(graph))
        self.check_cases(802, cases, expected)

    def test_802_deep_chain_and_cycle(self):
        size = 10_000
        chain = [[i + 1] for i in range(size - 1)] + [[]]
        cycle = [[i + 1] for i in range(size - 1)] + [[0]]
        self.check_cases(802, [[chain], [cycle]], [list(range(size)), []])

    def test_875_examples_and_small_speed_oracle(self):
        cases = [[[3, 6, 7, 11], 8], [[30, 11, 23, 4, 20], 5], [[30, 11, 23, 4, 20], 6]]
        expected = [4, 30, 23]
        for size in range(1, 5):
            for values in product(range(1, 6), repeat=size):
                for hours in sorted({size, size + 1, sum(values), (size + sum(values)) // 2}):
                    cases.append([list(values), hours]); expected.append(speed_oracle(values, hours))
        self.check_cases(875, cases, expected)

    def test_875_large_integer_hours(self):
        self.check_cases(875, [[[10**9] * 10_000, 10_000], [[10**9] * 10_000, 10**9],
                               [[10**9], 10**9]], [10**9, 10_000, 1])

    def test_1438_examples_and_exhaustive_windows(self):
        cases = [[[8, 2, 4, 7], 4], [[10, 1, 2, 4, 7, 2], 5], [[4, 2, 2, 2, 4, 4, 2, 2], 0]]
        expected = [2, 4, 3]
        for size in range(1, 7):
            for values in product((1, 3, 6), repeat=size):
                for limit in (0, 1, 2, 5):
                    cases.append([list(values), limit]); expected.append(window_oracle(values, limit))
        self.check_cases(1438, cases, expected)

    def test_1438_linear_size_queues(self):
        self.check_cases(1438, [[list(range(1, 100_001)), 123], [[7] * 100_000, 0],
                                [[1, 10**9] * 50_000, 0]], [124, 100_000, 1])

    def test_2406_examples_and_closed_endpoint_overlap(self):
        cases = [[[[5, 10], [6, 8], [1, 5], [2, 3], [1, 10]]],
                 [[[1, 3], [5, 6], [8, 10], [11, 13]]], [[[1, 5], [5, 8]]]]
        expected = [3, 1, 2]
        options = [(left, right) for left in range(1, 5) for right in range(left, 5)]
        for size in range(1, 5):
            for values in combinations_with_replacement(options, size):
                rows = [list(value) for value in reversed(values)]
                cases.append([rows]); expected.append(groups_oracle(rows))
        self.check_cases(2406, cases, expected)

    def test_2406_maximum_count(self):
        self.check_cases(2406, [[[[1, 10**6] for _ in range(100_000)]],
                                [[[2*i+1, 2*i+1] for i in range(100_000)]]], [100_000, 1])

    def test_871_examples_and_exhaustive_station_subsets(self):
        cases = [[1, 1, []], [100, 1, [[10, 100]]],
                 [100, 10, [[10, 60], [20, 30], [30, 30], [60, 40]]],
                 [25, 5, [[5, 5], [10, 5], [15, 10]]]]
        expected = [0, -1, 2, 3]
        rng = random.Random(871)
        for _ in range(900):
            target = rng.randint(2, 25)
            positions = sorted(rng.sample(range(1, target), rng.randint(0, min(target-1, 7))))
            stations = [[position, rng.randint(1, 12)] for position in positions]
            fuel = rng.randint(1, target)
            cases.append([target, fuel, stations]); expected.append(refuel_oracle(target, fuel, stations))
        self.check_cases(871, cases, expected)

    def test_871_all_stations_and_large_fuel(self):
        self.check_cases(871, [[501, 1, [[i, 1] for i in range(1, 501)]],
                               [10**9, 1, [[1, 10**9-1]]], [10**9, 1, []]], [500, 1, -1])

    def test_1547_examples_and_cut_permutations(self):
        cases = [[7, [1, 3, 4, 5]], [9, [5, 6, 1, 4, 2]]]
        expected = [16, 22]
        for length in range(2, 9):
            for size in range(1, min(length, 7)):
                for positions in combinations(range(1, length), size):
                    cuts = list(reversed(positions))
                    cases.append([length, cuts]); expected.append(cuts_oracle(length, cuts))
        self.check_cases(1547, cases, expected)

    def test_1547_boundaries_and_many_cuts(self):
        # Unit pieces form an optimal binary tree: L*(floor(log2 L)+2)-2^(floor(log2 L)+1).
        length = 101
        expected = length * (length.bit_length() + 1) - 2**length.bit_length()
        self.check_cases(1547, [[10**6, [1]], [length, list(range(100, 0, -1))]], [10**6, expected])

    def test_2246_examples_exhaustive_and_relabelled_trees(self):
        cases = [[[-1, 0, 0, 1, 1, 2], 'abacbe'], [[-1, 0, 0, 0], 'aabc']]
        expected = [3, 3]
        for size in range(1, 6):
            for ancestors in product(*(range(i) for i in range(1, size))):
                parent = [-1, *ancestors]
                for letters in product('ab', repeat=size):
                    labels = ''.join(letters)
                    cases.append([parent, labels]); expected.append(tree_oracle(parent, labels))
        rng = random.Random(2246)
        for _ in range(200):
            size = rng.randint(2, 14)
            parent = [-1] + [rng.randrange(i) for i in range(1, size)]
            labels = ''.join(rng.choice('abc') for _ in range(size))
            rest = list(range(1, size)); rng.shuffle(rest)
            mapping = [0, *rest]
            changed, text = [-1] * size, [''] * size
            for node in range(size):
                text[mapping[node]] = labels[node]
                if node: changed[mapping[node]] = mapping[parent[node]]
            cases.append([changed, ''.join(text)]); expected.append(tree_oracle(changed, ''.join(text)))
        self.check_cases(2246, cases, expected)

    def test_2246_deep_tree_without_recursion(self):
        parent = [-1] + list(range(99_999))
        self.check_cases(2246, [[parent, 'ab'*50_000], [parent, 'a'*100_000]], [100_000, 1])

    def test_2416_examples_duplicates_and_pairwise_prefixes(self):
        cases = [[['abc', 'ab', 'bc', 'b']], [['abcd']], [['a', 'a', 'ab']]]
        expected = [[5, 4, 3, 2], [4], [3, 3, 4]]
        for size in range(1, 5):
            for words in product(('a', 'b', 'aa', 'ab', 'ba', 'bb'), repeat=size):
                cases.append([list(words)]); expected.append(prefix_oracle(words))
        self.check_cases(2416, cases, expected)

    def test_2416_maximum_total_characters(self):
        words = ['a'*1000] * 1000
        # Distinct 3-character prefixes, followed by a shared suffix; almost 1M nodes.
        diverse = [chr(97+i//676) + chr(97+i//26%26) + chr(97+i%26) + 'z'*997 for i in range(1000)]
        first_counts = {}; second_counts = {}
        for word in diverse:
            first_counts[word[:1]] = first_counts.get(word[:1], 0) + 1
            second_counts[word[:2]] = second_counts.get(word[:2], 0) + 1
        expected = [first_counts[word[:1]] + second_counts[word[:2]] + 998 for word in diverse]
        self.check_cases(2416, [[words], [diverse]], [[10**6]*1000, expected])

    def test_manifest_hashes_and_pairing(self):
        manifest = json.loads((ROOT / 'manifest.json').read_bytes())
        self.assertEqual(manifest['assignment_sha256'], hashlib.sha256((ROOT / 'assignment.public-safe.json').read_bytes()).hexdigest())
        pairs = {(row['id'], row['language']) for row in manifest['source_inventory']}
        self.assertEqual(pairs, {(pid, language) for pid in METHODS for language in ('python', 'javascript')})
        self.assertEqual(len(manifest['source_inventory']), 16)
        for item in manifest['files']:
            self.assertEqual(hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest(), item['sha256'], item['path'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PairedSolutions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'test_methods': result.testsRun, 'case_counts_per_language': COUNTS,
                      'failures': len(result.failures), 'errors': len(result.errors),
                      'skipped': len(result.skipped), 'evidence_class': 'developer-tests-not-judge-qualification'}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
