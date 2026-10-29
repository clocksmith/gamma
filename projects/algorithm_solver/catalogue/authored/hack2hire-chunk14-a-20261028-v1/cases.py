"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h14a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _upper(i, width): return _code(i, width).upper()


def _word(rng, alphabet='abcdefgh', lo=1, hi=8): return ''.join(rng.choice(alphabet) for _ in range(rng.randrange(lo, hi + 1)))


def _stl(rng):
    words = [_word(rng) for _ in range(rng.randrange(1, 13))]
    seps = [' ' * rng.choice((1, 1, 1, 2, 3)) for _ in words[1:]]
    s = words[0] + ''.join(a + b for a, b in zip(seps, words[1:]))
    if rng.random() < 0.2: s = ' ' + s
    if rng.random() < 0.2: s = s + '  '
    return [s, rng.randrange(1, 16)]


_SYMS, _QTY, _IDS = ['AAPL', ' IBM', '  GE', 'MSFT'], ['0100', '0050', '0200'], ['ABC123', 'XYZ999', 'ID0001', '7Q7Q7Q']


def _trade(rng): return '%s,%s,%s,%s' % (rng.choice(_SYMS), rng.choice('BS'), rng.choice(_QTY), rng.choice(_IDS))


def _stm(rng):
    house = [_trade(rng) for _ in range(rng.randrange(0, 11))]
    street = [_trade(rng) for _ in range(rng.randrange(0, 8))] + [t for t in house if rng.random() < 0.4]
    rng.shuffle(street)
    return [house, street[:12]]


def _smr(rng):
    codes = rng.sample(['A', 'B', 'C', 'DD', 'EEE', 'AB'], rng.randrange(0, 5))
    pool = ['A', 'B', 'C', 'DD', 'EEE', 'AB', 'ZZ']
    records = [[rng.randrange(0, 7), rng.choice(pool), rng.randrange(-5, 6)] for _ in range(rng.randrange(0, 13))]
    return [codes, records]


def _sst(rng, uid):
    while True:
        chunks = []
        for _ in range(rng.randrange(0, 9)):
            r = rng.random()
            if r < 0.15: chunks.append('')
            elif r < 0.3: chunks.append(_word(rng, 'ab', 0, 3) + '<END>' + _word(rng, 'ab<', 0, 3))
            elif r < 0.5: chunks.append(rng.choice(['<', '<E', '<EN', '<END', 'ND>', 'D>', '>', 'END>', 'N']))
            else: chunks.append(_word(rng, 'ab <>ED', 1, 5))
        try:
            validate_domain(uid, [chunks]); return [chunks]
        except ValueError:
            continue


def _smm(rng):
    m, n = rng.randrange(1, 7), rng.randrange(1, 7)
    return [[_word(rng, 'ab', n, n) for _ in range(m)], _word(rng, 'ab', 1, 4)]


def _sro(rng): return [_word(rng, rng.choice(['ab', 'abc', 'aab', 'abcd', 'aaab']), 1, 8)]


def _sbs(rng):
    year = rng.choice([2023, 2024, 1900, 2000, 2100, 2025])
    names = rng.sample(['Basic', 'Pro', 'Max', 'Lite', 'Family'], 3)
    plans = [[nm, rng.randrange(1, 3000)] for nm in names]
    days = sorted(rng.sample(range(1, 366 + (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))), rng.randrange(0, 9)))
    events, active = [], None
    for d in days:
        date = _o.datetime.date(year, 1, 1) + _o.datetime.timedelta(days=d - 1)
        if active is None: active = rng.choice(names); events.append([date.isoformat(), 'START', active])
        elif rng.random() < 0.5: events.append([date.isoformat(), 'END', None]); active = None
        else: active = rng.choice([x for x in names if x != active]); events.append([date.isoformat(), 'SWITCH', active])
    return [plans, events]


def _sub(rng):
    nums = [rng.randrange(1, 21) for _ in range(rng.randrange(0, 13))]
    return [nums, rng.randrange(0, sum(nums) + 5)]


def _tgc(rng):
    pool = ['red', 'blue', 'x-1', 'big_a', 'z9', 'tag']
    groups = [[rng.choice(pool) for _ in range(rng.randrange(0, 6))] for _ in range(rng.randrange(0, 7))]
    return [groups, rng.sample(pool, rng.randrange(0, 3))]


def _tnl(rng): return [_word(rng, 'ab \n\n', 0, 30), rng.randrange(0, 7)]


def _tsf(rng):
    parts = []
    for _ in range(rng.randrange(0, 8)):
        parts.append(rng.choice(['Hi ', '{a}', '{b}', '{zz}', ' and #', '{c, plural, one{# cat} other{# cats}}', '{n, plural, one{one} other{# many}}',
                                 '{c, plural, one{} other{#}}', ', ', '{a}{b}']))
    keys = ['a', 'b', 'c', 'n']
    values = [_word(rng, 'xy #1', 0, 4), _word(rng, 'q12', 0, 3), rng.choice(['0', '1', '2', '17', '1000000']), rng.choice(['1', '5'])]
    keep = [i for i in range(4) if rng.random() < 0.8]
    return [''.join(parts), [keys[i] for i in keep], [values[i] for i in keep]]


def _tbf(rng, uid):
    if uid == _o.TBF1:
        return [[_word(rng, 'ab |+-#', 1, 12) for _ in range(rng.randrange(1, 6))]]
    width = rng.randrange(1, 13)
    sentences = []
    for _ in range(rng.randrange(1, 5)):
        hi = width if uid == _o.TBF3 else 9
        sentences.append(' '.join(_word(rng, 'abc.,', 1, min(hi, 9)) for _ in range(rng.randrange(1, 7))))
    return [sentences, width]


def _ttw1(rng):
    return [''.join(rng.choice(['the ', 'The', ' cat', 'CAT', 'a', 'b', '-', ' ', '\n', '42', 'x', "isn't ", 'zeta', 'Q', 'q', 'y']) for _ in range(rng.randrange(0, 40)))]


def _ttw2(rng):
    calls = []
    for _ in range(rng.randrange(0, 25)):
        calls.append(('addText', _ttw1(rng)[0]) if rng.random() < 0.6 else ('getTop10',))
    return _ops('WordFrequencyTracker', [], calls)


def _tkb(rng):
    calls = []
    for _ in range(rng.randrange(0, 25)):
        calls.append(('recordSale', rng.choice(['b1', 'b2', 'B1', 'zz', 'a9']), rng.randrange(1, 6)) if rng.random() < 0.6 else ('getTopK', rng.randrange(0, 7)))
    return _ops('BookSalesTracker', [], calls)


def _tkp(rng):
    calls, ids = [], rng.sample(range(0, 50), 30)
    for _ in range(rng.randrange(0, 25)):
        if rng.random() < 0.6 and ids: calls.append(('addPin', ids.pop(), rng.randrange(-3, 4), rng.choice(['a', 'b'])))
        else: calls.append(('getTopK', rng.choice(['a', 'b', 'c']), rng.randrange(0, 6)))
    return _ops('PinManager', [], calls)


def _tkl(rng):
    nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(0, 13))]
    return [nums, rng.randrange(0, len(nums) + 1)]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.STL:
        args = [['a', 1], ['hello world', 11], ['hello world', 10], ['  a  bb ccc ', 4], ['abcdefgh ab cd', 3], ['ab cd', 1]]
        args += [_stl(rng) for _ in range(250)]
    elif uid in o.STM:
        a, b, c = 'AAPL,B,0100,ABC123', 'AAPL,B,0100,XYZ999', '  GE,S,0050,ID0001'
        args = [[[], []], [[a], [a]], [[a, a], [a]], [[a], [b]], [[a, c], [b, c, c]], [[a, b], [b, b]]]
        args += [_stm(rng) for _ in range(250)]
    elif uid == o.SMR:
        args = [[[], []], [['B', 'A'], [[5, 'A', 1], [3, 'B', 2], [5, 'B', 7], [5, 'B', 8], [4, 'C', 9]]], [['X'], [[1, 'Y', 1]]], [['A'], [[2, 'A', -1], [2, 'A', 4], [0, 'A', 3]]]]
        args += [_smr(rng) for _ in range(250)]
    elif uid in o.SST:
        args = [[[]], [['ab', '', 'cd']], [['a', '', 'b<END>c', 'd']], [['<END>x', 'y']], [['', 'q', '<END>']], [['x<END>y<END>']]]
        if uid == o.SST2: args += [[['ab<E', 'ND>', 'z']], [['a', '<', 'E', '', 'N', 'D>']], [['<EN', 'D'], ], [['x<', 'END>']]]
        args += [_sst(rng, uid) for _ in range(250)]
    elif uid == o.SMM:
        args = [[['a'], 'a'], [['ab', 'ba'], 'ab'], [['aaa', 'aaa', 'aaa'], 'aa'], [['abc'], 'abcd'], [['ab', 'cb'], 'b']]
        args += [_smm(rng) for _ in range(250)]
    elif uid == o.SRO:
        args = [['a'], ['aa'], ['aab'], ['aaab'], ['abc'], ['bba'], ['zzyy'], ['aaabb']]
        args += [_sro(rng) for _ in range(250)]
    elif uid == o.SBS:
        plans = [['Basic', 1000], ['Pro', 3100], ['Max', 2900]]
        args = [[plans, []], [plans, [['2023-01-01', 'START', 'Basic']]], [plans, [['2024-02-10', 'START', 'Pro'], ['2024-02-20', 'SWITCH', 'Max'], ['2024-03-01', 'END', None]]],
                [plans, [['2023-12-31', 'START', 'Basic']]], [plans, [['2023-03-05', 'START', 'Basic'], ['2023-03-06', 'END', None], ['2023-03-07', 'START', 'Max']]]]
        cycle = ['Basic', 'Pro', 'Max']
        big = [[(_o.datetime.date(2024, 1, 1) + _o.datetime.timedelta(days=d)).isoformat(), 'SWITCH' if d else 'START', cycle[d % 3]] for d in range(366)]
        args.append([[['Basic', 10**6], ['Pro', 999999], ['Max', 1]], big])
        args += [_sbs(rng) for _ in range(250)]
    elif uid == o.SUB:
        args = [[[], 0], [[], 1], [[5], 5], [[5], 0], [[3, 34, 4, 12, 5, 2], 9], [[3, 34, 4, 12, 5, 2], 30], [[2, 2, 2], 6], [[2, 2, 2], 8]]
        args += [_sub(rng) for _ in range(250)]
    elif uid == o.TGC:
        args = [[[], []], [[['a', 'b'], ['b', 'c'], ['d']], ['b']], [[['a', 'b'], ['b', 'c'], ['d']], []], [[['a', 'a', 'b']], ['a', 'b']], [[['x']], ['y']]]
        args += [_tgc(rng) for _ in range(250)]
    elif uid == o.TNL:
        args = [['', 3], ['a\nb\nc\n', 2], ['a\nb\nc', 2], ['a\nb\nc', 0], ['\n\n\n', 2], ['one', 5], ['a\n', 1], ['a\nb\n', 9]]
        args += [_tnl(rng) for _ in range(250)]
    elif uid == o.TSF:
        args = [['', [], []], ['Hello {name}!', ['name'], ['Ann']], ['{n, plural, one{# file} other{# files}} left', ['n'], ['1']],
                ['{n, plural, one{# file} other{# files}} left', ['n'], ['0']], ['{x} {n, plural, one{a} other{b}}', [], []], ['{a}{a}', ['a'], ['#']]]
        args += [_tsf(rng) for _ in range(250)]
    elif uid == o.TBF1:
        args = [[['a']], [['hello', 'hi', 'hey you']], [[' ', 'x ']]]
        args += [_tbf(rng, uid) for _ in range(250)]
    elif uid in o.TBF:
        args = [[['a'], 1], [['the quick brown fox'], 10], [['a bb ccc', 'dddd'], 5], [['ab cde ab cde'], 10]]
        if uid == o.TBF2: args += [[['abcdefgh x'], 3]]
        args += [_tbf(rng, uid) for _ in range(250)]
    elif uid == o.TTW1:
        args = [[''], ['Hello, hello WORLD!'], ['a b c d e f g h i j k l a'], ["it's 2 o'clock; IT is"]]
        args += [_ttw1(rng) for _ in range(250)]
    elif uid == o.TTW2:
        args = [_ops('WordFrequencyTracker', [], [('getTop10',), ('addText', 'b a b'), ('getTop10',), ('addText', 'A-a'), ('getTop10',)]),
                _ops('WordFrequencyTracker', [], [('addText', 'ab'), ('addText', 'c'), ('getTop10',)])]
        args += [_ttw2(rng) for _ in range(250)]
    elif uid == o.TKB:
        args = [_ops('BookSalesTracker', [], [('getTopK', 3), ('recordSale', 'b', 2), ('recordSale', 'a', 2), ('getTopK', 5), ('recordSale', 'b', 1), ('getTopK', 1), ('getTopK', 0)])]
        args += [_tkb(rng) for _ in range(250)]
    elif uid == o.TKP:
        args = [_ops('PinManager', [], [('getTopK', 'art', 2), ('addPin', 7, 5, 'art'), ('addPin', 3, 5, 'art'), ('addPin', 9, 8, 'food'), ('addPin', 1, -2, 'art'),
                                        ('getTopK', 'art', 2), ('getTopK', 'food', 9), ('getTopK', 'art', 0)])]
        args += [_tkp(rng) for _ in range(250)]
    elif uid == o.TKL:
        args = [[[], 0], [[3, 1, 2], 2], [[5, 5, 1], 2], [[-1, -2], 2], [[4], 0]]
        args += [_tkl(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _border(w): return '+' + '-' * w + '+'


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    if uid == o.STL:
        out.append(([' '.join(['abcd'] * 40000), 9], 20000))
        out.append(([' '.join(['abcd'] * 40000), 200000], 1))
        out.append(([' '.join(['x' * 10] * 18000), 5], 18000))
        out.append(([' ' * 100 + 'y' + ' ' * 100, 1], 1))
    elif uid in o.STM:
        house = ['%s,%s,%04d,H%05d' % (_upper(i // 10000, 4), 'BS'[i % 2], i % 10000, i) for i in range(50000)]
        street = ['%s,%s,%04d,S%05d' % (_upper(i // 10000, 4), 'BS'[i % 2], i % 10000, i) for i in range(50000)]
        out.append(([house, house[::-1]], []))
        out.append(([house, street[::-1]], sorted(house + street) if uid == o.STM1 else []))
        out.append(([house, street[:25000] + house[25000:]], sorted(house[:25000] + street[:25000]) if uid == o.STM1 else []))
    elif uid == o.SMR:
        codes = [_upper(j, 3) for j in range(19, -1, -1)]
        records = [[t, _upper(j, 3), t * 100 + j] for t in range(2499, -1, -1) for j in range(20)]
        out.append(([codes, records], [[t] + [t * 100 + j for j in range(20)] for t in range(2500)]))
        records = []
        for t in range(25000): records += [[t * 7, 'AAA', 1], [t * 7, 'AAA', -t]]
        out.append(([codes, records], [[t * 7, -t] + [None] * 19 for t in range(25000)]))
    elif uid in o.SST:
        chunks = ['abc'] * 50000
        out.append(([chunks[:40000] + ['x<END>y'] + chunks[40001:]], chunks[:40000] + ['x']))
        out.append(([['abc'] * 49999 + ['<END>']], ['abc'] * 49999))
        out.append(([['abcd'] * 50000], ['abcd'] * 50000))
        if uid == o.SST2:
            out.append(([chunks[:30000] + ['zz<E', 'ND>'] + chunks[30002:]], chunks[:30000] + ['zz']))
            out.append(([['<'] * 25000 + ['E', 'N', 'D', '>'] + [''] * 24996], ['<'] * 24999))
    elif uid == o.SMM:
        n = 316
        out.append(([['a' * n] * n, 'a' * 100], 2 * n * (n - 99) + (n - 99) ** 2))
        out.append(([['ab' * 50000], 'ab' * 50], 49951))
        out.append(([['a'] * 100000, 'a' * 100], 99901))
        out.append(([['a'] * 100000, 'a'], 300000))
    elif uid == o.SRO:
        out.append((['a' * 50000 + 'b' * 50000], 'ab' * 50000))
        out.append((['b' * 50001 + 'a' * 49999], ''))
        out.append((['b' * 49999 + 'a' * 50000], 'ab' * 49999 + 'a'))
        s = ''.join(chr(97 + i % 26) for i in range(100000))
        expect = ''.join((chr(97 + 2 * p) + chr(98 + 2 * p)) * s.count(chr(97 + 2 * p)) for p in range(13))
        out.append(([s], expect))
        # z (50000 of 100000) may lead or follow; after a leading 'a' the odd remainder forces z first
        out.append((['z' * 50000 + 'y' * 49999 + 'a'], 'a' + 'zy' * 49999 + 'z'))
    elif uid == o.SUB:
        out.append(([[10000] * 200, 100000], True))
        out.append(([[10000] * 200, 99999], False))
        out.append(([[9999] * 199 + [9], 99999], True))
        out.append(([[2 * (i % 5000 + 1) for i in range(200)], 99999], False))
    elif uid == o.TGC:
        groups = [['common'] + ['t%d' % ((i * 9 + j) % 20000) for j in range(9)] for i in range(10000)]
        out.append(([groups, ['common']], sorted('t%d' % v for v in range(20000))))
        hit = sorted({t for g in groups if 't5' in g for t in g} - {'common', 't5'})
        out.append(([groups, ['common', 't5']], hit))
        out.append(([groups, ['nothing']], []))
    elif uid == o.TNL:
        text = 'line\n' * 40000
        out.append(([text, 100000], text)); out.append(([text, 3], 'line\n' * 3)); out.append(([text, 0], ''))
        out.append((['ab\n' * 66666 + 'zz', 2], 'ab\nzz'))
    elif uid == o.TSF:
        unit = '{n, plural, one{# item} other{# items}} for {who}; {missing} '
        reps = 100000 // len(unit)
        out.append(([unit * reps, ['n', 'who'], ['1', 'Bo']], '1 item for Bo; {missing} ' * reps))
        out.append(([unit * reps, ['n', 'who'], ['1000000', '#']], '1000000 items for #; {missing} ' * reps))
        out.append((['{k}' * 33333, ['k'], ['x' * 20]], 'x' * 20 * 33333))
    elif uid == o.TBF1:
        sentences = [chr(33 + i % 90) * (1 + i % 100) for i in range(1000)]
        rows = []
        for s in sentences: rows += [_border(100), '|' + s + ' ' * (100 - len(s)) + '|', _border(100)]
        out.append(([sentences], rows))
    elif uid in o.TBF:
        sentence = ' '.join(['ab', 'cde'] * 10)
        if uid == o.TBF2: lines = ['ab cde ab ', 'cde ab cde'] * 3 + ['ab cde    ']
        else: lines = ['ab  cde ab', 'cde ab cde'] * 3 + ['ab cde    ']
        rows = []
        for _ in range(1000): rows += [_border(10)] + ['|' + x + '|' for x in lines] + [_border(10)]
        out.append(([[sentence] * 1000, 10], rows))
        long = ' '.join(['abcd'] * 20)
        rows = []
        for _ in range(1000): rows += [_border(99), '|' + long + '|', _border(99)]
        if uid == o.TBF2: out.append(([[long] * 1000, 100], rows))
    elif uid == o.TTW1:
        out.append(([' '.join(_code(i % 5000, 3) for i in range(50000))], [[_code(i, 3), 10] for i in range(10)]))
        out.append((['Zebra! ' * 20000], [['zebra', 20000]]))
        out.append((['.' * 200000], []))
    elif uid == o.TTW2:
        calls, expected = [], [None]
        for i in range(9999, -1, -1):
            calls += [('addText', _code(i, 3)), ('getTop10',)]
            expected += [None, [[_code(j, 3), 1] for j in range(i, min(i + 10, 10000))]]
        out.append((_ops('WordFrequencyTracker', [], calls), expected))
        out.append((_ops('WordFrequencyTracker', [], [('addText', ' '.join(['hello'] * 30000 + ['World'] * 3000)), ('getTop10',)]),
                    [None, None, [['hello', 30000], ['world', 3000]]]))
    elif uid == o.TKB:
        calls, expected = [], [None]
        for i in range(10000): calls.append(('recordSale', 'B%05d' % (9999 - i), 1)); expected.append(None)
        for i in range(9999): calls.append(('getTopK', 20)); expected.append(['B%05d' % j for j in range(20)])
        calls.append(('recordSale', 'B09999', 10000)); expected.append(None)
        out.append((_ops('BookSalesTracker', [], calls), expected))
        calls, expected = [], [None]
        for i in range(10000): calls.append(('recordSale', 'B%05d' % i, 1)); expected.append(None)
        for i in range(9999, 0, -1): calls.append(('recordSale', 'B%05d' % i, 10000)); expected.append(None)
        calls.append(('getTopK', 5)); expected.append(['B%05d' % j for j in range(1, 6)])
        out.append((_ops('BookSalesTracker', [], calls), expected))
    elif uid == o.TKP:
        calls, expected = [], [None]
        for i in range(19999): calls.append(('addPin', i, i % 100, 'x')); expected.append(None)
        calls.append(('getTopK', 'x', 10000)); expected.append([p for _, p in sorted((-(i % 100), i) for i in range(19999))][:10000])
        out.append((_ops('PinManager', [], calls), expected))
        calls, expected = [], [None]
        for i in range(19997): calls.append(('addPin', 10**9 - i, i, 'ab'[i % 2])); expected.append(None)
        calls += [('getTopK', 'a', 3), ('getTopK', 'b', 3)]; expected += [[10**9 - 19996, 10**9 - 19994, 10**9 - 19992], [10**9 - 19995, 10**9 - 19993, 10**9 - 19991]]
        out.append((_ops('PinManager', [], calls), expected))
    elif uid == o.TKL:
        nums = [(i * 7919) % 100003 - 50000 for i in range(100000)]
        desc = sorted(nums, reverse=True)
        out.append(([nums, 100000], desc)); out.append(([nums, 10], desc[:10])); out.append(([nums, 0], []))
        out.append(([[7] * 100000, 50000], [7] * 50000))
    return out

