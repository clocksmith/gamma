"""Cases builder for all 88 problems in batch 03."""
from collections import defaultdict, deque
from itertools import combinations, permutations, product
import ast
import html
import json
import math
from pathlib import Path
import random
import re
import string

import oracles as o

ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / 'projects/algorithm_solver/catalogue/authored/downloaded-general88-v1'
ASSIGNMENT = json.loads((BATCH / 'assignment.public-safe.json').read_text())
IDS = tuple(p['id'] for p in ASSIGNMENT['problems'])


def official_examples(path, pid):
    if pid == 186:
        return [
            ([['t', 'h', 'e', ' ', 's', 'k', 'y', ' ', 'i', 's', ' ', 'b', 'l', 'u', 'e']],
             ['b', 'l', 'u', 'e', ' ', 'i', 's', ' ', 's', 'k', 'y', ' ', 't', 'h', 'e']),
            ([['a']], ['a'])
        ]
    question = json.loads(path.read_text())['data']['question']
    content = question['content']
    if not content:
        return []
    body = re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>', '\n', content)
    body = html.unescape(re.sub(r'<[^>]*>', '', body))
    examples = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|Follow up:|$)', body, re.S):
        inp = match[1].strip()
        out = match[2].strip()
        try:
            node = ast.parse('f(' + inp + ')', mode='eval').body
            args = [ast.literal_eval(k.value) for k in node.keywords]
            declared, _ = json.JSONDecoder().raw_decode(out)
        except Exception:
            continue
        examples.append((args, declared))
    assert examples, f'Missing official examples for {pid}'
    return examples


def build(_statements=None):
    rng = random.Random(2026102803)
    data = {i: [] for i in IDS}
    seen = {i: set() for i in IDS}

    def add(pid, args, category='independent-seeded-small', want=None):
        key = json.dumps(args, separators=(',', ':'))
        if key in seen[pid]:
            return
        seen[pid].add(key)
        data[pid].append({
            'args': args,
            'expected': o.expected(pid, args) if want is None else want,
            'category': category
        })

    if _statements is not None:
        for pid in IDS:
            stmt_path = Path(_statements) / f'{pid}.json'
            for args, declared in official_examples(stmt_path, pid):
                want = o.expected(pid, args)
                if pid not in o.FUNCTIONAL_ADAPTER_IDS:
                    assert o.matches(pid, args, declared, want), ('official-example-oracle-disagreement', pid, args, declared, want)
                add(pid, args, 'official-example')

    # Domain-specific boundary and structured cases
    # 11: Container With Most Water
    add(11, [[1, 1]], 'minimal-boundary')
    add(11, [[1, 2, 1]], 'small-triplet')
    add(11, [[4, 3, 2, 1, 4]], 'equal-boundaries')
    for _ in range(15):
        n = rng.randint(2, 20)
        add(11, [[rng.randint(0, 100) for _ in range(n)]])

    # 15: 3Sum
    add(15, [[0, 0, 0]], 'zero-triplet')
    add(15, [[0, 1, 1]], 'no-triplet')
    add(15, [[-1, 0, 1, 2, -1, -4]], 'classic-example')
    for _ in range(15):
        n = rng.randint(3, 16)
        add(15, [[rng.randint(-15, 15) for _ in range(n)]])

    # 22: Generate Parentheses
    for n in range(1, 6):
        add(22, [n], f'n={n}')

    # 26: Remove Duplicates from Sorted Array
    add(26, [[]], 'empty-list')
    add(26, [[1]], 'single-element')
    add(26, [[1, 1, 1, 1]], 'all-identical')
    for _ in range(15):
        n = rng.randint(1, 20)
        add(26, [sorted(rng.randint(0, 10) for _ in range(n))])

    # 27: Remove Element
    add(27, [[], 1], 'empty-list')
    add(27, [[1], 1], 'single-matching')
    add(27, [[1], 2], 'single-non-matching')
    for _ in range(15):
        n = rng.randint(1, 20)
        vals = [rng.randint(0, 5) for _ in range(n)]
        add(27, [vals, rng.randint(0, 5)])

    # 31: Next Permutation
    add(31, [[1]], 'single-element')
    add(31, [[1, 2]], 'two-ascending')
    add(31, [[2, 1]], 'two-descending')
    add(31, [[3, 2, 1]], 'fully-descending')
    for _ in range(15):
        n = rng.randint(2, 8)
        add(31, [[rng.randint(1, 5) for _ in range(n)]])

    # 33: Search in Rotated Sorted Array
    add(33, [[1], 1], 'single-found')
    add(33, [[1], 0], 'single-not-found')
    add(33, [[3, 1], 1], 'two-rotated-found')
    for _ in range(15):
        n = rng.randint(1, 16)
        distinct = sorted(rng.sample(range(-20, 20), n))
        pivot = rng.randrange(n)
        rotated = distinct[pivot:] + distinct[:pivot]
        target = rng.choice(rotated) if rng.random() < 0.6 else rng.randint(-30, 30)
        add(33, [rotated, target])

    # 34: Find First and Last Position of Element in Sorted Array
    add(34, [[], 0], 'empty')
    add(34, [[1], 1], 'single-found')
    add(34, [[2, 2], 2], 'two-found')
    for _ in range(15):
        n = rng.randint(1, 20)
        nums = sorted(rng.randint(0, 8) for _ in range(n))
        add(34, [nums, rng.randint(0, 8)])

    # 36: Valid Sudoku
    board_empty = [['.' for _ in range(9)] for _ in range(9)]
    add(36, [board_empty], 'all-empty')
    for _ in range(15):
        b = [['.' for _ in range(9)] for _ in range(9)]
        for _ in range(rng.randint(10, 30)):
            r, c = rng.randint(0, 8), rng.randint(0, 8)
            b[r][c] = str(rng.randint(1, 9))
        add(36, [b])

    # 38: Count and Say
    for n in range(1, 12):
        add(38, [n])

    # 39: Combination Sum
    add(39, [[2], 1], 'impossible')
    add(39, [[2], 4], 'exact-multiple')
    for _ in range(15):
        n = rng.randint(2, 6)
        cands = sorted(rng.sample(range(2, 12), n))
        add(39, [cands, rng.randint(4, 15)])

    # 40: Combination Sum II
    add(40, [[1], 2], 'impossible')
    add(40, [[1, 1], 2], 'single-solution')
    for _ in range(15):
        n = rng.randint(2, 8)
        cands = [rng.randint(1, 8) for _ in range(n)]
        add(40, [cands, rng.randint(4, 15)])

    # 41: First Missing Positive
    add(41, [[1]], 'single-one')
    add(41, [[2]], 'single-two')
    add(41, [[0]], 'single-zero')
    add(41, [[-1, -2]], 'negatives')
    for _ in range(15):
        n = rng.randint(1, 20)
        add(41, [[rng.randint(-5, 10) for _ in range(n)]])

    # 42: Trapping Rain Water
    add(42, [[]], 'empty')
    add(42, [[1]], 'single')
    add(42, [[2, 0, 2]], 'v-trough')
    for _ in range(15):
        n = rng.randint(3, 20)
        add(42, [[rng.randint(0, 6) for _ in range(n)]])

    # 43: Multiply Strings
    add(43, ['0', '0'], 'zeros')
    add(43, ['9', '9'], 'single-digit-carry')
    add(43, ['123', '456'], 'multi-digit')
    for _ in range(15):
        add(43, [str(rng.randint(0, 100000)), str(rng.randint(0, 100000))])

    # 45: Jump Game II
    add(45, [[0]], 'single')
    add(45, [[1, 0]], 'two-step')
    for _ in range(15):
        n = rng.randint(2, 15)
        nums = [rng.randint(1, 4) for _ in range(n - 1)] + [0]
        add(45, [nums])

    # 46: Permutations
    add(46, [[1]], 'single')
    add(46, [[1, 2]], 'pair')
    add(46, [[1, 2, 3]], 'triplet')
    for _ in range(10):
        n = rng.randint(1, 5)
        add(46, [list(range(1, n + 1))])

    # 48: Rotate Image
    for n in (1, 2, 3, 4):
        mat = [[r * n + c for c in range(n)] for r in range(n)]
        add(48, [mat])
    for _ in range(10):
        n = rng.randint(2, 5)
        mat = [[rng.randint(-10, 10) for _ in range(n)] for _ in range(n)]
        add(48, [mat])

    # 49: Group Anagrams
    add(49, [['']], 'single-empty')
    add(49, [['a']], 'single-char')
    add(49, [['eat', 'tea', 'tan', 'ate', 'nat', 'bat']], 'classic')
    for _ in range(15):
        k = rng.randint(2, 10)
        words = [''.join(rng.choices('abcde', k=rng.randint(1, 4))) for _ in range(k)]
        add(49, [words])

    # 50: Pow(x, n)
    add(50, [2.0, 0], 'zero-power')
    add(50, [2.0, -2], 'negative-power')
    add(50, [1.0, 100000], 'one-power')
    for _ in range(15):
        x = round(rng.uniform(-3.0, 3.0), 2)
        if x == 0.0:
            x = 1.0
        n = rng.randint(-6, 6)
        add(50, [x, n])

    # 52: N-Queens II
    for n in range(1, 9):
        add(52, [n])

    # 53: Maximum Subarray
    add(53, [[-1]], 'single-negative')
    add(53, [[1]], 'single-positive')
    for _ in range(15):
        n = rng.randint(2, 20)
        add(53, [[rng.randint(-15, 15) for _ in range(n)]])

    # 54: Spiral Matrix
    add(54, [[[1]]], '1x1')
    add(54, [[[1, 2, 3]]], '1x3')
    add(54, [[[1], [2], [3]]], '3x1')
    for _ in range(15):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        mat = [[rng.randint(-10, 10) for _ in range(c)] for _ in range(r)]
        add(54, [mat])

    # 55: Jump Game
    add(55, [[0]], 'single-zero')
    add(55, [[2, 0, 0]], 'exact-reach')
    for _ in range(15):
        n = rng.randint(2, 15)
        add(55, [[rng.randint(0, 3) for _ in range(n)]])

    # 56: Merge Intervals
    add(56, [[]], 'empty')
    add(56, [[[1, 4]]], 'single')
    add(56, [[[1, 4], [4, 5]]], 'touching')
    for _ in range(15):
        k = rng.randint(1, 8)
        ivs = []
        for _ in range(k):
            a = rng.randint(0, 20)
            b = a + rng.randint(0, 10)
            ivs.append([a, b])
        add(56, [ivs])

    # 57: Insert Interval
    add(57, [[], [1, 2]], 'empty-base')
    add(57, [[[1, 3], [6, 9]], [2, 5]], 'overlap')
    for _ in range(15):
        k = rng.randint(1, 6)
        cur = 0
        ivs = []
        for _ in range(k):
            cur += rng.randint(1, 4)
            nxt = cur + rng.randint(1, 5)
            ivs.append([cur, nxt])
            cur = nxt
        a = rng.randint(0, 25)
        b = a + rng.randint(0, 8)
        add(57, [ivs, [a, b]])

    # 59: Spiral Matrix II
    for n in range(1, 7):
        add(59, [n])

    # 60: Permutation Sequence
    for n in range(1, 5):
        for k in range(1, math.factorial(n) + 1):
            add(60, [n, k])

    # 62: Unique Paths
    for m in range(1, 6):
        for n in range(1, 6):
            add(62, [m, n])

    # 63: Unique Paths II
    add(63, [[[0]]], 'single-open')
    add(63, [[[1]]], 'single-blocked')
    for _ in range(15):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        grid = [[1 if rng.random() < 0.25 else 0 for _ in range(c)] for _ in range(r)]
        add(63, [grid])

    # 64: Minimum Path Sum
    add(64, [[[5]]], '1x1')
    for _ in range(15):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        grid = [[rng.randint(0, 10) for _ in range(c)] for _ in range(r)]
        add(64, [grid])

    # 71: Simplify Path
    add(71, ['/home/'], 'trailing-slash')
    add(71, ['/../'], 'above-root')
    add(71, ['/home//foo/'], 'double-slash')
    add(71, ['/a/./b/../../c/'], 'relative-steps')
    for _ in range(15):
        parts = rng.choices(['', '.', '..', 'foo', 'bar', 'baz'], k=rng.randint(2, 7))
        add(71, ['/' + '/'.join(parts)])

    # 72: Edit Distance
    add(72, ['', ''], 'both-empty')
    add(72, ['a', ''], 'one-empty')
    add(72, ['horse', 'ros'], 'classic')
    for _ in range(15):
        w1 = ''.join(rng.choices('abcd', k=rng.randint(0, 6)))
        w2 = ''.join(rng.choices('abcd', k=rng.randint(0, 6)))
        add(72, [w1, w2])

    # 73: Set Matrix Zeroes
    add(73, [[[0]]], 'single-zero')
    add(73, [[[1]]], 'single-one')
    for _ in range(15):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        mat = [[0 if rng.random() < 0.2 else rng.randint(1, 9) for _ in range(c)] for _ in range(r)]
        add(73, [mat])

    # 74: Search a 2D Matrix
    add(74, [[[1]], 1], 'single-found')
    add(74, [[[1]], 2], 'single-not-found')
    for _ in range(15):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        vals = sorted(rng.sample(range(-20, 50), r * c))
        mat = [vals[i * c:(i + 1) * c] for i in range(r)]
        target = rng.choice(vals) if rng.random() < 0.6 else rng.randint(-30, 60)
        add(74, [mat, target])

    # 75: Sort Colors
    add(75, [[]], 'empty')
    add(75, [[0]], 'single')
    for _ in range(15):
        n = rng.randint(1, 20)
        add(75, [[rng.randint(0, 2) for _ in range(n)]])

    # 76: Minimum Window Substring
    add(76, ['a', 'a'], 'single-match')
    add(76, ['a', 'aa'], 'insufficient')
    for _ in range(15):
        s = ''.join(rng.choices('ABCD', k=rng.randint(1, 15)))
        t = ''.join(rng.choices('ABCD', k=rng.randint(1, 5)))
        add(76, [s, t])

    # 77: Combinations
    for n in (1, 2, 3, 4):
        for k in range(1, n + 1):
            add(77, [n, k])

    # 78: Subsets
    for n in range(0, 5):
        add(78, [list(range(1, n + 1))])

    # 79: Word Search
    board = [['A', 'B', 'C', 'E'], ['S', 'F', 'C', 'S'], ['A', 'D', 'E', 'E']]
    for w in ['ABCCED', 'SEE', 'ABCB']:
        add(79, [board, w])
    for _ in range(12):
        r, c = rng.randint(1, 4), rng.randint(1, 4)
        b = [[rng.choice('ABC') for _ in range(c)] for _ in range(r)]
        w = ''.join(rng.choices('ABC', k=rng.randint(1, 5)))
        add(79, [b, w])

    # 80: Remove Duplicates from Sorted Array II
    add(80, [[]], 'empty')
    add(80, [[1]], 'single')
    add(80, [[1, 1, 1, 1]], 'four-identical')
    for _ in range(15):
        n = rng.randint(1, 20)
        add(80, [sorted(rng.randint(0, 6) for _ in range(n))])

    # 81: Search in Rotated Sorted Array II
    add(81, [[1, 0, 1, 1, 1], 0], 'found')
    add(81, [[2, 5, 6, 0, 0, 1, 2], 3], 'not-found')
    for _ in range(15):
        n = rng.randint(1, 16)
        vals = sorted(rng.randint(-5, 5) for _ in range(n))
        p = rng.randrange(n)
        rotated = vals[p:] + vals[:p]
        target = rng.choice(rotated) if rng.random() < 0.6 else rng.randint(-10, 10)
        add(81, [rotated, target])

    # 84: Largest Rectangle in Histogram
    add(84, [[]], 'empty')
    add(84, [[2]], 'single')
    for _ in range(15):
        n = rng.randint(1, 16)
        add(84, [[rng.randint(0, 10) for _ in range(n)]])

    # 88: Merge Sorted Array
    add(88, [[0], 0, [1], 1], 'm0')
    add(88, [[1], 1, [], 0], 'n0')
    for _ in range(15):
        m, n = rng.randint(0, 8), rng.randint(0, 8)
        if m == 0 and n == 0:
            m = 1
        nums1 = sorted(rng.randint(-10, 10) for _ in range(m)) + [0] * n
        nums2 = sorted(rng.randint(-10, 10) for _ in range(n))
        add(88, [nums1, m, nums2, n])

    # 89: Gray Code
    for n in range(1, 6):
        add(89, [n])

    # 90: Subsets II
    add(90, [[]], 'empty')
    add(90, [[1]], 'single')
    add(90, [[1, 2, 2]], 'duplicates')
    for _ in range(12):
        n = rng.randint(1, 6)
        add(90, [[rng.randint(1, 4) for _ in range(n)]])

    # 91: Decode Ways
    add(91, ['0'], 'leading-zero')
    add(91, ['10'], 'ten')
    add(91, ['27'], 'twenty-seven')
    for _ in range(15):
        s = ''.join(rng.choices('01239', k=rng.randint(1, 8)))
        add(91, [s])

    # 93: Restore IP Addresses
    add(93, ['0000'], 'all-zeros')
    add(93, ['25525511135'], 'classic')
    for _ in range(15):
        s = ''.join(rng.choices('01239', k=rng.randint(4, 12)))
        add(93, [s])

    # 96: Unique Binary Search Trees
    for n in range(1, 12):
        add(96, [n])

    # 97: Interleaving String
    add(97, ['', '', ''], 'all-empty')
    add(97, ['a', '', 'a'], 'one-empty')
    for _ in range(15):
        s1 = ''.join(rng.choices('ab', k=rng.randint(0, 6)))
        s2 = ''.join(rng.choices('ab', k=rng.randint(0, 6)))
        if rng.random() < 0.5:
            i, j = 0, 0
            s3 = []
            while i < len(s1) or j < len(s2):
                if i < len(s1) and (j == len(s2) or rng.random() < 0.5):
                    s3.append(s1[i])
                    i += 1
                else:
                    s3.append(s2[j])
                    j += 1
            add(97, [s1, s2, ''.join(s3)])
        else:
            s3 = ''.join(rng.choices('ab', k=len(s1) + len(s2)))
            add(97, [s1, s2, s3])

    # 115: Distinct Subsequences
    add(115, ['', ''], 'empty')
    add(115, ['rabbbit', 'rabbit'], 'classic')
    for _ in range(15):
        s = ''.join(rng.choices('abc', k=rng.randint(1, 10)))
        t = ''.join(rng.choices('abc', k=rng.randint(1, 4)))
        add(115, [s, t])

    # 120: Triangle
    add(120, [[[2]]], 'single')
    for _ in range(15):
        n = rng.randint(1, 6)
        tri = [[rng.randint(-5, 10) for _ in range(r + 1)] for r in range(n)]
        add(120, [tri])

    # 122: Best Time to Buy and Sell Stock II
    add(122, [[1]], 'single')
    add(122, [[7, 6, 4, 3, 1]], 'descending')
    for _ in range(15):
        n = rng.randint(2, 20)
        add(122, [[rng.randint(0, 20) for _ in range(n)]])

    # 123: Best Time to Buy and Sell Stock III
    add(123, [[1]], 'single')
    add(123, [[3, 3, 5, 0, 0, 3, 1, 4]], 'classic')
    for _ in range(15):
        n = rng.randint(2, 20)
        add(123, [[rng.randint(0, 20) for _ in range(n)]])

    # 127: Word Ladder
    add(127, ['hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log', 'cog']], 'classic')
    add(127, ['hit', 'cog', ['hot', 'dot', 'dog', 'lot', 'log']], 'unreachable')
    for _ in range(10):
        words = sorted(list({''.join(rng.choices('ab', k=3)) for _ in range(6)}))
        if len(words) >= 2:
            add(127, [words[0], words[1], words])

    # 128: Longest Consecutive Sequence
    add(128, [[]], 'empty')
    add(128, [[1]], 'single')
    for _ in range(15):
        n = rng.randint(1, 20)
        add(128, [[rng.randint(-10, 10) for _ in range(n)]])

    # 130: Surrounded Regions
    add(130, [[['O']]], 'single-O')
    add(130, [[['X']]], 'single-X')
    for _ in range(15):
        r, c = rng.randint(2, 6), rng.randint(2, 6)
        b = [[rng.choice(['X', 'O']) for _ in range(c)] for _ in range(r)]
        add(130, [b])

    # 131: Palindrome Partitioning
    add(131, ['a'], 'single')
    add(131, ['aab'], 'classic')
    for _ in range(12):
        s = ''.join(rng.choices('abc', k=rng.randint(1, 6)))
        add(131, [s])

    # 134: Gas Station
    add(134, [[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], 'classic')
    add(134, [[2, 3, 4], [3, 4, 3]], 'impossible')
    for _ in range(15):
        n = rng.randint(1, 10)
        gas = [rng.randint(1, 8) for _ in range(n)]
        cost = [rng.randint(1, 8) for _ in range(n)]
        add(134, [gas, cost])

    # 135: Candy
    add(135, [[1]], 'single')
    add(135, [[1, 0, 2]], 'classic')
    for _ in range(15):
        n = rng.randint(1, 16)
        add(135, [[rng.randint(0, 10) for _ in range(n)]])

    # 136: Single Number
    add(136, [[1]], 'single')
    for _ in range(15):
        pairs = [rng.randint(-20, 20) for _ in range(rng.randint(1, 6))]
        single = rng.randint(21, 40)
        arr = pairs + pairs + [single]
        rng.shuffle(arr)
        add(136, [arr])

    # 137: Single Number II
    add(137, [[2]], 'single')
    for _ in range(15):
        triples = [rng.randint(-20, 20) for _ in range(rng.randint(1, 5))]
        single = rng.randint(21, 40)
        arr = triples * 3 + [single]
        rng.shuffle(arr)
        add(137, [arr])

    # 139: Word Break
    add(139, ['leetcode', ['leet', 'code']], 'classic')
    add(139, ['catsandog', ['cats', 'dog', 'sand', 'and', 'cat']], 'impossible')
    for _ in range(15):
        dict_words = [''.join(rng.choices('ab', k=rng.randint(1, 3))) for _ in range(rng.randint(1, 4))]
        s = ''.join(rng.choices('ab', k=rng.randint(1, 8)))
        add(139, [s, dict_words])

    # 152: Maximum Product Subarray
    add(152, [[-2]], 'single-negative')
    add(152, [[2, 3, -2, 4]], 'classic')
    for _ in range(15):
        n = rng.randint(1, 12)
        add(152, [[rng.randint(-4, 4) for _ in range(n)]])

    # 154: Find Minimum in Rotated Sorted Array II
    add(154, [[1]], 'single')
    add(154, [[2, 2, 2, 0, 1]], 'classic')
    for _ in range(15):
        n = rng.randint(1, 16)
        vals = sorted(rng.randint(-10, 10) for _ in range(n))
        p = rng.randrange(n)
        add(154, [vals[p:] + vals[:p]])

    # 164: Maximum Gap
    add(164, [[]], 'empty')
    add(164, [[10]], 'single')
    add(164, [[3, 6, 9, 1]], 'classic')
    for _ in range(15):
        n = rng.randint(2, 16)
        add(164, [[rng.randint(0, 100) for _ in range(n)]])

    # 165: Compare Version Numbers
    add(165, ['1.01', '1.001'], 'leading-zeros')
    add(165, ['1.0', '1.0.0'], 'trailing-zeros')
    add(165, ['0.1', '1.1'], 'different')
    for _ in range(15):
        v1 = '.'.join(str(rng.randint(0, 10)) for _ in range(rng.randint(1, 4)))
        v2 = '.'.join(str(rng.randint(0, 10)) for _ in range(rng.randint(1, 4)))
        add(165, [v1, v2])

    # 166: Fraction to Recurring Decimal
    add(166, [1, 2], 'terminating')
    add(166, [2, 1], 'integer')
    add(166, [4, 333], 'recurring')
    add(166, [-50, 8], 'negative')
    for _ in range(15):
        num = rng.randint(-100, 100)
        den = rng.choice([v for v in range(-50, 51) if v != 0])
        add(166, [num, den])

    # 174: Dungeon Game
    add(174, [[[-3]]], 'single-negative')
    add(174, [[[3]]], 'single-positive')
    for _ in range(15):
        r, c = rng.randint(1, 4), rng.randint(1, 4)
        mat = [[rng.randint(-8, 5) for _ in range(c)] for _ in range(r)]
        add(174, [mat])

    # 186: Reverse Words in a String II
    add(186, [['a']], 'single-char')
    add(186, [list('a b c')], 'three-single-letter-words')
    for _ in range(15):
        words = [''.join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 4))) for _ in range(rng.randint(1, 5))]
        add(186, [list(' '.join(words))])

    # 187: Repeated DNA Sequences
    add(187, ['AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT'], 'classic')
    add(187, ['AAAAAAAAAAAAA'], 'homopolymer')
    for _ in range(15):
        s = ''.join(rng.choices('ACGT', k=rng.randint(10, 30)))
        add(187, [s])

    # 200: Number of Islands
    add(200, [[['1']]], 'single-1')
    add(200, [[['0']]], 'single-0')
    for _ in range(15):
        r, c = rng.randint(1, 6), rng.randint(1, 6)
        grid = [[rng.choice(['0', '1']) for _ in range(c)] for _ in range(r)]
        add(200, [grid])

    # 201: Bitwise AND of Numbers Range
    add(201, [0, 0], 'zero')
    add(201, [1, 1], 'one')
    add(201, [5, 7], 'classic')
    for _ in range(15):
        a = rng.randint(0, 1000)
        b = a + rng.randint(0, 100)
        add(201, [a, b])

    # 207: Course Schedule
    add(207, [1, []], 'single-course')
    add(207, [2, [[1, 0]]], 'acyclic')
    add(207, [2, [[1, 0], [0, 1]]], 'cyclic')
    for _ in range(15):
        n = rng.randint(2, 6)
        edges = []
        for _ in range(rng.randint(1, 8)):
            u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
            if u != v:
                edges.append([u, v])
        add(207, [n, edges])

    # 210: Course Schedule II
    add(210, [1, []], 'single-course')
    add(210, [2, [[1, 0]]], 'acyclic')
    add(210, [2, [[1, 0], [0, 1]]], 'cyclic')
    for _ in range(15):
        n = rng.randint(2, 6)
        edges = []
        for _ in range(rng.randint(1, 8)):
            u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
            if u != v:
                edges.append([u, v])
        add(210, [n, edges])

    # 216: Combination Sum III
    for k in (1, 2, 3, 4):
        for target in (1, 5, 9, 15, 25):
            add(216, [k, target])

    # 223: Rectangle Area
    add(223, [-3, 0, 3, 4, 0, -1, 9, 2], 'classic')
    add(223, [-2, -2, 2, 2, -2, -2, 2, 2], 'identical')
    for _ in range(15):
        ax1, ay1 = rng.randint(-10, 5), rng.randint(-10, 5)
        ax2, ay2 = ax1 + rng.randint(1, 8), ay1 + rng.randint(1, 8)
        bx1, by1 = rng.randint(-10, 5), rng.randint(-10, 5)
        bx2, by2 = bx1 + rng.randint(1, 8), by1 + rng.randint(1, 8)
        add(223, [ax1, ay1, ax2, ay2, bx1, by1, bx2, by2])

    # 227: Basic Calculator II
    add(227, ['3+2*2'], 'precedence')
    add(227, [' 3/2 '], 'spaces-division')
    add(227, [' 3+5 / 2 '], 'mixed')
    for _ in range(15):
        tokens = [str(rng.randint(1, 20))]
        for _ in range(rng.randint(1, 4)):
            tokens.append(rng.choice(['+', '-', '*', '/']))
            tokens.append(str(rng.randint(1, 20)))
        add(227, [' '.join(tokens)])

    # 239: Sliding Window Maximum
    add(239, [[1], 1], 'single')
    add(239, [[1, -1], 1], 'k1')
    for _ in range(15):
        n = rng.randint(2, 20)
        nums = [rng.randint(-20, 20) for _ in range(n)]
        k = rng.randint(1, n)
        add(239, [nums, k])

    # 241: Different Ways to Add Parentheses
    add(241, ['2-1-1'], 'classic')
    add(241, ['2*3-4*5'], 'classic2')
    for _ in range(10):
        nums = [str(rng.randint(1, 8)) for _ in range(rng.randint(2, 4))]
        ops = [rng.choice(['+', '-', '*']) for _ in range(len(nums) - 1)]
        expr = ''.join(val for pair in zip(nums, ops) for val in pair) + nums[-1]
        add(241, [expr])

    # 310: Minimum Height Trees
    add(310, [1, []], 'single-node')
    add(310, [2, [[0, 1]]], 'two-nodes')
    for _ in range(12):
        n = rng.randint(3, 8)
        edges = []
        for i in range(1, n):
            edges.append([i, rng.randint(0, i - 1)])
        add(310, [n, edges])

    # 331: Verify Preorder Serialization of a Binary Tree
    add(331, ['9,3,4,#,#,1,#,#,2,#,6,#,#'], 'valid')
    add(331, ['1,#'], 'invalid-short')
    add(331, ['9,#,#,1'], 'invalid-extra')
    for _ in range(15):
        toks = rng.choices(['1', '2', '#'], k=rng.randint(1, 10))
        add(331, [','.join(toks)])

    # 332: Reconstruct Itinerary
    add(332, [[['MUC', 'LHR'], ['JFK', 'MUC'], ['SFO', 'SJC'], ['LHR', 'SFO']]], 'classic')
    add(332, [[['JFK', 'SFO'], ['JFK', 'ATL'], ['SFO', 'ATL'], ['ATL', 'JFK'], ['ATL', 'SFO']]], 'classic2')
    add(332, [[['JFK', 'KUL'], ['JFK', 'NRT'], ['NRT', 'JFK']]], 'cycle-branch')
    add(332, [[['JFK', 'AAA'], ['AAA', 'JFK'], ['JFK', 'BBB']]], 'lex-order-test')
    add(332, [[['JFK', 'A'], ['A', 'B'], ['B', 'JFK'], ['JFK', 'C']]], 'triangle-and-stem')
    add(332, [[['JFK', 'X'], ['X', 'Y'], ['Y', 'Z']]], 'simple-path')

    # 347: Top K Frequent Elements
    add(347, [[1], 1], 'single')
    for _ in range(15):
        num_distinct = rng.randint(2, 6)
        distinct_vals = rng.sample(range(1, 30), num_distinct)
        k = rng.randint(1, num_distinct)
        counts = [rng.randint(num_distinct + 5, num_distinct + 20) - i * 2 for i in range(k)]
        tail_count = max(1, counts[-1] - rng.randint(2, 4))
        tail_counts = [tail_count] * (num_distinct - k)
        all_counts = counts + tail_counts
        nums = []
        for val, cnt in zip(distinct_vals, all_counts):
            nums.extend([val] * cnt)
        rng.shuffle(nums)
        add(347, [nums, k])

    # 373: Find K Pairs with Smallest Sums
    add(373, [[1, 7, 11], [2, 4, 6], 3], 'classic')
    for _ in range(15):
        l1 = sorted(rng.randint(-10, 10) for _ in range(rng.randint(1, 6)))
        l2 = sorted(rng.randint(-10, 10) for _ in range(rng.randint(1, 6)))
        k = rng.randint(1, len(l1) * len(l2))
        add(373, [l1, l2, k])

    # 375: Guess Number Higher or Lower II
    for n in range(1, 12):
        add(375, [n])

    # 388: Longest Absolute File Path
    add(388, ['dir\n\tsubdir1\n\tsubdir2\n\t\tfile.ext'], 'classic')
    add(388, ['dir\n\tsubdir1\n\t\tfile1.ext\n\t\tsubsubdir1\n\tsubdir2\n\t\tsubsubdir2\n\t\t\tfile2.ext'], 'classic2')
    add(388, ['a'], 'no-file')
    add(388, ['file.txt'], 'single-file')
    for _ in range(12):
        lines = ['root']
        cur_depth = 0
        for _ in range(rng.randint(2, 6)):
            nxt_depth = rng.randint(1, cur_depth + 1)
            is_file = rng.random() < 0.4
            name = (f'file{rng.randint(1, 9)}.txt' if is_file else f'dir{rng.randint(1, 9)}')
            lines.append('\t' * nxt_depth + name)
            cur_depth = nxt_depth if not is_file else max(0, nxt_depth - 1)
        add(388, ['\n'.join(lines)])

    # 400: Nth Digit
    add(400, [3], 'single-digit')
    add(400, [11], 'two-digit')
    for _ in range(15):
        add(400, [rng.randint(1, 50000)])

    for pid in IDS:
        assert len(data[pid]) >= 5, f'Insufficient cases for {pid}: {len(data[pid])}'
    return data
