"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h03b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _music(rng, level, n):
    names = ['addSong', 'playSong', 'playSong', 'playSong', 'getAnalytics'] + (['getLastThreeSongs'] * 2 if level >= 2 else []) + \
        (['removeSong'] if level >= 3 else [])
    calls, songs = [('addSong', rng.choice(['Hey', 'Blue', 'Hey', 'Song 2']))], 1
    for _ in range(n):
        op = rng.choice(names)
        if op == 'addSong': calls.append((op, rng.choice(['Hey', 'Blue', 'Rain', 'Song 2', 'A']))); songs += 1
        elif op == 'playSong': calls.append((op, rng.randrange(1, songs + 1), rng.randrange(1, 5)))
        elif op == 'getAnalytics': calls.append((op,))
        elif op == 'getLastThreeSongs': calls.append((op, rng.randrange(1, 6)))
        else: calls.append((op, rng.randrange(1, songs + 3)))
    return _ops('MusicPlayer', [], calls)


def _chain(rng, n):
    out, stack = [], []
    for _ in range(n):
        if stack and rng.random() < 0.45: out.append('<- ' + stack.pop())
        else:
            f = rng.choice(['main', 'a', 'b', 'c_1']); stack.append(f); out.append('-> ' + f)
    return out


def _hand(rng, deck, size=5):
    return [deck.pop() for _ in range(size)]


def _deck(rng, ranks=_o.RANKS, suits=_o.SUITS):
    d = [f'{r} of {s}' for r in ranks for s in suits]; rng.shuffle(d); return d


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.MAXT:
        args = [[[5], [3], 0], [[5], [3], 2], [[1, 1], [1, 1], 0], [[2, 3], [1, 10], 10], [[10**6], [1], 40]]
        for _ in range(300):
            n = rng.randrange(1, 4)
            args.append([[rng.randrange(1, 12) for _ in range(n)], [rng.randrange(1, 8) for _ in range(n)], rng.randrange(0, 25)])
    elif uid == o.MERGE:
        args = [[[]], [[[]]], [[['1, 7']]], [[['1, 7'], ['1, -7']]], [[['0, 0', '5, -3'], ['2, 4', '5, 3', '9, 1']]]]
        for _ in range(300):
            streams = []
            for _ in range(rng.randrange(0, 5)):
                ts = sorted(rng.randrange(0, 15) for _ in range(rng.randrange(0, 6)))
                streams.append([f'{t}, {rng.randrange(-9, 10)}' for t in ts])
            args.append([streams])
    elif uid == o.ZERO:
        args = [[n] for n in range(1, 400)] + [[rng.randrange(1, 10**6)] for _ in range(100)] + [[10**15], [2**49 - 1], [3 * 2**40 + 1]]
    elif uid == o.ROTF:
        args = [[[7]], [[1, 2]], [[2, 1]], [[3, 1, 2]], [[2, 1, 3]], [[1, 3, 2]], [[-5, 10**9, -10**9]]]
        for _ in range(300):
            n = rng.randrange(1, 9); base = sorted(rng.sample(range(-20, 20), n))
            r = rng.random()
            if r < 0.4: s = rng.randrange(n); a = base[s:] + base[:s]
            elif r < 0.7: s = rng.randrange(n); a = (base[s:] + base[:s])[::-1]
            else: a = base[:]; rng.shuffle(a)
            args.append([a])
    elif uid == o.LAYER:
        args = [[[1], [1]], [[1, 2], [2, 1]], [[1, 2, 3], [3, 1, 2]], [[1, 2, 3], [2, 1, 3]], [[3, 2, 1], [1, 2, 3]]]
        for _ in range(300):
            n = rng.randrange(1, 7); cur = rng.sample(range(-10, 10), n); want = cur[:]
            if rng.random() < 0.7: rng.shuffle(want)
            args.append([cur, want])
    elif uid == o.BALLS:
        args = [[[[0, 0]], 0], [[[0, 0], [0, 1]], 0], [[[0, 0], [0, 1]], 1], [[[0, 0], [1, 1]], 10], [[[0, 0], [0, 5], [0, 10], [3, 5]], 5]]
        for _ in range(300):
            pts = rng.sample([[x, y] for x in range(6) for y in range(6)], rng.randrange(1, 14))
            args.append([pts, rng.randrange(0, 4)])
    elif uid == o.VCONV:
        args = [[[0], 1], [[1], 1], [[1, 1], 2], [[1, 1, 0], 2], [[1, 1, 1, 1, 1, 1], 3], [[1, 0, 1, 1, 0, 1, 1, 1], 3]]
        for _ in range(300):
            n = rng.randrange(1, 13); a = [1 if rng.random() < rng.choice([0.3, 0.6, 0.9]) else 0 for _ in range(n)]
            args.append([a, rng.randrange(1, n + 1)])
    elif uid == o.CHAIN:
        args = [[[]], [['-> main']], [['-> a', '<- a', '-> b', '<- b']], [['-> a', '-> b', '<- b', '-> b', '<- b', '<- a', '-> a']]]
        args += [[_chain(rng, rng.randrange(0, 20))] for _ in range(300)]
    elif uid in (o.MUSIC1, o.MUSIC2, o.MUSIC3):
        level = (o.MUSIC1, o.MUSIC2, o.MUSIC3).index(uid) + 1
        args = [_ops('MusicPlayer', [], [('getAnalytics',)]),
                _ops('MusicPlayer', [], [('addSong', 'A'), ('addSong', 'B'), ('playSong', 2, 1), ('playSong', 2, 1), ('playSong', 1, 7), ('playSong', 2, 3), ('getAnalytics',)])]
        if level >= 2: args.append(_ops('MusicPlayer', [], [('addSong', 'A'), ('getLastThreeSongs', 9), ('playSong', 1, 9), ('getLastThreeSongs', 9)]))
        if level >= 3: args.append(_ops('MusicPlayer', [], [('addSong', 'A'), ('removeSong', 1), ('removeSong', 1), ('removeSong', 2), ('playSong', 1, 4), ('getAnalytics',)]))
        args += [_music(rng, level, rng.randrange(1, 30)) for _ in range(300)]
    elif uid in (o.NGRAM1, o.NGRAM2):
        args = [['a', []], ['a b', ['a b']], ['a b c', ['a b', 'b c']], ['a b c', ['b c']], ['a a a a', ['a a']]]
        if uid == o.NGRAM2: args += [['a b c d', ['a b', 'a b c', 'c d']], ['a b c d e', ['a b c d e', 'b c']]]
        vocab = ['a', 'b', 'c', 'dog', 'ran']
        for _ in range(300):
            words = [rng.choice(vocab) for _ in range(rng.randrange(1, 12))]
            grams = set()
            for _ in range(rng.randrange(0, 6)):
                ln = 2 if uid == o.NGRAM1 else rng.randrange(2, 5)
                grams.add(' '.join(rng.choice(vocab) for _ in range(ln)))
            args.append([' '.join(words), sorted(grams)])
    elif uid in (o.PARTY1, o.PARTY2):
        args = [[[], []], [[['p1', '1', '3']], [['p1', 'soma']]],
                [[['p1', '1', '3'], ['p2', '3', '5'], ['p3', '7', '8']], [['p3', 'soma'], ['p2', 'soma'], ['p1', 'soma']]],
                [[['a', '0', '10'], ['b', '2', '4'], ['c', '3', '12']], [['a', 'x'], ['b', 'x'], ['c', 'y']]]]
        for _ in range(300):
            n = rng.randrange(0, 9); ids = rng.sample(['p' + str(i) for i in range(20)], n)
            win = []
            for pid in ids:
                s = rng.randrange(0, 20); win.append([pid, str(s), str(s + rng.randrange(1, 6))])
            geo = [[pid, rng.choice(['mission', 'soma', 'noe'])] for pid in ids]; rng.shuffle(geo)
            args.append([win, geo])
    elif uid == o.PAINT:
        args = [[k, n] for k in range(1, 7) for n in range(1, 6)] + [[10**9, 1], [1, 200000], [2, 199999]]
        args += [[rng.randrange(1, 10**9), rng.randrange(1, 3000)] for _ in range(60)]
    elif uid == o.PHONE:
        args = [[[], '2'], [['a', 'b', 'd'], '2'], [['cat', 'act', 'bat', 'cats'], '228'], [['hello'], '43556'], [['ab'], '10'], [['ab'], '20']]
        pool = ['cat', 'bat', 'act', 'dog', 'fog', 'eh', 'gi', 'tree', 'used', 'a', 'z', 'cat']
        for _ in range(300):
            words = [rng.choice(pool) for _ in range(rng.randrange(0, 8))]
            w = rng.choice(pool)
            number = ''.join(str(next(d for d in range(2, 10) if ch in _o.KEYPAD[d])) for ch in w)
            if rng.random() < 0.2: number = ''.join(rng.choice('0123456789') for _ in range(rng.randrange(1, 5)))
            args.append([words, number])
    elif uid in (o.POKER1, o.POKER2):
        fixed = [['A of hearts', 'K of hearts', 'Q of hearts', 'J of hearts', '10 of hearts'],
                 ['A of spades', '2 of hearts', '3 of clubs', '4 of hearts', '5 of diamonds'],
                 ['9 of spades', '9 of hearts', '9 of diamonds', '4 of spades', '4 of diamonds'],
                 ['2 of spades', '7 of hearts', '9 of clubs', 'J of clubs', 'K of diamonds'],
                 ['Q of clubs', 'K of clubs', 'A of clubs', '2 of clubs', '3 of diamonds']]
        if uid == o.POKER1: args = [[h] for h in fixed]
        else: args = [[[fixed[0], fixed[3]]], [[fixed[1]]], [[fixed[2], fixed[1], fixed[3]]],
                      [[['2 of spades', '2 of hearts', '5 of clubs', '5 of hearts', '9 of diamonds'], ['2 of clubs', '2 of diamonds', '5 of spades', '5 of diamonds', '9 of hearts']]]]
        for _ in range(400):
            ranks = rng.choice([_o.RANKS, _o.RANKS[:5], ('2', '3', '4', '5', 'A'), ('9', '10', 'J', 'Q', 'K', 'A')])
            suits = rng.choice([_o.SUITS, _o.SUITS[:1], _o.SUITS[:2]])
            deck = _deck(rng, ranks, suits)
            players = 1 if uid == o.POKER1 else rng.randrange(1, min(5, len(deck) // 5) + 1)
            if len(deck) < 5 * players: deck = _deck(rng)
            hands = [_hand(rng, deck) for _ in range(players)]
            args.append([hands[0]] if uid == o.POKER1 else [hands])
    elif uid == o.PRODMM:
        args = [[['push'], [0]], [['push'], [-7]], [['push', 'push', 'pop'], [3, -4, 3]], [['push', 'push', 'pop', 'push'], [5, 5, 5, -1]]]
        for _ in range(300):
            ops, xs, bag = [], [], []
            for _ in range(rng.randrange(1, 15)):
                if len(bag) > 1 and rng.random() < 0.4:
                    v = rng.choice(bag); bag.remove(v); ops.append('pop'); xs.append(v)
                else:
                    v = rng.randrange(-6, 7); bag.append(v); ops.append('push'); xs.append(v)
            args.append([ops, xs])
    elif uid == o.PURCH:
        args = [[[1], [], []], [[5], [1], [4]], [[5], [1], [5]], [[1, 2, 3], [1, 2, 3, 1], [6, 5, 2, 0]]]
        for _ in range(300):
            n = rng.randrange(1, 10); prices = sorted(rng.randrange(1, 10) for _ in range(n)); q = rng.randrange(0, 6)
            args.append([prices, [rng.randrange(1, n + 1) for _ in range(q)], [rng.randrange(0, 40) for _ in range(q)]])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.MAXT:
        n = 20000  # all services equal: each full round of upgrades costs n*c
        out.append(([[7] * n, [3] * n, 10**9], 7 * (1 + 10**9 // (3 * n))))
        out.append(([[10**6], [1], 10**9], 10**6 * (1 + 10**9)))
        tp = [10**6] * (n - 1) + [1]  # one slow service with cost 1: it alone is upgraded until it reaches 10**6, then all are needed
        out.append(([tp, [10**6] * (n - 1) + [1], 999999], 10**6))
    elif uid == o.MERGE:
        streams = [[f'{t}, {1 if s % 2 == 0 else -1}' for t in range(10)] for s in range(10000)]  # 5000 +1 and 5000 -1 per tick
        out.append(([streams], [f'{t}, 0' for t in range(10)]))
        one = [f'{t}, 1' for t in range(100000)]
        out.append(([[one]], [f'{t}, {t + 1}' for t in range(100000)]))
        streams = [[f'{s}, 1000000'] for s in range(10000)]
        out.append(([streams[::-1]], [f'{s}, {(s + 1) * 10**6}' for s in range(10000)]))
    elif uid == o.ZERO:
        out.append(([2**49], 50))  # halve 49 times, then 1 -> 0
        out.append(([10**15], o.ref_zero(10**15)))
    elif uid == o.ROTF:
        n = 100000; base = list(range(n))
        out.append(([base], 0))
        out.append(([base[::-1]], 1))
        out.append(([base[1:] + base[:1]], 3))  # flip, rotate, flip
        out.append(([base[n // 2:] + base[:n // 2]], n // 2))  # n/2 rotations; the flip route needs n/2+2
        out.append(([[1, 0] + base[2:]], -1))  # not a rotation of sorted or reversed sorted
    elif uid == o.LAYER:
        n = 100000; base = list(range(n))
        out.append(([base, base[:]], 0))
        out.append(([base, base[::-1]], n - 1))
        out.append(([base, base[-1:] + base[:-1]], 1))
        out.append(([base, [1, 0] + base[2:]], n - 1))  # only element 0 can stay
    elif uid == o.BALLS:
        n = 100000
        out.append(([[[0, 2 * i] for i in range(n)], 2], 1))
        out.append(([[[0, 2 * i] for i in range(n)], 1], n))
        grid = [[3 * x, 3 * y] for x in range(316) for y in range(316)]  # 99856 balls, d=3 joins the whole grid
        out.append(([grid, 3], 1))
        out.append(([grid, 2], len(grid)))
    elif uid == o.VCONV:
        n = 100000
        out.append(([[1] * n, 1000], n + 1000 * 999 // 2))
        out.append(([[1] * n, n], n * (n + 1) // 2))
        out.append(([[0] * n, 7], 0))
        out.append(([[i % 2 for i in range(n)], 1], n // 2))
    elif uid == o.CHAIN:
        out.append(([['-> a', '-> b', '<- b', '<- a'] * 25000], ['a']))
        out.append(([['-> f'] * 50000 + ['<- f'] * 50000], ['f']))
        out.append(([['-> m'] + ['-> x', '-> y', '<- y', '-> y', '<- y', '<- x'] * 16666], ['m', 'x', 'y']))
    elif uid in (o.MUSIC1, o.MUSIC2, o.MUSIC3):
        level = (o.MUSIC1, o.MUSIC2, o.MUSIC3).index(uid) + 1
        songs = 2000
        calls = [('addSong', 'S' + str(i)) for i in range(1, songs + 1)]
        exp = [None] + list(range(1, songs + 1))
        # song i is played by users 1..(i % 7); repeat plays by the same users do not change counts
        for rep in range(2):
            for i in range(1, songs + 1):
                for u in range(1, i % 7 + 1): calls.append(('playSong', i, u)); exp.append(None)
        order = sorted(range(1, songs + 1), key=lambda i: (-(i % 7), i))
        for _ in range(100): calls.append(('getAnalytics',)); exp.append([['S' + str(i), i % 7] for i in order])
        if level >= 2:
            # user 1 last played (in the second round) the largest ids with i % 7 >= 1
            last = [i for i in range(songs, 0, -1) if i % 7 >= 1][:3]
            for _ in range(100): calls.append(('getLastThreeSongs', 1)); exp.append(last)
        if level >= 3:
            for i in range(songs, 1000, -1): calls.append(('removeSong', i)); exp.append(True)
            last = [i for i in range(1000, 0, -1) if i % 7 >= 1][:3]
            calls.append(('getLastThreeSongs', 1)); exp.append(last)
            order = sorted(range(1, 1001), key=lambda i: (-(i % 7), i))
            for _ in range(50): calls.append(('getAnalytics',)); exp.append([['S' + str(i), i % 7] for i in order])
        out.append((_ops('MusicPlayer', [], calls), exp))
    elif uid in (o.NGRAM1, o.NGRAM2):
        n = 100000
        out.append((['a ' * (n - 1) + 'a', ['a a']], ['a a'] * (n // 2)))
        out.append((['x ' * (n - 1) + 'x', ['q r']], ['x'] * n))
        if uid == o.NGRAM2:
            grams = ['a a', 'a a a', 'a a a a', 'a a a a a'] + ['w%s z' % chr(97 + i % 26) for i in range(5000)]
            out.append((['a ' * (n - 1) + 'a', grams], ['a a a a a'] * (n // 5)))
    elif uid in (o.PARTY1, o.PARTY2):
        n = 100000
        win = [['p' + str(i), str(i), str(i + 1)] for i in range(n)]  # touching unit windows
        geo = [['p' + str(i), 'h' + str(i % 4)] for i in range(n)]
        if uid == o.PARTY1:
            out.append(([win, geo], [['h' + str(h), str(i), str(i + 1)] for h in range(4) for i in range(h, n, 4)]))
            out.append(([win, [[p, 'one'] for p, _, _ in win]], [['one', '0', str(n)]]))
        else:
            out.append(([win, geo], [['h' + str(h), 1] for h in range(4)]))
            nest = [['p' + str(i), str(i), str(2 * n - i)] for i in range(n)]
            out.append(([nest, [[p, 'one'] for p, _, _ in nest]], [['one', n]]))
    elif uid == o.PAINT:
        out.append(([10**9, 10**9], 10**9 * pow(10**9 - 1, 10**9 - 1, o.MOD) % o.MOD))  # closed form via built-in pow
        out.append(([2, 10**9], 2))
        out.append(([1, 10**9], 0))
    elif uid == o.PHONE:
        words = ['cat', 'bat', 'act'] * 3333 + ['abc']
        out.append(([words, '228'], [w for w in words if w != 'abc']))
        out.append(([['a' * 20] * 10000, '2' * 20], ['a' * 20] * 10000))
    elif uid == o.POKER2:
        hands = [[f'{r} of {s}' for r in rs] for s, rs in zip(o.SUITS, [('2', '3', '4', '5', '6'), ('3', '4', '5', '6', '7'), ('4', '5', '6', '7', '8'), ('5', '6', '7', '8', '9')])]
        out.append(([hands], [3]))
    elif uid == o.PRODMM:
        n = 100000
        out.append(([['push'] * n, list(range(1, n + 1))], list(range(1, n + 1))))
        h = n // 2
        ops = ['push'] * h + ['pop'] * (h - 1)
        xs = list(range(-h // 2, h - h // 2)) + list(range(-h // 2, -h // 2 + h - 1))
        low, top = -h // 2, -h // 2 + h - 1  # pushes ascend from low; pops then remove ascending from low
        exp = [(low + i) * low for i in range(h)] + [top * (low + j + 1) for j in range(h - 1)]
        out.append(([ops, xs], exp))
    elif uid == o.PURCH:
        n = 100000
        out.append(([[1] * n, list(range(1, n + 1)), [n] * n], [n - p + 1 for p in range(1, n + 1)]))
        out.append(([[10**9] * n, [1] * n, [10**15] * n], [10**5] * n))
        out.append(([list(range(1, n + 1)), [1] * n, [i * (i + 1) // 2 for i in range(n)]], list(range(n))))
    return out
