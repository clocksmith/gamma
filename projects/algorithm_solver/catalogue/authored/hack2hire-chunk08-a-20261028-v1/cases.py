"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h08a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _pay(rng):
    rows, payments = [], []
    for i in range(rng.randrange(0, 9)):
        pid = 'p%d' % i; amt = rng.choice([1, 5, 10, 100, 1000000000])
        rows.append([pid, 'PAYMENT', rng.choice(['CREDIT', 'CREDIT_CARD', 'PAYPAL', 'DEBIT', 'GIFT', 'A']), '', str(rng.choice([0, 1, 2, 5, 9])), str(amt)])
        payments.append([pid, amt])
    for j in range(rng.randrange(0, 6)):
        if not payments: break
        p = rng.choice(payments)
        if p[1] < 1: continue
        x = rng.randrange(1, p[1] + 1) if p[1] < 50 else rng.choice([1, p[1] // 2, p[1]])
        p[1] -= x
        rows.append(['r%d' % j, 'REFUND', '', p[0], str(rng.randrange(0, 10)), str(x)])
    rng.shuffle(rows)
    total = sum(int(r[5]) for r in rows if r[1] == 'PAYMENT')
    return [rows, rng.choice([1, 7, 50, 1000, total, total + 3, rng.randrange(0, total + 2), rng.randrange(0, total + 2)])]


def _name(rng, words, width):
    return ' '.join(''.join(rng.choice(words)) for _ in range(rng.randrange(1, width)))


def _pel(rng):
    calls, now = [], 0
    keys = ['a', 'b', 'c', 'd', 'e', 'f']
    for _ in range(rng.randrange(1, 25)):
        now += rng.choice([0, 0, 1, 2, 5])
        if rng.random() < 0.5: calls.append(('get', rng.choice(keys), now))
        else: calls.append(('set', rng.choice(keys), rng.randrange(0, 50), rng.randrange(0, 4), now + rng.choice([-1, 0, 1, 2, 3, 10, 100]) if now else rng.choice([0, 1, 3, 10]), now))
    return _ops('PriorityExpiryLRUCache', [rng.randrange(1, 5)], calls)


def _pbs(rng):
    nbs = ['n1', 'n2', 'Up']
    props = [['%s%d' % (rng.choice('abcxyz'), i), rng.choice(nbs), str(rng.choice([1, 2, 3, 4, 5, 8, 10, 1000]))] for i in range(rng.randrange(0, 12))]
    rng.shuffle(props)
    calls = [('book', rng.choice(nbs + ['zz']), rng.choice([1, 2, 3, 5, 7, 10, 13, 20, 1001])) for _ in range(rng.randrange(1, 8))]
    return _ops('BookingSystem', [props], calls)


def _ri(rng):
    start = rng.randrange(-10, 11); sign = rng.choice([-1, 1]); end = start + sign * rng.randrange(0, 15)
    step = rng.choice([1, 2, 3, 7, 1000000000]) * (sign if rng.random() < 0.8 else -sign)
    n = _o.range_length(start, end, step); calls, used = [], 0
    for _ in range(rng.randrange(0, 15)):
        if used < n and rng.random() < 0.5: calls.append(('next',)); used += 1
        else: calls.append(('hasNext',))
    return _ops('RangeIterator', [start, end, step], calls)


def _tele(rng):
    n, m = rng.randrange(1, 6), rng.randrange(1, 7)
    g = [[1 if rng.random() < 0.15 else 0 for _ in range(m)] for _ in range(n)]
    g[0][0] = 0; g[n - 1][m - 1] = 0
    empty = [(r, c) for r in range(n) for c in range(m) if not g[r][c] and (r, c) not in ((0, 0), (n - 1, m - 1))]
    rng.shuffle(empty)
    ent = empty[:rng.randrange(0, len(empty) // 2 + 1)]
    exits = [x for x in empty if x not in ent] + [(0, 0), (n - 1, m - 1)]
    tps = [[r, c] + list(rng.choice(exits)) for r, c in ent]
    tps = [t for t in tps if (t[0], t[1]) != (t[2], t[3])]
    if rng.random() < 0.5:  # a ladder: the last cell of each row teleports into the next row
        g = [[1 if rng.random() < 0.05 else 0 for _ in range(m)] for _ in range(n)]; g[0][0] = 0; g[n - 1][m - 1] = 0
        tps = [[r, m - 1, r + 1, rng.randrange(0, max(1, m - 1))] for r in range(n - 1) if m > 1]
        for r1, c1, r2, c2 in tps: g[r1][c1] = 0; g[r2][c2] = 0
        tps = [t for t in tps if (t[0], t[1]) != (0, 0) and (t[2], t[3]) not in {(x[0], x[1]) for x in tps}]
    return [g, tps]


def _bot(rng):
    calls, now = [], 0
    for _ in range(rng.randrange(1, 25)):
        now += rng.choice([0, 0, 1, 1, 2, 4])
        calls.append(('isBot', rng.choice(['1.2.3.4', '10.0.0.1', '8']), now))
    return _ops('DetectionSystem', [rng.randrange(1, 4), rng.choice([1, 2, 3, 5, 1000000000])], calls)


def _rbs(rng, uid):
    rows = []
    for i in range(rng.randrange(0, 10)):
        rows.append(['t%d' % rng.randrange(1000) + 'x%d' % i, rng.choice(['u1', 'u2', 'U', 'w_9']), rng.choice(['', '0', '5', '100', '1000000000']),
                     rng.choice(['', '', '0', '7', '100', '1000000000']), str(rng.choice([0, 1, 2, 2, 5, 9]))])
    rng.shuffle(rows)
    return [rows, rng.choice([0, 1, 2, 5, 9, 10])] if uid == _o.RBS2 else [rows]


def _boot(rng, uid):
    while True:
        n = rng.randrange(1, 9)
        prog = ['%s %s' % (rng.choice(['plus', 'next', 'jump', 'jump']), rng.choice(['0', '1', '-1', '+2', '-3', '4', '+1000000', '-1000000'])) for _ in range(n)]
        if uid == _o.BOOT1 or _o.run_boot(_o.parse_boot(prog))[0] != 'end': return [prog]


def _tbl(rng):
    nr, nc = rng.randrange(1, 5), rng.randrange(1, 5); calls = []
    for _ in range(rng.randrange(1, 20)):
        op = rng.choice(['selectTable', 'selectRow', 'selectCell', 'setColor', 'setColor', 'getColor', 'getColor'])
        if op == 'selectTable': calls.append((op,))
        elif op == 'selectRow': calls.append((op, rng.randrange(nr)))
        elif op in ('selectCell', 'getColor'): calls.append((op, rng.randrange(nr), rng.randrange(nc)))
        else: calls.append((op, rng.choice(['red', 'blue', '#00ff00', 'z'])))
    return _ops('Table', [nr, nc], calls)


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.PAY:
        args = [[[], 0], [[], 5], [[['p', 'PAYMENT', 'DEBIT', '', '3', '10']], 4],
                [[['a', 'PAYMENT', 'PAYPAL', '', '1', '5'], ['b', 'PAYMENT', 'CREDIT', '', '0', '5'], ['c', 'PAYMENT', 'CREDIT_CARD', '', '9', '5'], ['r', 'REFUND', '', 'b', '2', '5']], 7],
                [[['x', 'PAYMENT', 'ZED', '', '1', '3'], ['y', 'PAYMENT', 'BANK', '', '1', '3'], ['w', 'PAYMENT', 'BANK', '', '1', '3']], 8]]
        args += [_pay(rng) for _ in range(250)]
    elif uid == o.PFP:
        args = [['A'], ['AB'], ['AA'], ['ABBA'], ['ABAB'], ['ABCCBA'], ['AABBAB'], ['ZZZZZZ']]
        for _ in range(250):
            unit = ''.join(rng.choice('ABC') for _ in range(rng.randrange(1, 5)))
            blocks = []
            for _ in range(rng.randrange(1, 7)):
                b = list(unit); rng.shuffle(b); blocks.append(''.join(b))
            s = ''.join(blocks)
            if rng.random() < 0.3:
                i = rng.randrange(len(s)); s = s[:i] + rng.choice('ABD') + s[i + 1:]
            args.append([s])
    elif uid in (o.PS1, o.PS2):
        words = ['a', 'b', 'A', 'B', 'c', 'x', '1']
        for _ in range(250):
            names = [_name(rng, [w * rng.randrange(1, 3) for w in words], 4) for _ in range(rng.randrange(0, 8))]
            names = [' '.join(w[:12] for w in nm.split(' ')) for nm in names]
            prefix = ''.join(rng.choice('abAB1x') for _ in range(rng.randrange(1, 4)))
            if names and rng.random() < 0.7:  # usually a (case-swapped) prefix of some word, so matches are common
                w = rng.choice(rng.choice(names).split(' ')); prefix = w[:rng.randrange(1, len(w) + 1)].swapcase() if rng.random() < 0.5 else w[:rng.randrange(1, len(w) + 1)]
                if uid == o.PS2 and rng.random() < 0.5: prefix += rng.choice('ab1')
            args.append([names, prefix, rng.choice([1, 2, 3, 5, 100])] if uid == o.PS1 else [names, prefix])
        base = [['Ab cd', 'cd Ab', 'ab', 'AB x', 'b ab'], 'ab']
        args = ([base + [2], base + [10], [[], 'q', 1], [['Same Name', 'Same Name', 'same'], 'S', 5]] if uid == o.PS1 else
                [base, [[], 'q'], [['Same Name', 'Same Name', 'same'], 'sAm'], [['abc abd', 'xab'], 'abcz']]) + args
    elif uid == o.PEL:
        args = [_ops('PriorityExpiryLRUCache', [1], [('get', 'a', 0)]),
                _ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 5, 100, 0), ('set', 'b', 2, 1, 100, 0), ('set', 'c', 3, 9, 100, 1), ('get', 'a', 1), ('get', 'b', 1), ('get', 'c', 2)]),
                _ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 5, 3, 0), ('set', 'b', 2, 1, 100, 0), ('get', 'a', 3), ('set', 'c', 3, 0, 4, 3), ('set', 'd', 4, 0, 9, 4), ('get', 'b', 4), ('get', 'd', 5)]),
                _ops('PriorityExpiryLRUCache', [2], [('set', 'a', 1, 1, 9, 0), ('set', 'b', 2, 1, 9, 0), ('get', 'a', 1), ('set', 'c', 3, 1, 9, 1), ('get', 'a', 1), ('get', 'b', 1)])]
        args += [_pel(rng) for _ in range(250)]
    elif uid == o.PQ:
        args = [[[]], [[1]], [[5]], [[2, 2, 3, 1]], [[1, 1, 1]], [[3, 2, 1]], [[1000000000, 1]]]
        for _ in range(250): args.append([[rng.choice([1, 2, 3, 4, 5, 8, 1000000000]) for _ in range(rng.randrange(0, 12))]])
    elif uid == o.PBS:
        args = [_ops('BookingSystem', [[]], [('book', 'a', 1)]),
                _ops('BookingSystem', [[['p1', 'a', '3'], ['p2', 'a', '5'], ['p3', 'a', '2'], ['p4', 'b', '9']]], [('book', 'a', 4), ('book', 'a', 4), ('book', 'a', 1), ('book', 'b', 10)]),
                _ops('BookingSystem', [[['z', 'n', '4'], ['y', 'n', '4'], ['x', 'n', '8']]], [('book', 'n', 8), ('book', 'n', 8), ('book', 'n', 1)])]
        args += [_pbs(rng) for _ in range(250)]
    elif uid == o.RUP1:
        args = [[[], []], [['a'], []], [['a', 'b'], [0, 0]], [['a', 'b', 'c'], [5, 7]], [['a', 'b', 'c', 'd'], [1000000000, 3, 2, 0]], [['x', 'x'], [1, 1]]]
        for _ in range(250):
            n = rng.randrange(0, 12)
            args.append([['u%d' % rng.randrange(20) for _ in range(n)], [rng.choice([0, 1, 2, 3, 7, rng.randrange(10**9 + 1)]) for _ in range(2 * (n // 2))]])
    elif uid == o.RUP2:
        args = [[[]], [[['a', 'g']]], [[['a', 'g'], ['b', 'g']]], [[['a', 'g'], ['b', 'h']]], [[['a', 'B'], ['b', 'A'], ['c', 'A'], ['d', 'C'], ['e', 'B']]]]
        for _ in range(250):
            args.append([[['u%d' % i, rng.choice(['g1', 'g2', 'g3', 'G', 'z'][:rng.randrange(1, 6)])] for i in range(rng.randrange(0, 14))]])
    elif uid == o.RI:
        args = [_ops('RangeIterator', [0, 0, 1], [('hasNext',)]), _ops('RangeIterator', [0, 3, 1], [('hasNext',), ('next',), ('next',), ('next',), ('hasNext',)]),
                _ops('RangeIterator', [5, -1, -2], [('next',), ('next',), ('next',), ('hasNext',)]), _ops('RangeIterator', [0, 10, -1], [('hasNext',)]),
                _ops('RangeIterator', [-1000000000, 1000000000, 1000000000], [('next',), ('next',), ('hasNext',)])]
        args += [_ri(rng) for _ in range(250)]
    elif uid == o.TELE:
        args = [[[[0]], []], [[[0, 0, 0]], []], [[[0, 1, 0]], []], [[[0, 0], [0, 0]], []], [[[0, 0, 0], [0, 0, 0]], [[0, 2, 1, 0]]],
                [[[0, 0, 0], [0, 0, 0]], [[0, 1, 0, 0]]], [[[0, 0, 0, 0], [0, 1, 0, 0]], [[0, 2, 1, 2]]], [[[0, 0], [0, 0]], [[0, 1, 1, 0]]]]
        args += [_tele(rng) for _ in range(250)]
    elif uid == o.BOT:
        args = [_ops('DetectionSystem', [1, 1], [('isBot', '1', 0), ('isBot', '1', 0), ('isBot', '1', 1)]),
                _ops('DetectionSystem', [2, 3], [('isBot', '1.1', 1), ('isBot', '2', 2), ('isBot', '1.1', 3), ('isBot', '1.1', 3), ('isBot', '1.1', 4), ('isBot', '1.1', 6)])]
        args += [_bot(rng) for _ in range(250)]
    elif uid == o.RFI:
        args = [[[], ''], [['a'], ''], [['toast', 'tea', 'oats'], 'toast'], [['aa', 'a', 'b'], 'ab'], [['zz'], 'zzz']]
        for _ in range(250):
            args.append([[''.join(rng.choice('abcz') for _ in range(rng.randrange(1, 6))) for _ in range(rng.randrange(0, 8))],
                         ''.join(rng.choice('abcdz') for _ in range(rng.randrange(0, 25)))])
    elif uid in (o.RBS1, o.RBS2, o.RBS3):
        base = [['t2', 'u1', '100', '', '5'], ['t1', 'u1', '', '30', '5'], ['t3', 'u2', '0', '50', '1'], ['t4', 'u1', '', '', '0'], ['t5', 'u2', '60', '', '2']]
        args = [[[]], [base]] if uid != o.RBS2 else [[[], 0], [base, 0], [base, 1], [base, 5], [base, 4]]
        args += [_rbs(rng, uid) for _ in range(250)]
    elif uid in (o.BOOT1, o.BOOT2):
        args = [[['jump 0']], [['plus 3', 'jump -1']], [['next 0', 'plus 1', 'jump -2']], [['jump 2', 'plus 5', 'jump -1']], [['plus -4', 'jump +5']]]
        if uid == o.BOOT1: args += [[['plus 1']], [['next 0', 'plus 2']]]
        args += [_boot(rng, uid) for _ in range(250)]
    elif uid == o.RSD:
        args = [['?', 0, 0], ['?', 5, 4], ['?', 5, 5], ['5', 5, 0], ['5', 4, 9], ['??', 18, 9], ['?1?', 3, 1], ['?1?', 4, 1], ['0?0', 0, 9]]
        for _ in range(250):
            pat = ''.join(rng.choice('0123456789???') for _ in range(rng.randrange(1, 8)))
            cap = rng.randrange(0, 10)
            while (cap + 1) ** pat.count('?') > 20000: pat = pat.replace('?', '1', 1)
            hi = sum(int(c) for c in pat if c != '?') + cap * pat.count('?')
            lo = sum(int(c) for c in pat if c != '?')
            args.append([pat, rng.choice([lo, hi, hi + 1, rng.randrange(0, 70), rng.randrange(lo, hi + 1), rng.randrange(lo, hi + 1), rng.randrange(lo, hi + 1)]), cap])
    elif uid == o.TBL:
        args = [_ops('Table', [1, 1], [('getColor', 0, 0)]), _ops('Table', [2, 3], [('setColor', 'red'), ('getColor', 1, 2)]),
                _ops('Table', [2, 3], [('selectRow', 1), ('setColor', 'red'), ('selectCell', 1, 0), ('setColor', 'blue'), ('selectTable',), ('getColor', 1, 0), ('setColor', 'z'),
                                       ('getColor', 1, 1), ('selectRow', 0), ('setColor', 'red'), ('getColor', 0, 2), ('getColor', 1, 2)])]
        args += [_tbl(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.PAY:
        types = ['PAYPAL', 'CREDIT', 'DEBIT', 'CREDIT_CARD']; n = 50000
        tx = [['p%05d' % i, 'PAYMENT', types[i % 4], '', str(i), '1000'] for i in range(n)]
        for i in range(0, n, 2):  # two refunds of 200 on every even payment: 600 left there, 1000 on odd ones
            tx += [['ra%05d' % i, 'REFUND', '', 'p%05d' % i, str(n + i), '200'], ['rb%05d' % i, 'REFUND', '', 'p%05d' % i, str(n + i), '200']]
        tx.reverse()
        order = []  # CREDIT (i%4==1), CREDIT_CARD (3), PAYPAL (0), then DEBIT (2); each newest first
        for r in (1, 3, 0, 2): order += [i for i in range(n - 1, -1, -1) if i % 4 == r]
        avail = lambda i: 1000 if i % 2 else 600  # noqa: E731
        out.append(([tx, 10**14], [['p%05d' % i, avail(i)] for i in order]))
        want = 12500 * 1000 + 7 * 1000 + 500
        part = [['p%05d' % i, avail(i)] for i in order[:12507]] + [['p%05d' % order[12507], 500]]
        out.append(([tx, want], part))
    elif uid == o.PFP:
        n = 100000
        divisors = [d for d in range(1, n + 1) if n % d == 0]
        out.append((['AB' * (n // 2)], [d for d in divisors if d % 2 == 0]))
        out.append((['Q' * n], divisors))
        out.append((['A' * (n - 1) + 'B'], [n]))
    elif uid == o.PS1:
        n = 100000
        name = lambda i: ' '.join(['aa'] * (i % 10) + ['Shop%05d' % i])  # noqa: E731
        names = [name(i) for i in range(n)]
        ranked = [name(i) for p in range(10) for i in range(p, n, 10)]
        out.append(([names, 'sH', 100], ranked[:100]))
        out.append(([names, 'shop', n], ranked))
        out.append(([names, 'aa', n], [name(i) for i in range(n) if i % 10]))  # every 'aa' match is at word 0; ordered by name
        out[-1] = (out[-1][0], sorted(out[-1][1]))
    elif uid == o.PS2:
        letters = 'abcdefghijkl'
        names = ['q%04d %s' % (i, letters[:i % 12 + 1]) for i in range(3000)]
        exp = [[nm for i, nm in enumerate(names) if i % 12 + 1 >= L] for L in range(1, 13)] + [[], []]
        out.append(([names, 'ABCDEFGHIJKLmn'], exp))
        same = ['Aa Aa Aa Aa Aa'] * 3000
        out.append(([same, 'aA'], [same, same]))
        out.append(([same, 'aaaaaaaaaaaaaaaaaaaa'], [same, same] + [[]] * 18))
    elif uid == o.PEL:
        c = 1000; calls = []; exp = [None]
        for j in range(c): calls.append(('set', 'p%d' % j, j, j, 2 * 10**9, 0)); exp.append(None)
        m = 48000
        for i in range(m): calls.append(('set', 'n%d' % i, i, 10**9, 2 * 10**9, 1)); exp.append(None)  # evicts p0..p999 by priority, then oldest n
        for j in range(c): calls.append(('get', 'p%d' % j, 2)); exp.append(-1)
        for i in range(m - c, m): calls.append(('get', 'n%d' % i, 2)); exp.append(i)
        out.append((_ops('PriorityExpiryLRUCache', [c], calls), exp))
        calls = []; exp = [None]
        for j in range(c): calls.append(('set', 'e%d' % j, j, 0, j + 1, 0)); exp.append(None)
        for j in range(c): calls.append(('set', 'f%d' % j, j, 0, 2 * 10**9, 5000)); exp.append(None)  # each insert evicts the earliest-expired e
        for r in range(48):
            for j in range(c): calls.append(('get', 'e%d' % j if r % 2 else 'f%d' % j, 6000)); exp.append(-1 if r % 2 else j)
        out.append((_ops('PriorityExpiryLRUCache', [c], calls), exp))
        calls = [('set', 'k%d' % i, i, i % 3, 2 * 10**9, i) for i in range(50000)]; exp = [None] * 50001
        for i in range(50000): calls.append(('get', 'k%d' % i, 50000)); exp.append(-1 if i < 49999 else 49999)
        out.append((_ops('PriorityExpiryLRUCache', [1], calls), exp))
    elif uid == o.PQ:
        n = 100000
        out.append(([[10**9] * n], list(range(n, -1, -1))))
        out.append(([[n - i for i in range(n)]], [n - 2 * t for t in range(n // 2 + 1)]))
        out.append(([[1] * n], [n, 0]))
    elif uid == o.PBS:
        props, calls, exp = [], [], [None]
        for k in range(25):
            nb = 'nb%02d' % k
            props += [['k%02dp%02d' % (k, j), nb, '10'] for j in range(12)]
        for k in range(25):
            nb = 'nb%02d' % k
            calls += [('book', nb, 55), ('book', nb, 55), ('book', nb, 55), ('book', nb, 20000)]
            exp += [['k%02dp%02d' % (k, j) for j in range(6)], ['k%02dp%02d' % (k, j) for j in range(6, 12)], [], []]
        calls += [('book', 'nb00', 1)] * 200; exp += [[]] * 200
        out.append((_ops('BookingSystem', [props], calls), exp))
        props, calls, exp = [], [], [None]
        for k in range(25):
            nb = 'm%02d' % k
            props += [['m%02dp%02d' % (k, j), nb, str(j + 1)] for j in range(12)]
            calls += [('book', nb, 12)] * 7  # 12 alone, then pairs summing to exactly 12 (1+11, 2+10, ..., 5+7), then only 6 is left
            exp += [['m%02dp11' % k]] + [['m%02dp%02d' % (k, j), 'm%02dp%02d' % (k, 10 - j)] for j in range(5)] + [[]]
        out.append((_ops('BookingSystem', [props], calls), exp))
        props = [['h%02d' % j, 'all', '1000'] for j in range(12)]
        calls = [('book', 'all', 6000)] * 2 + [('book', 'all', 6000 + i) for i in range(297)]
        out.append((_ops('BookingSystem', [props], calls), [None, ['h%02d' % j for j in range(6)], ['h%02d' % j for j in range(6, 12)]] + [[]] * 297))
    elif uid == o.RUP1:
        n = 100000
        u = ['u%05d' % i for i in range(n)]
        out.append(([u, [0] * n], [[u[0], u[n - 1]]] + [[u[n - 2 * k], u[n - 2 * k - 1]] for k in range(1, n // 2)]))
        m = n - 1
        out.append(([u[:m], [m - k - 1 for k in range(m - 1)]], [[u[m - 1 - 2 * j], u[m - 2 - 2 * j]] for j in range(m // 2)] + [[u[0]]]))
    elif uid == o.RUP2:
        users = [['a%05d' % i, 'A'] for i in range(50000)] + [['b%05d' % i, 'B'] for i in range(30000)] + [['c%05d' % i, 'C'] for i in range(20000)]
        exp = [['a%05d' % i, 'b%05d' % i] for i in range(10000)]
        for j in range(40000):
            exp.append(['a%05d' % (10000 + j), 'b%05d' % (10000 + j // 2) if j % 2 == 0 else 'c%05d' % ((j - 1) // 2)])
        out.append(([users], exp))
        out.append(([[['u%05d' % i, 'g%05d' % i] for i in range(100000)]], [['u%05d' % i, 'u%05d' % (i + 1)] for i in range(0, 100000, 2)]))
        out.append(([[['u%05d' % i, 'same'] for i in range(100000)]], []))
    elif uid == o.RI:
        calls = [('hasNext',), ('next',)] * 50000
        exp = [None] + [x for i in range(50000) for x in (True, i * 10000)]
        out.append((_ops('RangeIterator', [0, 10**9, 10**4], calls), exp))
        calls = [('hasNext',), ('next',), ('hasNext',), ('next',)] + [('hasNext',)] * 99996
        out.append((_ops('RangeIterator', [10**9, -10**9, -10**9], calls), [None, True, 10**9, True, 0] + [False] * 99996))
        out.append((_ops('RangeIterator', [-10**9, 10**9, 1], [('next',)] * 100000), [None] + [-10**9 + i for i in range(100000)]))
    elif uid == o.TELE:
        s = 316
        g = [[0] * s for _ in range(s)]
        tps = [[r, s - 1, r + 1, 0] for r in range(s - 1)]
        out.append(([g, tps], (s - 1) * s))
        out.append(([g, tps[:-1] + [[s - 1, s - 2, 0, 1]]], -1))  # last row teleports back into row 0: a loop
        out.append(([[[0] * 100000], []], 99999))
        row = [0] * 100000; row[50000] = 1
        out.append(([[row], []], -1))
        out.append(([[[0] * 20001], [[0, c, 0, c + 1] for c in range(1, 20000, 2)]], 10000))  # 10000 teleports: every move also skips a cell for free
    elif uid == o.BOT:
        calls = [('isBot', '1.1.1.1', i // 2) for i in range(100000)]

        def count(i):
            t = i // 2
            return i - max(0, 2 * (t - 9)) + 1
        out.append((_ops('DetectionSystem', [3, 10], calls), [None] + [count(i) > 3 for i in range(100000)]))
        calls = [('isBot', '10.%d.%d.%d' % (x // 65536, x // 256 % 256, x % 256), i) for i in range(100000) for x in [i % 50000]]
        out.append((_ops('DetectionSystem', [1, 10**9], calls), [None] + [i >= 50000 for i in range(100000)]))
        out.append((_ops('DetectionSystem', [100000, 1], [('isBot', '9', 7)] * 100000), [None] + [False] * 100000))
    elif uid == o.RFI:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        ing = ''.join(ch * 4 * (k + 1) for k, ch in enumerate(letters))
        recipes = [letters[i % 26] * (i % 100 + 1) for i in range(10000)]
        out.append(([recipes, ing], sum(1 for i in range(10000) if i % 100 + 1 <= 4 * (i % 26 + 1))))
        out.append(([['abcdefghij' * 10] * 10000, 'abcdefghij' * 10], 10000))
        out.append(([['z'] * 100000, 'a' * 100000], 0))
    elif uid in (o.RBS1, o.RBS2, o.RBS3):
        n = 100000
        tx = [['t%05d' % i, 'u%03d' % (i % 1000), '100', '' if i % 2 == 0 else '30', str(i)] for i in range(n)]
        tx.reverse()
        if uid == o.RBS1: out.append(([tx], [['u%03d' % u, 10000 if u % 2 == 0 else 7000] for u in range(1000)]))
        if uid == o.RBS2:
            out.append(([tx, 49999], [['u%03d' % u, 5000 if u % 2 == 0 else 3500] for u in range(1000)]))
            out.append(([tx, 999], [['u%03d' % u, 100 if u % 2 == 0 else 70] for u in range(1000)]))
        if uid == o.RBS3:
            out.append(([tx], [['u%03d' % u, 10000, 10000] if u % 2 == 0 else ['u%03d' % u, 7000, 7000] for u in range(1000)]))
            big = [['t%05d' % i, 'z', '1000000000' if i < n // 2 else '', '' if i < n // 2 else '1000000000', str(i)] for i in range(n)]
            out.append(([big[::-1]], [['z', 0, 5 * 10**13]]))
            tied = [['t%05d' % i, 'z', '' if i < n // 2 else '1000000000', '1000000000' if i < n // 2 else '', '0'] for i in range(n)]
            out.append(([tied[::-1]], [['z', 0, 0]]))
    elif uid in (o.BOOT1, o.BOOT2):
        n = 100000
        loop = ['plus 1'] * (n - 1) + ['jump -%d' % (n - 1)]
        if uid == o.BOOT1:
            out.append(([loop], [0, n - 1]))
            out.append(([['next 0'] * n], [-1, 0]))
            out.append(([['jump +2', 'plus 1000000'] * (n // 2)], [-1, 0]))
        else:
            out.append(([loop], [n - 1, n - 1]))
            out.append(([['next 99999'] + ['plus 2'] * (n - 2) + ['jump -99998']], [n - 1, 2 * (n - 2)]))
            out.append(([['jump 0'] * n], [-1, 0]))
            out.append(([['jump +1'] * (n - 1) + ['jump -%d' % (n - 1)]], [n - 1, 0]))
    elif uid == o.RSD:
        n = 100000
        out.append((['?' * n, n, 9], '0' * 88888 + '1' + '9' * 11111))
        out.append((['5' * (n - 1) + '?', 10**6, 9], ''))
        out.append((['?7' * (n // 2), 500000, 3], '37' * (n // 2)))
        out.append((['?' * n, 0, 0], '0' * n))
    elif uid == o.TBL:
        calls = [('selectTable',), ('setColor', 't')]; exp = [None, None, None]
        for i in range(33332):
            calls += [('selectRow', i), ('setColor', 'r%d' % (i % 10)), ('getColor', i, 99999 - i)]; exp += [None, None, 'r%d' % (i % 10)]
        out.append((_ops('Table', [100000, 100000], calls), exp))
        calls = []; exp = [None]
        for i in range(25000):
            calls += [('selectCell', i, i), ('setColor', 'c%d' % (i % 7))]; exp += [None, None]
        calls += [('selectTable',), ('setColor', 't2')]; exp += [None, None]
        for i in range(49998): calls.append(('getColor', i % 25000, i % 25000)); exp.append('t2')
        out.append((_ops('Table', [100000, 100000], calls), exp))
    return out
