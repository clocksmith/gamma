"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h05x_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _hhmm(m):
    return '%02d:%02d' % (m // 60, m % 60)


def _css(rng):
    n = rng.randrange(1, 15)
    pool = rng.choice([[1, 2], [1, 2, 3], [1, 2, 3, 4, 6], [10**9, 5 * 10**8, 2]])
    return [[rng.choice(pool) for _ in range(n)]]


def _dasher(variant):
    def gen(rng):
        marks = [0, 1, 659, 660, 661, 839, 840, 1019, 1020, 1199, 1200, 1438, 1439]
        def pick(): return rng.choice(marks) if rng.random() < 0.4 else rng.randrange(1440)
        rows = []
        for i in range(rng.randrange(0, 9)):
            a = pick(); b = pick()
            a, b = min(a, b), max(a, b)
            oid = ('o' if rng.random() < 0.7 else 'Ord') + str(i)
            finish = 'cancelled' if variant == 3 and rng.random() < 0.3 else 'delivered'
            rows.append((a, 0, oid, 'accepted')); rows.append((b, 1, oid, finish))
        rows.sort(key=lambda r: (r[0], r[1]))
        return [[[_hhmm(r[0]), r[2], r[3]] for r in rows]]
    return gen


def _als(rng):
    calls = []
    for _ in range(rng.randrange(0, 40)):
        x = rng.random()
        if x < 0.5:
            lux = rng.randrange(0, 21) if rng.random() < 0.8 else rng.randrange(0, 100001)
            calls.append(('record', 1 if rng.random() < 0.75 else 0, lux, rng.randrange(0, 11)))
        elif x < 0.7: calls.append(('getLatestLux',))
        else:
            a = rng.randrange(0, 13); calls.append(('getAverageLux', a, rng.randrange(a, 13)))
    return _ops('ALSWrapper', [], calls)


def _cg(rng):
    deck = list(range(52)); rng.shuffle(deck)
    calls = []
    for _ in range(rng.randrange(0, 45)):
        x = rng.random()
        if x < 0.6: calls.append(('playRound',))
        elif x < 0.85: calls.append(('getScore', rng.choice('AB')))
        else: calls.append(('getWinner',))
    return _ops('CardGame', [deck], calls)


def _dcb(rng):
    t, calls = 0, []
    for _ in range(rng.randrange(0, 40)):
        t += rng.choice([0, 0, 1, 1, 2, 3, 6])
        calls.append(('request', t, rng.random() < 0.4, rng.random() < 0.5))
    return _ops('DualCircuitBreaker', [rng.randrange(1, 4), rng.randrange(1, 6)], calls)


def _daw(rng):
    words = [''.join(rng.choice('abc') for _ in range(rng.randrange(1, 5))) for _ in range(rng.randrange(1, 6))]
    subs = []
    for s in '1@$?':
        for c in rng.sample('abc', rng.randrange(0, 4)): subs.append([s, c])
    rng.shuffle(subs)
    tokens = []
    for _ in range(rng.randrange(1, 9)):
        if rng.random() < 0.6:
            w = list(rng.choice(words))
            for i in range(len(w)):
                if rng.random() < 0.4: w[i] = rng.choice('1@$?')
            tokens.append(''.join(w))
        else:
            tokens.append(''.join(rng.choice('abc1@$?') for _ in range(rng.randrange(1, 5))))
    return [words, subs, ' '.join(tokens)]


GEN = {_o.CSS: _css, _o.DP1: _dasher(1), _o.DP2: _dasher(2), _o.DP3: _dasher(3), _o.ALS: _als, _o.CG1: _cg, _o.CG2: _cg,
       _o.DCB: _dcb, _o.DAW: _daw}

_CG1_DECK = [51, 0] + list(range(1, 51))
_CG2_DECK = [12, 0, 13, 26] + [c for c in range(52) if c not in (0, 12, 13, 26)]
HAND = {
    _o.CSS: [[[1, 1, 1]], [[2, 1, 1, 2]], [[3, 1, 2, 3, 3]], [[1, 2]], [[5]], [[1, 1, 1, 1]]],
    _o.DP1: [[[['09:00', 'a', 'accepted'], ['09:10', 'b', 'accepted'], ['09:30', 'a', 'delivered'], ['09:40', 'b', 'delivered']]], [[]],
             [[['10:00', 'x', 'accepted'], ['10:00', 'x', 'delivered']]]],
    _o.DP2: [[[['10:50', 'a', 'accepted'], ['11:10', 'a', 'delivered']]], [[['13:59', 'a', 'accepted'], ['17:01', 'a', 'delivered']]]],
    _o.DP3: [[[['11:00', 'a', 'accepted'], ['11:05', 'b', 'accepted'], ['11:20', 'a', 'cancelled'], ['11:30', 'b', 'delivered']]],
             [[['08:00', 'a', 'accepted'], ['08:30', 'a', 'delivered']]]],
    _o.ALS: [_ops('ALSWrapper', [], [('record', 1, 50, 10), ('record', 0, 999, 20), ('getLatestLux',), ('record', 1, 30, 5), ('getLatestLux',),
                                     ('getAverageLux', 0, 10), ('getAverageLux', 11, 100), ('record', 1, 7, 10), ('getLatestLux',), ('getAverageLux', 10, 10)]),
             _ops('ALSWrapper', [], [('getLatestLux',), ('getAverageLux', 0, 0)])],
    _o.CG1: [_ops('CardGame', [_CG1_DECK], [('playRound',), ('getScore', 'A'), ('getWinner',)] + [('playRound',)] * 26 + [('getScore', 'B'), ('getWinner',)])],
    _o.CG2: [_ops('CardGame', [_CG2_DECK], [('playRound',), ('getScore', 'A'), ('getScore', 'B'), ('playRound',), ('getWinner',)])],
    _o.DCB: [_ops('DualCircuitBreaker', [2, 5], [('request', 0, False, True), ('request', 1, False, True), ('request', 2, True, False), ('request', 3, True, False),
                                                  ('request', 4, True, True), ('request', 6, False, True), ('request', 8, True, True), ('request', 11, True, True),
                                                  ('request', 11, False, False)])],
    _o.DAW: [[['ass', 'hell'], [['@', 'a'], ['$', 's'], ['3', 'e'], ['1', 'l'], ['1', 'i']], '@$$ is h3ll and he11o sh1t a$s'], [['ab'], [], 'a@ ab ab'],
             [['ab'], [], '?b']],
}


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = list(HAND[uid]) + [GEN[uid](rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    n = 100000
    if uid == o.CSS:
        out.append(([[1] * n], n - 2))
        out.append(([[10**9] * n], n - 2))
        # 2 1 1 2 1 1 ... 2: only neighbouring 2s (middle 1 + 1) are stable
        out.append(([[2, 1, 1] * 33333 + [2]], 33333))
        out.append(([list(range(1, n + 1))], 0))
        out.append(([[1, 2] * (n // 2)], 0))
    elif uid in o.DASHER:
        v = o.DASHER[uid]
        ids = ['o' + str(i) for i in range(10000)]
        allday = [['00:00', i, 'accepted'] for i in ids] + [['23:59', i, 'delivered'] for i in ids]
        out.append(([allday], 30 * 10000 * (1439 + (360 if v >= 2 else 0))))
        chain = []
        for m in range(1439): chain += [[_hhmm(m), 'c' + str(m), 'accepted'], [_hhmm(m + 1), 'c' + str(m), 'delivered']]
        chain.sort(key=lambda r: r[0])
        out.append(([chain], 30 * (1439 + (360 if v >= 2 else 0))))
        out.append(([[['12:00', i, 'accepted'] for i in ids] + [['12:00', i, 'delivered'] for i in ids]], 0))
        if v == 3:
            half = [['00:00', i, 'accepted'] for i in ids] + [['23:59', i, 'cancelled' if k % 2 else 'delivered'] for k, i in enumerate(ids)]
            out.append(([half], 30 * 5000 * 1799))
    elif uid == o.ALS:
        calls, want = [], [None]
        for i in range(10000): calls.append(('record', 1, i, 10**6 - i)); want.append(None)
        for _ in range(9999): calls.append(('getAverageLux', 0, 10**6)); want.append(4999)
        out.append((_ops('ALSWrapper', [], calls), want))
        calls, want = [], [None]
        for i in range(9999):
            calls += [('record', 1 if i % 2 == 0 else 0, i, i * 100), ('getLatestLux',)]; want += [None, i if i % 2 == 0 else i - 1]
        out.append((_ops('ALSWrapper', [], calls), want))
        calls, want, total = [], [None], 0
        for i in range(10000):
            total += i % 7
            calls += [('record', 1, i % 7, 500000), ('getAverageLux', 500000, 500000)]; want += [None, total // (i + 1)]
        out.append((_ops('ALSWrapper', [], calls), want))
        calls, want = [], [None]
        for i in range(10000):
            calls += [('record', 1, 7, (i * 7919) % 1000001), ('getAverageLux', 0, 10**6)]; want += [None, 7]
        out.append((_ops('ALSWrapper', [], calls), want))
    elif uid in (o.CG1, o.CG2):
        if uid == o.CG1:
            deck, rounds, final = list(range(51, -1, -1)), ['A'] * 26, (26, 0, 'A')
        else:
            # every round pairs equal ranks: all rounds tie
            deck, rounds, final = [13 * s + r for r in range(13) for s in range(4)], ['TIE'] * 26, (0, 0, 'TIE')
        calls, want = [], [None]
        for k in range(26): calls += [('playRound',), ('getWinner',)]; want += [rounds[k], '' if k < 25 else final[2]]
        while len(calls) < 9997:
            calls += [('getScore', 'A'), ('getScore', 'B'), ('playRound',)]; want += [final[0], final[1], '']
        out.append((_ops('CardGame', [deck], calls), want))
        if uid == o.CG2:
            # A always holds the higher rank: A ranks 7..12 against B ranks 0..5, then two rank-6 ties
            a = [13 * s + r for r in range(12, 6, -1) for s in range(4)]
            b = [13 * s + r for r in range(5, -1, -1) for s in range(4)]
            deck = [x for pair in zip(a, b) for x in pair] + [6, 19, 32, 45]
            calls, want = [('playRound',)] * 27 + [('getScore', 'A'), ('getScore', 'B'), ('getWinner',)], [None] + ['A'] * 24 + ['TIE', 'TIE', '', 336, 0, 'A']
            out.append((_ops('CardGame', [deck], calls), want))
    elif uid == o.DCB:
        out.append((_ops('DualCircuitBreaker', [3, 10], [('request', i, True, False) for i in range(n)]), [None] + ['PRIMARY'] * n))
        out.append((_ops('DualCircuitBreaker', [3, 10], [('request', i, False, True) for i in range(n)]), [None] + ['SECONDARY'] * n))
        out.append((_ops('DualCircuitBreaker', [1, 2], [('request', i, False, False) for i in range(n)]), [None] + ['FAILED', 'BLOCKED'] * (n // 2)))
        out.append((_ops('DualCircuitBreaker', [2, 10**9], [('request', i, False, False) for i in range(n)]), [None, 'FAILED', 'FAILED'] + ['BLOCKED'] * (n - 2)))
        out.append((_ops('DualCircuitBreaker', [100, 1], [('request', 10**9, i % 100 == 99, True) for i in range(n)]),
                    [None] + ['SECONDARY' if i % 100 != 99 else 'PRIMARY' for i in range(n)]))
    elif uid == o.DAW:
        tokens = ['@$$', 'a5s', 'abc', 'as$'] * 625
        want = [i for i in range(len(tokens)) if i % 4 != 2]
        out.append(([['ass'], [['@', 'a'], ['$', 's'], ['5', 's']], ' '.join(tokens)], want))
        words = []
        for i in range(250):
            w, x = '', i
            for _ in range(8): w = 'abc'[x % 3] + w; x //= 3
            words.append(w)
        subs = [['?', 'a'], ['?', 'b'], ['?', 'c']]
        out.append(([words, subs, ' '.join(['????????'] * 1111)], list(range(1111))))
        out.append(([words, subs, ' '.join(['???????'] * 1250)], []))
        # tokens mixing letters and wildcards; abc-words of length 8 cover every ternary code below 250
        mixed = ['aa?????' + '?', 'ac??????', 'ccc?????', 'b???????']
        ok = [any(all(t == '?' or t == c for t, c in zip(tok, w)) for w in words) for tok in mixed]
        out.append(([words, subs, ' '.join(mixed * 277)], [i for i in range(4 * 277) if ok[i % 4]]))
    return out
