"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h15b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _code(i, width):
    s = ''
    for _ in range(width): s = chr(97 + i % 26) + s; i //= 26
    return s


def _fst(rng):
    vocab = ['foo', 'Foo', 'FOO', 'bar', 'x1', 'foo1', 'afoo', 'BAR']
    files = []
    for f in range(rng.randrange(0, 5)):
        lines = []
        for _ in range(rng.randrange(0, 6)):
            parts = [rng.choice(vocab) for _ in range(rng.randrange(0, 5))]
            line = ''
            for p in parts: line += p + rng.choice([' ', '-', ',', '.', '', ' ! '])
            lines.append(line)
        files.append(['file%d.txt' % f, lines])
    return [files, rng.choice(['foo', 'bar', 'x1', 'Bar', 'FoO'])]


def _imd(rng, uid):
    level = _o.IMD.index(uid) + 1
    keys, fields, values, prefixes = ['a', 'b', 'c'], ['f', 'g', 'fa', 'h1', 'fb'], ['', 'x', 'y1', 'zz'], ['', 'f', 'fa', 'g', 'z']
    calls, t, backups = [], 0, []
    for _ in range(rng.randrange(0, 50)):
        k, f = rng.choice(keys), rng.choice(fields)
        r = rng.random()
        if level <= 2:
            if r < 0.4: calls.append(('setData', k, f, rng.choice(values)))
            elif r < 0.6: calls.append(('getData', k, f))
            elif r < 0.8 or level == 1: calls.append(('deleteData', k, f))
            elif r < 0.9: calls.append(('scanData', k))
            else: calls.append(('scanDataByPrefix', k, rng.choice(prefixes)))
            continue
        t += rng.randrange(1, 4)
        if r < 0.15: calls.append(('setDataAt', k, f, rng.choice(values), t))
        elif r < 0.35: calls.append(('setDataAtWithTtl', k, f, rng.choice(values), t, rng.randrange(1, 12)))
        elif r < 0.5: calls.append(('getDataAt', k, f, t))
        elif r < 0.6: calls.append(('deleteDataAt', k, f, t))
        elif r < 0.7: calls.append(('scanDataAt', k, t))
        elif r < 0.8 or level == 3: calls.append(('scanDataByPrefixAt', k, rng.choice(prefixes), t))
        elif r < 0.9 or not backups: calls.append(('backup', t)); backups.append(t)
        else: calls.append(('restore', t, min(t - 1, rng.choice(backups) + rng.randrange(0, 3))))
    return _ops('InMemoryDB', [], calls)


def _iqr(rng):
    calls = []
    for _ in range(rng.randrange(0, 50)):
        r = rng.random()
        if r < 0.45: calls.append(('add', rng.randrange(0, 21)))
        elif r < 0.7: calls.append(('poll',))
        else: calls.append(('getRandom', rng.choice([rng.randrange(0, 10), rng.randrange(0, 10**15 + 1)])))
    return _ops('InfiniteQueue', [], calls)


def _lza(rng):
    arr = [rng.randrange(-5, 6) for _ in range(rng.randrange(0, 12))]
    cur, calls, maps = list(arr), [], 0
    for _ in range(rng.randrange(0, 25)):
        if rng.random() < 0.35 and maps < 8:
            maps += 1
            if rng.random() < 0.5: c = rng.randrange(-3, 4); calls.append(('map', 'add', c)); cur = [x + c for x in cur]
            else: c = rng.randrange(-2, 3); calls.append(('map', 'multiply', c)); cur = [x * c for x in cur]
        else:
            calls.append(('indexOf', rng.choice(cur) if cur and rng.random() < 0.6 else rng.randrange(-30, 31)))
    return _ops('LazyArray', [arr], calls)


def _dwc(rng):
    n = rng.randrange(0, 11)
    pos = rng.sample([p for p in range(-20, 21) if p], n)
    return [rng.randrange(0, 61), pos, [rng.randrange(1, 11) for _ in range(n)]]


def _esc(rng):
    n, m = rng.randrange(1, 6), rng.randrange(1, 7); calls = []
    for _ in range(rng.randrange(0, 40)):
        r = rng.random()
        if r < 0.6: calls.append(('advance', rng.randrange(m)))
        elif r < 0.8: calls.append(('countInRoom', rng.randrange(n)))
        else: calls.append(('topPlayers', rng.randrange(1, 8)))
    return _ops('EscapeRoom', [n, m], calls)


def _elr(rng):
    t, calls = rng.randrange(0, 3), []
    for _ in range(rng.randrange(0, 40)):
        t += rng.choice([0, 0, 1, 2, 3]); calls.append(('logEvent', rng.choice('abc'), t))
    return _ops('EventLogger', [rng.randrange(1, 6)], calls)


def _fvs(rng):
    rows, width = rng.randrange(0, 5), rng.randrange(0, 5)
    keys, values = ['k1', 'k2', 'k10', 'a_b', 'k'], ['', 'v', 'null', 'x:y', '1', ':']
    return [[[rng.choice(keys) + ':' + rng.choice(values) for _ in range(width)] for _ in range(rows)]]


def _label(minute):
    minute %= 10080
    day, rest = divmod(minute, 1440); hour, mm = divmod(rest, 60)
    h12 = hour % 12 or 12
    return '%s %d:%02d %s' % (_o.DAYS[day], h12, mm, 'AM' if hour < 12 else 'PM')


def _fmi(rng):
    a = rng.randrange(10080)
    b = a + rng.choice([0, rng.randrange(0, 60), rng.randrange(0, 600), rng.randrange(0, 10080)])
    return [_label(a), _label(b)]


def _fas(rng):
    words = []
    while len(words) < rng.randrange(1, 6):
        w = ''.join(rng.choice('abc') for _ in range(rng.randrange(1, 5)))
        if w not in words: words.append(w)
    if not words: words = ['a']
    return [words, ''.join(rng.choice('abcd') for _ in range(rng.randrange(0, 16)))]


def _fkd(rng):
    arr = [rng.randrange(1, 7) for _ in range(rng.randrange(1, 31))]
    return [arr, rng.randrange(1, min(len(arr), 8) + 1)]


def _serialize(values, kids):
    out = [values[0], None]
    for v in range(len(values)):
        out.extend(values[c] for c in kids[v]); out.append(None)
    while out[-1] is None: out.pop()
    return out


def _fpt(rng):
    n = rng.randrange(1, 30); values = [rng.randrange(1, 4) for _ in range(n)]
    kids = [[] for _ in range(n)]; parent = [None] * n
    for v in range(1, n):  # BFS-consistent: parents in order
        p = rng.randrange(max(0, v - 4), v)
        while kids[p] and p + 1 < v and rng.random() < 0.3: p += 1
        kids[p].append(v); parent[v] = p
    order, kid2 = [0], [[] for _ in range(n)]
    for v in order:  # relabel in BFS order so the serialization matches
        for c in kids[v]: order.append(c)
    index = {v: i for i, v in enumerate(order)}
    vals2 = [values[v] for v in order]
    for v in order: kid2[index[v]] = [index[c] for c in kids[v]]
    if rng.random() < 0.5:
        v = rng.randrange(n); chain = []
        while v is not None and len(chain) < 6: chain.append(vals2[index[v]]); v = parent[v]
        path = chain[::-1][rng.randrange(0, len(chain)):] or [1]
        if rng.random() < 0.3: path = path + [rng.randrange(1, 4)]
    else: path = [rng.randrange(1, 4) for _ in range(rng.randrange(1, 5))]
    return [_serialize(vals2, kid2), path]


def _fri(rng):
    open_ = rng.randrange(0, 6); close = open_ + rng.randrange(1, 31); cap = rng.randrange(1, 5)
    res = []
    for _ in range(rng.randrange(0, 8)):
        s = rng.randrange(open_, close); e = rng.randrange(s + 1, close + 1)
        trial = sorted(res + [[s, e, rng.randrange(1, cap + 1)]], key=lambda r: r[0])
        try: _o.fri_domain(open_, close, cap, trial, 1); res = trial
        except ValueError: pass
    return [open_, close, cap, res, rng.randrange(1, cap + 1)]


def _khd(rng):
    names = ['amy', 'bob', 'cat', 'dan', 'eve']; loans = []
    for _ in range(rng.randrange(0, 13)):
        b, l = rng.sample(names, 2); loans.append([b, l, str(rng.randrange(0, 21))])
    return [loans, rng.randrange(1, 4)]


def _fir(rng):
    r, c = rng.randrange(1, 8), rng.randrange(1, 8)
    w = rng.random()
    board = [[rng.choices(['a', 'b', ''], [w, 0.3, 0.3])[0] for _ in range(c)] for _ in range(r)]
    x, y = rng.randrange(r), rng.randrange(c); board[x][y] = ''
    return [board, [x, y], rng.choice('ab')]


def _gtr(rng):
    n, q = rng.randrange(1, 11), rng.randrange(0, 11)
    return [[rng.randrange(1, 6) for _ in range(n)], [rng.randrange(1, 7) for _ in range(q)], [rng.randrange(1, 7) for _ in range(q)]]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); o = _o; args = []
    if uid == o.FST:
        args = [[[], 'foo'], [[['a.txt', ['Foo bar', 'nothing', 'foo-FOO xfoo foo1']], ['b.txt', ['bar']], ['c', []]], 'foo'],
                [[['a', ['x1 X1 x12', 'X1']]], 'x1'], [[['a', ['foofoo foo']]], 'FOO']]
        args += [_fst(rng) for _ in range(250)]
    elif uid in o.IMD:
        level = o.IMD.index(uid) + 1
        if level == 1:
            args = [_ops('InMemoryDB', [], [('setData', 'a', 'f', 'x'), ('getData', 'a', 'f'), ('getData', 'a', 'g'), ('getData', 'b', 'f'), ('setData', 'a', 'f', 'y'),
                                            ('getData', 'a', 'f'), ('deleteData', 'a', 'f'), ('deleteData', 'a', 'f'), ('deleteData', 'z', 'f'), ('getData', 'a', 'f')]),
                    _ops('InMemoryDB', [], [])]
        elif level == 2:
            args = [_ops('InMemoryDB', [], [('setData', 'a', 'fb', '2'), ('setData', 'a', 'f', '1'), ('setData', 'a', 'g', ''), ('scanData', 'a'), ('scanDataByPrefix', 'a', 'f'),
                                            ('scanDataByPrefix', 'a', 'fb'), ('scanDataByPrefix', 'a', 'z'), ('scanData', 'b'), ('deleteData', 'a', 'f'), ('scanData', 'a')])]
        else:
            seq = [('setDataAtWithTtl', 'a', 'f', 'x', 1, 5), ('getDataAt', 'a', 'f', 5), ('getDataAt', 'a', 'f', 6), ('setDataAt', 'a', 'g', 'y', 7),
                   ('setDataAtWithTtl', 'a', 'h', 'z', 8, 2), ('scanDataAt', 'a', 9), ('scanDataByPrefixAt', 'a', 'h', 10), ('deleteDataAt', 'a', 'h', 11), ('deleteDataAt', 'a', 'g', 12)]
            if level == 4:
                seq = [('setDataAtWithTtl', 'a', 'f', 'x', 1, 10), ('setDataAt', 'b', 'g', 'y', 2), ('backup', 3), ('setDataAt', 'a', 'h', 'z', 4), ('deleteDataAt', 'b', 'g', 5),
                       ('backup', 6), ('restore', 20, 5), ('scanDataAt', 'a', 21), ('getDataAt', 'b', 'g', 22), ('getDataAt', 'a', 'f', 27), ('getDataAt', 'a', 'f', 28),
                       ('restore', 30, 6), ('getDataAt', 'b', 'g', 31), ('scanDataAt', 'a', 32), ('backup', 33)]
            args = [_ops('InMemoryDB', [], seq)]
        args += [_imd(rng, uid) for _ in range(250)]
    elif uid == o.IQR:
        args = [_ops('InfiniteQueue', [], [('poll',), ('getRandom', 3), ('add', 5), ('add', 7), ('add', 9), ('getRandom', 0), ('getRandom', 4), ('poll',), ('getRandom', 10**15),
                                           ('poll',), ('poll',), ('poll',)])]
        args += [_iqr(rng) for _ in range(250)]
    elif uid == o.LZA:
        args = [_ops('LazyArray', [[1, 2, 3, 2]], [('indexOf', 2), ('map', 'multiply', 2), ('indexOf', 2), ('indexOf', 4), ('map', 'add', -1), ('indexOf', 5), ('indexOf', 4),
                                                   ('map', 'multiply', 0), ('indexOf', 0), ('indexOf', 1)]),
                _ops('LazyArray', [[]], [('indexOf', 0), ('map', 'multiply', 0), ('indexOf', 0)]), _ops('LazyArray', [[-3, 3]], [('map', 'multiply', -1), ('indexOf', 3)])]
        args += [_lza(rng) for _ in range(250)]
    elif uid == o.DWC:
        args = [[0, [], []], [5, [1, -1], [3, 3]], [9, [1, -1], [3, 3]], [10, [2, 5, -1, -4], [1, 4, 2, 2]], [0, [3], [1]], [1, [3], [1]]]
        args += [_dwc(rng) for _ in range(250)]
    elif uid == o.ESC:
        args = [_ops('EscapeRoom', [3, 4], [('topPlayers', 10), ('advance', 2), ('advance', 1), ('advance', 2), ('advance', 2), ('countInRoom', 2), ('countInRoom', 0),
                                           ('topPlayers', 3), ('advance', 1), ('topPlayers', 4)]),
                _ops('EscapeRoom', [1, 2], [('advance', 1), ('topPlayers', 1), ('countInRoom', 0)])]
        args += [_esc(rng) for _ in range(250)]
    elif uid == o.ELR:
        args = [_ops('EventLogger', [10], [('logEvent', 'a', 0), ('logEvent', 'a', 5), ('logEvent', 'b', 5), ('logEvent', 'a', 10), ('logEvent', 'a', 19), ('logEvent', 'a', 20)])]
        args += [_elr(rng) for _ in range(250)]
    elif uid == o.FVS:
        args = [[[]], [[[], []]], [[['a:1', 'b:2'], ['a:3', 'c:null']]], [[['a:1', 'a:2'], ['b:x:y', 'b:']]]]
        args += [_fvs(rng) for _ in range(250)]
    elif uid == o.FMI:
        args = [['Mon 10:00 AM', 'Mon 10:20 AM'], ['Fri 11:58 AM', 'Fri 12:07 PM'], ['Sun 11:50 PM', 'Mon 12:10 AM'], ['Tue 3:03 PM', 'Tue 3:04 PM'], ['Wed 9:05 AM', 'Wed 9:05 AM'],
                ['Mon 12:00 AM', 'Sun 11:59 PM'], ['Mon 12:01 AM', 'Mon 12:00 AM'], ['Thu 12:00 PM', 'Thu 12:00 AM']]
        args += [_fmi(rng) for _ in range(250)]
    elif uid == o.FAS:
        args = [[['abc'], 'xbca'], [['ab', 'ba'], 'xba'], [['zz', 'q'], 'abc'], [['abc'], ''], [['aab', 'b'], 'abab']]
        args += [_fas(rng) for _ in range(250)]
    elif uid == o.FKD:
        args = [[[1], 1], [[1, 2, 1, 3], 3], [[1, 1, 1], 2], [[1, 2, 2, 2, 3, 1], 3], [[5, 5, 6, 6], 2]]
        args += [_fkd(rng) for _ in range(250)]
    elif uid in o.FPT:
        t = [1, None, 3, 2, 4, None, 5, 6, None, None, 3]
        args = [[t, [1]], [t, [1, 3, 5]], [t, [1, 4, 3]], [t, [3, 5]], [t, [2]], [t, [1, 3, 7]], [[7], [7]], [[7], [7, 7]]]
        args += [_fpt(rng) for _ in range(250)]
    elif uid == o.FRI:
        args = [[0, 10, 2, [], 1], [0, 10, 2, [[2, 5, 2]], 1], [0, 10, 3, [[0, 4, 1], [2, 6, 1], [6, 10, 3]], 2], [5, 8, 1, [[5, 6, 1], [7, 8, 1]], 1]]
        args += [_fri(rng) for _ in range(250)]
    elif uid == o.KHD:
        args = [[[], 1], [[['amy', 'bob', '10'], ['cat', 'bob', '5'], ['amy', 'cat', '5']], 1], [[['amy', 'bob', '10'], ['cat', 'bob', '5'], ['amy', 'cat', '5']], 2],
                [[['amy', 'bob', '10'], ['cat', 'bob', '10']], 2], [[['amy', 'bob', '0']], 1]]
        args += [_khd(rng) for _ in range(250)]
    elif uid == o.FIR:
        args = [[[['']], [0, 0], 'a'], [[['a', 'a', 'a', '']], [0, 3], 'a'], [[['a', 'a', 'a', '']], [0, 3], 'b'], [[['a'], ['a'], [''], ['a']], [2, 0], 'a'],
                [[['a', '', '', ''], ['', 'a', '', ''], ['', '', '', ''], ['', '', '', 'a']], [2, 2], 'a'], [[['', '', '', 'b'], ['', '', 'b', ''], ['', '', '', ''], ['b', '', '', '']], [2, 1], 'b']]
        args += [_fir(rng) for _ in range(250)]
    elif uid == o.GTR:
        args = [[[3, 3, 5], [3, 5, 9], [5, 7, 1]], [[1], [], []], [[2, 2], [2], [2]]]
        args += [_gtr(rng) for _ in range(250)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow from their construction."""
    o = _o; out = []
    if uid == o.FST:
        line = 'Foo bar foo-FOO xfoo 12'
        files = [['f%d.txt' % i, [line if j % 2 == 0 else 'nothing to see here....' for j in range(400)]] for i in range(100)]
        out.append(([files, 'foo'], [['f%d.txt' % i, '600'] + [line] * 200 for i in range(100)]))
        out.append(([files, 'xfo'], []))
    elif uid == o.IMD1:
        calls, exp = [], [None]
        for i in range(40000): calls.append(('setData', _code(i % 500, 2), _code(i, 4), _code(i * 7, 5))); exp.append(None)
        for i in range(0, 40000, 2): calls.append(('getData', _code(i % 500, 2), _code(i, 4))); exp.append(_code(i * 7, 5))
        for i in range(0, 40000, 4): calls.append(('deleteData', _code(i % 500, 2), _code(i, 4))); exp.append(True)
        for i in range(0, 40000, 4): calls.append(('deleteData', _code(i % 500, 2), _code(i, 4))); exp.append(False)
        for i in range(0, 20000, 2): calls.append(('getData', _code(i % 500, 2), _code(i, 4))); exp.append('' if i % 4 == 0 else _code(i * 7, 5))
        out.append((_ops('InMemoryDB', [], calls), exp))
    elif uid == o.IMD2:
        calls, exp = [], [None]
        for i in reversed(range(2000)): calls.append(('setData', 'big', _code(i, 3), 'v%d' % i)); exp.append(None)
        full = [_code(i, 3) + '(v%d)' % i for i in range(2000)]
        for _ in range(30): calls.append(('scanData', 'big')); exp.append(full)
        for _ in range(30): calls.append(('scanDataByPrefix', 'big', 'a')); exp.append(full[:676])
        for _ in range(30): calls.append(('scanDataByPrefix', 'big', 'ab')); exp.append(full[26:52])
        calls.append(('scanData', 'none')); exp.append([])
        for i in range(0, 2000, 2): calls.append(('deleteData', 'big', _code(i, 3))); exp.append(True)
        calls.append(('scanData', 'big')); exp.append(full[1::2])
        out.append((_ops('InMemoryDB', [], calls), exp))
    elif uid == o.IMD3:
        calls, exp, keys = [], [None], [_code(j, 2) for j in range(100)]
        for i in range(30000):
            calls.append(('setDataAtWithTtl', keys[i % 100], _code(i, 4), _code(i, 3), i + 1, 40000 if i % 2 == 0 else 5)); exp.append(None)
        for i in range(30000):
            calls.append(('getDataAt', keys[i % 100], _code(i, 4), 30001 + i)); exp.append(_code(i, 3) if i % 2 == 0 else '')
        for j in range(100):
            t = 60001 + j
            calls.append(('scanDataAt', keys[j], t))
            exp.append(['%s(%s)' % (_code(i, 4), _code(i, 3)) for i in range(j, 30000, 100) if i % 2 == 0 and i + 40001 > t])
        for j in range(100):
            t = 60101 + j
            calls.append(('scanDataByPrefixAt', keys[j], 'b', t))
            exp.append(['%s(%s)' % (_code(i, 4), _code(i, 3)) for i in range(j, 30000, 100) if i % 2 == 0 and i + 40001 > t and _code(i, 4).startswith('b')])
        for i in range(1, 20000, 2):
            calls.append(('deleteDataAt', keys[i % 100], _code(i, 4), 70000 + i)); exp.append(False)
        for idx, i in enumerate(range(25000, 30000, 2)):
            t = 100000 + 3 * idx
            calls.append(('setDataAt', keys[i % 100], _code(i, 4), 'n', t)); exp.append(None)
            calls.append(('deleteDataAt', keys[i % 100], _code(i, 4), t + 1)); exp.append(True)
            calls.append(('getDataAt', keys[i % 100], _code(i, 4), t + 2)); exp.append('')
        out.append((_ops('InMemoryDB', [], calls), exp))
    elif uid == o.IMD4:
        calls, exp, keys = [], [None], [_code(j, 2) for j in range(10)]
        for i in range(1000):
            if i % 2 == 0: calls.append(('setDataAt', keys[i % 10], _code(i, 3), 'v%d' % i, i + 1))
            else: calls.append(('setDataAtWithTtl', keys[i % 10], _code(i, 3), 'v%d' % i, i + 1, 10**6))
            exp.append(None)
        calls.append(('backup', 1001)); exp.append(10)
        t = 2000
        for c in range(200):
            calls.append(('setDataAt', 'junk', 'f', 'x', t)); exp.append(None)
            calls.append(('restore', t + 1, 1001)); exp.append(None)
            calls.append(('getDataAt', 'junk', 'f', t + 2)); exp.append('')
            calls.append(('backup', t + 3)); exp.append(10)
            t += 4
        restore_at = t - 3
        stamp = 0
        for i in range(1, 1000, 2):
            expiry = restore_at + (i + 1 + 10**6 - 1001)
            calls.append(('getDataAt', keys[i % 10], _code(i, 3), expiry - 1)); exp.append('v%d' % i)
            calls.append(('getDataAt', keys[i % 10], _code(i, 3), expiry)); exp.append('')
            stamp = expiry
        calls.append(('scanDataAt', keys[0], stamp + 1)); exp.append(['%s(v%d)' % (_code(i, 3), i) for i in range(0, 1000, 10)])
        calls.append(('backup', stamp + 2)); exp.append(5)
        out.append((_ops('InMemoryDB', [], calls), exp))
    elif uid == o.IQR:
        calls, exp = [], [None]
        for i in range(50000): calls.append(('add', 3 * i)); exp.append(None)
        for i in range(20000): calls.append(('poll',)); exp.append(3 * i)
        for j in range(15000): r = 10**15 - 7919 * j; calls.append(('getRandom', r)); exp.append(3 * (20000 + r % 30000))
        for i in range(14999): calls.append(('poll',)); exp.append(3 * (20000 + i))
        out.append((_ops('InfiniteQueue', [], calls), exp))
        calls, exp = [], [None]
        for i in range(30000): calls += [('add', i), ('poll',), ('getRandom', i)]; exp += [None, i, -1]
        out.append((_ops('InfiniteQueue', [], calls), exp))
    elif uid == o.LZA:
        arr = [i - 50000 for i in range(100000)]
        maps = [('add', 7), ('multiply', -3), ('add', 1000), ('multiply', 2), ('multiply', 1000), ('add', -999999), ('multiply', 1000)]
        a, b = 1, 0
        for op, c in maps:
            if op == 'add': b += c
            else: a *= c; b *= c
        calls, exp = [('map', op, c) for op, c in maps], [None] * (1 + len(maps))
        for i in range(0, 100000, 2): calls.append(('indexOf', a * (i - 50000) + b)); exp.append(i)
        for i in range(0, 20000): calls.append(('indexOf', a * (i - 50000) + b + 1 + i % 1000)); exp.append(-1)
        out.append((_ops('LazyArray', [arr], calls), exp))
        calls, exp = [], [None]
        for i in range(30000): calls += [('map', 'add', 1), ('indexOf', 1 + i - 50000 + i)]; exp += [None, i]
        out.append((_ops('LazyArray', [arr[:]], calls), exp))
        calls = [('map', 'multiply', 0), ('map', 'add', 5), ('indexOf', 5), ('indexOf', 0)]
        out.append((_ops('LazyArray', [[9] * 100000], calls), [None, None, None, 0, -1]))
    elif uid == o.DWC:
        pos, cost = [], []
        for i in range(1, 50001): pos += [i, -i]; cost += [1, 2]
        out.append(([10**15, pos, cost], 100000))
        out.append(([60000, pos, cost], 52500))
        out.append(([0, pos, cost], 0))
        out.append(([3 * 10**14, [10**9 - i for i in range(100000)], [10**9] * 100000], 100000))
    elif uid == o.ESC:
        calls, exp = [], [None]
        for _ in range(50000): calls.append(('advance', 0)); exp.append(None)
        calls.append(('topPlayers', 3)); exp.append([0, 1, 2])
        for _ in range(49):
            for p in range(1, 1000): calls.append(('advance', p)); exp.append(None)
        for _ in range(40): calls.append(('topPlayers', 1000)); exp.append(list(range(1000)))
        calls += [('countInRoom', 49), ('countInRoom', 0), ('countInRoom', 50000), ('countInRoom', 99999)]; exp += [999, 0, 1, 0]
        out.append((_ops('EscapeRoom', [100000, 1000], calls), exp))
        calls, exp = [], [None]
        for p in range(99999, 50000, -1): calls.append(('advance', p)); exp.append(None)
        for _ in range(30): calls.append(('topPlayers', 1000)); exp.append(list(range(99999, 98999, -1)))
        calls += [('countInRoom', 1), ('countInRoom', 0)]; exp += [49999, 50001]
        calls.append(('advance', 99999)); exp.append(None)
        calls.append(('topPlayers', 2)); exp.append([99999, 99998])
        out.append((_ops('EscapeRoom', [2, 100000], calls), exp))
    elif uid == o.ELR:
        names = ['alpha', 'beta', 'gamma', 'delta', 'eps']
        out.append((_ops('EventLogger', [10], [('logEvent', names[i % 5], i) for i in range(100000)]), [None] + [(i // 5) % 2 == 0 for i in range(100000)]))
        out.append((_ops('EventLogger', [5], [('logEvent', names[i % 5], i) for i in range(100000)]), [None] + [True] * 100000))
        out.append((_ops('EventLogger', [10**9], [('logEvent', 'same', 10**9) for _ in range(100000)]), [None, True] + [False] * 99999))
    elif uid == o.FVS:
        src = [['k%d:r%dc%d' % (c % 100, r, c) for c in range(200)] for r in range(1000)]
        out.append(([src], ['k%d:r999c%d' % (j, 100 + j) for j in sorted(range(100), key=lambda j: 'k%d' % j)]))
        src = [['a%d:%d' % (c, r) for c in range(200)] for r in range(999)] + [['b%d:x:%d' % (c, c) for c in range(200)]]
        out.append(([src], sorted(['a%d:998' % c for c in range(200)] + ['b%d:x:%d' % (c, c) for c in range(200)], key=lambda e: e.split(':', 1)[0])))
    elif uid == o.FAS:
        words = ['z' * (1 + i % 47) + _code(i, 3) for i in range(999)] + ['ba' * 25]
        out.append(([words, 'ab' * 5000], 'ba' * 25))
        words = ['b' * k for k in range(1, 51)] + ['a' * a + 'b' * b for a in range(1, 11) for b in range(1, 41)] + ['a' * 50] + ['a' * k for k in range(1, 50)]
        out.append(([words, 'a' * 10000], 'a' * 50))
        out.append(([['z' * 50] + ['y' * i for i in range(1, 50)], 'abcdefghijklmnopqrstuvwx' * 416], ''))
    elif uid == o.FKD:
        out.append(([[i % 1000 + 1 for i in range(100000)], 1000], 1000))
        out.append(([[i % 1000 + 1 for i in range(100000)], 1], 1))
        out.append(([[1] * 99999 + [2], 2], 2))
        out.append(([list(range(1, 100001)), 100000], 100000))
        out.append(([[1] * 50000 + [2] * 50000, 3], -1))
    elif uid in o.FPT:
        chain = [1 if d != 5000 else 2 for d in range(10000)]
        tree = [chain[0], None]
        for d in range(1, 10000): tree += [chain[d], None]
        tree.pop()
        out.append(([tree, [1] * 1000], True))
        out.append(([tree, [1] * 999 + [2]], uid == o.FPT2))
        out.append(([tree, [2] + [1] * 999], uid == o.FPT2))
        out.append(([tree, [1] * 999 + [3]], False))
        broom = [7, None] + [x for _ in range(999) for x in (1, None)] + list(range(2, 9002))
        out.append(([broom, [1] * 999 + [9001]], uid == o.FPT2))
        out.append(([broom, [7] + [1] * 999], True))
        out.append(([broom, [1] * 998 + [9002]], False))
        star = [1, None] + [1] * 9999
        out.append(([star, [1, 1]], True))
        out.append(([star, [1, 2]], False))
        out.append(([star, [1, 1, 1]], False))
    elif uid == o.FRI:
        res = [[10 * i, 10 * i + 15, 1] for i in range(100000)]
        free1 = [[0, 10]] + [[10 * i + 5, 10 * i + 10] for i in range(1, 99999)] + [[999995, 1000010]]
        out.append(([0, 1000010, 2, res, 1], free1))
        out.append(([0, 1000010, 2, res, 2], [[1000005, 1000010]]))
        out.append(([0, 10**9, 10**9, [[0, 10**9, 10**9]], 1], []))
        out.append(([0, 10**9, 10**9, [], 10**9], [[0, 10**9]]))
    elif uid == o.KHD:
        loans = [['b' + _code(i % 1000, 3), 'l' + _code(i % 500, 3), str(i % 1000 + 1)] for i in range(100000)]
        out.append(([loans, 1], 'b' + _code(999, 3)))
        out.append(([loans, 1000], 'b' + _code(0, 3)))
        out.append(([loans, 1001], ''))
        out.append(([loans, 500], 'b' + _code(500, 3)))
        loans = [['b' + _code(i % 1000, 3), 'lend', '999999999'] for i in range(100000)]
        out.append(([loans, 7], 'b' + _code(6, 3)))
    elif uid == o.FIR:
        board = [[''] * 300 for _ in range(300)]
        for c in (10, 11, 12): board[150][c] = 'a'
        for d in (1, 2, 3): board[200 + d][100 - d] = 'b'
        board[299][296] = board[299][297] = board[299][299] = 'a'
        out.append(([board, [150, 13], 'a'], True))
        out.append(([board, [150, 9], 'a'], True))
        out.append(([board, [150, 14], 'a'], False))
        out.append(([board, [150, 13], 'b'], False))
        out.append(([board, [200, 100], 'b'], True))
        out.append(([board, [204, 96], 'b'], True))
        out.append(([board, [299, 298], 'a'], True))
        out.append(([board, [0, 0], 'a'], False))
    elif uid == o.GTR:
        n = 100000
        server = list(range(1, n + 1)); total = n * (n + 1) // 2; totals = []
        for j in range(n): total += (10**9 - j) - (j + 1); totals.append(total)
        out.append(([server, list(range(1, n + 1)), [10**9 - j for j in range(n)]], totals))
        out.append(([[7] * n, [7 if j % 2 == 0 else 8 for j in range(n)], [8 if j % 2 == 0 else 7 for j in range(n)]], [800000 if j % 2 == 0 else 700000 for j in range(n)]))
        out.append(([[10**9] * n, [5] * n, [6] * n], [10**14] * n))
    return out
