"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h04b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


USERS = ['al', 'bo', 'cy', 'di']
CHATS = ['c1', 'c2', 'c3']


def _chat(rng, level, n):
    names = ['recordEvent', 'recordEvent', 'getUserCount'] + (['getChatCount'] if level >= 2 else []) + (['getChatUserCount'] if level >= 3 else [])
    t, last, calls = rng.randrange(0, 5), {}, []
    for _ in range(n):
        t += rng.choice([0, 0, 1, 1, 2, 5])
        op = rng.choice(names)
        if op == 'recordEvent':
            u = rng.choice(USERS)
            if last.get(u, -1) >= t: op = 'getUserCount'
            else:
                last[u] = t; calls.append((op, t, u, rng.choice(CHATS))); continue
        if op == 'getUserCount': calls.append((op, t, rng.choice(USERS + ['zz'])))
        else: calls.append((op, t, rng.choice(CHATS + ['c9'])))
    return _ops('ChatEventAggregator', [rng.choice([1, 2, 3, 5, 10])], calls)


def _eq(rng, uid):
    signs = ['+'] if uid == _o.EQ1 else ['+', '-']
    names = ['v' + str(i) for i in range(rng.randrange(1, 9))]
    order = list(names); rng.shuffle(order)
    lines = []
    for i, name in enumerate(order):
        earlier = names if uid == _o.EQ3 and rng.random() < 0.12 else order[i + 1:]  # level 3 sometimes references anything (cycles)
        terms = []
        for _ in range(rng.randrange(1, 4)):
            pool = earlier + (['zz'] if uid == _o.EQ3 and rng.random() < 0.03 else [])
            terms.append(rng.choice(pool) if pool and rng.random() < 0.6 else str(rng.choice([0, 1, 2, 7, 99, 999999])))
        expr = terms[0] + ''.join(' ' + rng.choice(signs) + ' ' + t for t in terms[1:])
        if uid == _o.EQ3 and rng.random() < 0.04: continue  # leave a variable undefined
        lines.append(name + ' = ' + expr)
    rng.shuffle(lines)
    target = rng.choice(names) if uid != _o.EQ3 or rng.random() < 0.9 else 'q'
    if uid != _o.EQ3: target = order[rng.randrange(len(order))]
    return [[target] + lines]


def _desc(rng):
    words = ['Cozy', 'studio', 'apartment', '1', 'one', 'bedroom', '1br', '1BD', 'Studios', 'bedrooms', 'near', 'park', '-', ',', '2', 'big', 'STUDIO']
    seps = [' ', ' ', '-', ', ', '!', '']
    out = ''
    for _ in range(rng.randrange(0, 8)): out += rng.choice(words) + rng.choice(seps)
    return out[:500]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.BSV:
        args = [[[], 0], [[5], 5], [[5], 4], [[5], 6], [[1, 1, 1], 1], [[1, 2, 2, 2, 3], 2], [[1, 2, 2, 4], 3], [[-10**9, 10**9], 10**9]]
        for _ in range(250):
            arr = sorted(rng.randrange(-5, 6) for _ in range(rng.randrange(0, 12)))
            args.append([arr, rng.randrange(-7, 8)])
    elif uid == o.BTC:
        args = [[''], ['a'], ['aaaa'], ['ab'], ['aabbbc'], ['Aa'], ['abcd'], ['zyxwZYXW']]
        for _ in range(250):
            alpha = rng.choice(['ab', 'abc', 'aAbB', 'abcdefgh', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'])
            args.append([''.join(rng.choice(alpha) for _ in range(rng.randrange(0, 40)))])
    elif uid == o.TRANS:
        args = [[[]], [[['5', 'u1', '/a']]], [[['2', 'u1', '/b'], ['1', 'u1', '/a'], ['1', 'u2', '/a']]], [[['10', 'u1', '/a'], ['9', 'u1', '/a']]]]
        for _ in range(250):
            logs, used = [], set()
            for _ in range(rng.randrange(0, 12)):
                u, t = rng.choice(['u1', 'u2', 'u3']), rng.randrange(0, 15)
                if (u, t) in used: continue
                used.add((u, t)); logs.append([str(t), u, rng.choice(['/a', '/b', '/c', 'Home', 'x.y'])])
            args.append([logs])
    elif uid == o.CAKE:
        args = [[[0, 0, 0], []], [[0, 0, 0], [[0, 0, 0], [1, 0, 0]]], [[5, 5, 5], [[5, 5, 5], [0, 0, 1]]]]
        for _ in range(250):
            args.append([[rng.randrange(0, 8) for _ in range(3)], [[rng.randrange(0, 4) for _ in range(3)] for _ in range(rng.randrange(0, 8))]])
    elif uid in (o.EQ1, o.EQ2, o.EQ3):
        args = [[['x', 'x = 5']], [['x', 'y = 2', 'x = y + y + 1']], [['a', 'a = 0']]]
        if uid != o.EQ1: args.append([['x', 'x = 1 - 2 - 3']])
        if uid == o.EQ3: args += [[['x']], [['x', 'x = x']], [['x', 'x = y + 1', 'y = x']], [['x', 'x = 1 + q']], [['x', 'x = 3', 'y = y']]]
        for _ in range(250): args += [_eq(rng, uid)]
    elif uid == o.WAIT:
        args = [[[]], [[1]], [[3]], [[1, 1, 1]], [[3, 1, 2]], [[2, 2]]]
        for _ in range(250): args.append([[rng.randrange(1, 7) for _ in range(rng.randrange(0, 10))]])
    elif uid == o.ELEV:
        args = [[[], ['0', 'up']], [[['5', 'idle']], ['0', 'down']], [[['3', 'up']], ['3', 'up']], [[['3', 'up']], ['2', 'up']],
                [[['3', 'down'], ['1', 'up'], ['5', 'idle']], ['3', 'down']]]
        for _ in range(250):
            ev = [[str(rng.randrange(0, 12)), rng.choice(['up', 'down', 'idle'])] for _ in range(rng.randrange(0, 7))]
            args.append([ev, [str(rng.randrange(0, 12)), rng.choice(['up', 'down'])]])
    elif uid in (o.CHAT1, o.CHAT2, o.CHAT3):
        level = (o.CHAT1, o.CHAT2, o.CHAT3).index(uid) + 1
        args = [_ops('ChatEventAggregator', [1], []), _ops('ChatEventAggregator', [3], [('recordEvent', 1, 'al', 'c1'), ('recordEvent', 2, 'bo', 'c1'),
                                                                                     ('getUserCount', 3, 'al'), ('getUserCount', 4, 'al')])]
        args += [_chat(rng, level, rng.randrange(1, 25)) for _ in range(250)]
    elif uid == o.PWD:
        args = [[[], []], [['a'], ['a']], [['a'], ['b']], [['b'], ['a']], [['z'], ['a']], [['abc', 'abc'], ['abcd', 'acd']]]
        for _ in range(250):
            k = rng.randrange(0, 4); al = rng.choice(['ab', 'abc', 'xyza'])
            args.append([[''.join(rng.choice(al) for _ in range(rng.randrange(1, 9))) for _ in range(k)],
                         [''.join(rng.choice(al) for _ in range(rng.randrange(1, 5))) for _ in range(k)]])
    elif uid == o.CPRIME:
        args = [[n] for n in [1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 19, 23, 37, 101, 113, 197, 199, 911, 1193, 999331, 999999937, 10**9, 2 ** 29, 3779, 7793, 11939, 19391, 37199, 71993, 93911, 193939, 331999, 919393, 939391, 993319, 999331, 993331]]
        for _ in range(200): args.append([rng.randrange(1, rng.choice([100, 10**4, 10**6, 10**9]) + 1)])
    elif uid == o.ALLOC:
        args = [[1, []], [1, [['store', '0', '1'], ['store', '0', '1'], ['free', '0', '1'], ['free', '0', '1']]],
                [5, [['store', '3', '4'], ['store', '0', '1'], ['free', '4', '2'], ['store', '2', '2']]]]
        for _ in range(250):
            t = rng.randrange(1, 13)
            args.append([t, [[rng.choice(['store', 'store', 'free']), str(rng.randrange(t)), str(rng.randrange(1, t + 1))] for _ in range(rng.randrange(0, 12))]])
    elif uid == o.COINS:
        args = [[0, [5], [7]], [0, [5, 0], [0, 9]], [1, [0, 0, 0], [1, 2, 3]], [10**9, [0], [10**9]]]
        for _ in range(250):
            n = rng.randrange(1, 11)
            args.append([rng.randrange(0, 4), [rng.randrange(0, 4) for _ in range(n)], [rng.randrange(0, 10) for _ in range(n)]])
    elif uid == o.COLLATZ:
        args = [[n] for n in [1, 2, 3, 6, 7, 27, 97, 871, 77031, 837799, 8400511, 10**7, 9999999]]
        for _ in range(200): args.append([rng.randrange(1, rng.choice([100, 10**4, 10**7]) + 1)])
    elif uid == o.HOUSES:
        args = [[1, 1, 0, 0], [1, 3, 0, 1], [2, 1, 0, 0], [2, 2, 0, 1], [3, 3, 1, 1], [10**9, 10**9, 0, 10**9 - 1], [10**9, 2, 1, 1]]
        for _ in range(250):
            k = rng.randrange(1, 6)
            args.append([rng.choice([rng.randrange(1, 8), rng.randrange(1, 10**9 + 1)]), k, rng.randrange(k), rng.randrange(k)])
    elif uid == o.LOAD:
        args = [[[], []], [[['s1', 0]], []], [[['s1', 5]], [[0, 's1', 'LIGHT'], [60, 's1', 'HEAVY'], [121, 's1', 'STANDARD'], [5, 'zz', 'HEAVY']]],
                [[['a', 1], ['b', 2]], [[7, 'a', 'LIGHT'], [7, 'a', 'LIGHT'], [86399, 'b', 'HEAVY']]]]
        for _ in range(250):
            servers = [[s, rng.randrange(0, 10)] for s in rng.sample(['s1', 's2', 's3', 'web-1'], rng.randrange(0, 4))]
            reqs = [[rng.randrange(0, 300), rng.choice(['s1', 's2', 's3', 'web-1', 'x']), rng.choice(['LIGHT', 'STANDARD', 'HEAVY'])] for _ in range(rng.randrange(0, 12))]
            args.append([servers, reqs])
    elif uid == o.BED:
        args = [[[], []], [['Studio apartment'], [1]], [['Spacious 1-bedroom'], [0]], [['one bedroom, not a studio'], [1]], [['2 bedrooms'], [0]],
                [['1BR near park', 'studios', 'cozy 1 bedroom!'], [0, 1, 0]], [['x1br', 'studio1'], [0, 1]]]
        for _ in range(250):
            k = rng.randrange(0, 6)
            args.append([[_desc(rng) for _ in range(k)], [rng.randrange(2) for _ in range(k)]])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.BSV:
        n = 100000; arr = [i // 2 for i in range(n)]  # each value v at indices 2v, 2v+1
        out.append(([arr, 31337], 62674))
        out.append(([[2 * i for i in range(n)], 2 * 777 + 1], 777))
        out.append(([[5] * n, 4], -1))
    elif uid == o.BTC:
        s = 'a' * 50000 + 'b' * 50000  # two leaves, equal counts: 'a' (lower id) left
        out.append(([s], {'ch': '#', 'count': 100000, 'left': {'ch': 'a', 'count': 50000, 'left': None, 'right': None},
                          'right': {'ch': 'b', 'count': 50000, 'left': None, 'right': None}}))
        # 52 letters of near-equal counts; expected from the independent re-sorting reference
        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        s2 = ''.join(alpha[i % 52] for i in range(100000))
        out.append(([s2], o.ref_btc(s2)))
    elif uid == o.TRANS:
        n = 100000; logs = [[str(n - i), 'u' + str(i % 1000), '/r' + str((n - i) % 7)] for i in range(n)]
        # user u has timestamps n-i for i = u (mod 1000): 100 entries each; resource '/r' + (t % 7)
        out.append(([logs], o.ref_trans(logs)))
        logs2 = [[str(i), 'solo', 'p'] for i in range(n)]
        out.append(([logs2], [['START', 'p', 1], ['p', 'END', 1], ['p', 'p', n - 1]]))
    elif uid == o.CAKE:
        n = 100000
        out.append(([[10**9, 10**9, 10**9], [[1, 2, 3]] * n], [True] * n))
        out.append(([[50000, 10**9, 0], [[1, 0, 0]] * n], [True] * 50000 + [False] * 50000))
    elif uid in (o.EQ1, o.EQ2, o.EQ3):
        n = 20000  # chain v0 = 1, v_i = v_{i-1} + 1 (+ 0 - 0 for levels 2-3): v_{n-1} = n; listed in reverse order
        sub = '' if uid == o.EQ1 else ' - 0'
        lines = ['v%d = v%d + 1%s' % (i, i - 1, sub) for i in range(n - 1, 0, -1)] + ['v0 = 1']
        out.append(([['v%d' % (n - 1)] + lines], n))
        if uid == o.EQ3:
            cyc = ['v%d = v%d + 1' % (i, (i + 1) % n) for i in range(n)]
            out.append(([['v0'] + cyc], None))
    elif uid == o.WAIT:
        n = 100000
        # all equal h: task i finishes at (h-1)*n + i + 1; waiting = sum(i+1) + n*(h-1)*n - n*h... computed exactly below
        h = 10**4; total = sum((h - 1) * n + i + 1 - h for i in range(n))
        out.append(([[h] * n], total))
        out.append(([[1] * n], n * (n - 1) // 2))
    elif uid == o.ELEV:
        n = 100000; ev = [[str(10**8 + i), 'down'] for i in range(n)]
        out.append(([ev, ['100000000', 'down']], 0))
        out.append(([ev[:-1] + [['999999999', 'idle']], ['0', 'up']], n - 1))
    elif uid in (o.CHAT1, o.CHAT2, o.CHAT3):
        level = (o.CHAT1, o.CHAT2, o.CHAT3).index(uid) + 1
        m = 100; calls, exp = [], [None]
        for t in range(10000):  # one event per second by user u(t%10) in chat c(t%3)
            calls.append(('recordEvent', t, 'u' + str(t % 10), 'c' + str(t % 3))); exp.append(None)
        T = 9999
        for _ in range(5000): calls.append(('getUserCount', T, 'u3')); exp.append(10)
        if level >= 2:
            for _ in range(5000): calls.append(('getChatCount', T, 'c0')); exp.append(sum(1 for t in range(T - m + 1, T + 1) if t % 3 == 0))
        if level >= 3:
            for _ in range(5000): calls.append(('getChatUserCount', T, 'c1')); exp.append(len({t % 10 for t in range(T - m + 1, T + 1) if t % 3 == 1}))
        out.append((_ops('ChatEventAggregator', [m], calls), exp))
        big = _ops('ChatEventAggregator', [10**9], [('recordEvent', t, 'u' + str(t % 7), 'c0') for t in range(20000)] + [('getUserCount', 20000, 'u0')])
        out.append((big, [None] + [None] * 20000 + [len(range(0, 20000, 7))]))
    elif uid == o.PWD:
        new = 'ab' * 50000; old = 'bc' * 25000  # 'a'->'b', 'b'->'c': each 'ab' pair can supply 'bc'
        out.append(([[new], [old]], ['YES']))
        out.append(([[new], ['z' + 'a' * 99999]], ['NO']))
        out.append(([['z' * 10] * 10000, ['a' * 5] * 10000], ['YES'] * 10000))
    elif uid == o.CPRIME:
        for n in (999999937, 999331, 193939, 999999999):
            out.append(([n], o.ref_cprime(n)))
    elif uid == o.ALLOC:
        t = 2000; reqs = [['store', str((7 * i) % t), '1'] for i in range(t)]  # fills every slot exactly once
        exp = []
        used = set()
        for i in range(t):
            p = (7 * i) % t
            while p in used: p = (p + 1) % t
            used.add(p); exp.append(p)
        out.append(([t, reqs], exp))
        reqs2 = [['store', '0', '1000'], ['store', '1500', '1000']] + [['store', str(i), '999'] for i in range(1998)]
        out.append(([t, reqs2], [0, 1000] + [-1] * 1998))
    elif uid == o.COINS:
        n = 700
        out.append(([0, [n] + [0] * (n - 1), [0] + [1] * (n - 1)], n - 1))
        out.append(([n, [10**4] * n, [10**9] * n], n * 10**9))
        out.append(([0, [0] * n, [1] * n], 1))  # no energy anywhere: only house 0 is reachable
    elif uid == o.COLLATZ:
        out.append(([8400511], 685))
        out.append(([9999999], o.ref_collatz(9999999)))
    elif uid == o.HOUSES:
        out.append(([10**9, 10**9, 5, 5], o.ref_houses(10**9, 10**9, 5, 5)))
    elif uid == o.LOAD:
        servers = [['s' + str(i), i] for i in range(1000)]
        reqs = [[(i // 1000) * 61, 's' + str(i % 1000), 'HEAVY'] for i in range(100000)]  # 100 per server, 61 s apart: no bursts
        out.append(([servers, reqs], [['s' + str(i), i + 100 * 6] for i in range(1000)]))
        reqs2 = [[0, 's0', 'LIGHT']] * 100000
        out.append(([servers[:1], reqs2], [['s0', 100000 * (1 + 3)]]))
    elif uid == o.BED:
        out.append(([['Bright studio, ' + 'x' * 400] * 10000, [1] * 10000], [0] * 10000))
        out.append(([['one - bedroom ' * 35] * 10000, [0] * 10000], [1] * 10000))
    return out
