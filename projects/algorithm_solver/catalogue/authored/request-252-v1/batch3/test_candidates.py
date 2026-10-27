#!/usr/bin/env python3
"""Bounded development checks with independent oracles, not judge qualification."""
import collections
import copy
import functools
import hashlib
import heapq
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RNG = random.Random(25203)
CASES = []


def add(pid, args, expected, kind='independent_small_oracle'):
    CASES.append({'problem_id': pid, 'arguments': args, 'expected': expected, 'kind': kind})


def examples():
    rows = {
        3223: [(['abaacbcbb'], 5), (['aa'], 2)],
        3232: [([[1, 2, 3, 4, 10]], False), ([[1, 2, 3, 4, 5, 14]], True), ([[5, 5, 5, 25]], True)],
        3241: [([[[0, 1], [0, 2]]], [2, 4, 3]), ([[[0, 1]]], [1, 2]), ([[[2, 4], [0, 1], [2, 3], [0, 2]]], [4, 6, 3, 5, 5])],
        3508: [([['Router', 'addPacket', 'addPacket', 'addPacket', 'addPacket', 'addPacket', 'forwardPacket', 'addPacket', 'getCount'], [[3], [1, 4, 90], [2, 5, 90], [1, 4, 90], [3, 5, 95], [4, 5, 105], [], [5, 2, 110], [5, 100, 110]]], [None, True, True, False, True, True, [2, 5, 90], True, 1]), ([['Router', 'addPacket', 'forwardPacket', 'forwardPacket'], [[2], [7, 4, 90], [], []]], [None, True, [7, 4, 90], []])],
        3518: [(['abba', 2], 'baab'), (['aa', 2], ''), (['bacab', 1], 'abcba')],
        3525: [([[1, 2, 3, 4, 5], 3, [[2, 2, 0, 2], [3, 3, 3, 0], [0, 1, 0, 1]]], [2, 2, 2]), ([[1, 2, 4, 8, 16, 32], 4, [[0, 2, 0, 2], [0, 2, 0, 1]]], [1, 0]), ([[1, 1, 2, 1, 1], 2, [[2, 1, 0, 1]]], [5])],
        3532: [([2, [1, 3], 1, [[0, 0], [0, 1]]], [True, False]), ([4, [2, 5, 6, 8], 2, [[0, 1], [0, 2], [1, 3], [2, 3]]], [False, False, True, True])],
        3542: [([[0, 2]], 1), ([[3, 1, 2, 1]], 3), ([[1, 2, 1, 2, 1, 2]], 4)],
        3552: [([['A..', '.A.', '...']], 2), ([['.#...', '.#.#.', '.#.#.', '...#.']], 13)],
        3561: [(['abc'], 'c'), (['adcb'], ''), (['zadb'], 'db')],
        3568: [([['S.', 'XL'], 2], 2), ([['LS', 'RL'], 4], 3), ([['L.S', 'RXL'], 3], -1)],
        3576: [([[1, -1, 1, -1, 1], 3], True), ([[-1, -1, -1, 1, 1, 1], 5], False)],
        3583: [([[6, 3, 6]], 1), ([[0, 1, 0, 0]], 1), ([[8, 4, 2, 8, 4]], 2)],
        3588: [([[[1, 1], [1, 2], [3, 2], [3, 3]]], 2), ([[[1, 1], [2, 2], [3, 3]]], -1)],
        3599: [([[1, 2, 3], 2], 1), ([[2, 3, 3, 2], 3], 2), ([[1, 1, 2, 3, 1], 2], 0)],
        3612: [(['a#b%*'], 'ba'), (['z*#'], '')],
        3619: [([[[0, 2, 1, 0, 0], [0, 5, 0, 0, 5], [0, 0, 1, 0, 0], [0, 1, 4, 7, 0], [0, 2, 0, 0, 8]], 5], 2), ([[[3, 0, 3, 0], [0, 3, 0, 3], [3, 0, 3, 0]], 3], 6)],
    }
    for pid, pairs in rows.items():
        for args, expected in pairs:
            add(pid, args, expected, 'public_example')


@functools.lru_cache(None)
def removal_oracle(s):
    answer = len(s)
    for i, char in enumerate(s):
        left = s.rfind(char, 0, i)
        right = s.find(char, i + 1)
        if left >= 0 and right >= 0:
            rest = s[:left] + s[left + 1:right] + s[right + 1:]
            answer = min(answer, removal_oracle(rest))
    return answer


@functools.lru_cache(None)
def zero_oracle(values):
    if not any(values):
        return 0
    answer = len(values)
    for left in range(len(values)):
        for right in range(left + 1, len(values) + 1):
            minimum = min(values[left:right])
            if minimum == 0:
                continue
            changed = tuple(0 if left <= i < right and v == minimum else v
                            for i, v in enumerate(values))
            answer = min(answer, 1 + zero_oracle(changed))
    return answer


def portal_oracle(grid):
    """Dijkstra over exact route-local used-letter masks, not global expansion."""
    m, n = len(grid), len(grid[0])
    heap = [(0, 0, 0, 0)]
    seen = set()
    while heap:
        moves, r, c, used = heapq.heappop(heap)
        state = (r, c, used)
        if state in seen:
            continue
        seen.add(state)
        if (r, c) == (m - 1, n - 1):
            return moves
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] != '#':
                heapq.heappush(heap, (moves + 1, nr, nc, used))
        ch = grid[r][c]
        if ch in 'AB':
            flag = 1 << (ord(ch) - ord('A'))
            if not used & flag:
                for nr in range(m):
                    for nc in range(n):
                        if grid[nr][nc] == ch:
                            heapq.heappush(heap, (moves, nr, nc, used | flag))
    return -1


def classroom_oracle(grid, energy):
    m, n = len(grid), len(grid[0])
    flags = {}
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S':
                start = (r, c)
            elif ch == 'L':
                flags[r, c] = 1 << len(flags)
    all_litter = (1 << len(flags)) - 1
    initial = (*start, energy, 0)
    queue = collections.deque([(initial, 0)])
    seen = {initial}
    while queue:
        (r, c, left, mask), moves = queue.popleft()
        if mask == all_litter:
            return moves
        if not left:
            continue
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] != 'X':
                charge = energy if grid[nr][nc] == 'R' else left - 1
                state = (nr, nc, charge, mask | flags.get((nr, nc), 0))
                if state not in seen:
                    seen.add(state)
                    queue.append((state, moves + 1))
    return -1


def flip_oracle(nums, k):
    start = tuple(nums)
    queue = collections.deque([(start, 0)])
    seen = {start}
    while queue:
        values, steps = queue.popleft()
        if len(set(values)) == 1:
            return steps <= k
        for i in range(len(values) - 1):
            changed = list(values)
            changed[i] *= -1
            changed[i + 1] *= -1
            state = tuple(changed)
            if state not in seen:
                seen.add(state)
                queue.append((state, steps + 1))
    return False


def random_cases():
    for _ in range(100):
        s = ''.join(RNG.choices('abc', k=RNG.randint(1, 8)))
        add(3223, [s], removal_oracle(s))
        nums = [RNG.randint(1, 99) for _ in range(RNG.randint(1, 15))]
        choices = [sum(v for v in nums if len(str(v)) == digits) for digits in (1, 2)]
        add(3232, [nums], any(2 * chosen > sum(nums) for chosen in choices))
        n = RNG.randint(2, 15)
        edges = [[i, RNG.randrange(i)] for i in range(1, n)]
        graph = [[] for _ in range(n)]
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)
        times = []
        for start in range(n):
            distances = {start: 0}
            queue = [start]
            for u in queue:
                for v in graph[u]:
                    if v not in distances:
                        distances[v] = distances[u] + (1 if v % 2 else 2)
                        queue.append(v)
            times.append(max(distances.values()))
        add(3241, [edges], times)
        limit = RNG.randint(2, 6)
        operations, arguments, expected = ['Router'], [[limit]], [None]
        pending = []
        timestamp = 1
        for _ in range(60):
            action = RNG.randrange(4)
            if action < 2:
                timestamp += RNG.randrange(2)
                packet = [RNG.randint(1, 5), RNG.randint(1, 4), timestamp]
                operations.append('addPacket')
                arguments.append(packet)
                valid = packet not in pending
                expected.append(valid)
                if valid:
                    if len(pending) == limit:
                        pending.pop(0)
                    pending.append(packet)
            elif action == 2:
                operations.append('forwardPacket')
                arguments.append([])
                expected.append(pending.pop(0) if pending else [])
            else:
                destination = RNG.randint(1, 4)
                low, high = sorted([RNG.randint(1, timestamp), RNG.randint(1, timestamp + 1)])
                operations.append('getCount')
                arguments.append([destination, low, high])
                expected.append(sum(d == destination and low <= t <= high for _, d, t in pending))
        add(3508, [operations, arguments], expected)
        half = ''.join(RNG.choices('abcd', k=RNG.randrange(7)))
        middle = RNG.choice(['', 'x']) if half else 'x'
        s = half + middle + half[::-1]
        permutations = sorted(set(''.join(p) for p in itertools.permutations(half)))
        rank = RNG.randint(1, len(permutations) + 2)
        value = permutations[rank - 1] if rank <= len(permutations) else None
        add(3518, [s, rank], value + middle + value[::-1] if value is not None else '')
        n = RNG.randint(1, 12)
        nums = [RNG.randint(1, 50) for _ in range(n)]
        k = RNG.randint(1, 5)
        queries = [[RNG.randrange(n), RNG.randint(1, 100), RNG.randrange(n), RNG.randrange(k)] for _ in range(20)]
        values, expected = nums.copy(), []
        for index, value, start, x in queries:
            values[index] = value
            product = 1
            total = 0
            for item in values[start:]:
                product *= item
                total += product % k == x
            expected.append(total)
        add(3525, [nums, k, queries], expected)
        n = RNG.randint(1, 12)
        nums = sorted(RNG.randint(0, 40) for _ in range(n))
        difference = RNG.randint(0, 10)
        queries = list(itertools.product(range(n), repeat=2))
        reachable = [[False] * n for _ in range(n)]
        for source in range(n):
            queue = [source]
            reachable[source][source] = True
            for u in queue:
                for v in range(n):
                    if not reachable[source][v] and abs(nums[u] - nums[v]) <= difference:
                        reachable[source][v] = True
                        queue.append(v)
        add(3532, [n, nums, difference, queries], [reachable[u][v] for u, v in queries])
        values = [RNG.randrange(4) for _ in range(RNG.randint(1, 6))]
        add(3542, [values], zero_oracle(tuple(values)))
        m, n = RNG.randint(1, 4), RNG.randint(1, 4)
        cells = RNG.choices('...#AB', k=m * n)
        cells[0] = RNG.choice('.AB')
        grid = [''.join(cells[r * n:(r + 1) * n]) for r in range(m)]
        add(3552, [grid], portal_oracle(grid))
        s = ''.join(RNG.choices('abcdxyz', k=RNG.randint(1, 30)))
        result = s
        while True:
            position = next((i for i in range(len(result) - 1)
                             if abs(ord(result[i]) - ord(result[i + 1])) in (1, 25)), None)
            if position is None:
                break
            result = result[:position] + result[position + 2:]
        add(3561, [s], result)
        m, n = RNG.randint(1, 4), RNG.randint(1, 4)
        cells = RNG.choices('...RX', k=m * n)
        locations = RNG.sample(range(m * n), RNG.randint(1, min(4, m * n)))
        cells[locations[0]] = 'S'
        for location in locations[1:]:
            cells[location] = 'L'
        grid = [''.join(cells[r * n:(r + 1) * n]) for r in range(m)]
        energy = RNG.randint(1, 6)
        add(3568, [grid, energy], classroom_oracle(grid, energy))
        nums = RNG.choices([-1, 1], k=RNG.randint(1, 8))
        k = RNG.randint(1, len(nums))
        add(3576, [nums, k], flip_oracle(nums, k))
        nums = [RNG.randrange(15) for _ in range(RNG.randint(3, 12))]
        answer = sum(nums[i] == nums[j] * 2 == nums[k] for i, j, k in itertools.combinations(range(len(nums)), 3))
        add(3583, [nums], answer)
        coords = RNG.sample(list(itertools.product(range(1, 8), repeat=2)), RNG.randint(1, 12))
        area = 0
        for a, b, c in itertools.combinations(coords, 3):
            if any(u[0] == v[0] or u[1] == v[1] for u, v in ((a, b), (a, c), (b, c))):
                area = max(area, abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])))
        add(3588, [coords], area or -1)
        nums = [RNG.randint(1, 1000000000) for _ in range(RNG.randint(1, 9))]
        k = RNG.randint(1, len(nums))
        answer = math.inf
        for cuts in itertools.combinations(range(1, len(nums)), k - 1):
            boundaries = (0, *cuts, len(nums))
            pieces = []
            for left, right in zip(boundaries, boundaries[1:]):
                value = 0
                for num in nums[left:right]:
                    value ^= num
                pieces.append(value)
            answer = min(answer, max(pieces))
        add(3599, [nums, k], answer)
        s = ''.join(RNG.choices('abc*#%', k=RNG.randint(1, 20)))
        result = ''
        for ch in s:
            result = result[:-1] if ch == '*' else result + result if ch == '#' else result[::-1] if ch == '%' else result + ch
        add(3612, [s], result)
        m, n = RNG.randint(1, 5), RNG.randint(1, 5)
        grid = [[RNG.randrange(6) for _ in range(n)] for _ in range(m)]
        k = RNG.randint(1, 8)
        parent = list(range(m * n))
        def find(i):
            while parent[i] != i:
                i = parent[i]
            return i
        for r in range(m):
            for c in range(n):
                if grid[r][c]:
                    for nr, nc in ((r - 1, c), (r, c - 1)):
                        if nr >= 0 and nc >= 0 and grid[nr][nc]:
                            parent[find(r * n + c)] = find(nr * n + nc)
        sums = collections.Counter()
        for r in range(m):
            for c in range(n):
                if grid[r][c]:
                    sums[find(r * n + c)] += grid[r][c]
        add(3619, [grid, k], sum(value % k == 0 for value in sums.values()))


def structured_cases():
    add(3223, ['a' * 200000], 2, 'structured_edge')
    n = 10000
    prefix = [0]
    for i in range(n):
        prefix.append(prefix[-1] + 2 - i % 2)
    add(3241, [[[i - 1, i] for i in range(1, n)]],
        [max(prefix[i], prefix[n] - prefix[i + 1]) for i in range(n)], 'structured_edge')
    add(3518, ['a' * 10000, 1], 'a' * 10000, 'structured_edge')
    add(3518, ['a' * 10000, 2], '', 'structured_edge')
    n = 100000
    queries = [[i, 1, i, 1] for i in range(100)]
    add(3525, [[1] * n, 5, queries], [n - i for i in range(100)], 'structured_edge')
    add(3542, [list(range(100000))], 99999, 'structured_edge')
    add(3552, [['.' * 120 for _ in range(120)]], 238, 'structured_edge')
    add(3552, [['A' * 120 for _ in range(120)]], 0, 'structured_edge')
    add(3561, ['ab' * 50000], '', 'structured_edge')
    add(3568, [['SLLLLLLLLLL'], 10], 10, 'structured_edge')
    add(3568, [['SLLLLLLLLLL'], 9], -1, 'structured_edge')
    add(3576, [[-1] * 100000, 1], True, 'structured_edge')
    add(3583, [[0] * 100000], math.comb(100000, 3) % 1000000007, 'structured_edge')
    add(3588, [[[1, 1], [1000000, 1], [1, 1000000]]], 999998000001, 'structured_edge')
    add(3599, [[1000000000] * 250, 125], 0, 'structured_edge')
    add(3612, ['a' + '#' * 19], 'a' * (2 ** 19), 'structured_edge')
    add(3619, [[[1000000] * 1000 for _ in range(100)], 1000000], 1, 'structured_edge')


def run():
    started = time.monotonic()
    examples()
    random_cases()
    structured_cases()
    ids = sorted({row['problem_id'] for row in CASES})
    modules = {}
    sources = {}
    for pid in ids:
        path = ROOT / 'python' / f'{pid}.py'
        compile(path.read_text(), str(path), 'exec')
        spec = importlib.util.spec_from_file_location(f'candidate_{pid}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[pid] = module
        js = ROOT / 'javascript' / f'{pid}.js'
        subprocess.run(['node', '--check', str(js)], check=True, timeout=10, capture_output=True)
        sources[str(pid)] = {'python': hashlib.sha256(path.read_bytes()).hexdigest(), 'javascript': hashlib.sha256(js.read_bytes()).hexdigest()}
    for index, row in enumerate(CASES):
        args = copy.deepcopy(row['arguments'])
        before = copy.deepcopy(args)
        actual = modules[row['problem_id']].solve(*args)
        if actual != row['expected']:
            raise AssertionError(('python', index, row['problem_id'], row['arguments'], row['expected'], actual))
        if args != before:
            raise AssertionError(('python mutated input', index, row['problem_id']))
    # Expected values are not sent to the Node candidate process.
    payload = [{'problem_id': row['problem_id'], 'arguments': row['arguments']} for row in CASES]
    runner = subprocess.run(['node', '--max-old-space-size=384', str(HERE / 'runner.js')],
                            input=json.dumps(payload), text=True, capture_output=True, timeout=90, check=True)
    results = json.loads(runner.stdout)
    if len(results) != len(CASES):
        raise AssertionError('Node result count mismatch')
    for index, (row, actual) in enumerate(zip(CASES, results)):
        if actual != row['expected']:
            raise AssertionError(('javascript', index, row['problem_id'], row['arguments'], row['expected'], actual))
    counts = {str(pid): dict(collections.Counter(r['kind'] for r in CASES if r['problem_id'] == pid)) for pid in ids}
    receipt = {'schema': 'gamma.local-candidate-tests.v1', 'seed': 25203, 'base_commit': 'bc252ef318b165396288cd3f3d0ecbd4b84c03da',
               'cases_per_language': len(CASES), 'language_assertions': 2 * len(CASES), 'syntax_checks': 2 * len(ids),
               'input_immutability_checks': 2 * len(CASES), 'by_problem': counts, 'source_sha256': sources,
               'duration_seconds': round(time.monotonic() - started, 3), 'test_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'runner_sha256': hashlib.sha256((HERE / 'runner.js').read_bytes()).hexdigest(), 'qualification': False,
               'limitations': 'Finite public-example and original independent bounded oracle checks; no protected/private cases, hidden judge, performance certification, admission or serving changes.'}
    (HERE / 'test-results.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['cases_per_language', 'language_assertions', 'syntax_checks', 'duration_seconds']}))


if __name__ == '__main__':
    run()
