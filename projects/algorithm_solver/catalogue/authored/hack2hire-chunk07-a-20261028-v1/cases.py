"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from math import isqrt
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h07a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _symbols(count, option_safe):
    letters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ' if option_safe else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    out = []
    for a in letters:
        for b in letters:
            for c in letters:
                out.append(a + b + c)
                if len(out) == count: return out
    return out


def _trades(rng, uid):
    if uid == _o.MARGIN3:
        stocks = rng.sample(['A', 'B', 'AB', 'Z', 'Q'], rng.randrange(1, 4))
        pool = stocks + [s + 'O' for s in stocks]
    else:
        pool = rng.sample(['A', 'B', 'C', 'AO', 'ZZ', 'AAPL'], rng.randrange(1, 5))
    out, ts = [], rng.randrange(0, 50)
    for _ in range(rng.randrange(1, 9)):
        ts += rng.choice([0, 0, 1, 7])
        q = rng.choice([1, 1, 2, 3, 5, 10, rng.randrange(1, 40)])
        price = rng.choice([1, 2, 3, 5, 10, 50, 100, 300, 1000, rng.randrange(1, 400)])
        out.append([str(ts), rng.choice(pool), rng.choice('BBS'), str(q), str(price)])
    return out


def _expr_grid(rng):
    m, n = rng.randrange(1, 5), rng.randrange(1, 5)
    kind = rng.random()
    g = []
    for r in range(m):
        row = []
        for c in range(n):
            if kind < 0.5:   # mostly alternating checkerboard
                row.append(rng.choice('0123456789') if (r + c) % 2 == 0 else rng.choice('+-'))
            else:
                row.append(rng.choice('0123456789+-+-'))
        g.append(row)
    if not any(ch.isdigit() for row in g for ch in row): g[0][0] = '7'
    return g


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.LCSS:
        args = [['', ''], ['a', ''], ['', 'a'], ['abc', 'abc'], ['abc', 'cba'], ['axbxc', 'zabcz'], ['ab', 'ba'], ['aaaa', 'aa']]
        for _ in range(250):
            alpha = rng.choice(['ab', 'abc', 'abcdef', 'xyz'])
            args.append([''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 14))), ''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 14)))])
    elif uid == o.HOUSES:
        args = [[[5]], [[1, 2, 3]], [[0, 2, 1]], [[1, 1, 1]], [[3, 1, 2, 5, 4]], [[-1, 0, 1]], [[10**9, -10**9]]]
        for _ in range(250):
            span = rng.choice([4, 8, 20])
            args.append([[rng.randrange(-span // 2, span // 2) for _ in range(rng.randrange(1, 20))]])
    elif uid == o.SEMI:
        args = [[''], ['a'], ['aa'], ['aaa'], ['aabba'], ['aaabb'], ['baaabaaab'], ['  !!'], ['AaA']]
        for _ in range(250):
            alpha = rng.choice(['ab', 'a', 'abc', 'aB '])
            args.append([''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 16)))])
    elif uid == o.UNDER:
        args = [[[1], 1], [[2], 1], [[1, 2, 3], 3], [[3, 1, 1, 1, 3], 3], [[5, 5, 5], 4], [[10**9], 10**15]]
        for _ in range(250):
            args.append([[rng.randrange(1, 10) for _ in range(rng.randrange(1, 15))], rng.randrange(1, 40)])
    elif uid == o.CASE:
        args = [['a'], ['A'], ['aA'], ['Aa'], ['aAa'], ['abAB'], ['aBbA'], ['ZzZ']]
        for _ in range(250):
            alpha = rng.choice(['aAbB', 'abcABC', 'xX', 'qwertyQWERTY'])
            args.append([''.join(rng.choice(alpha) for _ in range(rng.randrange(1, 20)))])
    elif uid in o.MARGINS:
        args = [[[['1', 'A', 'B', '10', '50']]], [[['1', 'A', 'B', '10', '200']]], [[['1', 'A', 'B', '5', '100'], ['2', 'A', 'S', '9', '120']]],
                [[['1', 'A', 'B', '2', '400'], ['1', 'B', 'B', '2', '400'], ['2', 'C', 'B', '1', '300']]]]
        if uid == o.MARGIN3:
            args += [[[['1', 'A', 'B', '100', '10'], ['2', 'AO', 'B', '100', '5']]], [[['1', 'A', 'B', '500', '1'], ['2', 'AO', 'B', '500', '2']]],
                     [[['1', 'A', 'B', '1', '10'], ['2', 'AO', 'B', '3', '400']]]]
        for _ in range(250): args.append([_trades(rng, uid)])
    elif uid == o.FRAME:
        args = [[[[5]], 1], [[[1, 2], [3, 4]], 2], [[[1, 1], [1, 1]], 2], [[[1, 2, 3], [4, 9, 6], [7, 8, 9]], 3], [[[-1, -2], [-3, -4]], 1]]
        for _ in range(250):
            m, n = rng.randrange(1, 7), rng.randrange(1, 7)
            vals = rng.choice([[0, 1, 2], list(range(-5, 6)), [7]])
            args.append([[[rng.choice(vals) for _ in range(n)] for _ in range(m)], rng.randrange(1, min(m, n) + 1)])
    elif uid == o.NONOVER:
        args = [[[]], [[[1, 2]]], [[[1, 2], [2, 3]]], [[[1, 3], [2, 4]]], [[[1, 10], [2, 3], [3, 4], [4, 5]]], [[[0, 10**9], [0, 1]]]]
        for _ in range(250):
            tasks = []
            for _ in range(rng.randrange(0, 11)):
                s = rng.randrange(0, 15); tasks.append([s, s + rng.randrange(1, 6)])
            args.append([tasks])
    elif uid == o.FLOOR:
        args = [[[5], [1], 0], [[5], [3], 10], [[1, 5], [2, 1], 7], [[3, 3, 3], [1, 2, 3], 5], [[10**9], [10**4], 0]]
        for _ in range(250):
            n = rng.randrange(1, 7)
            args.append([[rng.randrange(1, 20) for _ in range(n)], [rng.randrange(1, 6) for _ in range(n)], rng.randrange(0, 120)])
    elif uid == o.BXOR:
        args = [[1, 2, 3], [2, 3, 1], [1, 7, 7], [1, 7, 3], [5, 6, 3], [8, 15, 6], [10**9 - 1, 10**9, 2**31 - 1]]
        while len(args) < 250:
            lo = rng.choice([1, rng.randrange(1, 100), rng.randrange(1, 10**9 - 70)])
            hi = lo + rng.randrange(1, 70); k = rng.choice([1, 2, 3, rng.randrange(1, 128), rng.randrange(1, 2**31)])
            try: validate_domain(uid, [lo, hi, k])
            except ValueError: continue
            args.append([lo, hi, k])
    elif uid == o.HEALTH:
        args = [[[5], ['a'], 1], [[1, 2, 3], ['a', 'b', 'a'], 1], [[1, 2, 3], ['a', 'b', 'c'], 2], [[4, 4], ['x', 'y'], 5]]
        for _ in range(250):
            n = rng.randrange(1, 12); names = rng.sample(['a', 'b', 'c', 'd', 'e', 'f1', 'g9'], rng.randrange(1, 6))
            args.append([[rng.randrange(1, 20) for _ in range(n)], [rng.choice(names) for _ in range(n)], rng.randrange(1, 8)])
    elif uid == o.SPLIT:
        args = [[[1, 1]], [[1, 2]], [[1, 2, 1]], [[1, 1, 2, 2]], [[3, 3, 3, 3]], [[-10**9, 10**9, -10**9]]]
        for _ in range(250):
            args.append([[rng.randrange(-3, 4) for _ in range(rng.randrange(2, 15))]])
    elif uid == o.REWARD:
        args = [[[]], [[['a', '0', '5']]], [[['a', '1', '5']]], [[['a', '1', '5'], ['b', '1', '7']]], [[['a', '2', '5'], ['b', '1', '7'], ['c', '2', '1']]]]
        for _ in range(250):
            args.append([[['t%d' % i, str(rng.randrange(0, 6)), str(rng.choice([0, 1, 5, rng.randrange(0, 100)]))] for i in range(rng.randrange(0, 11))]])
    elif uid == o.TESTEFF:
        args = [[[0]], [[1, 1]], [[1, 2]], [[1, 3]], [[1, 1, 3, 3]], [[5, 1, 5, 2, 2, 2]], [[0, 10**9]]]
        for _ in range(250):
            args.append([[rng.randrange(0, rng.choice([4, 10, 30])) for _ in range(rng.randrange(1, 16))]])
    elif uid == o.EXPR:
        args = [[[['7']]], [[['1', '+'], ['+', '2']]], [[['9', '-'], ['-', '9']]], [[['1', '+', '9']]], [[['+', '3'], ['4', '5']]], [[['0', '-', '9']]]]
        for _ in range(250): args.append([_expr_grid(rng)])
    elif uid == o.BOARD:
        args = [[[5]], [[1, 1]], [[1, 2]], [[1, 2, 3]], [[0, 10, 11, 21]], [[11, 21, 0, 10]], [[-5, 5, 6]]]
        for _ in range(250):
            args.append([[rng.randrange(-20, 20) for _ in range(rng.randrange(1, 10))]])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.LCSS:
        out.append((['a' * 1000, 'a' * 1000], 1000))
        out.append((['ab' * 500, 'ba' * 500], 999))           # 'abab...a' (y without its first character) is a prefix of x
        out.append((['abc' * 333 + 'a', 'z' * 1000], 0))
        out.append((['a' * 1000, 'b' * 999 + 'a'], 1))
    elif uid == o.HOUSES:
        n = 100000
        out.append(([list(range(n))], list(range(1, n + 1))))
        out.append(([list(range(0, n, 2)) + list(range(1, n, 2))], [1] * (n - 1) + [2]))   # every odd point but the last has both neighbours occupied
        out.append(([list(range(-10**9, -10**9 + n))[::-1]], list(range(1, n + 1))))
        out.append(([[7] * n], [1] * n))
    elif uid == o.SEMI:
        out.append((['aab' * 66666], 199998))
        out.append((['a' * 200000], 2))
        out.append((['aabb' * 50000], 200000))
    elif uid == o.UNDER:
        n = 100000
        out.append(([[1] * n, 50000], 50000))
        out.append(([[10**9] * n, 10**15], n))
        out.append(([[10**9] * n, 10**9 - 1], 0))
    elif uid == o.CASE:
        lower = 'abcdefghijklmnopqrstuvwxyz'
        out.append(([lower * 4000 + lower.upper() * 3000], 26))
        out.append((['Aa' * 100000], 0))
    elif uid in o.MARGINS:
        syms = _symbols(1000, uid == o.MARGIN3)
        buys = [[str(i), syms[i], 'B', '1', '1'] for i in range(1000)]
        out.append(([buys], [['CASH', '0']] + [[s, '1'] for s in sorted(syms)]))
        big = [[str(i), syms[i], 'B', '1000', '10000'] for i in range(1000)]
        out.append(([big], [['CASH', str(1000 - 10**10)]] + [[s, '1000'] for s in sorted(syms)] if uid == o.MARGIN1 else [['CASH', '1000']]))
        if uid == o.MARGIN3:
            pair_block = [['1', 'A', 'B', '2', '500'], ['1', 'AO', 'B', '2', '500'], ['1', 'AO', 'S', '5', '500'], ['1', 'A', 'S', '5', '500']]
            out.append(([pair_block * 250], [['CASH', '1000']]))
            solo_block = [['1', 'A', 'B', '2', '500'], ['1', 'AO', 'B', '2', '600'], ['1', 'A', 'S', '5', '500']]
            out.append(([solo_block * 333 + [['2', 'A', 'B', '1', '1']]], [['CASH', '999'], ['A', '1']]))
    elif uid == o.FRAME:
        out.append(([[[7] * 100 for _ in range(100)], 37], 7))
        for k in (1, 2, 34, 50, 100):
            g = [[r * 100 + c for c in range(100)] for r in range(100)]
            top = 100 - k   # values strictly increase right and down, so the bottom-right frame dominates every other frame cell-wise
            cells = {(top + i, top + j) for i in range(k) for j in (0, k - 1)} | {(top + i, top + j) for i in (0, k - 1) for j in range(k)}
            out.append(([g, k], sum(r * 100 + c for r, c in cells)))
    elif uid == o.NONOVER:
        n = 100000
        out.append(([[[i, i + 1] for i in range(n)]], n))
        out.append(([[[0, 10**9]] * n], 1))
        out.append(([[[i, 200000 - i] for i in range(n)]], 1))
    elif uid == o.FLOOR:
        n = 100000
        out.append(([[1] * n, [1] * n, 10**9], 1 + 10**9 // n))
        out.append(([[10**9] * n, [10**4] * n, 0], 10**9))
        t = (1 + isqrt(1 + 8 * 10**9)) // 2          # largest T with T(T-1)/2 <= 10^9 for values 1..n, unit costs
        assert t * (t - 1) // 2 <= 10**9 < (t + 1) * t // 2 and t <= n
        out.append(([list(range(1, n + 1)), [1] * n, 10**9], t))
    elif uid == o.BXOR:
        out.append(([1, 10**9, 2**31 - 1], 2**30 - 1))
        out.append(([1, 10**9, 2**29 - 1], 2**29 - 1))
        out.append(([10**9 - 1, 10**9, 2**31 - 1], (10**9 - 1) ^ 10**9))
        out.append(([2, 10**9, 1], 1))
    elif uid == o.HEALTH:
        n = 100000
        out.append(([[1] * n, ['s%d' % (i % 1000) for i in range(n)], 10], 1000))
        out.append(([[10**6] * n, ['s%d' % (i % 1000) for i in range(n)], 100000], 10**11))
        out.append(([[i % 1000 + 1 for i in range(n)], ['s%d' % (i % 1000) for i in range(n)], 3], 100 * (1000 + 999 + 998)))
    elif uid == o.SPLIT:
        n = 100000
        out.append(([list(range(n))], n))
        out.append(([[0] * n], 2))
        out.append(([[i % 500 for i in range(n)]], 1000))
    elif uid == o.REWARD:
        n = 100000
        out.append(([[['t%d' % i, '1000000000', '1000000'] for i in range(n)]], 10**11))
        out.append(([[['t%d' % i, '1', str(i % 10**6)] for i in range(n)]], n - 1))
        out.append(([[['t%d' % i, '0', '5'] for i in range(n)]], 0))
        out.append(([[['t%d' % i, str(i % 1000), '7'] for i in range(n)]], 999 * 7))
    elif uid == o.TESTEFF:
        n = 100000
        out.append(([[5] * n], n))
        out.append(([list(range(n))], 1))
        out.append(([[i // 2 for i in range(n)]], n // 2 + 1))
        out.append(([[i * 1000 for i in range(n)][::-1]], 1))
    elif uid == o.EXPR:
        out.append(([[['9'] * 300 for _ in range(300)]], 9))
        out.append(([[['9' if (r + c) % 2 == 0 else '+' for c in range(300)] for r in range(300)]], 2700))
        out.append(([[['9' if (r + c) % 2 == 0 else '-' for c in range(300)] for r in range(300)]], 9))
    elif uid == o.BOARD:
        n = 100000
        out.append(([list(range(n))], 49999))
        out.append(([[3] * n], 1))
        out.append(([[-10**9] * (n // 2) + [10**9] * (n // 2)], 1))
        out.append(([list(range(n))[::-1]], 49999))
    return out
