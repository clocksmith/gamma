"""Bounded host-only independent cases; full snapshots and generated archives stay private."""
from copy import deepcopy
import importlib.util
from itertools import product
import json
from pathlib import Path
import random

ROOT = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load('continuation_d_oracles', ROOT / 'oracles.py')
EXAMPLES = load('continuation_d_examples', ROOT / 'examples.py').EXAMPLES


def maximum_cases(pid):
    """Analytic witnesses; transport/runtime admission remains a separate gate."""
    if pid == 3702:
        rows = [([[0]*100000], 0), ([[0]*99999+[10**9]], 100000), ([[10**9]*100000], 99999)]
    elif pid == 3703:
        rows = [(['('*50000+')'*50000, 50000], ''), (['()'*50000, 1], ''),
                ([')'*50000+'('*50000, 50000], ')'*50000+'('*50000)]
    elif pid == 3704:
        rows = [([10**digits], oracle.power_ten_no_zero_pairs(digits)) for digits in range(5, 16)]
    elif pid == 3708:
        sequence = [1, 1]
        while sequence[-1]+sequence[-2] <= 10**9: sequence.append(sequence[-1]+sequence[-2])
        rows = [([[1]*100000], 2), ([sequence+[10**9]*(100000-len(sequence))], len(sequence))]
    elif pid == 3713:
        rows = [(['a'*1000], 1000), ([('abcdefghijklmnopqrstuvwxyz'*39)[:1000]], 988)]
    elif pid == 3714:
        rows = [(['a'*100000], 100000), (['ab'*50000], 100000), ([('abc'*33334)[:100000]], 99999)]
    elif pid in (3719, 3721):
        n = 1500 if pid == 3719 else 100000
        rows = [([[2]*n], 0), ([[1, 2]*(n//2)], n), ([list(range(1, n+1))], n)]
    elif pid == 3720:
        rows = [(['a'*300, 'a'*300], ''), (['b'*300, 'a'*300], 'b'*300),
                (['a'*299+'b', 'a'*299+'b'], 'a'*298+'ba'), (['abc'*100, 'z'*300], '')]
    elif pid == 3722:
        rows = [(['a'*1000], 'a'*1000), (['z'+'a'*999], 'a'*999+'z')]
    else:
        raise ValueError('exact assigned identity required')
    out = []
    for args, expected in rows:
        oracle.validate(pid, args)
        out.append({'args': args, 'expected': expected, 'compare': 'return', 'category': 'analytic-domain-maximum', 'isolate': True})
    return out


def build_cases(pid, *, include_maximum=False):
    if type(pid) is not int or pid not in oracle.IDS: raise ValueError('exact assigned identity required')
    rows, seen = [], set()
    rng = random.Random(2026102800+pid)
    def add(args, category, supplied=None, has_supplied=False):
        oracle.validate(pid, args)
        key = json.dumps(args, sort_keys=True, separators=(',', ':'))
        if key in seen: return
        expected = oracle.reference(pid, args)
        if has_supplied and not oracle.exact(expected, supplied): raise ValueError('independent reference disagrees with official example')
        rows.append({'args': deepcopy(args), 'expected': expected, 'compare': 'return', 'category': category})
        seen.add(key)
    for args, answer in EXAMPLES[pid]: add(args, 'official-public-example', answer, True)
    if pid == 3702:
        for n in range(1, 6):
            for values in product(range(4), repeat=n): add([list(values)], 'exhaustive-small-subsets')
        add([[10**9]*16], 'maximum-reference-width')
        for _ in range(48): add([[rng.randrange(10**9+1) for _ in range(rng.randrange(1, 13))]], 'seeded-full-numeric-small-subsets')
    elif pid == 3703:
        for n in range(2, 9):
            for text in product('()', repeat=n):
                for k in range(1, n//2+1): add([''.join(text), k], 'exhaustive-literal-simultaneous-rewrites')
        for _ in range(48):
            n = rng.randrange(2, 80)
            add([''.join(rng.choices('()', k=n)), rng.randrange(1, n//2+1)], 'seeded-cascade-and-no-removal')
    elif pid == 3704:
        for n in range(2, 601): add([n], 'exhaustive-ordered-positive-complements')
        for n in (999, 1000, 1001, 9999, 10000, 10001, 11111, 19999, 20000): add([n], 'decimal-boundary-no-zero-pairs')
        for _ in range(48): add([rng.randrange(2, 20001)], 'seeded-bounded-positive-complements')
    elif pid == 3708:
        for n in range(3, 6):
            for values in product((1, 2, 3), repeat=n): add([list(values)], 'exhaustive-small-positive-intervals')
        for _ in range(48): add([[rng.randrange(1, 10**9+1) for _ in range(rng.randrange(3, 25))]], 'seeded-full-numeric-intervals')
        for values in ([1, 1, 2, 3, 5, 8, 13], [1, 2, 3, 6, 9, 15], [10**9]*3): add([values], 'fib-boundary-and-reset')
    elif pid in (3713, 3714):
        for n in range(1, 6):
            for values in product('abc', repeat=n): add([''.join(values)], 'exhaustive-small-frequency-substrings')
        alphabet = 'abcdefghijklmnopqrstuvwxyz' if pid == 3713 else 'abc'
        for _ in range(48): add([''.join(rng.choices(alphabet, k=rng.randrange(1, 25)))], 'seeded-full-alphabet-intervals')
        for text in ('aaabbbcccc', 'abababcc', 'abccba', 'aabbaaacc', 'cccccc'): add([text], 'single-pair-triple-frequency-boundaries')
    elif pid in (3719, 3721):
        for n in range(1, 5):
            for values in product((1, 2, 3, 4), repeat=n): add([list(values)], 'exhaustive-distinct-parity-intervals')
        for _ in range(64): add([[rng.choice((1, 2, 3, 4, 99999, 100000)) for _ in range(rng.randrange(1, 25))]], 'seeded-repeated-identity-intervals')
        for values in ([1, 2, 1], [2, 1, 4, 1, 2], [1, 2, 3, 4, 3, 2, 1], [2, 2, 2], [1, 3, 5]): add([values], 'distinct-not-occurrence-parity')
    elif pid == 3720:
        for n in range(1, 4):
            for first in product('abc', repeat=n):
                for second in product('abc', repeat=n): add([''.join(first), ''.join(second)], 'exhaustive-small-permutation-order')
        for _ in range(48):
            n = rng.randrange(1, 9)
            add([''.join(rng.choices('abcxyz', k=n)), ''.join(rng.choices('abcxyz', k=n))], 'seeded-duplicates-and-backtracking')
        for first, second in [('abbc', 'abcb'), ('abc', 'cba'), ('aaaa', 'aaab'), ('zzza', 'zzaz')]: add([first, second], 'strict-successor-and-impossible-boundaries')
    else:
        for n in range(1, 7):
            for values in product('abc', repeat=n): add([''.join(values)], 'exhaustive-prefix-suffix-index-maps')
        for _ in range(48): add([''.join(rng.choices('abcdefghijklmnopqrstuvwxyz', k=rng.randrange(1, 41)))], 'seeded-full-alphabet-reversals')
    if include_maximum:
        for case in maximum_cases(pid):
            key = json.dumps(case['args'], sort_keys=True, separators=(',', ':'))
            if key not in seen: rows.append(case); seen.add(key)
    return rows
