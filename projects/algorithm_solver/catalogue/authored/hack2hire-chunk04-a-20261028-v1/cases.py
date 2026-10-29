"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from itertools import product
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h04a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _credit(rng, level, n):
    calls, made = [], 0
    for _ in range(n):
        names = ['addAccount'] + (['addAccountWithReferral', 'addAccountWithReferral', 'getTotalCredit', 'getTotalCredit'] if made else [])
        if made and level == 2: names += ['getTopAccounts', 'getTopAccounts']
        op = rng.choice(names); credit = rng.choice([0, 1, 5, 10, 10**6, rng.randrange(100)])
        if op == 'addAccount': calls.append((op, credit)); made += 1
        elif op == 'addAccountWithReferral': calls.append((op, credit, rng.randrange(made))); made += 1
        elif op == 'getTotalCredit': calls.append((op, rng.randrange(made)))
        else: calls.append((op, rng.randrange(1, 6)))
    return _ops('AccountCreditTracker', [], calls)


DC = ['A', 'B', 'a', 'dc1', 'dc10', 'dc2']


def _command(rng, level):
    kw = rng.choice(['REGISTER', 'REGISTER', 'ROUTE', 'ROUTE', 'ROUTE', 'UP', 'DOWN', 'RELEASE', 'RELEASE', 'BOGUS', 'route'])
    num = lambda lo, hi: rng.choice([str(rng.randrange(lo, hi + 1)), str(lo), str(hi), str(lo - 1), str(hi + 1), 'x', '05', '-0', '1.5'] + [str(rng.randrange(-3, 4))] * 15)
    if kw == 'REGISTER':
        t = [kw, rng.choice(DC), num(-90, 90), num(-180, 180), rng.choice(['1', '2', '3', '0', '-1', str(rng.randrange(1, 4))])]
    elif kw in ('ROUTE', 'route'): t = [kw, num(-90, 90), num(-180, 180)]
    elif kw == 'BOGUS': t = [kw]
    else: t = [kw, rng.choice(DC)]
    if rng.random() < 0.05: t = t[:-1] if len(t) > 1 else t + ['extra']
    return ' '.join(t)


def _router(rng, level, n):
    return _ops('RequestRouter', [], [('processCommand', _command(rng, level)) for _ in range(n)])


def _snap(rng, level, n, users):
    calls, snaps = [], 0
    names = ['follow', 'follow', 'follow', 'unfollow', 'snapshot'] + (['isFollowing'] * 2 if snaps else [])
    for _ in range(n):
        names = ['follow', 'follow', 'follow', 'unfollow', 'snapshot']
        if snaps: names += ['isFollowing', 'isFollowing'] + (['getFollowees'] if level >= 2 else []) + (['recommend', 'recommend'] if level >= 3 else [])
        op = rng.choice(names)
        f, e = rng.sample(users, 2)
        if op in ('follow', 'unfollow'): calls.append((op, f, e))
        elif op == 'snapshot': calls.append((op,)); snaps += 1
        elif op == 'isFollowing': calls.append((op, f, e, rng.randrange(snaps)))
        elif op == 'getFollowees': calls.append((op, f, rng.randrange(snaps)))
        else: calls.append((op, f, rng.randrange(snaps), rng.randrange(1, 4)))
    return _ops('SocialNetwork', [], calls)


def _iter(rng):
    vals = [rng.randrange(-3, 6) for _ in range(rng.randrange(0, 8))]
    b = [rng.choice(vals + [7, -1]) for _ in range(rng.randrange(0, 5))] if vals or rng.random() < 0.5 else []
    total = len(b) + sum(1 for x in vals if x not in b)
    calls, left = [], total
    for _ in range(rng.randrange(0, 2 * total + 3)):
        if left and rng.random() < 0.6: calls.append(('next',)); left -= 1
        else: calls.append(('hasNext',))
    return _ops('SubarrayFirstIterator', [vals, b], calls)


def _incident_logs(rng, n):
    logs = []
    for _ in range(n):
        logs.append('%d,%s,%d,%d' % (rng.randrange(0, 30), rng.choice(['m1', 'm2', 'shop']), rng.choice([200, 200, 500, 404, 503]), rng.choice([0, 1, 1, 2, 3, 7])))
    return logs


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid in (o.CREDIT1, o.CREDIT2):
        level = 1 if uid == o.CREDIT1 else 2
        args = [_ops('AccountCreditTracker', [], []), _ops('AccountCreditTracker', [], [('addAccount', 10**6), ('getTotalCredit', 0)])]
        if level == 2: args.append(_ops('AccountCreditTracker', [], [('addAccount', 3), ('addAccount', 3), ('getTopAccounts', 20), ('addAccountWithReferral', 0, 1), ('getTopAccounts', 1)]))
        args += [_credit(rng, level, rng.randrange(1, 25)) for _ in range(250)]
    elif uid in (o.ROUTE1, o.ROUTE2, o.ROUTE3):
        level = (o.ROUTE1, o.ROUTE2, o.ROUTE3).index(uid) + 1
        args = [_ops('RequestRouter', [], [('processCommand', 'ROUTE 0 0'), ('processCommand', 'REGISTER a 90 180 1'), ('processCommand', 'REGISTER a 0 0 1'),
                                           ('processCommand', 'REGISTER b -90 -180 1'), ('processCommand', 'ROUTE -90 -180'), ('processCommand', 'ROUTE 0 0'),
                                           ('processCommand', 'ROUTE 0 0'), ('processCommand', 'DOWN a'), ('processCommand', 'RELEASE a'), ('processCommand', 'ROUTE 1 1')])]
        args += [_router(rng, level, rng.randrange(1, 30)) for _ in range(250)]
    elif uid in (o.SNAP1, o.SNAP2, o.SNAP3):
        level = (o.SNAP1, o.SNAP2, o.SNAP3).index(uid) + 1
        args = [_ops('SocialNetwork', [], [('snapshot',), ('isFollowing', 1, 2, 0)]),
                _ops('SocialNetwork', [], [('follow', 1, 2), ('snapshot',), ('unfollow', 1, 2), ('follow', 1, 2), ('unfollow', 1, 2), ('snapshot',),
                                           ('isFollowing', 1, 2, 0), ('isFollowing', 1, 2, 1), ('isFollowing', 2, 1, 0)])]
        for _ in range(250):
            users = rng.choice([[1, 2, 3], [0, 1, 2, 3, 4, 5], [7, 10**9, 42, 5]])
            args.append(_snap(rng, level, rng.randrange(1, 40), users))
    elif uid == o.STAY:
        args = [[[], 0, 0], [[[0]], 0, 0], [[[1, 2], [3]], 1, 3], [[[5, 5, 6], [6, 7], [7, 5]], 5, 7], [[[10**6]], 10**6, 10**6]]
        for _ in range(250):
            n = rng.randrange(0, 6); start = rng.randrange(0, 6); end = start + rng.randrange(0, 6)
            avail = [rng.sample(range(0, 13), rng.randrange(0, 12)) for _ in range(n)]
            args.append([avail, start, end])
    elif uid == o.ITER:
        args = [_ops('SubarrayFirstIterator', [[], []], [('hasNext',)]), _ops('SubarrayFirstIterator', [[1, 2, 2, 3], [2]], [('hasNext',), ('next',), ('next',), ('next',), ('hasNext',)])]
        args += [_iter(rng) for _ in range(250)]
    elif uid == o.STOCK:
        args = [[0, 0, 0], [0, 1, 0], [3, 5, 2], [0, 0, 2], [2, 0, 4], [250, 250, 500], [0, 0, 500], [500, 0, 500], [0, 500, 500], [500, 500, 500], [1, 0, 499]]
        args += [[rng.randrange(0, 12), rng.randrange(0, 12), rng.randrange(0, 25)] for _ in range(200)]
        args += [[rng.randrange(0, 501), rng.randrange(0, 501), rng.randrange(0, 501)] for _ in range(20)]
    elif uid == o.LOVE:
        args = [[[], 1], [[['a', 'b', 'hi'], ['a', 'b', 'love'], ['c', 'b', 'x'], ['b', 'a', '']], 5], [[['x', 'x', 'self']], 1]]
        for _ in range(250):
            people = ['al', 'bo', 'cy', 'di', 'b', 'a1', 'a_']
            msgs = [[rng.choice(people), rng.choice(people), rng.choice(['love you', 'hi', ''])] for _ in range(rng.randrange(0, 15))]
            args.append([msgs, rng.randrange(1, 6)])
    elif uid in (o.INC1, o.INC2, o.INC3):
        args = [[[], 1, 1] if uid == o.INC1 else [[], 1, 1, 0],
                [['3,m,500,2', '1,m,500,2', '2,m,200,5', '9,m,500,4'], 3, 4] if uid == o.INC1 else [['3,m,500,2', '1,m,500,2', '2,m,200,5', '9,m,500,4', '9,m,200,1'], 3, 2, 50]]
        for _ in range(250):
            logs = _incident_logs(rng, rng.randrange(0, 15))
            if uid == o.INC1: args.append([logs, rng.randrange(1, 6), rng.randrange(1, 8)])
            else: args.append([logs, rng.randrange(1, 6), rng.randrange(1, 6), rng.choice([0, 10, 25, 50, 51, 75, 100])])
    elif uid == o.TREE:
        args = [[[[5]], '0'], [[[1], [2]], '0'], [[[1, 2], [3]], '1'], [[[0], [1], [2]], '2']]
        for _ in range(250):
            k = rng.randrange(1, 7); ids = rng.sample(range(0, 40), 20); groups = []
            for _ in range(k): s = rng.randrange(1, 4); groups.append(ids[:s]); ids = ids[s:]
            args.append([groups, str(rng.randrange(o.tree_count(groups)))])
    elif uid == o.TIME:
        args = [list(d) for d in product(range(10), repeat=4) if rng.random() < 0.06] + [[0, 0, 0, 0], [2, 3, 5, 9], [9, 9, 9, 9], [1, 2, 3, 4], [2, 4, 0, 0]]
    elif uid == o.SCHED:
        args = [['0000000', 0, 0], ['0000000', 1, 8], ['8888888', 56, 0], ['???????', 14, 4], ['?1?2?3?', 10, 2], ['8?????0', 8, 8]]
        for _ in range(250):
            p = ''.join(rng.choice('0123?????') for _ in range(7)); day = rng.randrange(0, 5)
            work = sum(int(c) for c in p if c != '?') + rng.randrange(0, p.count('?') * day + 2)
            args.append([p, work, day])
    elif uid == o.ATM:
        args = [[[1], 1], [[5], 2], [[2, 5, 1], 2], [[10**9], 10**9], [[3, 3, 3], 1]]
        args += [[[rng.randrange(1, 12) for _ in range(rng.randrange(1, 10))], rng.randrange(1, 5)] for _ in range(250)]
    elif uid in (o.BAL1, o.BAL2, o.BAL3):
        args = [[[]], [['t1,a,5,3', 't2,a,-7,1', 't1,b,2,0', 't3,b,-2,0']], [['x,acct_1,-1,0', 'y,acct_1,1,1', 'x,acct_1,-1,2']]]
        for _ in range(250):
            logs = ['%s,%s,%d,%d' % (rng.choice(['t1', 't2', 't3', 'T1', 'tx_9', 't' + str(rng.randrange(20))]), rng.choice(['user_A', 'company_X', 'b', 'B']),
                                     rng.choice([0, 1, -1, 5, -5, 100, -100, 10**9 - 1, -(10**9 - 1)]), rng.randrange(0, 6)) for _ in range(rng.randrange(0, 12))]
            args.append([logs])
    elif uid == o.ADD:
        vals = [str(v) for v in range(-100, 101)] + ['00', '007', '-0', '-00', '000', '0100', '-099', '-100']
        args = [[list(a), list(b)] for a in vals for b in vals if rng.random() < 0.006] + [[['-', '1', '0', '0'], ['-', '1', '0', '0']], [['1', '0', '0'], ['1', '0', '0']]]
    elif uid == o.AGG:
        now = 10**9
        args = [[[], '0'], [[['1.5', 'm', 'COMPLETED', 'u', str(now)], ['2.05', 'm', 'COMPLETED', 'u', str(now - 86399)], ['3', 'm', 'COMPLETED', 'u', str(now - 86400)],
                            ['4', 'n', 'PENDING', 'u', str(now)], ['9', 'n', 'COMPLETED', 'u', str(now + 1)]], str(now)]]
        for _ in range(250):
            txs = [[rng.choice(['0', '0.01', '0.1', '1', '10.5', '99.99', '999999999.99', str(rng.randrange(100))]), rng.choice(['m1', 'm2', 'shop']),
                    rng.choice(['COMPLETED', 'COMPLETED', 'PENDING', 'FAILED']), rng.choice(['u1', 'u2']),
                    str(now + rng.choice([1, 0, -1, -3599, -3600, -86399, -86400, -86401, -rng.randrange(0, 100000)]))] for _ in range(rng.randrange(0, 10))]
            args.append([txs, str(now)])
    elif uid == o.MINE:
        args = [[[], []], [[['1', '10']], [['t', '1', '1', '5'], ['u', '1', '2', '1']]], [[['1', '10'], ['2', '0']], [['t', '1', '2', '10'], ['u', '1', '2', '1'], ['v', '2', '1', '11']]]]
        for _ in range(250):
            names = rng.sample(['1', '2', '3', '10', '0', '007', '99'], rng.randrange(0, 6))
            accts = [[a, str(rng.randrange(0, 20))] for a in names]
            pool = names + ['555']
            txs = [['t' + str(i), rng.choice(pool), rng.choice(pool), str(rng.randrange(0, 15))] for i in range(rng.randrange(0, 10))]
            args.append([accts, txs])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.CREDIT1:
        calls = [('addAccount', 5)] + [('addAccountWithReferral', 1, 0)] * 9999 + [('getTotalCredit', 0)] * 5000 + [('getTotalCredit', 9999)] * 5000
        out.append((_ops('AccountCreditTracker', [], calls), [None, 0] + list(range(1, 10000)) + [10004] * 5000 + [1] * 5000))
    elif uid == o.CREDIT2:
        calls, exp = [('addAccount', 0)], [None, 0]
        for i in range(1, 10000):
            calls += [('addAccountWithReferral', 1, 0), ('getTopAccounts', 20)]
            exp += [i, [0] + list(range(1, min(i, 19) + 1))]
        out.append((_ops('AccountCreditTracker', [], calls), exp))
    elif uid in (o.ROUTE1, o.ROUTE2, o.ROUTE3):
        # dc{i} at (i%181-90, i//181); only dc90 sits at (0,0); dc271, dc89, dc91 are the three at squared distance 1.
        cmds = ['REGISTER dc%d %d %d 999999999' % (i, i % 181 - 90, i // 181) for i in range(300)]
        exp = ['OK'] * 300
        if uid == o.ROUTE1:
            cmds += ['ROUTE 0 0'] * 2700; exp += ['dc90'] * 2700
        else:
            cmds += ['ROUTE 0 0'] * 1000 + ['DOWN dc90'] + ['ROUTE 0 0'] * 1500
            exp += ['dc90'] * 1000 + ['OK'] + ['dc271', 'dc89', 'dc91'] * 500
            if uid == o.ROUTE3:
                cmds += ['RELEASE dc90'] * 199; exp += ['OK'] * 199
        out.append((_ops('RequestRouter', [], [('processCommand', c) for c in cmds]), [None] + exp))
    elif uid in (o.SNAP1, o.SNAP2, o.SNAP3):
        calls = [('follow', 0, j) for j in range(1, 5001)] + [('snapshot',)] + [('unfollow', 0, j) for j in range(1, 5001, 2)] + [('snapshot',)]
        exp = [None] * 5000 + [0] + [None] * 2500 + [1]
        for j in range(1, 3001):
            calls += [('isFollowing', 0, j, 0), ('isFollowing', 0, j, 1)]; exp += [True, j % 2 == 0]
        if uid != o.SNAP1:
            calls += [('getFollowees', 0, 0)] * 20 + [('getFollowees', 0, 1)] * 20
            exp += [list(range(1, 5001))] * 20 + [list(range(2, 5001, 2))] * 20
        out.append((_ops('SocialNetwork', [], calls), [None] + exp))
        if uid == o.SNAP3:
            # user 0 follows 1..50; user i follows 100..100+i-1 and 0, so 100+j scores 50-j.
            calls = [('follow', 0, i) for i in range(1, 51)]
            for i in range(1, 51): calls += [('follow', i, 100 + j) for j in range(i)] + [('follow', i, 0)]
            calls += [('snapshot',)] + [('recommend', 0, 0, 10)] * 300 + [('recommend', 7, 0, 100)] * 300
            exp = [None] * (len(calls) - 601) + [0] + [list(range(100, 110))] * 300 + [_snap3_seven()] * 300
            out.append((_ops('SocialNetwork', [], calls), [None] + exp))
    elif uid == o.STAY:
        avail = [list(range(1000, 1100)) for _ in range(300)]
        exp = [[i] for i in range(300)] + [[i, j] for i in range(300) for j in range(300) if i != j]
        out.append(([avail, 1000, 1099], exp))
    elif uid == o.ITER:
        a = list(range(100000)); b = list(range(0, 100000, 2))
        seq = b + list(range(1, 100000, 2))
        calls = [('hasNext',), ('next',)] * 99999 + [('hasNext',)]
        exp = [None]
        for v in seq[:99999]: exp += [True, v]
        exp.append(True)
        out.append((_ops('SubarrayFirstIterator', [a, b], calls), exp))
    elif uid == o.LOVE:
        msgs = [['s%d' % (i % 1000), 'r%d' % (i % 500), 'love'] for i in range(100000)]
        out.append(([msgs, 10], sorted('r%d' % j for j in range(500))[:10]))
    elif uid in (o.INC1, o.INC2, o.INC3):
        if uid == o.INC1:
            logs = ['%d,m,500,1' % t for t in range(50000)]
            out.append(([logs, 10, 10], ['9,m,500']))
        else:
            logs = ['%d,m,500,1' % t for t in range(25000)] + ['%d,m,200,1' % t for t in range(25000)]
            out.append(([logs[::-1], 10, 5, 50], ['4,m,500']))
    elif uid == o.TREE:
        groups = [[4 * g + i for i in range(4)] for g in range(500)]
        last = str(o.tree_count(groups) - 1)
        out.append(([groups, '0'], [[groups[i][0], 0] for i in range(1, 499)] + [[0, groups[499][0]]]))
        out.append(([groups, last], [[groups[i][3], 1999] for i in range(498)] + [[groups[498][3], 1999]]))
    elif uid == o.SCHED:
        out.append((['???????', 56, 8], ['8888888']))
        out.append((['???????', 7, 8], sorted(''.join(map(str, c)) for c in _compositions(7, 7))))
    elif uid == o.ATM:
        n = 100000
        out.append(([[10**9] * n, 1], list(range(1, n + 1))))
        out.append(([list(range(n, 0, -1)), 1], list(range(n, 0, -1))))
    elif uid in (o.BAL1, o.BAL2, o.BAL3):
        logs = ['t%d,a%d,%d,%d' % (i % 50000 if uid != o.BAL1 else i, i % 100, 1 if i % 2 == 0 else -1, i) for i in range(100000)]
        names = sorted('a%d' % j for j in range(100))
        if uid == o.BAL1: exp = [[a, 1000 if int(a[1:]) % 2 == 0 else -1000] for a in names]
        elif uid == o.BAL2: exp = [[a, 500 if int(a[1:]) % 2 == 0 else -500] for a in names]
        else: exp = [[[a, 500 if int(a[1:]) % 2 == 0 else 0] for a in names], ['t%d' % i for i in range(1, 50000, 2)]]
        out.append(([logs], exp))
    elif uid == o.AGG:
        now = 10**9
        txs = [['1.01', 'm%d' % (i % 100), 'COMPLETED', 'u', str(now - (i % 48) * 3600)] for i in range(100000)]
        cnt = {}
        for i in range(100000):
            if i % 48 < 24: cnt[i % 100] = cnt.get(i % 100, 0) + 1
        out.append(([txs, str(now)], [['m%d' % j, '%d.%02d' % divmod(101 * cnt[j], 100), cnt[j]] for j in sorted(cnt, key=lambda j: 'm%d' % j)]))
    elif uid == o.MINE:
        accts = [[str(i), '1000'] for i in range(10000)]
        txs = [['t%d' % i, str(i % 10000), str((i + 1) % 10000), '1'] for i in range(100000)]
        out.append(([accts, txs], [[a, '1000'] for a in sorted(str(i) for i in range(10000))]))
        txs = [['t%d' % i, str(i % 10000), str((i + 1) % 10000), '2000'] for i in range(100000)]
        out.append(([accts, txs], [[a, '1000'] for a in sorted(str(i) for i in range(10000))]))
    return out


def _snap3_seven():
    """User 7 follows 100..106 and 0; 0 follows 1..50, all unfollowed by 7 except via 0 -> each of 1..50 scores 1;
    users 107..149 are not reachable from 7 (7's followees 100..106 follow nobody). Top 100 by (score desc, id asc) = 1..50 minus 7."""
    return [i for i in range(1, 51) if i != 7]


def _compositions(total, parts):
    if parts == 1: return [[total]]
    return [[first] + rest for first in range(total + 1) for rest in _compositions(total - first, parts - 1)]
