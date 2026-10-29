"""Private case generation from file-local independent references over INFERRED domains."""
from datetime import datetime, timedelta
import importlib.util
from math import comb
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h08b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _iso(dt, seconds): return dt.strftime('%Y-%m-%dT%H:%M:%S' if seconds else '%Y-%m-%dT%H:%M')


def _snake_trace(rng):
    r, c = rng.randrange(1, 6), rng.randrange(1, 6)
    ops, rows = ['SnakeGame'], [[r, c]]
    for _ in range(rng.randrange(0, 30)):
        ops.append('move'); rows.append([rng.choice('UDLRRDDR')])
    return [ops, rows]


def _ttt_trace(rng):
    n, m = rng.randrange(1, 6), rng.randrange(1, 6); k = rng.randrange(1, max(n, m) + 1)
    cells = [(r, c) for r in range(n) for c in range(m)]; rng.shuffle(cells)
    ops, rows = ['TicTacToe'], [[n, m, k]]
    for i, (r, c) in enumerate(cells[:rng.randrange(0, len(cells) + 1)]):
        candidate = [ops + ['move'], rows + [[r, c, 1 + i % 2]]]
        try: validate_domain(_o.TTT, candidate)
        except ValueError: break
        ops, rows = candidate
    return [ops, rows]


def _spam(rng):
    base = datetime(rng.choice([1999, 2000, 2024]), rng.choice([2, 12]), 28, 23, 59, 50)
    people = ['a', 'b', 'c', '+1555', 'x-9']
    calls = [[rng.choice(people[:3]), rng.choice(people[2:]), _iso(base + timedelta(seconds=rng.choice([0, 5, 9, 15, rng.randrange(0, 400000)])), True)]
             for _ in range(rng.randrange(0, 9))]
    reports = [[rng.choice(people[2:]), _iso(base + timedelta(seconds=rng.choice([0, 5, 10, 20, rng.randrange(0, 400000)])), True)]
               for _ in range(rng.randrange(0, 9))]
    return [calls, reports, rng.choice([0, 1, 5, 10, 86400, 10**9])]


def _template(rng, nested):
    keys = rng.sample(['a', 'b', 'name', 'X_1', 'z9', 'long_key'], rng.randrange(1, 6))
    values = []
    for i, k in enumerate(keys):
        parts = [rng.choice(['', 'v', 'hello', ' ', '!x?', '|~'])]
        if nested:
            for _ in range(rng.randrange(0, 3)):
                if i + 1 < len(keys): parts.append('{' + rng.choice(keys[i + 1:]) + '}')   # references only later keys: acyclic
                parts.append(rng.choice(['', '-', 'w']))
        values.append(''.join(parts))
    txt = ''.join(rng.choice(['{' + rng.choice(keys) + '}', 'q', ' ', '~', 'abc', '(', ')']) for _ in range(rng.randrange(0, 10)))
    return [txt, keys, values]


def _tetris(rng):
    rows, cols = rng.randrange(1, 8), rng.randrange(1, 8)
    while True:
        h, w = rng.randrange(1, min(rows, 3) + 1), rng.randrange(1, min(cols, 3) + 1)
        blk = [[rng.choice([0, 1, 1]) for _ in range(w)] for _ in range(h)]
        if any(any(r) for r in blk): break
    fill = rng.choice([0.0, 0.3, 0.6, 0.9])
    bg = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if rng.random() < fill * r / rows: bg[r][c] = 1
    return [bg, blk, rng.randrange(0, cols - w + 1)]


def _graph(rng):
    n = rng.randrange(1, 9); names = ['n%d' % i for i in range(n)]
    adj = []
    for _ in range(rng.randrange(0, 2 * n + 1)):
        a, b = rng.sample(range(n), 2) if n > 1 else (0, 0)
        if a != b: adj.append([names[a], names[b]])
    return [names, adj]


def _flights(rng):
    base = datetime(2024, 2, 28, 22, 0)
    flights = []
    for user in rng.sample(['u1', 'u2', 'bob'], rng.randrange(1, 4)):
        t = base + timedelta(minutes=rng.randrange(0, 60)); here = rng.choice(['JFK', 'SFO', 'LHR'])
        for _ in range(rng.randrange(1, 4)):
            dep = t; arr = dep + timedelta(minutes=rng.choice([30, 90, 200]))
            there = rng.choice(['JFK', 'SFO', 'LHR', 'NRT'])
            flights.append([here, _iso(dep, False), there, _iso(arr, False), user])
            here = there if rng.random() < 0.8 else rng.choice(['ORD', 'SFO'])
            t = arr + timedelta(minutes=rng.choice([0, 0, 45, 600]))
    rng.shuffle(flights)
    stamps = [f[1] for f in flights] + [f[3] for f in flights] + [_iso(base - timedelta(days=1), False), _iso(base + timedelta(days=3), False)]
    at = rng.choice(stamps) if rng.random() < 0.6 else _iso(base + timedelta(minutes=rng.randrange(0, 1500)), False)
    return [flights, rng.choice(['u1', 'u2', 'bob', 'nobody']), at]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.PARITY:
        args = [[b] for b in range(256)]
    elif uid == o.HIKE:
        args = [[[0], 0], [[0], 5], [[0, 5], 0], [[0, 0, 0], 1], [[0, 3, 4, 10], 0], [[0, 3, 4, 10], 1], [[0, 3, 4, 10], 2], [[0, 3, 4, 10], 9]]
        for _ in range(250):
            t = [0]
            for _ in range(rng.randrange(0, 12)): t.append(t[-1] + rng.choice([0, 1, 2, 5, 10, rng.randrange(0, 50)]))
            args.append([t, rng.randrange(0, 14)])
    elif uid == o.SPATH:
        args = [[1, [], 0, 0], [2, [], 0, 1], [2, [[0, 1]], 0, 1], [3, [[0, 0], [1, 1]], 0, 2], [4, [[0, 1], [1, 2], [2, 3], [0, 3]], 0, 2], [5, [[1, 2], [2, 1]], 2, 1]]
        for _ in range(250):
            n = rng.randrange(1, 12)
            edges = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randrange(0, 2 * n))]
            args.append([n, edges, rng.randrange(n), rng.randrange(n)])
    elif uid == o.SNAKE:
        args = [[['SnakeGame'], [[1, 1]]], [['SnakeGame', 'move'], [[1, 1], ['R']]], [['SnakeGame', 'move', 'move'], [[2, 2], ['D'], ['R']]],
                [['SnakeGame'] + ['move'] * 6, [[1, 3], ['R'], ['L'], ['R'], ['L'], ['R'], ['L']]],
                [['SnakeGame'] + ['move'] * 12, [[2, 2]] + [[d] for d in 'RDLURDLURDLU']]]
        for _ in range(250): args.append(_snake_trace(rng))
    elif uid == o.SPAM:
        args = [[[], [], 0], [[['a', 'r', '2024-01-01T00:00:00']], [['r', '2024-01-01T00:00:05']], 5],
                [[['a', 'r', '2024-01-01T00:00:00']], [['r', '2024-01-01T00:00:06']], 5],
                [[['a', 'r', '1999-12-31T23:59:59']], [['r', '2000-01-01T00:00:00']], 1],
                [[['a', 'r', '2000-02-28T23:59:59'], ['b', 'r', '2000-03-01T00:00:00']], [['r', '2000-02-29T12:00:00']], 43201],
                [[['b', 'r', '2024-05-05T10:00:00'], ['a', 'r', '2024-05-05T10:00:00'], ['a', 's', '2024-05-05T10:00:00']], [['r', '2024-05-05T10:00:00'], ['r', '2024-05-05T10:00:00']], 0]]
        for _ in range(250): args.append(_spam(rng))
    elif uid == o.BEE:
        args = [['a', [], []], ['a', [], ['aaaa', 'aaa', 'aaaaa']], ['e', ['b', 'n'], ['been', 'bee', 'nene', 'bean', 'eebn']], ['x', ['x'], ['xxxx', 'xxxx']]]
        for _ in range(250):
            letters = rng.sample('abcdefg', rng.randrange(1, 6))
            words = [''.join(rng.choice('abcdefgh') for _ in range(rng.randrange(1, 7))) for _ in range(rng.randrange(0, 10))]
            args.append([letters[0], letters[1:], words])
    elif uid == o.REPL:
        args = [['', 'a', 'b'], ['aaa', 'aa', 'b'], ['aaaa', 'aa', ''], ['abc', 'abcd', 'x'], ['abcabc', 'bc', 'XYZ'], ['a{b}c', '{b}', '!'], ['  ', ' ', '--']]
        for _ in range(250):
            alpha = rng.choice(['ab', 'a', 'abc', 'a b'])
            src = ''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 20)))
            tgt = ''.join(rng.choice(alpha) for _ in range(rng.randrange(1, 4)))
            args.append([src, tgt, ''.join(rng.choice('xyz') for _ in range(rng.randrange(0, 4)))])
    elif uid == o.READ:
        args = [[[1], 1], [[5], 1], [[5], 5], [[5], 6], [[3, 6, 7, 11], 8], [[3, 6, 7, 11], 3], [[30, 11, 23, 4, 20], 5], [[30, 11, 23, 4, 20], 6]]
        for _ in range(250):
            pages = [rng.randrange(1, 30) for _ in range(rng.randrange(1, 10))]
            args.append([pages, rng.randrange(1, 40)])
    elif uid in o.SUBS:
        args = [[[1], 1], [[1], 2], [[2, 2], 4], [[3, 34, 4, 12, 5, 2], 9], [[3, 34, 4, 12, 5, 2], 30], [[1, 1, 1], 2], [[5, 3, 5, 2, 3], 8]]
        for _ in range(250):
            nums = [rng.choice([1, 2, 3, 5, 7, 10, rng.randrange(1, 30)]) for _ in range(rng.randrange(1, 12))]
            args.append([nums, rng.randrange(1, sum(nums) + 3)])
    elif uid == o.WRAP:
        args = [['a', ['a']], ['a', ['b']], ['abc', ['b', 'bc']], ['hello world', ['o', 'l']], ['abcd bcd', ['cd', 'bc', 'b']], ['aaa aa', ['aa', 'a']]]
        for _ in range(250):
            words = [''.join(rng.choice('abc') for _ in range(rng.randrange(1, 7))) for _ in range(rng.randrange(1, 5))]
            elements = [''.join(rng.choice('abcd') for _ in range(rng.randrange(1, 4))) for _ in range(rng.randrange(1, 5))]
            args.append([' '.join(words), elements])
    elif uid in o.TPLS:
        if uid == o.TPL1:
            args = [['', [], []], ['plain', [], []], ['{a}', ['a'], ['']], ['Hi {name}, {name}!', ['name'], ['Ann']], ['{a}{b}', ['a', 'b'], ['1', '2']]]
        else:
            args = [['', ['a'], ['x']], ['{a}', ['a', 'b'], ['<{b}>', 'B']], ['{a}{a}', ['a', 'b', 'c'], ['{b}{c}', '{c}', 'z']], ['[{x}]', ['x'], ['']]]
        for _ in range(250): args.append(_template(rng, uid == o.TPL2))
    elif uid in o.TETS:
        args = [[[[0]], [[1]], 0], [[[0, 0], [0, 0]], [[1, 1]], 0], [[[0, 0], [1, 0]], [[1, 1]], 0], [[[0, 0, 0], [0, 0, 0], [1, 0, 1]], [[0, 1, 0], [1, 1, 1]], 0],
                [[[0, 0, 0], [0, 0, 0], [1, 1, 0]], [[1], [1]], 2], [[[0, 0, 0], [1, 0, 0], [1, 0, 1]], [[1, 1], [0, 1]], 1]]
        while len(args) < 260:
            a = _tetris(rng)
            try: validate_domain(uid, a)
            except ValueError: continue
            args.append(a)
    elif uid == o.COLOR:
        args = [[['a'], []], [['a', 'b'], [['a', 'b']]], [['a', 'b', 'c'], [['a', 'b'], ['b', 'c'], ['c', 'a']]],
                [['a', 'b', 'c', 'd'], [['a', 'b'], ['a', 'c'], ['a', 'd'], ['b', 'c'], ['b', 'd'], ['c', 'd']]], [['WA', 'OR', 'ID'], [['WA', 'OR'], ['OR', 'WA']]]]
        for _ in range(250): args.append(_graph(rng))
    elif uid == o.TTT:
        args = [[['TicTacToe'], [[3, 3, 3]]], [['TicTacToe', 'move'], [[1, 1, 1], [0, 0, 2]]],
                [['TicTacToe'] + ['move'] * 5, [[3, 3, 3], [0, 0, 1], [1, 0, 2], [1, 1, 1], [2, 0, 2], [2, 2, 1]]],
                [['TicTacToe'] + ['move'] * 3, [[2, 4, 2], [0, 3, 1], [1, 0, 2], [1, 2, 1]]]]
        for _ in range(250): args.append(_ttt_trace(rng))
    elif uid == o.TRI:
        args = [[0, 0, 1, 1, 2, 2, 0, 0, 5, 5], [0, 0, 4, 0, 0, 4, 1, 1, 5, 5], [0, 0, 4, 0, 0, 4, 9, 9, 2, 2], [0, 0, 4, 0, 0, 4, 2, 2, 4, 0],
                [0, 0, 4, 0, 0, 4, -1, 0, 5, 0], [-10**7, -10**7, 10**7, -10**7, -10**7, 10**7, 0, 0, 10**7, 10**7],
                [-10**7, -10**7, 10**7, 10**7 - 1, -10**7 + 1, 10**7, 10**7, 10**7, -10**7, -10**7]]
        for _ in range(250):
            s = rng.choice([3, 6, 20, 10**7])
            args.append([rng.randrange(-s, s + 1) for _ in range(10)])
    elif uid == o.FLIGHT:
        args = [[[], 'u', '2024-01-01T00:00'], [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T16:00', 'u']], 'u', '2024-01-01T09:59'],
                [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T16:00', 'u']], 'u', '2024-01-01T10:00'],
                [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T16:00', 'u']], 'u', '2024-01-01T12:00'],
                [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T16:00', 'u']], 'u', '2024-01-01T16:00'],
                [[['SFO', '2024-01-02T08:00', 'LAX', '2024-01-02T09:30', 'u'], ['JFK', '2024-01-01T10:00', 'SFO', '2024-01-02T08:00', 'u']], 'u', '2024-01-02T08:00'],
                [[['JFK', '2024-01-01T10:00', 'SFO', '2024-01-01T16:00', 'u']], 'v', '2024-01-01T12:00']]
        for _ in range(250): args.append(_flights(rng))
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _distinct_parts(k, largest):
    """All partitions of k into distinct parts <= largest, each ascending, in lexicographic order (direct recursion on the smallest part)."""
    out = []

    def go(rest, low, acc):
        if rest == 0: out.append(acc[:]); return
        for part in range(low, min(rest, largest) + 1):
            acc.append(part); go(rest - part, part + 1, acc); acc.pop()
    go(k, 1, [])
    return out


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.HIKE:
        n = 100000
        out.append(([list(range(n)), n - 2], 1))
        out.append(([list(range(n)), 0], n - 1))
        out.append(([[i * 10000 for i in range(n)], 9], 10000 * 10000))    # 99999 unit gaps in 10 days: ceil(99999 / 10) gaps per day
        out.append(([[0] * n, 100000], 0))
        out.append(([[0] + [10**9] * (n - 1), 5], 10**9))
    elif uid == o.SPATH:
        n = 100000
        path = [[i + 1, i] for i in range(n - 1)][::-1]
        out.append(([n, path, 0, n - 1], n - 1))
        out.append(([n, path + [[i, i] for i in range(100000)], n - 1, 0], n - 1))
        out.append(([n, path + [[0, n - 1]], 0, n // 2], n // 2))           # cycle of length n: distance min(n/2, n/2)
        out.append(([n, [[i, i + 1] for i in range(0, n - 2)] + [[0, 1]] * 100000, 0, n - 1], -1))
        out.append(([n, [[0, i] for i in range(1, n)], n - 1, 1], 2))
    elif uid == o.SNAKE:
        moves = ['R'] * 100000
        out.append(([['SnakeGame'] + ['move'] * len(moves), [[1, 100000]] + [[d] for d in moves]], [None] + [True] * 99999 + [False]))
        side = 300; moves = []
        for r in range(side):
            moves += ['R' if r % 2 == 0 else 'L'] * (side - 1)
            if r < side - 1: moves.append('D')
        assert len(moves) == 89999
        moves += ['D'] + ['U', 'L'] * 5000
        out.append(([['SnakeGame'] + ['move'] * len(moves), [[side, side]] + [[d] for d in moves]], [None] + [True] * 89999 + [False] * 10001))
        moves = ['R', 'L'] * 50000          # length 2 after move 5; move 10 grows into the occupied cell
        out.append(([['SnakeGame'] + ['move'] * len(moves), [[1, 2]] + [[d] for d in moves]], [None] + [True] * 9 + [False] * 99991))
    elif uid == o.SPAM:
        n = 100000
        same = '2024-02-29T12:00:00'
        calls = [['c%d' % (i % 10), 'victim', same] for i in range(n)]
        out.append(([calls, [['victim', same]] * n, 0], [['c%d' % i, 10000 * n] for i in range(10)]))
        start = datetime(2000, 2, 28, 12, 0, 0)
        stamps = [_iso(start + timedelta(seconds=i), True) for i in range(n)]
        out.append(([[['x', 'r', s] for s in stamps], [['r', s] for s in stamps[::-1]], 2], [['x', 5 * n - 6]]))
        out.append(([[['x', 'r', s] for s in stamps], [['q', s] for s in stamps], 10**9], []))
        start = datetime(1999, 12, 31, 23, 0, 0)
        stamps = [_iso(start + timedelta(seconds=i), True) for i in range(n)]
        out.append(([[['y%d' % (i % 2), 'r', s] for i, s in enumerate(stamps)], [['r', stamps[n // 2]]], 0], [['y%d' % ((n // 2) % 2), 1]]))
    elif uid == o.BEE:
        n = 100000
        good, bad = 'abcdefghabcdefghabcd', 'abcdefghabcdefghabcz'
        out.append((['a', list('bcdefgh'), [good] * n], [good] * n))
        out.append((['a', list('bcdefgh'), [good, bad] * (n // 2)], [good] * (n // 2)))
        out.append((['z', list('abcdefghijklmnopqrstuvwxy'), ['abc'] * n], []))
    elif uid == o.REPL:
        out.append((['a' * 100000, 'aa', 'b'], 'b' * 50000))
        out.append((['ab' * 50000, 'ab', ''], ''))
        out.append((['a' * 99999 + 'b', 'a' * 50000 + 'b', 'X'], 'a' * 49999 + 'X'))
        out.append((['x' * 100000, 'x', 'y' * 20], 'y' * 2000000))
        out.append((['ab' * 50000, 'abab' * 24999 + 'c', 'Q'], 'ab' * 50000))
    elif uid == o.READ:
        n = 100000
        out.append(([[10**9] * n, n], 10**9))
        out.append(([[10**9] * n, 10**9], 100000))
        out.append(([[1] * n, n - 1], -1))
        out.append(([[1] * n, 10**9], 1))
        out.append(([[10**9] * n, 2 * n], 5 * 10**8))
    elif uid == o.SUB1:
        out.append(([list(range(1000, 2000)), 10**6], True))     # 333-element sums cover [388278, 610389]; 10^6 has complement 499500
        out.append(([[2 * i for i in range(500, 1500)], 10**6 + 1], False))   # odd target, even values
        out.append(([[10**6] * 1000, 10**9 - 500000], False))
        out.append(([[10**6] * 1000, 10**9 - 10**6], True))
        out.append(([[999983] * 500 + [2] * 500, 999983 * 500 + 1000 - 999], False))
        out.append(([[1] * 1000, 10**9], False))
    elif uid == o.SUB2:
        out.append(([[1] * 1000, 1], 1000))
        out.append(([[1] * 1000, 500], comb(1000, 500) % o.MOD))
        out.append(([[1] * 1000, 999], 1000))
        out.append(([[2] * 1000, 999], 0))
        out.append(([[3] * 1000, 3 * 333], comb(1000, 333) % o.MOD))
        out.append(([[7] * 1000, 10**9], 0))
    elif uid == o.SUB3:
        out.append(([[1] * 100, 50], [[1] * 50]))
        out.append(([list(range(1, 101)), 30], _distinct_parts(30, 100)))
        out.append(([list(range(100, 0, -1)), 50], _distinct_parts(50, 100)))
        out.append(([[2 * i for i in range(1, 101)], 9999], []))
        out.append(([[100] * 100, 10000], [[100] * 100]))
        out.append(([[10**6] * 50 + [1] * 50, 10000], []))
    elif uid == o.WRAP:
        words = ['abcdefghij'] * 9090
        out.append(([' '.join(words), ['zz'] * 999 + ['j']], ' '.join(['abcdefghi[j]'] * 9090)))
        word = 'a' * 20
        elems = ['a' * i + 'b' for i in range(20)] + ['a' * 20] + ['a' * i for i in range(1, 20)]
        out.append(([' '.join([word] * 4761), elems], ' '.join(['[' + word + ']'] * 4761)))
        out.append(([' '.join(['xyz'] * 25000), ['q' * 20] * 1000], ' '.join(['xyz'] * 25000)))
    elif uid == o.TPL1:
        out.append((['{x}' * 33333, ['x'], ['abc']], 'abc' * 33333))
        out.append((['q' * 100000, ['x'], ['abc']], 'q' * 100000))
        keys = ['k%d' % i for i in range(2000)]
        out.append(([''.join('{%s}' % k for k in keys[:1000]) + '~', keys, ['v' * 1000] * 2000], 'v' * 1000000 + '~'))
    elif uid == o.TPL2:
        keys = ['k%d' % i for i in range(2000)]
        values = ['{k%d}a' % (i + 1) for i in range(1999)] + ['z']
        out.append((['{k0}' * 1000, keys, values], ('z' + 'a' * 1999) * 1000))
        keys = ['d%d' % i for i in range(21)]
        values = ['{d%d}{d%d}' % (i + 1, i + 1) for i in range(20)] + ['x']
        out.append((['{d0}', keys, values], 'x' * 2 ** 20))
        out.append((['{d20}' * 20000, keys, values], 'x' * 20000))
    elif uid in o.TETS:
        empty = [[0] * 300 for _ in range(300)]
        landed = [row[:] for row in empty]
        for r in range(290, 300):
            for c in range(290, 300): landed[r][c] = 1
        out.append(([empty, [[1] * 10 for _ in range(10)], 290], landed))
        bottom = [[0] * 300 for _ in range(299)] + [[0] * 10 + [1] * 290]
        filled = [[0] * 300 for _ in range(299)] + [[1] * 300]
        out.append(([bottom, [[1] * 10], 0], filled if uid == o.TET1 else [[0] * 300 for _ in range(300)]))
        stair = [[1 if c < r else 0 for c in range(300)] for r in range(300)]      # row r has r filled cells on the left
        hook = [[0] * 9 + [1]] * 10                                                 # one column at block column 9
        # column 299 is empty in every stair row, so the hook (block column 9) reaches the floor: rows 290..299
        result = [row[:] for row in stair]
        for r in range(290, 300): result[r][299] = 1
        cleared = [[0] * 300] + result[:299]                                        # row 299 is now full (299 + 1 cells)
        out.append(([stair, hook, 290], result if uid == o.TET1 else cleared))
    elif uid == o.COLOR:
        names = ['v%d' % i for i in range(20)]
        out.append(([names, [[names[i], names[(i + 1) % 20]] for i in range(20)]], True))       # even cycle
        rim = names[1:]
        out.append(([names, [[names[0], v] for v in rim] + [[rim[i], rim[(i + 1) % 19]] for i in range(19)]], False))   # odd wheel W19
        out.append(([names, [[names[a], names[b]] for a in range(4) for b in range(a + 1, 4)]], False))                # K4 plus isolated nodes
        parts = [names[:7], names[7:14], names[14:]]
        out.append(([names, [[a, b] for i in range(3) for j in range(i + 1, 3) for a in parts[i] for b in parts[j]]], True))   # complete tripartite
        u, w, z = names[:5], names[5:10], names[10]
        groetzsch = [[u[i], u[(i + 1) % 5]] for i in range(5)] + [[w[i], u[(i + 1) % 5]] for i in range(5)] + [[w[i], u[(i - 1) % 5]] for i in range(5)] + [[w[i], z] for i in range(5)]
        out.append(([names, groetzsch], False))   # Groetzsch graph: triangle-free with chromatic number 4
    elif uid == o.TTT:
        ops = ['TicTacToe'] + ['move'] * 20000
        rows = [[100000, 100000, 5]] + [[0, 2 * i, 1] if j == 0 else [1, 2 * i + 1, 2] for i in range(10000) for j in range(2)]
        out.append(([ops, rows], [None] + [0] * 20000))
        rows = [[1000, 10000, 10000]] + [[0, i, 1] if j == 0 else [5, i, 2] for i in range(10000) for j in range(2)]
        rows = rows[:-1]                                                            # player 1 completes the row on move 19999
        out.append(([['TicTacToe'] + ['move'] * 19999, rows], [None] + [0] * 19998 + [1]))
        rows = [[1000, 1000, 100]] + [[i, i, 1] if j == 0 else [i, i + 1, 2] for i in range(100) for j in range(2)]
        out.append(([['TicTacToe'] + ['move'] * 199, rows[:200]], [None] + [0] * 198 + [1]))
        rows = [[1000, 1000, 100]] + [[i, 999 - i, 2] if j == 0 else [i, 997 - i, 1] for i in range(100) for j in range(2)]
        out.append(([['TicTacToe'] + ['move'] * 199, rows[:200]], [None] + [0] * 198 + [2]))
        order = [c for c in range(0, 1000, 2)] + [c for c in range(1, 1000, 2)]    # p1 builds row 0 out of order; runs merge at the end
        rows = [[3, 1000, 1000]] + [[0, c, 1] if j == 0 else [2, c, 2] for c in order for j in range(2)]
        out.append(([['TicTacToe'] + ['move'] * 1999, rows[:2000]], [None] + [0] * 1998 + [1]))
    elif uid == o.FLIGHT:
        n = 100000; base = datetime(2024, 2, 28, 0, 0)
        port = lambda i: 'AAA' if i % 2 == 0 else 'BBB'
        flights = [[port(i), _iso(base + timedelta(minutes=10 * i), False), port(i + 1), _iso(base + timedelta(minutes=10 * i + 5), False), 'trav'] for i in range(n - 1)]
        flights += [['ZZZ', _iso(base, False), 'YYY', _iso(base + timedelta(minutes=1), False), 'other']]
        mixed = flights[::-1]
        j = 54321
        out.append(([mixed, 'trav', _iso(base + timedelta(minutes=10 * j + 7), False)], port(j + 1)))
        out.append(([mixed, 'trav', _iso(base + timedelta(minutes=10 * j), False)], port(j)))
        out.append(([mixed, 'trav', _iso(base + timedelta(minutes=10 * j + 3), False)], ''))
        out.append(([mixed, 'trav', _iso(base - timedelta(minutes=1), False)], 'AAA'))
        out.append(([mixed, 'trav', '2099-12-31T23:59'], port(n - 1)))
        out.append(([mixed, 'nobody', '2024-03-01T00:00'], ''))
    return out
