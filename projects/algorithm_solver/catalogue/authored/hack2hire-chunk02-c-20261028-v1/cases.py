"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h02c_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _wkv(rng, n):
    calls, t = [], 0
    for _ in range(n):
        t += rng.choice([0, 0, 1, 2, 5])
        if rng.random() < 0.5: calls.append(('put', rng.randrange(6), rng.randrange(100), t))
        else: calls.append(('get', rng.randrange(7), t))
    return _ops('WindowedKeyValueStore', [rng.randrange(1, 5), rng.randrange(1, 8)], calls)


def _header(rng, uid):
    langs = ['en', 'fr', 'de', 'es']; regions = ['US', 'CA', 'FR', 'GB', 'DE']
    toks = []
    for _ in range(rng.randrange(1, 7)):
        k = rng.random()
        if uid != _o.ALH1 and k < 0.3: t = rng.choice(langs)
        elif uid in (_o.ALH3, _o.ALH4) and k < 0.4: t = '*'
        else: t = rng.choice(langs) + '-' + rng.choice(regions)
        if uid == _o.ALH4 and rng.random() < 0.6: t += ';q=' + rng.choice(['0', '1', '0.5', '0.25', '0.9', '1.0', '0.500', '0.001'])
        toks.append(t)
    return rng.choice([',', ', ', ' , ']).join(toks)


def _supported(rng):
    tags = [l + '-' + r for l in ['en', 'fr', 'de', 'es', 'it'] for r in ['US', 'CA', 'FR', 'GB', 'DE']]
    rng.shuffle(tags); return tags[:rng.randrange(0, 9)]


def _abt(rng, uid, n):
    names = ['a', 'b', 'c', 'd', 'e'][:rng.randrange(2, 6)]
    accounts = [[x, rng.choice([0, 1, 7, 100, 999, rng.randrange(10**9)])] for x in names]
    txs = []
    for _ in range(rng.randrange(0, 12)):
        f, t = rng.sample(names, 2); txs.append([f, t, rng.choice([0, 1, 33, 50, 99, 100, rng.randrange(101)])])
    calls = []
    for _ in range(n):
        op = rng.choice(['getBalance', 'getBalances'] + (['getBalanceAfter'] * 2 if uid == _o.ABT2 else []))
        who = rng.choice(names + ['zz'])
        if op == 'getBalance': calls.append((op, who))
        elif op == 'getBalances': calls.append((op,))
        else: calls.append((op, who, rng.randrange(len(txs) + 1)))
    return _ops('TransactionSystem', [accounts, txs], calls)


def _csv_row(rng, forbidden, ignore):
    ids = ['a1', 'b2', 'c3', 'X9', 'a1', '', 'a 1', 'a-1']
    words = ['acme', 'corp', 'the', 'of', 'bad', 'widget', 'Acme', 'and']
    def phrase(): return ' '.join(rng.choice(words) for _ in range(rng.randrange(0, 4)))
    amount = rng.choice(['0', '10', '10.50', '01', '1.5', '3.', '99.99', 'x', '1000000'])
    day = rng.choice(['2024-02-29', '2023-02-29', '1899-12-31', '2099-12-31', '2020-13-01', '2020-1-01', '2021-04-31', '2021-04-30', 'abc'])
    fields = [rng.choice(ids), phrase(), phrase(), rng.choice(['retail', 'bad deal', 'ok', 'Retail']), amount, day]
    if rng.random() < 0.1: fields.append('extra')
    if rng.random() < 0.05: fields[1] = ' ' + fields[1]
    return ','.join(fields)


def _dash(rng, n):
    recs = []
    for i in range(n):
        a = rng.randrange(0, 1440); b = rng.randrange(a, 1440)
        recs.append([f'o{i}', f'{a // 60:02d}:{a % 60:02d}', 'ACCEPTED'])
        st = rng.choice(['DELIVERED', 'DELIVERED', 'CANCELED', None])
        if st: recs.append([f'o{i}', f'{b // 60:02d}:{b % 60:02d}', st])
    rng.shuffle(recs); return recs


def _cam(rng, n):
    calls = []
    for _ in range(n):
        op = rng.choice(['requestLog', 'pollCommand', 'sendLog', 'pollLog'])
        if op == 'requestLog': calls.append((op, rng.randrange(3), rng.randrange(50)))
        elif op == 'pollCommand': calls.append((op, rng.randrange(4)))
        elif op == 'sendLog': calls.append((op, rng.randrange(3), rng.randrange(50), rng.choice(['', 'ok', 'motion at door'])))
        else: calls.append((op,))
    return _ops('CameraLogServer', [], calls)


def _messages(rng, n):
    ids = sorted(rng.sample(range(1, 4 * n + 5), n)); return [[i, f'm{i}'] for i in ids]


def _pricing(rng, uid):
    services = ['db.t3', 'ec2.m5', 's3', 'lambda']
    table = {}
    for region in rng.sample(['us-east-1', 'eu-west-1', 'ap-south-1'], rng.randrange(0, 3)):
        table[region] = {}
        for s in rng.sample(services, rng.randrange(0, 5)):
            if uid != _o.COST1 and rng.random() < 0.5:
                limits = sorted(rng.sample(range(1, 40), rng.randrange(0, 4)))
                table[region][s] = [[l, rng.choice(['0.0170', '1', '0.005', '2.5', '0'])] for l in limits] + [[None, rng.choice(['0.0049', '0.1', '3'])]]
            else: table[region][s] = rng.choice(['0.0170', '1', '0.005', '2.5', '0', '0.0001', '123.4567'])
    return table


def _usage(rng):
    return {'region': rng.choice(['us-east-1', 'eu-west-1', 'ap-south-1']),
            'services': [{'service': rng.choice(['db.t3', 'ec2.m5', 's3', 'lambda', 'gpu']), 'hours': rng.choice([0, 1, 3, 20, 37, 50, rng.randrange(80)])}
                         for _ in range(rng.randrange(0, 6))]}


def _css(rng, level, n):
    names = ['a', 'a/b', 'a/b.txt', 'b.txt', 'c/a.txt', 'cab']
    users = ['u1', 'u2', 'u3']
    ops = ['addFile', 'addFile', 'copyFile', 'getFilesize'] + (['findFile'] if level >= 2 else []) + \
        (['addUser', 'addFileBy', 'addFileBy', 'mergeUser'] if level >= 3 else []) + (['backupUser', 'restoreUser'] if level >= 4 else [])
    calls = []
    for _ in range(n):
        op = rng.choice(ops)
        if op == 'addFile': calls.append((op, rng.choice(names), rng.randrange(0, 20)))
        elif op == 'copyFile': calls.append((op, rng.choice(names), rng.choice(names)))
        elif op == 'getFilesize': calls.append((op, rng.choice(names)))
        elif op == 'findFile': calls.append((op, rng.choice(['', 'a', 'c', 'a/']), rng.choice(['', '.txt', 'b', 'xt'])))
        elif op == 'addUser': calls.append((op, rng.choice(users), rng.randrange(0, 40)))
        elif op == 'addFileBy': calls.append((op, rng.choice(users), rng.choice(names), rng.randrange(0, 20)))
        elif op == 'mergeUser': calls.append((op, rng.choice(users), rng.choice(users)))
        else: calls.append((op, rng.choice(users)))
    return _ops('CloudStorage', [], calls)


def _snake(rng):
    pieces = ['my_counter', '__the_variable', 'a_b_c', 'x', 'Not_snake', 'a__b', 'trail_', '_', '__', 'var_1', 'v_1a', '1_a', 'ab_Cd',
              ' ', '.', '(', ')', '\n', 'snake_case_name', '9', '_lead_x', 'a1_b2', 'q_', '=', '"str_lit"']
    return ''.join(rng.choice(pieces) for _ in range(rng.randrange(0, 12)))


def _mine(rng, uid):
    n = rng.randrange(0, 12)
    txs = [[f't{i}', rng.randrange(1, 12), rng.choice([0, 1, 5, 5, 9, rng.randrange(30)])] for i in range(n)]
    if uid == _o.MINE3:
        for i, t in enumerate(txs): t.append(None if i == 0 or rng.random() < 0.3 else f't{rng.randrange(i)}')
        rng.shuffle(txs)
    return [txs, rng.randrange(0, 40)]


def _fx(rng):
    cur = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'BGP', 'CAD'][:rng.randrange(2, 8)]
    worth = {c: rng.choice([1, 2, 3, 5, 8, 10, 100]) for c in cur}
    rates = []
    for a in cur:
        for b in cur:
            if a != b and rng.random() < 0.4:
                ideal = worth[a] * 10000 // worth[b]
                v = max(1, ideal - rng.choice([0, 0, 1, 7, ideal // 10]))
                s = str(v // 10000) + ('.' + f'{v % 10000:04d}'.rstrip('0') if v % 10000 else '')
                rates.append([a, b, s])
    return [rates, rng.choice(cur + ['XXX']), rng.choice(cur)]


def _crs(rng, uid, n):
    calls, count = [], 0
    for _ in range(n):
        op = rng.choice(['insert', 'insertWithReferrer', 'insertWithReferrer', 'getLowestK'] + (['getNestedRevenue'] * 2 if uid == _o.CRS2 else []))
        if count == 0: op = 'insert'
        if op == 'insert': calls.append((op, rng.randrange(0, 20))); count += 1
        elif op == 'insertWithReferrer': calls.append((op, rng.randrange(0, 20), rng.randrange(count))); count += 1
        elif op == 'getLowestK': calls.append((op, rng.randrange(0, 6), rng.choice([0, 5, 10, 20, 40])))
        else: calls.append((op, rng.randrange(count), rng.randrange(0, 4)))
    return _ops('CustomerRevenueSystem', [], calls)


def _kvdb(rng, n):
    calls = []
    for _ in range(n):
        op = rng.choice(['set', 'set', 'get', 'delete', 'count', 'begin', 'rollback', 'commit'])
        if op == 'set': calls.append((op, rng.choice('abc'), rng.choice(['1', '2'])))
        elif op in ('get', 'delete'): calls.append((op, rng.choice('abcd')))
        elif op == 'count': calls.append((op, rng.choice(['1', '2', '3'])))
        else: calls.append((op,))
    return _ops('InMemoryKVDB', [], calls)


def _inv(rng, n):
    vocab = ['the', 'quick', 'brown', 'fox', 'The', 'QUICK', 'fox,', 'dog.', 'a1']
    docs = [[f'd{i}', ' '.join(rng.choice(vocab) for _ in range(rng.randrange(0, 8)))] for i in range(rng.randrange(0, 6))]
    calls = [('search', ' '.join(rng.choice(vocab + ['', '!']) for _ in range(rng.randrange(0, 4)))) for _ in range(n)]
    return _ops('DocumentLibrary', [docs], calls)


def _random_args(uid, rng):
    o = _o
    if uid == o.WKV: return _wkv(rng, rng.randrange(1, 30))
    if uid in (o.ALH1, o.ALH2, o.ALH3, o.ALH4): return [_header(rng, uid), _supported(rng)]
    if uid in (o.ABT1, o.ABT2): return _abt(rng, uid, rng.randrange(1, 8))
    if uid == o.AFS: return [[rng.randrange(-3, 4) for _ in range(rng.randrange(0, 12))]]
    if uid == o.BAC1: return [[rng.randrange(1, 6) for _ in range(rng.randrange(0, 12))]]
    if uid == o.BAC2: return [[rng.randrange(1, 6) for _ in range(rng.randrange(0, 12))], rng.randrange(1, 5)]
    if uid == o.CSV:
        forbidden = rng.sample(['bad', 'scam', 'widget'], rng.randrange(0, 3)); ignore = rng.sample(['the', 'of', 'and', 'corp'], rng.randrange(0, 4))
        return [['id,name,desc,category,amount,date'] + [_csv_row(rng, forbidden, ignore) for _ in range(rng.randrange(0, 8))], forbidden, ignore]
    if uid == o.DASH: return [_dash(rng, rng.randrange(0, 8))]
    if uid == o.CAM: return _cam(rng, rng.randrange(1, 25))
    if uid == o.CHAT1:
        m = _messages(rng, rng.randrange(1, 15))
        return [m, [[rng.choice(m)[0], rng.randrange(0, 4), rng.randrange(0, 4)] for _ in range(rng.randrange(0, 5))]]
    if uid == o.CHAT2:
        pool = _messages(rng, 20)
        return [[sorted(rng.sample(pool, rng.randrange(0, 8))) for _ in range(rng.randrange(0, 5))]]
    if uid in (o.COST1, o.COST2, o.COST3): return [_usage(rng), _pricing(rng, uid)]
    if uid in (o.CSS1, o.CSS2, o.CSS3, o.CSS4): return _css(rng, [o.CSS1, o.CSS2, o.CSS3, o.CSS4].index(uid) + 1, rng.randrange(1, 30))
    if uid == o.SNAKE: return [_snake(rng)]
    if uid in (o.MINE1, o.MINE2, o.MINE3): return _mine(rng, uid)
    if uid == o.FX: return _fx(rng)
    if uid in (o.CRS1, o.CRS2): return _crs(rng, uid, rng.randrange(1, 30))
    if uid == o.C4: return _ops('ConnectFour', [], [('play', rng.choice([-1, 7] + [rng.randrange(3)] * 3 + list(range(7)) * 2)) for _ in range(rng.randrange(1, 45))])
    if uid == o.KVDB: return _kvdb(rng, rng.randrange(1, 30))
    if uid == o.INV: return _inv(rng, rng.randrange(1, 8))
    raise ValueError(uid)


def _boundary(uid):
    o = _o
    if uid == o.WKV:
        return [_ops('WindowedKeyValueStore', [1, 1], [('put', 1, 1, 0), ('get', 1, 0), ('get', 1, 1), ('put', 2, 2, 1), ('get', 1, 1), ('get', 2, 1)]),
                _ops('WindowedKeyValueStore', [2, 10], [('put', 1, 1, 0), ('put', 2, 2, 0), ('get', 1, 5), ('put', 3, 3, 6), ('get', 2, 6), ('get', 1, 9), ('get', 1, 10)])]
    if uid in (o.ALH1, o.ALH2, o.ALH3, o.ALH4):
        rows = [['en-US, fr-CA, fr-FR', ['fr-FR', 'en-US']], ['fr-FR', []], ['en-US,en-US', ['en-US']]]
        if uid != o.ALH1: rows.append(['fr, en-US', ['en-US', 'fr-CA', 'fr-FR', 'de-DE']])
        if uid in (o.ALH3, o.ALH4): rows.append(['fr-FR, *', ['en-US', 'fr-FR', 'de-DE']])
        if uid == o.ALH4: rows += [['fr-FR;q=1, fr;q=0.5, *;q=0', ['en-US', 'fr-CA', 'fr-FR']], ['*;q=0.1, en;q=0, en-US', ['en-GB', 'en-US', 'de-DE']]]
        return rows
    if uid in (o.ABT1, o.ABT2):
        return [_ops('TransactionSystem', [[['a', 100], ['b', 0]], [['a', 'b', 50], ['b', 'a', 33]]], [('getBalances',), ('getBalance', 'b')] +
                     ([('getBalanceAfter', 'b', 0), ('getBalanceAfter', 'b', 1), ('getBalanceAfter', 'q', 2)] if uid == o.ABT2 else []))]
    if uid == o.AFS: return [[[]], [[5]], [[2, 3, 1, 3, 2]], [[-1, -1, 10**9, -10**9]]]
    if uid == o.BAC1: return [[[]], [[3]], [[1, 1, 1]], [[5, 1, 1, 1, 1, 1]]]
    if uid == o.BAC2: return [[[], 3], [[1, 2, 3, 4], 1], [[5, 1, 1, 1, 1, 1], 3]]
    if uid == o.CSV:
        return [[['h'], [], []], [['h', 'a1,Acme Corp,the acme corp,retail,10.50,2024-02-29', 'a1,Acme,widgets,retail,1,2024-01-01', 'a2,x,y,bad,1,2024-01-01'], ['bad'], ['the']]]
    if uid == o.DASH: return [[[]], [[['o1', '00:00', 'ACCEPTED'], ['o1', '23:59', 'DELIVERED']]], [[['o1', '10:00', 'ACCEPTED'], ['o1', '10:00', 'DELIVERED']]]]
    if uid == o.CAM: return [_ops('CameraLogServer', [], [('pollLog',), ('pollCommand', 1), ('requestLog', 1, 5), ('requestLog', 2, 6), ('requestLog', 1, 7),
                                                         ('pollCommand', 1), ('sendLog', 1, 5, 'x'), ('pollLog',), ('pollCommand', 1), ('pollCommand', 1)])]
    if uid == o.CHAT1: return [[[[1, 'a']], []], [[[1, 'a'], [5, 'b'], [9, 'c'], [12, 'd']], [[1, 0, 0], [9, 0, 0], [5, 0, 0]]],
                               [[[1, 'a'], [5, 'b'], [9, 'c'], [12, 'd']], [[1, 0, 0], [12, 0, 0]]], [[[1, 'a'], [2, 'b']], [[2, 100000, 100000]]]]
    if uid == o.CHAT2: return [[[]], [[[], []]], [[[[1, 'a'], [3, 'c']], [[2, 'b'], [3, 'c']], [[1, 'a']]]]]
    if uid in (o.COST1, o.COST2, o.COST3):
        rows = [[{'region': 'us-east-1', 'services': []}, {}],
                [{'region': 'us-east-1', 'services': [{'service': 'db.t3', 'hours': 20}, {'service': 'x', 'hours': 5}]}, {'us-east-1': {'db.t3': '0.017'}}],
                [{'region': 'r', 'services': [{'service': 's', 'hours': 1}]}, {'r': {'s': '0.005'}}],
                [{'region': 'r', 'services': [{'service': 's', 'hours': 1}]}, {'r': {'s': '0.0049'}}]]
        if uid != o.COST1:
            rows.append([{'region': 'r', 'services': [{'service': 's', 'hours': 7}, {'service': 's', 'hours': 5}, {'service': 't', 'hours': 1}]},
                         {'r': {'s': [[10, '1'], [None, '0.5']], 't': '1'}}])
        return rows
    if uid in (o.CSS1, o.CSS2, o.CSS3, o.CSS4):
        calls = [('addFile', 'a/b.txt', 10), ('addFile', 'a/b.txt', 3), ('copyFile', 'a', 'x'), ('copyFile', 'a/b.txt', 'c.txt'), ('getFilesize', 'c.txt'),
                 ('getFilesize', 'a')]
        if uid != o.CSS1: calls += [('findFile', 'a', '.txt'), ('findFile', '', ''), ('addFile', 'a.txt', 10), ('findFile', 'a', 'txt')]
        if uid in (o.CSS3, o.CSS4): calls += [('addUser', 'u1', 15), ('addUser', 'u1', 3), ('addFileBy', 'u1', 'u.txt', 10), ('copyFile', 'u.txt', 'v.txt'),
                                              ('addFileBy', 'u1', 'w', 5), ('addUser', 'u2', 4), ('mergeUser', 'u1', 'u2'), ('mergeUser', 'u1', 'u1')]
        if uid == o.CSS4: calls += [('backupUser', 'u1'), ('addFileBy', 'u1', 'z', 1), ('restoreUser', 'u1'), ('getFilesize', 'z'), ('restoreUser', 'u9')]
        return [_ops('CloudStorage', [], calls)]
    if uid == o.SNAKE: return [[''], ['my_counter = my_counter + 1'], ['__the_variable'], ['a__b _x_ x_ X_y var_1 _ __ a_b.c_d']]
    if uid in (o.MINE1, o.MINE2, o.MINE3):
        if uid == o.MINE3: return [[[], 0], [[['a', 5, 1, None], ['b', 1, 10, 'a']], 5], [[['a', 5, 1, None], ['b', 1, 10, 'a']], 6], [[['b', 1, 10, 'a'], ['a', 5, 1, None]], 6]]
        return [[[], 0], [[['a', 1, 0]], 1], [[['a', 2, 3], ['b', 1, 3], ['c', 1, 0]], 2], [[['a', 3, 4], ['b', 1, 2], ['c', 2, 2]], 3]]
    if uid == o.FX: return [[[], 'USD', 'USD'], [[], 'USD', 'EUR'], [[['BGP', 'USD', '109.0'], ['USD', 'EUR', '0.9']], 'BGP', 'EUR'],
                            [[['AAA', 'BBB', '2'], ['BBB', 'CCC', '0.5'], ['AAA', 'CCC', '1.5']], 'AAA', 'CCC']]
    if uid in (o.CRS1, o.CRS2):
        calls = [('insert', 10), ('insertWithReferrer', 5, 0), ('insertWithReferrer', 7, 1), ('getLowestK', 3, 0), ('getLowestK', 0, 0), ('getLowestK', 5, 13)]
        if uid == o.CRS2: calls += [('getNestedRevenue', 0, 0), ('getNestedRevenue', 0, 1), ('getNestedRevenue', 0, 2), ('getNestedRevenue', 2, 5)]
        return [_ops('CustomerRevenueSystem', [], calls)]
    if uid == o.C4:
        return [_ops('ConnectFour', [], [('play', c) for c in [0, 1, 0, 1, 0, 1, 0, 1]]), _ops('ConnectFour', [], [('play', c) for c in [0, 0, 1, 1, 2, 2, 3]]),
                _ops('ConnectFour', [], [('play', c) for c in [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3]]), _ops('ConnectFour', [], [('play', c) for c in [3, 2, 2, 1, 1, 0, 1, 0, 0, 6, 0]]),
                _ops('ConnectFour', [], [('play', 0)] * 8 + [('play', -1), ('play', 7)]),
                _ops('ConnectFour', [], [('play', c) for c in [0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3, 4, 5, 4, 5, 4, 5, 6, 0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3, 4, 5, 4, 5, 4, 5, 6, 6, 6, 6, 6, 6]])]
    if uid == o.KVDB:
        return [_ops('InMemoryKVDB', [], [('rollback',), ('commit',), ('set', 'a', '1'), ('begin',), ('set', 'a', '2'), ('begin',), ('delete', 'a'), ('count', '2'),
                                          ('rollback',), ('get', 'a'), ('count', '2'), ('commit',), ('get', 'a'), ('rollback',)])]
    if uid == o.INV:
        return [_ops('DocumentLibrary', [[]], [('search', 'x')]),
                _ops('DocumentLibrary', [[['d1', 'The quick brown fox'], ['d2', 'quick, BROWN!'], ['d3', 'brown quick']]], [('search', 'Quick brown'), ('search', ''), ('search', '!!'), ('search', 'fox')])]
    return []


def _maximum(uid):
    """(args, expected) rows whose expectation is derived analytically, not by a candidate."""
    o = _o; out = []
    if uid == o.WKV:
        calls = [('put', i, i * 7, i) for i in range(10000)] + [('get', i, 20000 - i) for i in range(9999, 0, -1)]
        out.append((_ops('WindowedKeyValueStore', [100000, 10**9], calls), [None] * 10001 + [i * 7 for i in range(9999, 0, -1)]))
        calls = [('put', i % 3, i, i) for i in range(10000)] + [('get', 0, 10**9)] * 9999
        out.append((_ops('WindowedKeyValueStore', [1, 1], calls), [None] * 10001 + [-1] * 9999))
    elif uid in (o.ALH1, o.ALH2, o.ALH3, o.ALH4):
        tags = [chr(97 + i // 26 % 26) + chr(97 + i % 26) + '-' + r for i in range(40) for r in ('US', 'GB', 'CA', 'FR', 'DE')][:200]
        out.append((['  ,  '.join(reversed(tags)), tags], list(reversed(tags))))
    elif uid in (o.ABT1, o.ABT2):
        accounts = [[f'{chr(97 + i // 676)}{chr(97 + i // 26 % 26)}{chr(97 + i % 26)}', 10**9] for i in range(1000)]
        txs = [[accounts[i % 1000][0], accounts[(i + 1) % 1000][0], 0] for i in range(5000)]
        calls = [('getBalances',)] * 1000 + ([('getBalanceAfter', accounts[7][0], 4000)] * 2500 if uid == o.ABT2 else [('getBalance', accounts[7][0])] * 2500)
        bal = [[a, 10**9] for a, _ in accounts]
        out.append((_ops('TransactionSystem', [accounts, txs], calls), [None] + [bal] * 1000 + [10**9] * 2500))
    elif uid == o.AFS:
        out.append(([[(i * 7919) % 100003 - 50000 for i in range(100000)]], None))
    elif uid == o.BAC1:
        out.append(([[10**9] * 100000], [list(range(0, 100000, 2)), list(range(1, 100000, 2))]))
    elif uid == o.BAC2:
        out.append(([[10**9] * 100000, 1000], [list(range(c, 100000, 1000)) for c in range(1000)]))
        out.append(([[1] * 100000, 1], [list(range(100000))]))
    elif uid == o.CSV:
        rows = ['h'] + [f'id{i},alpha beta {i},gamma delta {i},retail,{i}.25,2024-02-29' for i in range(9999)]
        out.append(([rows, ['scam', 'fraud'], ['the', 'of']], list(range(1, 10000))))
    elif uid == o.DASH:
        recs = [r for i in range(10000) for r in ([f'o{i}', '00:00', 'ACCEPTED'], [f'o{i}', '23:59', 'DELIVERED'])]
        out.append(([recs], 10000 * 1439 * 30))
    elif uid == o.CAM:
        calls = [('requestLog', i % 10, i) for i in range(10000)] + [('pollCommand', i % 10) for i in range(10000)]
        out.append((_ops('CameraLogServer', [], calls), [None] * 10001 + list(range(10000))))
        calls = [('sendLog', i, i, 'log') for i in range(10000)] + [('pollLog',)] * 10000
        out.append((_ops('CameraLogServer', [], calls), [None] * 10001 + [[i, i, 'log'] for i in range(10000)]))
    elif uid == o.CHAT1:
        m = [[2 * i, 'x'] for i in range(100000)]
        out.append(([m, [[2 * i, 0, 0] for i in range(99999, -1, -2)]], [[2 * i, 2 * i] for i in range(1, 100000, 2)]))
        out.append(([m, [[100000, 100000, 100000]] * 100000], [[0, 199998]]))
    elif uid == o.CHAT2:
        pages = [[[i * 50 + j, 'c'] for j in range(100)] for i in range(1000)]
        out.append(([pages], [[i, 'c'] for i in range(50 * 999 + 100)]))
    elif uid in (o.COST1, o.COST2, o.COST3):
        services = [{'service': f's{i % 50}', 'hours': 10**6} for i in range(2000)]
        table = {'r': {f's{i}': '99999.9999' for i in range(50)}}
        per = 40 * 10**6 * 999999999  # 40 entries of 1e6 hours each, rate in 1e-4 dollars
        cents = (per + 50) // 100
        total = 50 * per; tc = (total + 50) // 100
        fmt = lambda c: f'{c // 100}.{c % 100:02d}'
        expect = fmt(tc) if uid != o.COST3 else {'total': fmt(tc), 'services': [[f's{i}', fmt(cents)] for i in sorted(range(50), key=lambda i: f's{i}')]}
        out.append(([{'region': 'r', 'services': services}, table], expect))
    elif uid in (o.CSS1, o.CSS2, o.CSS3, o.CSS4):
        calls = [('addFile', f'f{i}', i) for i in range(2500)] + [('getFilesize', f'f{i}') for i in range(2499)] + [('copyFile', 'f1', 'f2')]
        out.append((_ops('CloudStorage', [], calls), [None] + [True] * 2500 + list(range(2499)) + [False]))
        if uid != o.CSS1:
            calls = [('addFile', f'f{i}', i) for i in range(2500)] + [('findFile', 'f24', '9')] * 2500
            hits = [f'f{i}({i})' for i in (2499, 2489, 2479, 2469, 2459, 2449, 2439, 2429, 2419, 2409, 249)]
            out.append((_ops('CloudStorage', [], calls), [None] + [True] * 2500 + [hits] * 2500))
        if uid in (o.CSS3, o.CSS4):
            calls = [('addUser', 'u1', 10**9)] + [('addFileBy', 'u1', f'f{i}', 1) for i in range(4998)] + [('mergeUser', 'u1', 'u1')]
            out.append((_ops('CloudStorage', [], calls), [None, True] + [10**9 - i - 1 for i in range(4998)] + [-1]))
        if uid == o.CSS4:
            calls = [('addUser', 'u1', 10**9)] + [('addFileBy', 'u1', f'f{i}', 1) for i in range(400)] + [('backupUser', 'u1'), ('restoreUser', 'u1')] * 1500
            out.append((_ops('CloudStorage', [], calls), [None, True] + [10**9 - i - 1 for i in range(400)] + [400, 400] * 1500))
    elif uid == o.SNAKE:
        out.append((['a_b ' * 25000], 'aB ' * 25000))
        out.append((['_' * 100000], '_' * 100000))
    elif uid in (o.MINE1, o.MINE2):
        txs = [[f't{i}', 50, 1] for i in range(100)]
        out.append(([txs, 5000], 100 if uid == o.MINE1 else [f't{i}' for i in range(100)]))
        out.append(([txs, 4999], 99 if uid == o.MINE1 else [f't{i}' for i in range(99)]))
    elif uid == o.MINE3:
        txs = [[f't{i}', 20, 1, None if i == 0 else f't{i - 1}'] for i in range(100)]
        out.append(([list(reversed(txs)), 2000], 100))
        out.append(([txs, 1999], 99))
    elif uid == o.FX:
        cur = [chr(65 + i // 26) + chr(65 + i % 26) + 'X' for i in range(30)]
        rates = [[cur[i], cur[i + 1], '2'] for i in range(29)] + [[cur[i + 1], cur[i], '0.5'] for i in range(29)]
        out.append(([rates, cur[0], cur[29]], str(2 ** 29)))
        out.append(([rates, cur[29], cur[0]], '0.' + str(5 ** 29).rjust(29, '0')))
    elif uid in (o.CRS1, o.CRS2):
        calls = [('insert', 1)] + [('insertWithReferrer', 1, i) for i in range(999)] + \
            ([('getNestedRevenue', 0, 20000)] * 1000 if uid == o.CRS2 else [('getLowestK', 100, 0)] * 1000)
        # chain: total(i) = 2 except the last customer (1); lowest k: id 999 first, then ids 0..98
        expect = [1000] * 1000 if uid == o.CRS2 else [[999] + list(range(99))] * 1000
        out.append((_ops('CustomerRevenueSystem', [], calls), [None] + list(range(1000)) + expect))
    elif uid == o.C4:
        out.append((_ops('ConnectFour', [], [('play', 0), ('play', 1)] * 3 + [('play', 0)] + [('play', 3)] * 4993), [None] + ['ONGOING'] * 6 + ['A_WINS'] + ['INVALID'] * 4993))
    elif uid == o.KVDB:
        calls = [('set', f'k{i}', 'v') for i in range(5000)] + [('begin',)] * 5000 + [('count', 'v')] * 4999 + [('set', 'k0', 'w'), ('commit',), ('rollback',)] + \
            [c for i in range(2498) for c in (('begin',), ('delete', f'k{i}'))]
        out.append((_ops('InMemoryKVDB', [], calls), [None] * 10001 + [5000] * 4999 + [None, True, False] + [None, None] * 2498))
    elif uid == o.INV:
        docs = [[f'd{i}', f'Alpha beta W{i} ' + 'pad ' * 20] for i in range(1000)]
        calls = [('search', 'alpha BETA')] * 150 + [('search', f'beta w{i}') for i in range(1000)]
        out.append((_ops('DocumentLibrary', [docs], calls), [None] + [[f'd{i}' for i in range(1000)]] * 150 + [[f'd{i}'] for i in range(1000)]))
    return out


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode()))
    args = _boundary(uid) + [_random_args(uid, rng) for _ in range(200)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in _maximum(uid):
            validate_domain(uid, a)
            if expected is None: expected = reference(uid, a)  # still within the reference budget
            rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows
