"""Small deterministic development cases, frozen before candidate authoring."""
from itertools import product
from pathlib import Path
import importlib.util
import random

_spec = importlib.util.spec_from_file_location('chunk05_frozen_reference', Path(__file__).with_name('oracles.py'))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
reference = _module.reference


def build_cases(key):
    rng = random.Random('hack2hire-chunk05-v1:' + key)
    rows = []
    def trace(constructor, initial, actions):
        rows.append([[constructor] + [op for op, args in actions], [initial] + [args for op, args in actions]])
    if key == 'passwords':
        rows = [[''.join(chars)] for n in range(8) for chars in product('ab', repeat=n)]
        rows += [['abc'], ['abca'], ['🙂a🙂b'], ['aaaaa']]
    elif key == 'coverage':
        for _ in range(70):
            r, c = rng.randrange(1, 5), rng.randrange(1, 5)
            rows.append([[[rng.randrange(2) for _ in range(c)] for _ in range(r)], [[rng.randrange(2) for _ in range(c)] for _ in range(r)]])
        rows += [[[], []], [[[1, 0], [0, 1]], [[1, 0], [0, 1]]]]
    elif key == 'squares':
        queries = [[r, c] for r in range(6) for c in range(6)]
        rows = [[queries], [[]], [[[1, 1000], [1000, 1], [0, 200]]]]
    elif key == 'date':
        rows = [list(p) for p in product([0, 1, 2, 12, 13, 28, 29, 30, 31, 1900, 2000, 2024, 9999, 10000], repeat=3)]
    elif key == 'decode':
        for _ in range(40):
            board = [''.join(rng.choice('ABCXYZ') for _ in range(4)) for _ in range(3)]
            x, y = rng.randrange(4), rng.randrange(3)
            rows.append([[f'[{x}, {y}]', *board]])
    elif key == 'cluster':
        rows = [[[]], [[-1]], [[2, 2, -1, 0]], [[-1, 0, 0, 1, 1, 2]]]
        for n in range(2, 20):
            rows.append([[-1] + [rng.randrange(i) for i in range(1, n)]])
    elif key == 'goodness':
        rows = [[[int(c) for c in p]] for n in range(6) for p in product('012', repeat=n)]
        rows += [[[rng.randrange(32) for _ in range(rng.randrange(10))]] for _ in range(65)]
    elif key == 'products':
        rows = [[[]], [[2, 2, 3]], [[97]*10], [[2]], [[2, 3, 5, 7, 11]]]
        rows += [[[rng.choice([2, 3, 5, 7, 97]) for _ in range(rng.randrange(10))]] for _ in range(55)]
    elif key == 'cars':
        rows = [[['ab', 'AB']], [['a#A', 'b#B']], [['a.A', 'b.B']], [['a..B', '.##.', 'A..b']]]
        for _ in range(45):
            width = height = 3
            slots = rng.sample(range(width*height), 4)
            cells = ['#' if rng.random() < .25 else '.' for _ in range(9)]
            for i, ch in zip(slots, 'abAB'): cells[i] = ch
            rows.append([[''.join(cells[i:i+3]) for i in range(0, 9, 3)]])
    elif key == 'earliest':
        rows = [[0, 0, 0, 0, ''], [0, 0, 1, 1, 'EN'], [0, 0, 1, 0, 'WNN']]
        for _ in range(100):
            rows.append([rng.randrange(-2, 3), rng.randrange(-2, 3), rng.randrange(-3, 4), rng.randrange(-3, 4), ''.join(rng.choice('EWNS') for _ in range(10))])
    elif key == 'adjacent':
        rows = [[''.join(p)] for n in range(7) for p in product('ab', repeat=n)]
        rows += [['abcabc'], ['zzzzzzzzz'], ['aaabbbccc']]
    elif key == 'referrals':
        rows = [[[], []], [['a', 'a', 'b'], ['b', 'c', 'd']]]
        for n in range(2, 18):
            edges = [(str(rng.randrange(i)), str(i)) for i in range(1, n)]
            rng.shuffle(edges)
            rows.append([[a for a, b in edges], [b for a, b in edges]])
    elif key == 'timeline':
        rows = [[[]], [[['a', 0, 2], ['a', 1, 3], ['b', 2, 4]]], [[['z', 0, 1], ['z', 1, 3]]]]
        for _ in range(80):
            schedules = []
            for _ in range(rng.randrange(12)):
                start = rng.randrange(-4, 9)
                schedules.append([rng.choice(['z', 'a', 'b']), start, start+rng.randrange(1, 5)])
            rows.append([schedules])
    elif key == 'retry':
        rows = [[[{'ok': 7}], 1, 0, 2], [[{'error': 'x'}, {'ok': 3}], 3, 5, 2], [[{'error': 'a'}, {'error': 'b'}], 2, 4, 3], [[], 3, 0, 1]]
        for _ in range(50):
            outcomes = [{'error': 'E'+str(i)} for i in range(rng.randrange(7))]
            if rng.randrange(2): outcomes.append({'ok': rng.randrange(100)})
            rows.append([outcomes, rng.randrange(1, 8), rng.randrange(6), rng.randrange(1, 4)])
    elif key == 'ratings':
        for _ in range(35):
            actions = [('rank', [None])]
            for _ in range(25):
                actions.append(('record', [rng.choice(['alice', 'bob', 'zoe']), rng.randrange(1, 6), rng.choice(['2026-01', '2026-02'])]))
                actions.append(('rank', [rng.choice([None, '2026-01', '2026-02', 'missing'])]))
            trace('CustomerSupportSystem', [], actions)
    elif key == 'access':
        parents = {'World': None, 'EU': 'World', 'US': 'World', 'FR': 'EU', 'Paris': 'FR', 'Nice': 'FR'}
        for _ in range(35):
            actions = [('grant', ['a', 'World']), ('revoke', ['a', 'EU']), ('canAccess', ['a', 'Paris']), ('canAccess', ['a', 'US'])]
            actions += [(rng.choice(['grant', 'revoke', 'canAccess']), [rng.choice(['a', 'b']), rng.choice(list(parents))]) for _ in range(40)]
            trace('AccessSystem', [parents], actions)
    elif key == 'orders':
        trace('CryptoOrderManager', [], [('apply', ['a,BUY,BTC,2,FILLED']), ('apply', ['a,BUY,BTC,7,NEW']), ('apply', ['a,BUY,BTC,3,FILLED']), ('status', ['a']), ('apply', ['a,BUY,BTC,7,NEW']), ('status', ['a']), ('apply', ['a,BUY,ETH,1,FILLED']), ('apply', ['a,BUY,BTC,5,FILLED']), ('apply', ['a,BUY,BTC,4,FILLED']), ('status', ['a'])])
        for _ in range(35):
            actions = []
            for _ in range(45):
                oid = rng.choice(['a', 'b', 'c'])
                actions += [('apply', [f'{oid}, BUY, BTC, {rng.randrange(1, 8)}, {rng.choice(["NEW", "FILLED"])}']), ('status', [oid])]
            trace('CryptoOrderManager', [], actions)
    elif key == 'crypto':
        for _ in range(30):
            actions = []
            for _ in range(45):
                oid = rng.choice(['a', 'b', 'c'])
                op = rng.choice(['place', 'pause', 'resume', 'cancel', 'complete'])
                actions.append((op, [oid, rng.choice(['BTC', 'ETH']), 5, rng.randrange(8), 'buy'] if op == 'place' else [oid]))
                actions.append(('listLive', [rng.choice([None, 'BTC', 'ETH'])]))
            trace('CryptoTradingSystem', [], actions)
    elif key == 'ip':
        for start in ['0.0.0.0', '0.0.0.254', '1.255.255.254', '127.255.255.255', '255.255.255.254', '255.255.255.255']:
            trace('IPRangeIterator', [start], [('hasNext', []), ('next', []), ('hasNext', []), ('next', []), ('next', []), ('hasNext', [])])
    elif key == 'meeting':
        for _ in range(35):
            actions = [('book', [0, 2]), ('book', [2, 4]), ('book', [1, 3])]
            for _ in range(30):
                start = rng.randrange(9); actions.append(('book', [start, start+rng.randrange(1, 5)]))
            actions += [('schedule', [room]) for room in ['z', 'a']]
            trace('MeetingScheduler', [['z', 'a']], actions)
        trace('MeetingScheduler', [[]], [('book', [0, 1])])
    elif key == 'pagination':
        for _ in range(50):
            pages = [[str(rng.randrange(100)) for _ in range(rng.randrange(1, 5))] for _ in range(rng.randrange(6))]
            actions = [('fetchCount', []), ('read', [0]), ('fetchCount', [])]
            for _ in range(12): actions += [('read', [rng.randrange(5)]), ('fetchCount', [])]
            trace('PaginationAPI', [pages], actions)
    elif key == 'path':
        for _ in range(35):
            actions = [('get', ['/']), ('delete', ['/']), ('set', ['/', 'x'])]
            for _ in range(55):
                op = rng.choice(['get', 'create', 'set', 'delete']); path = rng.choice(['/', '/a', '/b', '/a/b', '/a/c', '/a/b/c'])
                actions.append((op, [path, str(rng.randrange(8))] if op in ('create', 'set') else [path]))
            trace('PathKeyValueStore', [], actions)
    elif key == 'radix':
        for _ in range(40):
            actions = [('insert', [[1, 2, 3], 5]), ('insert', [[1, 2], 6]), ('insert', [[1, 4], 7]), ('get', [[1, 2, 3]]), ('get', [[1]]), ('insert', [[], 9]), ('get', [[]])]
            pool = [[rng.randrange(-2, 3) for _ in range(rng.randrange(6))] for _ in range(12)]
            for _ in range(40):
                seq = rng.choice(pool); op = rng.choice(['insert', 'get']); actions.append((op, [seq, rng.randrange(8)] if op == 'insert' else [seq]))
            trace('RadixCache', [], actions)
    elif key == 'rate':
        for rules in [[], [[0, 1]], [[2, 3]], [[2, 3], [4, 10]], [[4, 10], [2, 3]], [[1, 1], [1, 1]]]:
            for _ in range(6):
                now = 0; actions = []
                for _ in range(60):
                    now += rng.randrange(3); actions.append(('allow', [now]))
                trace('RateLimiter', [rules], actions)
    elif key == 'lru':
        for _ in range(40):
            actions = []
            for _ in range(60):
                op = rng.choice(['get', 'put', 'resize'])
                actions.append((op, [rng.randrange(5), rng.randrange(10)] if op == 'put' else [rng.randrange(5)]))
            trace('LRUCache', [rng.randrange(5)], actions)
    elif key == 'trading':
        for _ in range(40):
            actions = []
            for _ in range(50):
                if rng.randrange(2): actions.append(('addListing', [rng.choice(['s1', 's2']), rng.choice(['x', 'y']), rng.randrange(1, 10)]))
                else: actions.append(('buy', [rng.choice(['x', 'y']), rng.randrange(10)]))
            trace('TradingSystem', [], actions)
    else:
        raise ValueError('No reference cases for ' + key)
    return [{'args': args, 'expected': reference(key, args), 'category': 'author-frozen-small-reference'} for args in rows]
