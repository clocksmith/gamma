"""Deterministic public-domain cases, independent of delivered test expectations."""
import ast
import html
from itertools import permutations, product
import json
from pathlib import Path
import random
import re
import string

import oracles as o


class JSONNames(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in ('true', 'false', 'null'):
            raise ValueError('unexpected public-example token')
        return ast.copy_location(ast.Constant({'true': True, 'false': False, 'null': None}[node.id]), node)


def public_examples(path, pid):
    question = json.loads(Path(path).read_text())['data']['question']
    if question['questionFrontendId'] != str(pid):
        raise ValueError('official statement identity differs')
    body = re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>', '\n', question['content'])
    body = html.unescape(re.sub(r'<[^>]*>', '', body))
    result = []
    pattern = r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|$)'
    for match in re.finditer(pattern, body, re.S):
        node = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(node, ast.Call) or node.args or not node.keywords:
            raise ValueError('public example requires named ordered arguments')
        args = [ast.literal_eval(JSONNames().visit(k.value)) for k in node.keywords]
        declared = ast.literal_eval(JSONNames().visit(ast.parse(match[2].strip(), mode='eval').body))
        want = o.expected(pid, args)
        if not o.matches(pid, args, declared, want):
            raise ValueError(f'independent oracle disagrees with official example: {pid}')
        result.append(args)
    if not result:
        raise ValueError(f'no checked official examples: {pid}')
    return result


def build(statement_root):
    rng = random.Random(2026102701)
    cases = {pid: [] for pid in o.IDS}
    seen = {pid: set() for pid in o.IDS}

    def add(pid, args, category):
        o.validate(pid, args)
        key = json.dumps(args, separators=(',', ':'), sort_keys=True)
        if key not in seen[pid]:
            seen[pid].add(key)
            cases[pid].append({'args': args, 'expected': o.expected(pid, args), 'category': category})

    for pid in o.IDS:
        for args in public_examples(Path(statement_root) / f'{pid}.json', pid):
            add(pid, args, 'official-example')

    # Exhaustive tiny cases and near-boundary arithmetic are different strata.
    for n in range(2, 5):
        selected = []
        for xs in product(range(-2, 3), repeat=n):
            for target in range(-4, 5):
                try:
                    o.sum_pairs(xs, target)
                except ValueError:
                    continue
                selected.append([list(xs), target])
        rng.shuffle(selected)
        for args in selected[:128]:
            add(1, args, 'exhaustive-small-stratified')
    add(1, [[-1, 3] + [10**9] * 9998, 2], 'maximum-length-duplicates')
    add(1, [[-10**9, 0, 10**9], 10**9], 'signed-value-boundary')

    for n in range(1, 8):
        for letters in product('aB', repeat=n):
            add(5, [''.join(letters)], 'exhaustive-binary-alphabet')
    for s in ['a' * 1000, 'ab' * 500, 'a' * 499 + 'b' + 'a' * 500,
              string.ascii_letters + string.digits]:
        add(5, [s], 'length-ties-and-character-boundaries')

    printable = ''.join(map(chr, range(32, 127)))
    for char in printable:
        add(125, [char], 'every-printable-ascii-character')
        add(709, [char], 'every-printable-ascii-character')
    for s in [' ' * 200000, 'A' * 200000, 'A' * 199999 + 'b',
              'A' * 99999 + '!!' + 'a' * 99999]:
        add(125, [s], 'maximum-length-filter-and-endpoints')
    for n in range(-128, 257):
        add(326, [n], 'contiguous-small-domain')
    for k in range(20):
        for delta in (-1, 0, 1):
            n = 3**k + delta
            if -2**31 <= n <= 2**31 - 1:
                add(326, [n], 'power-and-neighbor')
    for n in (-2**31, 2**31 - 1):
        add(326, [n], 'int32-extremes')
    for n in range(129):
        add(338, [n], 'contiguous-small-domain')
    for n in [100000, 99999, *[2**k + d for k in range(7, 17) for d in (-1, 0, 1)]]:
        add(338, [n], 'bit-width-and-maximum-length')
    for n in range(1, 5):
        for xs in product((-2, 0, 2), repeat=n):
            add(414, [list(xs)], 'exhaustive-distinctness-and-duplicates')
            add(724, [list(xs)], 'exhaustive-signed-pivots')
    for xs in [[-2**31, 0, 2**31 - 1], [-2**31] * 10000,
               [2**31 - 1] * 9998 + [0, -2**31]]:
        add(414, [xs], 'int32-and-length-boundaries')
    for y in permutations(range(4)):
        for x in ([y[0]], list(reversed(y)), [y[1], y[3]]):
            add(496, [list(x), list(y)], 'exhaustive-small-orderings')
    add(496, [list(range(1000)), list(range(1000))], 'maximum-length-increasing')
    add(496, [list(range(999, -1, -1)), list(range(999, -1, -1))], 'maximum-length-decreasing')
    add(496, [[10000, 0], [10000, 0]], 'value-extremes')
    for row in ('qwertyuiop', 'asdfghjkl', 'zxcvbnm'):
        for word in (row, row.upper(), row.title(), row[0] * 100):
            add(500, [[word, word]], 'keyboard-case-and-duplicate-multiplicity')
    add(500, [['Q' * 100, 'a' * 100, 'Z' * 100, 'qAz'] * 5], 'maximum-word-count-and-length')
    for n in range(31):
        add(509, [n], 'complete-official-integer-domain')
    for s in ['A' * 50000, 'a ' * 24999 + 'b!', printable.replace(' ', '')]:
        add(557, [s], 'maximum-length-and-printable-punctuation')
    for n in (2, 4, 6):
        for xs in product((-1, 0, 1), repeat=n):
            add(561, [list(xs)], 'exhaustive-small-pairing-values')
    add(561, [[-10000, 10000] * 10000], 'maximum-length-and-value-extremes')
    for n in (3, 4):
        for xs in product((-2, -1, 0, 1, 2), repeat=n):
            add(628, [list(xs)], 'exhaustive-sign-and-zero-products')
    for xs in [[-1000, -1000] + [1000] * 9998, [-1000] * 10000, [0] * 10000]:
        add(628, [xs], 'maximum-length-and-product-magnitude')
    for n in range(1, 257):
        add(693, [n], 'complete-small-bit-patterns')
    for width in range(1, 32):
        value = int(('10' * 16)[:width], 2)
        for n in (value, max(1, value - 1), min(2**31 - 1, value + 1)):
            add(693, [n], 'alternating-width-and-neighbors')
    add(693, [2**31 - 1], 'int32-maximum')
    for n in range(1, 6):
        for xs in product(range(3), repeat=n):
            add(697, [list(xs)], 'exhaustive-small-subarrays')
    for xs in [[49999] * 50000, list(range(50000)), [0] + [49999] * 49998 + [0]]:
        add(697, [xs], 'maximum-length-and-value-boundaries')
    for xs in [[0] * 10000, [1000, -1000] * 5000, [1000] * 10000]:
        add(724, [xs], 'maximum-length-and-sum-extremes')
    for n in range(1, 6):
        for xs in product((30, 31, 100), repeat=n):
            add(739, [list(xs)], 'exhaustive-equal-and-warmer-temperatures')
    for xs in [[100] * 100000, [30] * 99999 + [100],
               [30 + i % 71 for i in range(100000)]]:
        add(739, [xs], 'maximum-length-temperature-patterns')
    for n in range(3, 20):
        for peak in range(1, n - 1):
            xs = list(range(peak)) + [n] + list(range(n - peak - 2, -1, -1))
            add(852, [xs], 'small-mountain-all-peak-positions')
    for xs in [[0] + list(range(99999, 0, -1)), list(range(99999)) + [0],
               list(range(50000)) + list(range(50000, 0, -1))]:
        add(852, [xs], 'maximum-length-peak-positions')
    for n in range(1, 7):
        for xs in permutations(range(n)):
            add(946, [list(range(n)), list(xs)], 'exhaustive-small-stack-permutations')
    for popped in [list(range(1000)), list(range(999, -1, -1)),
                   [999, 0] + list(range(1, 999))]:
        add(946, [list(range(1000)), popped], 'maximum-length-valid-and-invalid-permutations')

    for pid in o.IDS:
        if pid in (326, 338, 509, 693):
            continue
        for _ in range(96):
            if pid == 1:
                values = rng.sample(range(-1000, 1001), rng.randint(2, 30))
                i, j = rng.sample(range(len(values)), 2)
                args = [values, values[i] + values[j]]
                try:
                    o.validate(pid, args)
                except ValueError:
                    continue
            elif pid in (5, 125, 557, 709):
                alphabet = 'abAB09' if pid == 5 else printable.replace(' ', '') if pid == 557 else printable
                args = [''.join(rng.choices(alphabet, k=rng.randint(1, 100)))]
                if pid == 557 and rng.randrange(2):
                    args = [' '.join(args[0][i:i + 7] for i in range(0, len(args[0]), 7))]
            elif pid in (414, 561, 628, 697, 724, 739):
                bounds = {414: (-2**31, 2**31 - 1), 561: (-10000, 10000),
                          628: (-1000, 1000), 697: (0, 49999), 724: (-1000, 1000), 739: (30, 100)}
                n = 2 * rng.randint(1, 32) if pid == 561 else rng.randint(3 if pid == 628 else 1, 64)
                args = [[rng.randint(*bounds[pid]) for _ in range(n)]]
            elif pid == 496:
                values = rng.sample(range(10001), rng.randint(1, 40))
                args = [rng.sample(values, rng.randint(1, len(values))), values]
            elif pid == 500:
                args = [[''.join(rng.choices(string.ascii_letters, k=rng.randint(1, 30)))
                         for _ in range(rng.randint(1, 20))]]
            elif pid == 852:
                n = rng.randint(3, 100)
                peak = rng.randint(1, n - 2)
                args = [sorted(rng.sample(range(10000), peak)) + [1000000]
                        + sorted(rng.sample(range(10000), n - peak - 1), reverse=True)]
            elif pid == 946:
                values = rng.sample(range(1001), rng.randint(1, 40))
                args = [values, rng.sample(values, len(values))]
            else:
                order = ''.join(rng.sample(string.ascii_lowercase, 26))
                words = [''.join(rng.choices('abcxyz', k=rng.randint(1, 20)))
                         for _ in range(rng.randint(1, 100))]
                if rng.randrange(2):
                    rank = {v: i for i, v in enumerate(order)}
                    words.sort(key=lambda w: tuple(rank[c] for c in w))
                args = [words, order]
            add(pid, args, 'deterministic-random')
    for pid in o.IDS:
        # The runner also repeats the first call within each interpreter batch.
        cases[pid].append({**cases[pid][0], 'category': 'repeated-call-state-control'})
    return cases
