"""Public-example and generated development regressions for both languages.

Expected values stay in this parent process. These tests do not read corpus
holdouts, grant catalogue admission, or claim LeetCode judge acceptance.
"""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
IDS = (3894, 3898, 3903, 3908, 3912, 3917, 3921, 3925,
       3931, 3936, 4000, 4006, 4010, 4020, 4024, 4030)


def build_cases():
    cases = {pid: [] for pid in IDS}
    def add(pid, args, expected):
        cases[pid].append((args, expected))
    rng = random.Random(20261025)

    for timer in range(1001):
        expected = {0: 'Green', 30: 'Orange'}.get(timer, 'Red' if timer in range(31, 91) else 'Invalid')
        add(3894, [timer], expected)

    # Edge enumeration supplies an oracle independent of row summation.
    for n in range(1, 6):
        edges = list(itertools.combinations(range(n), 2))
        for mask in range(1 << len(edges)):
            matrix = [[0] * n for _ in range(n)]
            degrees = [0] * n
            for bit, (left, right) in enumerate(edges):
                if mask & (1 << bit):
                    matrix[left][right] = matrix[right][left] = 1
                    degrees[left] += 1
                    degrees[right] += 1
            add(3898, [matrix], degrees)
    add(3898, [[[int(i != j) for j in range(100)] for i in range(100)]], [99] * 100)

    for n in range(1, 6):
        for values in itertools.product(range(4), repeat=n):
            nums = list(values)
            for k in range(4):
                expected = next((i for i in range(n) if max(nums[:i + 1]) - min(nums[i:]) <= k), -1)
                add(3903, [nums, k], expected)
    for _ in range(100):
        nums = [rng.randrange(10**9 + 1) for _ in range(100)]
        k = rng.randrange(10**9 + 1)
        add(3903, [nums, k], next((i for i in range(100) if max(nums[:i+1])-min(nums[i:]) <= k), -1))
    add(3903, [[5, 0, 1, 4], 3], 3)
    add(3903, [[3, 2, 1], 1], -1)

    # Arithmetic digit extraction, independent of the string-based implementation.
    for n in list(range(501)) + [9999, 10000, 99999, 100000]:
        digits = []
        value = n
        while value:
            digits.append(value % 10)
            value //= 10
        digits = digits or [0]
        for digit in range(10):
            add(3908, [n, digit], digit in digits and digit != digits[-1])

    for n in range(1, 7):
        for values in itertools.product((1, 2, 3), repeat=n):
            nums = list(values)
            expected = [v for i, v in enumerate(nums) if all(v > x for x in nums[:i]) or all(v > x for x in nums[i+1:])]
            add(3912, [nums], expected)
    add(3912, [[1, 2, 4, 2, 3, 2]], [1, 2, 4, 3, 2])
    add(3912, [[100] * 100], [100, 100])

    for n in range(1, 8):
        for values in itertools.product((1, 2), repeat=n):
            nums = list(values)
            add(3917, [nums], [sum((v - x) % 2 != 0 for x in nums[i+1:]) for i, v in enumerate(nums)])
    add(3917, [list(range(1, 101))], [sum((v-x) % 2 != 0 for x in range(v+1, 101)) for v in range(1, 101)])

    points = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '6': 6, 'W': 0, 'WD': 1, 'NB': 1}
    event_lists = [list(v) for n in range(1, 5) for v in itertools.product(('0', '6', 'W', 'WD', 'NB'), repeat=n)]
    event_lists += [[rng.choice(list(points)) for _ in range(rng.randint(1, 1000))] for _ in range(100)]
    event_lists += [['W'] * 10 + ['6'] * 990, ['6'] * 1000, ['1', '4', 'W', '6', 'WD']]
    for events in event_lists:
        wickets = [i for i, event in enumerate(events) if event == 'W']
        prefix = events[:wickets[9] + 1] if len(wickets) >= 10 else events
        add(3921, [events], [sum(points[event] for event in prefix), prefix.count('W')])

    for n in range(1, 6):
        for values in itertools.product((1, 2, 100), repeat=n):
            nums = list(values)
            add(3925, [nums], nums + nums[::-1])
    add(3925, [list(range(1, 101))], list(range(1, 101)) + list(range(100, 0, -1)))

    for n in (2, 3):
        for values in itertools.product('0123456789', repeat=n):
            s = ''.join(values)
            add(3931, [s], all(abs(int(a)-int(b)) <= 2 for a, b in zip(s, s[1:])))
    add(3931, ['0' * 100], True)
    add(3931, ['0' * 99 + '3'], False)

    # Simulate swaps; do not use the implementation's zero-prefix formula.
    arrays = [list(v) for n in range(1, 9) for v in itertools.product((0, 1), repeat=n)]
    arrays += [[0] * 50 + [100] * 50, [100] * 100, [0] * 100, [0, 1, 0, 3, 12]]
    for nums in arrays:
        work = nums.copy()
        left, right, swaps = 0, len(work) - 1, 0
        while left < right:
            if work[left] != 0:
                left += 1
            elif work[right] == 0:
                right -= 1
            else:
                work[left], work[right] = work[right], work[left]
                swaps += 1
        add(3936, [nums], swaps)

    # Exhaust the full admitted n/s domain using enumeration, not greedy placement.
    for n in range(1, 6):
        largest = {}
        for value in range(10**n):
            largest[sum(map(int, str(value)))] = value
        for digit_sum in range(101):
            add(4000, [n, digit_sum], largest.get(digit_sum, -1))

    for n in range(1, 10):
        for values in itertools.product('01', repeat=n):
            s = ''.join(values)
            expected = 0
            for length in range(1, n + 1):
                # Compare multisets to both alternating target strings.
                prefix = sorted(s[:length])
                targets = [sorted((pattern * ((length + 1) // 2))[:length])
                           for pattern in ('01', '10')]
                expected += int(prefix in targets)
            add(4006, [s], expected)
    for s in ('0' * 100, '01' * 50, '0' * 50 + '1' * 50):
        add(4006, [s], sum(abs(s[:i].count('0') - s[:i].count('1')) <= 1 for i in range(1, 101)))

    for n in range(2, 5):
        for values in itertools.product(range(1, 7), repeat=n):
            nums = list(values)
            # Trial divisors are independent of the candidate's Euclidean algorithm.
            strengths = []
            for a, b in itertools.combinations(nums, 2):
                divisor = max(d for d in range(1, min(a, b) + 1) if a % d == b % d == 0)
                strengths.append(a * b // (divisor * divisor))
            add(4010, [nums], max(strengths))
    add(4010, [[99999, 100000]], 9999900000)
    add(4010, [[100000] * 2000], 1)
    for _ in range(100):
        nums = [rng.randint(1, 100000) for _ in range(rng.randint(2, 20))]
        add(4010, [nums], max(a*b//math.gcd(a,b)**2 for a,b in itertools.combinations(nums,2)))

    for n in range(1, 6):
        for length in range(1, 5):
            for values in itertools.product(range(n), repeat=length):
                floor = seconds = 0
                for target in values:
                    while floor != target:
                        floor += 1 if target > floor else -1
                        seconds += 1
                add(4020, [n, list(values)], seconds)
    add(4020, [100, [99, 0] * 50], 9900)

    for _ in range(400):
        drones = [[rng.randint(-25,25), rng.randint(-25,25), rng.randint(1,100)] for _ in range(rng.randint(1,100))]
        target = [rng.randint(-25,25), rng.randint(-25,25)]
        eligible = sorted((abs(x-target[0])+abs(y-target[1]), i) for i,(x,y,r) in enumerate(drones)
                          if abs(x-target[0])+abs(y-target[1]) <= r)
        add(4024, [drones, target], eligible[0][1] if eligible else -1)
    add(4024, [[[2,1,5], [4,4,5], [6,6,8]], [5,5]], 1)
    add(4024, [[[4,4,5]], [8,6]], -1)
    add(4024, [[[0,0,1], [0,0,1]], [0,0]], 0)
    add(4024, [[[-25,-25,100]], [25,25]], 0)

    for n in (1, 2, 3):
        for values in itertools.product('abcdefghijklmnopqrstuvwxyz', repeat=n):
            s = ''.join(values)
            bits = ''.join(format(ord(c), '08b') for c in s)
            add(4030, [s], bits == bits[::-1])
    for s in ('f' * 100, 'leet', 'vn', 'n' * 100):
        bits = ''.join(format(ord(c), '08b') for c in s)
        add(4030, [s], bits == bits[::-1])
    return cases


def exact(value):
    if isinstance(value, list):
        return ('list', tuple(exact(item) for item in value))
    return (type(value).__name__, value)


class SolutionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = build_cases()
        cls.requests = [{'id': pid, 'args': args} for pid in IDS for args, _ in cls.cases[pid]]
        node = os.environ.get('NODE_BIN') or shutil.which('node')
        if not node:
            raise RuntimeError('Node is required; dual-language checks cannot silently skip.')
        cls.results = {}
        for language, command in (('python', [sys.executable, str(ROOT/'run_python.py')]),
                                  ('javascript', [node, str(ROOT/'run_javascript.cjs')])):
            completed = subprocess.run(command, input=json.dumps(cls.requests), text=True,
                                       capture_output=True, timeout=40, check=True)
            observations = json.loads(completed.stdout)
            if len(observations) != len(cls.requests):
                raise AssertionError('Wrong result count: ' + language)
            cls.results[language] = observations
        cls.offsets = {}
        offset = 0
        for pid in IDS:
            cls.offsets[pid] = offset
            offset += len(cls.cases[pid])
        print('Development cases per language:', offset, flush=True)

    def check_problem(self, pid):
        start = self.offsets[pid]
        for index, (args, expected) in enumerate(self.cases[pid]):
            observations = [self.results[language][start+index] for language in ('python', 'javascript')]
            for language, observed in zip(('python', 'javascript'), observations):
                with self.subTest(problem=pid, case=index, language=language):
                    self.assertEqual(exact(observed['result']), exact(expected), repr(args)[:200])
                    self.assertTrue(observed['unchanged'], 'input mutation')
                    self.assertFalse(observed['aliases_input'], 'result aliases input')
            self.assertEqual(exact(observations[0]['result']), exact(observations[1]['result']))

    def test_manifest_sources(self):
        manifest = json.loads((ROOT/'manifest.json').read_text())
        seen = set()
        for row in manifest['source_inventory']:
            self.assertNotIn((row['id'], row['language']), seen)
            seen.add((row['id'], row['language']))
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(seen, {(pid, language) for pid in IDS for language in ('python', 'javascript')})
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(hashlib.sha256((ROOT/'assignment.public-safe.json').read_bytes()).hexdigest(), manifest['assignment_sha256'])


for problem_id in IDS:
    def check(self, pid=problem_id):
        self.check_problem(pid)
    setattr(SolutionsTest, f'test_problem_{problem_id}', check)

if __name__ == '__main__':
    unittest.main(verbosity=2)
