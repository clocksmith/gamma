"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h01a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _bank(rng, level, n):
    ids = ['a', 'b', 'c', 'd']
    calls, t, pays = [], 0, 0
    for _ in range(n):
        t += rng.choice([1, 2, 1000, _o.DAY_MS // 2, _o.DAY_MS])
        choices = ['createAccount', 'deposit', 'transfer'] + (['topSpenders'] if level >= 2 else []) + \
            (['pay', 'pay', 'getPaymentStatus'] if level >= 3 else []) + (['mergeAccounts', 'getBalance', 'getBalance'] if level >= 4 else [])
        op = rng.choice(choices); a, b = rng.choice(ids), rng.choice(ids)
        if op == 'createAccount': calls.append((op, t, a))
        elif op == 'deposit': calls.append((op, t, a, rng.randrange(1, 300)))
        elif op == 'transfer': calls.append((op, t, a, b, rng.randrange(1, 200)))
        elif op == 'topSpenders': calls.append((op, t, rng.randrange(1, 6)))
        elif op == 'pay': calls.append((op, t, a, rng.randrange(1, 250))); pays += 1
        elif op == 'getPaymentStatus': calls.append((op, t, a, 'payment' + str(rng.randrange(1, pays + 2))))
        elif op == 'mergeAccounts': calls.append((op, t, a, b))
        else: calls.append((op, t, a, rng.randrange(1, t + 1)))
    return _ops('BankingSystem', [], calls)


def _delivery(rng, level, n):
    calls, drivers = [], []
    for _ in range(n):
        choices = ['addDriver', 'addDelivery', 'addDelivery', 'getTotalCost'] + (['payUpTo', 'getTotalCostUnpaid'] if level >= 2 else []) + \
            (['getMaxActiveDriversInLast24Hours'] * 2 if level >= 3 else [])
        op = rng.choice(choices)
        if op == 'addDriver' or (op == 'addDelivery' and not drivers):
            d = rng.randrange(0, 10**9) if rng.random() < 0.5 else len(drivers)
            while d in drivers: d += 1
            drivers.append(d); calls.append(('addDriver', d, rng.choice([1, 999, 1000, 1001, 3333, rng.randrange(1, 100001)])))
        elif op == 'addDelivery':
            s = rng.randrange(0, 300000); calls.append((op, rng.choice(drivers), s, s + rng.choice([1, 59, 1800, 5400, rng.randrange(1, _o.DAY_S + 1)])))
        elif op in ('payUpTo', 'getMaxActiveDriversInLast24Hours'): calls.append((op, rng.randrange(0, 400000)))
        else: calls.append((op,))
    return _ops('DeliverySystem', [], calls)


def _document(rng, level, n):
    names = ['setProperty'] * 3 + ['getProperty'] * 2 + ['undo'] + (['redo'] if level >= 2 else []) + (['removeProperty', 'getProperties'] if level >= 3 else [])
    calls = []
    for _ in range(n):
        op = rng.choice(names); layer = rng.randrange(3); key = rng.choice(['color', 'size', 'shape'])
        if op == 'setProperty': calls.append((op, layer, key, rng.choice(['red', 'blue', '', '#fff', '10'])))
        elif op in ('getProperty', 'removeProperty'): calls.append((op, layer, key))
        elif op == 'getProperties': calls.append((op, layer))
        else: calls.append((op,))
    return _ops('Document', [], calls)


def _tennis(rng, name, getters, n, bias):
    calls = []
    for _ in range(n):
        if rng.random() < 0.6: calls.append(('pointTo', 'A' if rng.random() < bias else 'B'))
        else: calls.append((rng.choice(getters),))
    return _ops(name, [], calls)


def _fs(rng, nested, n):
    dirs = ['/a', '/a/b', '/a/bc', '/x', '/a/b/c']
    names = ['f.txt', 'fa.txt', 'g.py', 'readme', 'a.b.txt', 'fb.py', 'x_1.md']
    def leaf():
        k = rng.randrange(3)
        return ['sizeGreaterThan', rng.choice([0, 10, 50, 100])] if k == 0 else \
            ['extension', rng.choice(['txt', 'py', '', 'md', 'b'])] if k == 1 else ['namePrefix', rng.choice(['f', 'fa', '', 'a.', 'x'])]
    def expr(depth):
        if depth == 0 or rng.random() < 0.4: return leaf()
        k = rng.randrange(3)
        if k == 2: return ['not', expr(depth - 1)]
        return [['and', 'or'][k], [expr(depth - 1) for _ in range(rng.randrange(0, 4))]]
    calls = []
    for _ in range(n):
        if rng.random() < 0.55: calls.append(('addFile', rng.choice(dirs) + '/' + rng.choice(names), rng.choice([0, 10, 11, 50, 99, 100, 101])))
        else:
            d = rng.choice(['/'] + dirs)
            calls.append(('find', d, [leaf() for _ in range(rng.randrange(0, 3))] if not nested else expr(3)))
    return _ops('FileSystem', [], calls)


def _tree(rng, n, depth=0):
    node = {'key': 'k' + str(rng.randrange(100)), 'value': rng.choice(['', '$5', 'soup', '9.99']), 'active': rng.random() < 0.7, 'children': []}
    while n[0] > 0 and depth < 6 and rng.random() < 0.6:
        n[0] -= 1; node['children'].append(_tree(rng, n, depth + 1))
    return node


def _forest(rng, n):
    order = list(range(n)); rng.shuffle(order)
    parent = [0] * n
    for i, v in enumerate(order):
        parent[v] = v if i == 0 or rng.random() < 0.2 else order[rng.randrange(i)]
    return parent


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.ADS:
        args = [[[], [], {}, []], [['top'], [{'adId': 'x', 'maxDisplay': 0}], {}, [5]]]
        for _ in range(200):
            p = rng.randrange(0, 6); ads = [{'adId': 'ad' + str(i), 'maxDisplay': rng.randrange(0, 3)} for i in range(rng.randrange(0, 6))]
            state = {'ad' + str(i): rng.randrange(0, 3) for i in range(8) if rng.random() < 0.5}
            args.append([['p' + str(i) for i in range(p)], ads, state, [rng.choice([0, 1, 2, 7, 2**31 - 1]) for _ in range(p)]])
    elif uid in (o.CAM1, o.CAM2):
        def cam():
            n = rng.randrange(0, 9); times = sorted(rng.sample(range(0, 40), n)); return [times, [rng.randrange(0, 6) for _ in range(n)]]
        for _ in range(250):
            args.append(cam() + [rng.randrange(0, 6)] if uid == o.CAM1 else cam() + cam() + [rng.randrange(0, 6)])
        args.append([[0, 10**9], [10**9, 10**9], 10**9] if uid == o.CAM1 else [[0, 10**9], [10**9, 10**9], [10**9], [10**9], 0])
    elif uid == o.PACK:
        args = [[[0]], [[1]], [[0, 0, 0]], [[1, 1]], [[2, 3]], [[5, 7, 11]], [[6, 10, 15]]]
        args += [[[rng.randrange(0, 60) for _ in range(rng.randrange(1, 8))]] for _ in range(200)]
        args += [[[rng.randrange(0, 3000) for _ in range(50)]] for _ in range(10)]
    elif uid == o.CRAWL:
        hosts = ['http://a.com', 'http://b.com', 'http://a.com.au', 'http://sub.a.com']
        for _ in range(150):
            urls = [rng.choice(hosts) + rng.choice(['', '/', '/x', '/x/y', '/y.html']) for _ in range(rng.randrange(1, 10))]
            links = {u: [rng.choice(urls) for _ in range(rng.randrange(0, 4))] for u in urls if rng.random() < 0.8}
            args.append([rng.choice(urls), links])
        args.append(['http://a.com', {}])
    elif uid == o.MENU:
        args = [[{'key': 'root', 'value': '', 'active': False, 'children': []}], [{'key': 'root', 'value': '', 'active': True, 'children': []}]]
        args += [[_tree(rng, [rng.randrange(0, 25)])] for _ in range(200)]
    elif uid == o.ISLAND:
        args = [[[['0']]], [[['1']]], [[['1', '1'], ['1', '1']]]]
        for _ in range(200):
            m, n = rng.randrange(1, 8), rng.randrange(1, 8)
            args.append([[[rng.choice('01') for _ in range(n)] for _ in range(m)]])
    elif uid == o.FLIP:
        args = [['0', []], ['1', ['count:0', 'flip', 'count:0']]]
        for _ in range(200):
            n = rng.randrange(1, 12); s = ''.join(rng.choice('01') for _ in range(n))
            args.append([s, [rng.choice(['flip', 'count:' + str(rng.randrange(n))]) for _ in range(rng.randrange(0, 12))]])
    elif uid in (o.FOREST1, o.FOREST2):
        args = [[[0], 0] if uid == o.FOREST1 else [[0], [0, 0]], [[1, 1], 1] if uid == o.FOREST1 else [[1, 1], []]]
        for _ in range(250):
            n = rng.randrange(1, 15); parent = _forest(rng, n)
            args.append([parent, rng.randrange(n)] if uid == o.FOREST1 else [parent, [rng.randrange(n) for _ in range(rng.randrange(0, 5))]])
    elif uid in (o.DELIVERY1, o.DELIVERY2, o.DELIVERY3):
        level = (o.DELIVERY1, o.DELIVERY2, o.DELIVERY3).index(uid) + 1
        args = [_ops('DeliverySystem', [], [('getTotalCost',)])]
        args.append(_ops('DeliverySystem', [], [('addDriver', 1, 1000), ('addDelivery', 1, 0, 5400), ('getTotalCost',)]))
        args.append(_ops('DeliverySystem', [], [('addDriver', 1, 1), ('addDelivery', 1, 0, 1800), ('addDelivery', 1, 0, 1799), ('getTotalCost',)]))
        args += [[*_delivery(rng, level, rng.randrange(1, 40))] for _ in range(150)]
    elif uid in (o.DEPLOY1, o.DEPLOY2):
        args = [[[]], [['0,10080,allowed']], [['0,10080,allowed', '0,10080,freeze']], [['5,10,freeze']]]
        for _ in range(200):
            recs = []
            for _ in range(rng.randrange(0, 8)):
                a = rng.randrange(0, 60) if rng.random() < 0.8 else rng.randrange(0, o.WEEK)
                b = rng.randrange(a + 1, min(a + 30, o.WEEK) + 1)
                recs.append(f'{a},{b},{rng.choice(["allowed", "allowed", "freeze"])}')
            args.append([recs])
    elif uid in (o.BANK1, o.BANK2, o.BANK3, o.BANK4):
        level = (o.BANK1, o.BANK2, o.BANK3, o.BANK4).index(uid) + 1
        args = [_ops('BankingSystem', [], [('createAccount', 1, 'a'), ('createAccount', 2, 'a'), ('deposit', 3, 'a', 100), ('deposit', 4, 'z', 5), ('transfer', 5, 'a', 'a', 1)])]
        args += [[*_bank(rng, level, rng.randrange(1, 45))] for _ in range(200)]
    elif uid in (o.CARD1, o.CARD2, o.CARD3):
        deck = o.full_deck()
        for i in range(120):
            d = [list(c) for c in deck]
            if i: rng.shuffle(d)
            args.append([d] if uid == o.CARD1 else [d, rng.choice([1, 2, 3, 4, 5, 13, 17, 26, 51, 52, rng.randrange(1, 53)])])
    elif uid == o.CONNECT:
        args = [_ops('ConnectKGame', [1], [('placePiece', 'B', 0)]), _ops('ConnectKGame', [20], [('placePiece', 'R', -10**9)])]
        for _ in range(200):
            k = rng.randrange(1, 5); cols = rng.randrange(1, 5)
            args.append(_ops('ConnectKGame', [k], [('placePiece', rng.choice('BR'), rng.randrange(-1, cols - 1)) for _ in range(rng.randrange(1, 25))]))
    elif uid in (o.DOC1, o.DOC2, o.DOC3):
        level = (o.DOC1, o.DOC2, o.DOC3).index(uid) + 1
        args = [_ops('Document', [], [('undo',), ('getProperty', 0, 'color')])]
        args += [[*_document(rng, level, rng.randrange(1, 40))] for _ in range(200)]
    elif uid == o.TENNIS1:
        args = [_ops('TennisGame', [], [('getScore',), ('getWinner',), ('getPoints',)])]
        args += [[*_tennis(rng, 'TennisGame', ['getPoints', 'getScore', 'getWinner'], rng.randrange(1, 40), rng.choice([0.5, 0.3, 0.8]))] for _ in range(200)]
    elif uid == o.TENNIS2:
        args = [_ops('TennisSet', [], [('getGameScore',), ('getWinner',), ('getGames',)])]
        args += [[*_tennis(rng, 'TennisSet', ['getGames', 'getGameScore', 'getWinner'], rng.randrange(1, 300), rng.choice([0.5, 0.52, 0.7]))] for _ in range(150)]
    elif uid in (o.FIND1, o.FIND2):
        args = [_ops('FileSystem', [], [('find', '/', [] if uid == o.FIND1 else ['and', []])])]
        args += [[*_fs(rng, uid == o.FIND2, rng.randrange(1, 30))] for _ in range(200)]
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Domain-bound rows whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.ADS:
        ads = [{'adId': 'a' + str(i), 'maxDisplay': 1} for i in range(2000)]
        out.append(([['p' + str(i) for i in range(2000)], ads, {}, [0] * 2000], ['a' + str(i) for i in range(2000)]))
        out.append(([['p' + str(i) for i in range(2000)], ads, {}, [2**31 - 1] * 2000],
                    _ads_last(2000)))
    elif uid == o.CAM1:
        n = 100000
        out.append(([list(range(0, 2 * n, 2)), [i % 2 * 10**9 for i in range(n)], 1], [[2 * i, 2 * i] for i in range(1, n, 2)]))
        out.append(([list(range(n)), [10**9] * n, 10**9], [[0, n - 1]]))
    elif uid == o.CAM2:
        n = 100000
        out.append(([list(range(n)), [i % 2 for i in range(n)], list(range(n)), [1] * n, 1], [[i, i] for i in range(1, n, 2)]))
    elif uid == o.PACK:
        out.append(([[100000] * 100000], 0))
        out.append(([[99999, 1] * 50000], 100000))  # every p costs (p-1)+(-99999 mod p) >= 2 per pair; p=2,3 reach 2
    elif uid == o.CRAWL:
        links = {f'http://a.com/{i}': [f'http://a.com/{i + 1}', f'http://b.com/{i}'] for i in range(5000)}
        out.append((['http://a.com/0', links], sorted(f'http://a.com/{i}' for i in range(5001))))
    elif uid == o.MENU:
        chain = None
        for i in range(199):  # amended after freeze: depth 499 exceeded Python recursion in deepcopy and the easy16 transport encoder
            chain = {'key': 'k', 'value': 'v', 'active': True, 'children': [] if chain is None else [chain]}
        root = {'key': 'root', 'value': '', 'active': True, 'children': [chain] + [{'key': 'i', 'value': '$1', 'active': True, 'children': []} for _ in range(19800)]}
        out.append(([root], root))
        mixed = {'key': 'root', 'value': '', 'active': True, 'children': [{'key': 'c', 'value': '', 'active': i % 2 == 0, 'children': [{'key': 'i', 'value': '', 'active': True, 'children': []}]} for i in range(9999)]}
        kept = {'key': 'root', 'value': '', 'active': True, 'children': [{'key': 'c', 'value': '', 'active': True, 'children': [{'key': 'i', 'value': '', 'active': True, 'children': []}]} for i in range(5000)]}
        out.append(([mixed], kept))
    elif uid == o.ISLAND:
        out.append(([[['1'] * 300 for _ in range(300)]], [[90000, 0]]))
        out.append(([[[str((r + c) % 2) for c in range(300)] for r in range(300)]], [[1, _checker_edges(r, c)] for r in range(300) for c in range(300) if (r + c) % 2]))
    elif uid == o.FLIP:
        n = 100000
        out.append((['1' * n, ['flip', 'count:99999'] * 50000], [0, n] * 25000))
    elif uid == o.FOREST1:
        n = 100000
        out.append(([[max(i - 1, 0) for i in range(n)], 0], [-1] * n))
        out.append(([[i + 1 if i + 1 < n else i for i in range(n)], n - 1], [-1] * n))
    elif uid == o.FOREST2:
        n = 100000
        out.append(([[max(i - 1, 0) for i in range(n)], list(range(n))], [-1] * n))
        out.append(([[max(i - 1, 0) for i in range(n)], [n // 2] * 100000], [max(i - 1, 0) for i in range(n // 2)] + [-1] * (n - n // 2)))
    elif uid in (o.DELIVERY1, o.DELIVERY2, o.DELIVERY3):
        calls = [('addDriver', i, 100000) for i in range(2500)] + [('addDelivery', i, 10**9 - o.DAY_S, 10**9) for i in range(2499)] + [('getTotalCost',)]
        out.append((_ops('DeliverySystem', [], calls), [None] * 5000 + [f'{2499 * 24 * 1000}.00']))
        if uid != o.DELIVERY1:
            calls = [('addDriver', 0, 3)] + [('addDelivery', 0, i, i + 1) for i in range(3998)] + [('payUpTo', 1999), ('getTotalCostUnpaid',)] * 500
            out.append((_ops('DeliverySystem', [], calls), [None] * 4000 + [None, o.dollars(o.Fraction(1999 * 3, 3600))] * 500))
        if uid == o.DELIVERY3:
            calls = [('addDriver', i, 1) for i in range(1000)] + [('addDelivery', i, 0, o.DAY_S) for i in range(1000)] + [('getMaxActiveDriversInLast24Hours', o.DAY_S)] * 3000
            out.append((_ops('DeliverySystem', [], calls), [None] * 2001 + [1000] * 3000))
    elif uid == o.DEPLOY1:
        out.append(([['0,10080,allowed'] * 10000 + ['1,10079,freeze'] * 10000], 2))
    elif uid == o.DEPLOY2:
        out.append(([[f'{i},{i + 1},allowed' for i in range(10080)] + [f'{i},{i + 1},freeze' for i in range(0, 10080, 2)]], [[i, i + 1] for i in range(1, 10080, 2)]))
    elif uid in (o.BANK1, o.BANK2, o.BANK3, o.BANK4):
        calls = [('createAccount', 1, 'a'), ('createAccount', 2, 'b')] + [('deposit', 3 + i, 'a', 10**6) for i in range(4998)]
        exp = [None, True, True] + [10**6 * (i + 1) for i in range(4998)]
        out.append((_ops('BankingSystem', [], calls), exp))
        calls = [('createAccount', 1, 'a'), ('createAccount', 2, 'b'), ('deposit', 3, 'a', 1)] + [('transfer', 4 + i, 'ab'[i % 2], 'ba'[i % 2], 1) for i in range(4997)]
        out.append((_ops('BankingSystem', [], calls), [None, True, True, 1] + [0] * 4997))
        if uid != o.BANK1:
            calls = [('createAccount', i + 1, f'u{i}') for i in range(1000)] + [('topSpenders', 1001 + i, 1000) for i in range(2000)]
            top = sorted(f'u{i}(0)' for i in range(1000))
            out.append((_ops('BankingSystem', [], calls), [None] + [True] * 1000 + [top] * 2000))
        if uid in (o.BANK3, o.BANK4):
            calls = [('createAccount', 1, 'a'), ('deposit', 2, 'a', 10**6)] + [('pay', 3 + i, 'a', 100) for i in range(2000)] + \
                [('getPaymentStatus', o.DAY_MS + 5000 + i, 'a', f'payment{i + 1}') for i in range(2000)] + [('deposit', o.DAY_MS + 9000, 'a', 1)]
            out.append((_ops('BankingSystem', [], calls), [None, True, 10**6] + [f'payment{i + 1}' for i in range(2000)] + ['CASHBACK_RECEIVED'] * 2000 + [10**6 - 200000 + 4000 + 1]))
        if uid == o.BANK4:
            calls = [('createAccount', 1, 'a'), ('deposit', 2, 'a', 7)] + [('getBalance', 3 + i, 'a', 1 + (i % 2)) for i in range(4000)]
            out.append((_ops('BankingSystem', [], calls), [None, True, 7] + [0, 7] * 2000))
    elif uid == o.CARD1:
        out.append(([o.full_deck()], [[c for j, c in enumerate(o.full_deck()) if j % 4 == p] for p in range(4)]))
    elif uid == o.CARD2:
        out.append(([o.full_deck(), 52], [[c] for c in o.full_deck()]))
    elif uid == o.CARD3:
        out.append(([o.full_deck(), 1], [52]))
        out.append(([o.full_deck(), 52], [0] * 51 + [1]))
    elif uid == o.CONNECT:
        calls = [('placePiece', 'B', 0)] * 400
        out.append((_ops('ConnectKGame', [20], calls), [None] + [False] * 19 + [True] * 381))
        calls = [('placePiece', 'BR'[i % 2], 0) for i in range(400)]
        out.append((_ops('ConnectKGame', [20], calls), [None] + [False] * 400))
        calls = [('placePiece', 'B', c) for c in range(20)] + [('placePiece', 'R', 100 + 3 * i) for i in range(380)]
        out.append((_ops('ConnectKGame', [20], calls), [None] + [False] * 19 + [True] + [False] * 380))
    elif uid in (o.DOC1, o.DOC2, o.DOC3):
        calls = [('setProperty', i, 'color', 'red') for i in range(2500)] + [('undo',)] * 2500
        out.append((_ops('Document', [], calls), [None] * 2501 + [True] * 2500))
        if uid != o.DOC1:
            calls = [('setProperty', 0, 'k', str(i)) for i in range(1666)] + [('undo',)] * 1667 + [('redo',)] * 1667
            out.append((_ops('Document', [], calls), [None] * 1667 + [True] * 1666 + [False] + [True] * 1666 + [False]))
        if uid == o.DOC3:
            calls = [('setProperty', 0, 'k' + chr(97 + i % 26) * (1 + i // 26 % 9), 'v') for i in range(234)] + [('getProperties', 0)] * 4766
            props = sorted(['k' + chr(97 + i % 26) * (1 + i // 26 % 9), 'v'] for i in range(234))
            out.append((_ops('Document', [], calls), [None] * 235 + [props] * 4766))
    elif uid == o.TENNIS1:
        calls = [('pointTo', 'AB'[i % 2]) for i in range(4996)] + [('getScore',), ('getPoints',), ('getWinner',), ('pointTo', 'A')]
        out.append((_ops('TennisGame', [], calls), [None] * 4997 + ['Deuce', [2498, 2498], '', None]))
    elif uid == o.TENNIS2:
        calls = [('pointTo', 'AB'[i % 2]) for i in range(4996)] + [('getGameScore',), ('getGames',), ('getWinner',), ('pointTo', 'A')]
        out.append((_ops('TennisSet', [], calls), [None] * 4997 + ['Deuce', [0, 0], '', None]))
        calls = [('pointTo', 'A')] * 4999 + [('getGames',)]
        out.append((_ops('TennisSet', [], calls), [None] * 5000 + [[6, 0]]))
    elif uid in (o.FIND1, o.FIND2):
        calls = [('addFile', f'/d/s{i % 10}/f{i}.txt', i) for i in range(1500)] + \
            [('find', '/d', [['sizeGreaterThan', 1497]] if uid == o.FIND1 else ['or', [['sizeGreaterThan', 1497], ['not', ['extension', 'txt']]]])] * 500  # amended: 1500 finds exceeded ~1 CPU s per case (each find must scan the whole subtree)
        out.append((_ops('FileSystem', [], calls), [None] * 1501 + [['/d/s8/f1498.txt', '/d/s9/f1499.txt']] * 500))
    return out


def _ads_last(n):
    # index 2**31-1 modulo shrinking eligible list size m picks position (2**31-1) % m among remaining ads in order.
    remaining = list(range(n)); out = []
    for _ in range(n):
        i = (2**31 - 1) % len(remaining); out.append('a' + str(remaining.pop(i)))
    return out


def _checker_edges(r, c):
    return sum(1 for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if 0 <= rr < 300 and 0 <= cc < 300)
