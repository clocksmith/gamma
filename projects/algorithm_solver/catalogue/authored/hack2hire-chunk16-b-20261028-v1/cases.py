"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h16b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _mvb(rng):
    k = rng.randrange(1, 6)
    return [[rng.randrange(1, k + 1) for _ in range(rng.randrange(1, 14))]]


def _mcg(rng):
    rows, held, t = [], 0, 0
    for _ in range(rng.randrange(1, 16)):
        t += rng.randrange(0, 3)
        if held and rng.random() < 0.45:
            amount = rng.randrange(1, held + 1); held -= amount; kind = 'sell'
        else:
            amount = rng.randrange(1, 6); held += amount; kind = 'buy'
        rows.append([str(t), kind, str(amount), str(rng.randrange(1, 30))])
    return [rows]


def _mad(rng):
    return [rng.sample(range(-20, 21), rng.randrange(2, 12))]


def _mcf(rng):
    coins = [rng.randrange(1, 25) for _ in range(rng.randrange(1, 6))]
    if rng.random() < 0.7: coins.append(1)
    rng.shuffle(coins)
    return [coins, rng.randrange(1, 120)]


def _mdp(rng):
    return [rng.randrange(0, 30), rng.randrange(0, 30), rng.randrange(1, 10), rng.randrange(1, 10), rng.randrange(1, 20)]


def _mrc(rng):
    n = rng.randrange(1, 9)
    p = [rng.randrange(0, 10) for _ in range(n)]
    p[rng.randrange(n)] += (-sum(p)) % n
    return [p]


def _mre(rng):
    n = rng.randrange(1, 12); a, b = [], []
    for v in range(2, n + 1):
        u = rng.randrange(1, v)
        if rng.random() < 0.5: a.append(u); b.append(v)
        else: a.append(v); b.append(u)
    perm = list(range(1, n + 1)); rng.shuffle(perm)
    order = list(range(n - 1)); rng.shuffle(order)
    return [n, [perm[a[i] - 1] for i in order], [perm[b[i] - 1] for i in order]]


def _nid(rng):
    pts = rng.sample([(x, y) for x in range(5) for y in range(5)], rng.randrange(1, 20))
    return [[p[0] for p in pts], [p[1] for p in pts]]


def _ofm(rng):
    pool = ['a', 'b', 'c', 'd', 'e', 'f', 'g_1']
    names = rng.sample(pool, rng.randrange(0, 5)); sizes = [rng.randrange(1, 5) for _ in names]
    calls = []
    for _ in range(rng.randrange(0, 30)):
        r = rng.random()
        if r < 0.25: calls.append(('getOffset', rng.choice(pool)))
        elif r < 0.5: calls.append(('fieldAt', rng.randrange(0, 25)))
        elif r < 0.6: calls.append(('totalSize',))
        elif r < 0.8: calls.append(('addField', rng.choice(pool), rng.randrange(1, 5)))
        else: calls.append(('removeField', rng.choice(pool)))
    return _ops('ObjectLayout', [names, sizes], calls)


def _pst(rng):
    alphabet = rng.choice(['a', 'ab', 'abc', 'aA'])
    calls = []
    for _ in range(rng.randrange(0, 40)):
        calls.append(('track', rng.choice(alphabet)) if rng.random() < 0.6 else ('isPalindrome',))
    return _ops('PalindromeStream', [], calls)


def _pds(rng):
    k = rng.randrange(2, 8)
    digits = rng.sample('123456789', k); spots = rng.sample(range(9), k)
    s = ['?'] * 9
    for i, d in zip(spots, digits): s[i] = d
    return [''.join(s)]


def _pig(rng):
    words = ['apple', 'Egg', 'b', 'U', 'quiet', 'Hello', 'yes', 'xyz', 'IOU', 'Tree']
    return [' '.join(rng.choice(words) for _ in range(rng.randrange(0, 7)))]


def _pvo(rng):
    secs = [[rng.choice(['AA', 'B', 'CDE']), rng.randrange(1, 12), rng.randrange(0, 15), rng.randrange(0, 6)] for _ in range(rng.randrange(1, 7))]
    return [secs, rng.randrange(0, 80)]


def _pfp(rng):
    n = rng.randrange(1, 12)
    ids = rng.sample(range(1, 60), n); children = [[] for _ in ids]
    for i in range(1, n):
        if rng.random() < 0.8: children[rng.randrange(0, i)].append(ids[i])
    order = list(range(n)); rng.shuffle(order)
    names = ['f%d' % rng.randrange(0, 5) for _ in ids]
    target = rng.choice(ids) if rng.random() < 0.85 else 99
    return [[ids[i] for i in order], [children[i] for i in order], [names[i] for i in order], target]


def _date(d): return '20%02d-%02d-%02d' % (d // 336, d % 336 // 28 + 1, d % 28 + 1)


def _ppq(rng):
    items = ['milk', 'Big Box', 'tea 2']
    pairs = rng.sample([(i, d) for i in items for d in range(0, 40)], rng.randrange(0, 15))
    log = ['%s, %s, %d' % (i, _date(d), rng.randrange(0, 1000)) for i, d in pairs]
    queries = [[rng.choice(items + ['none']), _date(rng.randrange(0, 45))] for _ in range(rng.randrange(1, 8))]
    return [log, queries]


def _ppt(rng):
    calls = []
    for _ in range(rng.randrange(0, 40)):
        r = rng.random()
        if r < 0.5: calls.append(('update', rng.randrange(1, 12), rng.randrange(1, 20)))
        else: calls.append((rng.choice(['current', 'maximum', 'minimum']),))
    return _ops('ProductPrice', [], calls)


GEN = {_o.MVB: _mvb, _o.MCG: _mcg, _o.MAD: _mad, _o.MCF: _mcf, _o.MDP: _mdp, _o.MRC: _mrc, _o.MRE: _mre, _o.NID: _nid, _o.OFM: _ofm, _o.PST: _pst,
       _o.PDS: _pds, _o.PIG: _pig, _o.PVO: _pvo, _o.PFP: _pfp, _o.PPQ: _ppq, _o.PPT: _ppt}

HAND = {
    _o.MVB: [[[1]], [[1, 2, 1, 3, 3]], [[1, 1, 2, 2]], [[1, 2, 1, 2]], [[5, 6, 7, 5]], [[3, 1, 3, 2, 4, 2]]],
    _o.MCG: [[[['1', 'buy', '10', '5'], ['2', 'sell', '4', '9']]], [[['1', 'buy', '1', '10'], ['1', 'buy', '1', '20'], ['3', 'sell', '1', '25'], ['4', 'sell', '1', '25']]],
             [[['0', 'buy', '3', '9'], ['0', 'sell', '3', '1']]], [[['5', 'buy', '2', '1'], ['6', 'buy', '1', '100'], ['7', 'sell', '2', '60']]]],
    _o.MAD: [[[4, 2, 1, 3]], [[1, 3, 6, 10, 15]], [[3, 8, -10, 23, 19, -4, -14, 27]], [[0, 1000000]]],
    _o.MCF: [[[1], 1], [[2], 5], [[1, 2, 5], 10], [[1, 3], 7], [[1, 10**9], 300], [[4, 1, 4, 2], 100]],
    _o.MDP: [[0, 0, 1, 1, 1], [3, 5, 2, 3, 4], [3, 5, 2, 3, 6], [3, 5, 1, 1, 100], [4, 4, 5, 5, 1]],
    _o.MRC: [[[0]], [[1, 2, 3]], [[3, 2, 1]], [[2, 0, 1]], [[4, 0, 0, 0]], [[0, 0, 0, 4]]],
    _o.MRE: [[1, [], []], [2, [1], [2]], [3, [2, 3], [1, 1]], [4, [1, 3, 3], [2, 2, 4]]],
    _o.NID: [[[0], [0]], [[0, 1, -1, 0, 0], [0, 0, 0, 1, -1]], [[0, 5, -5, 0, 0], [0, 0, 0, 7, -1]], [[0, 1, 0, 1], [0, 0, 1, 1]]],
    _o.OFM: [_ops('ObjectLayout', [['foo', 'bar', 'baz'], [3, 6, 2]], [('getOffset', 'bar'), ('getOffset', 'baz'), ('getOffset', 'qux'), ('fieldAt', 0), ('fieldAt', 3),
                                                                       ('fieldAt', 10), ('fieldAt', 11), ('totalSize',), ('removeField', 'bar'), ('getOffset', 'baz'),
                                                                       ('addField', 'baz', 1), ('addField', 'bar', 4), ('getOffset', 'bar'), ('totalSize',)]),
             _ops('ObjectLayout', [[], []], [('totalSize',), ('fieldAt', 0), ('removeField', 'a')])],
    _o.PST: [_ops('PalindromeStream', [], [('isPalindrome',), ('track', 'a'), ('isPalindrome',), ('track', 'b'), ('isPalindrome',), ('track', 'a'), ('isPalindrome',),
                                           ('track', 'A'), ('isPalindrome',)])],
    _o.PDS: [['123456789'], ['1????????'], ['??????9??'], ['12??????9']],
    _o.PIG: [['apple'], ['Hello World'], [''], ['I am a Pig'], ['b c d']],
    _o.PVO: [[[['AA', 10, 20, 3], ['BB', 5, 6, 10]], 40], [[['A', 3, 1, 5]], 1], [[['A', 8, 1, 1]], 4], [[['A', 8, 1, 1]], 1], [[['A', 400, 1, 1]], 2],
             [[['A', 1, 0, 5], ['B', 2, 1, 5]], 3], [[['A', 5, 5, 0]], 100]],
    _o.PFP: [[[1, 2, 3, 4], [[2, 3], [4], [], []], ['root', 'a', 'b', 'c'], 4], [[1, 2, 3, 4], [[2, 3], [4], [], []], ['root', 'a', 'b', 'c'], 9],
             [[7, 8], [[], []], ['x', 'y'], 8], [[3, 1, 2], [[], [3], [1]], ['c', 'b', 'a'], 3]],
    _o.PPQ: [[['milk, 2023-01-05, 300', 'milk, 2023-01-02, 250', 'Big Box, 2023-01-03, 999'], [['milk', '2023-01-04'], ['milk', '2023-01-01'], ['milk', '2023-01-05'],
                                                                                              ['Big Box', '2024-01-01'], ['tea', '2023-01-05']]],
             [[], [['a', '2000-01-01']]]],
    _o.PPT: [_ops('ProductPrice', [], [('current',), ('update', 5, 10), ('update', 3, 20), ('current',), ('maximum',), ('minimum',), ('update', 3, 5), ('maximum',),
                                       ('minimum',), ('update', 5, 7), ('current',), ('maximum',)])],
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
    if uid == o.MVB:
        out.append(([list(range(1, n + 1))], 0))
        out.append(([[1, 2] * (n // 2)], 1))
        out.append(([list(range(1, n // 2 + 1)) * 2], n // 2 - 1))
        out.append(([[v for k in range(n // 4) for v in (2 * k + 1, 2 * k + 2, 2 * k + 1, 2 * k + 2)]], n // 4))
        out.append(([[10**9 - i // 7 for i in range(n)]], 0))
    elif uid == o.MCG:
        rows = [[str(i), 'buy', '1', str(i + 1)] for i in range(n // 2)] + [[str(n // 2 + i), 'sell', '1', '1000000'] for i in range(n // 2)]
        tenths = 50000 * 10**6 - 50000 * 50001 // 2
        out.append(([rows], '%d.%d' % (tenths // 10, tenths % 10)))
        rows = []
        for i in range(n // 2): rows += [[str(i), 'buy', '2', str(i + 1)], [str(i), 'sell', '1', '50000']]
        tenths = 50000 * 49999 // 2
        out.append(([rows], '%d.%d' % (tenths // 10, tenths % 10)))
        rows = []
        for i in range(n // 2): rows += [[str(i), 'buy', '10000', '1000000'], [str(i), 'sell', '10000', '1']]
        out.append(([rows], '0.0'))
        rows = []
        for i in range(n // 2): rows += [[str(10**9), 'buy', '10000', '1'], [str(10**9), 'sell', '10000', '1000000']]
        tenths = 50000 * 10000 * 999999
        out.append(([rows], '%d.%d' % (tenths // 10, tenths % 10)))
    elif uid == o.MAD:
        vals = [3 * ((i * 7919) % n) for i in range(n)]
        out.append(([vals], [[3 * i, 3 * i + 3] for i in range(n - 1)]))
        vals = [10 * i for i in range(n - 1)] + [1]
        out.append(([vals[::-1]], [[0, 1]]))
        vals = [-10**6 + 20 * i for i in range(n)]
        out.append(([vals], [[-10**6 + 20 * i, -10**6 + 20 * i + 20] for i in range(n - 1)]))
    elif uid == o.MCF:
        # 1, 2, 4, ..., 65536 (17 coins) reach 131071, then 100000 repeatedly: ceil((1e9 - 131071) / 1e5) = 9999
        out.append(([list(range(n, 0, -1)), 10**9], 17 + 9999))
        out.append(([[1, 10**9], 10**9], 10**9))
        out.append(([[2] * n, 10**9], -1))
        out.append(([[10**9 - i for i in range(n - 1)] + [1], 5], 5))
        out.append(([[1 << k for k in range(30)] * 3000, 10**9], 30))
    elif uid == o.MDP:
        out.append(([10**9, 10**9, 10**6, 10**6, 1], 10**9))
        out.append(([10**9, 0, 1, 10**6, 10**6], 10**9))
        out.append(([10**9, 5 * 10**8, 3, 4, 5], 4 * 10**9))
        out.append(([10**9, 10**9, 10**6, 10**6, 10**6], 10**15))
        out.append(([10**9, 10**9, 10**5, 10**5, 10**6], 2 * 10**14))
    elif uid == o.MRC:
        out.append(([[10**4] * (n // 2) + [0] * (n // 2)], 12500000000000))
        out.append(([[2, 0, 1] * 33333], 33333))
        out.append(([[5000] * n], 0))
        out.append(([[0] * (n // 2) + [10**4] * (n // 2)], 12500000000000))
    elif uid == o.MRE:
        out.append(([n, list(range(1, n)), list(range(2, n + 1))], 0))
        out.append(([n, list(range(2, n + 1)), list(range(1, n))], 0))
        out.append(([n, list(range(2, n + 1)), [1] * (n - 1)], n - 2))
        out.append(([n, [i if i % 2 else i + 1 for i in range(1, n)], [i + 1 if i % 2 else i for i in range(1, n)]], 49999))
    elif uid == o.NID:
        out.append(([[x for x in range(316) for _ in range(316)], [y for _ in range(316) for y in range(316)]], 314 * 314))
        out.append(([list(range(-50000, 50000)), [0] * n], 0))
        out.append(([[10**9 - 2 * (i // 300) for i in range(99900)], [-10**9 + 3 * (i % 300) for i in range(99900)]], 331 * 298))
    elif uid == o.OFM:
        names = ['n' + _code(i, 4) for i in range(50000)]
        calls, want = [], [None]
        for i in range(10000): calls.append(('getOffset', names[i])); want.append(2 * i)
        for i in range(10000): calls.append(('fieldAt', 2 * i + 1)); want.append(names[i])
        for i in range(10000): calls.append(('removeField', names[i])); want.append(True)
        calls.append(('removeField', names[0])); want.append(False)
        for i in range(10000): calls.append(('getOffset', names[10000 + i])); want.append(2 * i)
        calls += [('fieldAt', 99999), ('totalSize',)]; want += ['', 80000]
        for i in range(10000): calls.append(('addField', 'z' + _code(i, 4), 3)); want.append(True)
        calls.append(('addField', names[20000], 1)); want.append(False)
        for i in range(9000): calls.append(('fieldAt', 80000 + 3 * i + 2)); want.append('z' + _code(i, 4))
        calls.append(('totalSize',)); want.append(110000)
        out.append((_ops('ObjectLayout', [names, [2] * 50000], calls), want))
        calls = [('fieldAt', 10**10), ('fieldAt', 10**9 - 1), ('getOffset', 'f' + _code(99999, 4)), ('totalSize',)]
        out.append((_ops('ObjectLayout', [['f' + _code(i, 4) for i in range(n)], [10**4] * n], calls), [None, '', 'f' + _code(99999, 4), 10**9 - 10**4, 10**9]))
    elif uid == o.PST:
        calls, want = [], [None]
        for _ in range(49999): calls += [('track', 'a'), ('isPalindrome',)]; want += [None, True]
        out.append((_ops('PalindromeStream', [], calls), want))
        w = 'abcdefghij' * 2500
        calls, want = [], [None]
        for k, ch in enumerate(w + w[::-1]):
            calls.append(('track', ch)); want.append(None)
            if k + 1 in (1, 2, 3, 25000, 50000): calls.append(('isPalindrome',)); want.append(k + 1 in (1, 50000))
        out.append((_ops('PalindromeStream', [], calls), want))
        calls, want = [], [None]
        for k in range(49999): calls += [('track', 'ab'[k % 2]), ('isPalindrome',)]; want += [None, k % 2 == 0]
        out.append((_ops('PalindromeStream', [], calls), want))
    elif uid == o.PDS:
        out.append((['?????????'], 336))
    elif uid == o.PIG:
        words = ['apple' if i % 2 == 0 else 'Banana' for i in range(15000)]
        out.append(([' '.join(words)], ' '.join('appleway' if i % 2 == 0 else 'ananaBay' for i in range(15000))))
        out.append((['x' * 100000], 'x' * 99999 + 'xay'))
        out.append(([' '.join(['E'] * 50000)], ' '.join(['Eway'] * 50000)))
    elif uid == o.PVO:
        out.append(([[['AB', 1, 2, 10**6]] * n, 10**12], '200000000000.00'))
        out.append(([[['C', 3, 1, 10**6]] * n, 10**12], '100000000000.00'))
        out.append(([[['C', 3, 1, 10**6]] * n, 10], '3.33'))
        secs = [['X', 2, 3, 10] if i % 2 else ['Y', 7, 5, 10] for i in range(n)]
        out.append(([secs, 50000 * 20 + 7], '1500005.00'))
        secs = [['Z', 10**4, 10**4 - i % 10**4, 10**6] for i in range(n)]
        # 100 whole lots fit: ten each at S = 10000, 9999, ..., 9991, each lot worth S * 1e6
        out.append(([secs, 10**12], '999550000000.00'))
    elif uid == o.PFP:
        names = ['n' + _code(i, 4) for i in range(n)]
        out.append(([list(range(1, n + 1)), [[i + 2] for i in range(n - 1)] + [[]], names, n], '/'.join(names)))
        out.append(([list(range(1, n + 1)), [list(range(2, n + 1))] + [[] for _ in range(n - 1)], names, 77777], names[0] + '/' + names[77776]))
        out.append(([list(range(1, n + 1)), [[i + 2] for i in range(n - 1)] + [[]], names, 10**9], ''))
        ids = list(range(10**9, 10**9 - n, -1))
        out.append(([ids, [[ids[i + 1]] for i in range(n - 1)] + [[]], names, ids[2]], '/'.join(names[:3])))
    elif uid == o.PPQ:
        log = ['item %d, %s, %d' % (k, _date(33 * j), k * 1000 + j) for j in range(1000) for k in range(100)][::-1]
        queries, want = [], []
        for i in range(n - 100):
            k, j, r = i % 100, (i // 100) % 1000, i % 33
            queries.append(['item %d' % k, _date(33 * j + r)]); want.append(k * 1000 + j)
        for i in range(100): queries.append(['item %d' % (100 + i), _date(33599)]); want.append(-1)
        out.append(([log, queries], want))
    elif uid == o.PPT:
        calls, want = [], [None]
        for i in range(1, 30001): calls.append(('update', i, i)); want.append(None)
        calls += [('current',), ('maximum',), ('minimum',)]; want += [30000, 30000, 1]
        for i in range(1, 30001):
            calls += [('update', i, 10**9), ('minimum',)]; want += [None, i + 1 if i < 30000 else 10**9]
        calls += [('current',), ('maximum',)]; want += [10**9, 10**9]
        out.append((_ops('ProductPrice', [], calls), want))
        calls, want = [], [None]
        for i in range(49999): calls += [('update', 10**9 - i, i + 1), ('current',)]; want += [None, 1]
        out.append((_ops('ProductPrice', [], calls), want))
    return out
