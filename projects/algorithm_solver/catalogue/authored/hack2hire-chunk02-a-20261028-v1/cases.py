"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h02a_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def _ip(rng, near=None):
    if near is not None and rng.random() < 0.7:
        parts = near.split('/')[0].split('.')
        parts[3] = str(rng.randrange(256))
        if rng.random() < 0.3: parts[2] = str(rng.randrange(256))
        return '.'.join(parts)
    return '.'.join(str(rng.choice([0, 1, 10, 127, 192, 255, rng.randrange(256)])) for _ in range(4))


def _rules(rng, n):
    rules = []
    for _ in range(n):
        base = _ip(rng)
        target = base if rng.random() < 0.3 else base + '/' + str(rng.choice([0, 1, 8, 16, 24, 31, 32, rng.randrange(33)]))
        rules.append([rng.choice(['ALLOW', 'DENY']), target])
    return rules


def _gpu(rng, level, n, ids=6, span=30):
    calls, added = [], []
    for _ in range(n):
        op = rng.choice(['addCredit', 'addCredit', 'getBalance', 'getBalance', 'revokeCredit' if level == 1 else 'consumeCredit'])
        if op == 'addCredit':
            fresh = [c for c in ('c' + str(i) for i in range(ids)) if c not in added]
            if not fresh: op = 'getBalance'
            else:
                cid = rng.choice(fresh); added.append(cid); s = rng.randrange(span)
                calls.append((op, cid, rng.randrange(1, 20), s, s + rng.randrange(0, span))); continue
        if op == 'getBalance': calls.append((op, rng.randrange(span * 2)))
        elif op == 'revokeCredit': calls.append((op, 'c' + str(rng.randrange(ids + 1)), rng.randrange(span * 2)))
        else: calls.append((op, rng.randrange(1, 25), rng.randrange(span * 2)))
    return _ops('CreditSystem', [], calls)


def _fraud(rng, level, n, pool=4):
    calls = []
    for _ in range(n):
        op = rng.choice(['processEvent', 'processEvent', 'getDistinctPIICount'] + (['getSharedPIICount'] if level == 2 else []))
        if op == 'processEvent':
            calls.append((op, [rng.choice(['APPLY', 'LOAN', 'PAYMENT'])] +
                          [rng.choice(['', 'a' + str(rng.randrange(pool)), 'x' + str(rng.randrange(pool))]) for _ in range(4)]))
        else: calls.append((op,))
    return _ops('DistinctPIIValuesCounter', [], calls)


def _traits(rng, weighted, maxt=3, maxv=4):
    out = []
    for t in range(rng.randrange(1, maxt + 1)):
        vals = ['v' + str(j) for j in range(rng.randrange(1, maxv + 1))]
        out.append(['t' + str(t), [[v, rng.randrange(1, 6)] for v in vals] if weighted else vals])
    return out


def _forest(rng, n, label):
    nodes = [label(i) for i in range(n)]
    rel = []
    for i in range(1, n):
        if rng.random() < 0.8: rel.append([nodes[i], nodes[rng.randrange(i)]])
    rng.shuffle(rel)
    return rel


def _payments(rng, n, m):
    inv_ids = ['inv' + str(i) for i in range(m)]
    invoices = [f'{i},{rng.choice([100, 200, 300, rng.randrange(1, 500)])},2026-0{rng.randrange(1, 10)}-1{rng.randrange(10)}' for i in inv_ids]
    payments = []
    for p in range(n):
        memo = rng.choice(['', 'thanks', 'paying off:' + rng.choice(inv_ids + ['nope']), 'ref, paying off:' + rng.choice(inv_ids + ['zz']) + ' now', 'paying off:'])
        payments.append(f'p{p},{rng.choice([100, 200, 300, rng.randrange(1, 500)])},{memo}')
    return payments, invoices


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    O = _o
    if uid in (O.ADS1, O.ADS2):
        args = [[[], 1] if uid == O.ADS1 else [[], 1, 0, 5]]
        for _ in range(150):
            imps = [[str(rng.randrange(20)), rng.choice('abcdef')] for _ in range(rng.randrange(0, 15))]
            k = rng.randrange(1, 8)
            if uid == O.ADS1: args.append([imps, k])
            else: lo = rng.randrange(20); args.append([imps, k, lo, lo + rng.randrange(10)])
    elif uid == O.RECT:
        args = [[[]], [[[1, 3, 3]]], [[[0, 2, 5], [1, 5, 2], [1, 2, 4], [1, 5, 5]]]]
        args += [[[[rng.randrange(2), rng.randrange(1, 8), rng.randrange(1, 8)] for _ in range(rng.randrange(1, 12))]] for _ in range(200)]
    elif uid in (O.GPU1, O.GPU2):
        args = [_ops('CreditSystem', [], [])]
        args += [_gpu(rng, 1 if uid == O.GPU1 else 2, rng.randrange(1, 25)) for _ in range(250)]
    elif uid in (O.NFT1, O.NFT2, O.NFT3):
        for _ in range(200):
            t = _traits(rng, uid == O.NFT2)
            n = rng.randrange(0, 6) if uid != O.NFT3 else rng.randrange(0, O.n_combos(t) + 2)
            need = n * len(t) if uid != O.NFT3 else n
            args.append([t, n, [rng.randrange(10**15) if rng.random() < 0.5 else rng.randrange(10) for _ in range(need)]])
    elif uid in (O.LOAN1, O.LOAN2):
        args = [[[], []]]
        for _ in range(200):
            rel = _forest(rng, rng.randrange(1, 9), lambda i: 'co' + str(i))
            loans = [['L' + str(j), 'co' + str(rng.randrange(10))] + ([rng.choice([0, 5, 10, rng.randrange(100)])] if uid == O.LOAN2 else [])
                     for j in range(rng.randrange(0, 10))]
            rng.shuffle(loans)
            args.append([rel, loans])
    elif uid == O.SELLER:
        args = [[[]], [[[]]], [[['a']]], [[['a', 'b'], ['b', 'c'], ['a', 'b', 'c'], ['c', 'a', 'a']]]]
        args += [[[[rng.choice('abcdef') for _ in range(rng.randrange(0, 5))] for _ in range(rng.randrange(0, 8))]] for _ in range(200)]
    elif uid == O.AVG:
        args = [[[]], [[['a', '-1'], ['a', '0']]], [[['b', '-7'], ['b', '-2']]]]
        args += [[[[rng.choice(['ann', 'bob', 'cy', 'Di']), str(rng.randrange(-20, 21))] for _ in range(rng.randrange(1, 10))]] for _ in range(250)]
    elif uid == O.FIREWALL:
        args = [_ops('IpFirewall', [[]], [('isAllowed', '1.2.3.4')]), _ops('IpFirewall', [[['ALLOW', '0.0.0.0/0']]], [('isAllowed', '255.255.255.255')]),
                _ops('IpFirewall', [[['DENY', '10.0.0.5'], ['ALLOW', '10.0.0.0/8']]], [('isAllowed', '10.0.0.5'), ('isAllowed', '10.9.9.9'), ('isAllowed', '11.0.0.0')]),
                _ops('IpFirewall', [[['ALLOW', '192.168.1.77/24']]], [('isAllowed', '192.168.1.0'), ('isAllowed', '192.168.2.0')])]
        for _ in range(200):
            rules = _rules(rng, rng.randrange(0, 6))
            qs = [('isAllowed', _ip(rng, rng.choice(rules)[1] if rules else None)) for _ in range(rng.randrange(1, 8))]
            args.append(_ops('IpFirewall', [rules], qs))
    elif uid == O.IPO:
        args = [[[], 5], [[[1, 5, 10, 0]], 0]]
        for _ in range(250):
            users = rng.sample(range(1, 40), rng.randrange(0, 8))
            bids = [[u, rng.randrange(1, 6), rng.choice([5, 7, 9, rng.randrange(1, 12)]), rng.randrange(4)] for u in users]
            args.append([bids, rng.randrange(0, 25)])
    elif uid == O.TREE:
        args = [[[]], [[[1, 2]]], [[[1, 5], [2, 3]]]]
        args += [[_forest(rng, rng.randrange(1, 12), lambda i: rng_label(i))] for _ in range(200)]
    elif uid in (O.FRAUD1, O.FRAUD2):
        args = [_ops('DistinctPIIValuesCounter', [], [])]
        args += [_fraud(rng, 1 if uid == O.FRAUD1 else 2, rng.randrange(1, 25)) for _ in range(200)]
    elif uid in (O.PAY1, O.PAY2):
        args = [[[], []], [['p1,100,paying off:', 'p2,5,a, b, c'], ['i1,100,2026-01-01']]]
        args += [list(_payments(rng, rng.randrange(0, 8), rng.randrange(0, 6))) for _ in range(250)]
    elif uid == O.TRANSPOSE:
        args = [[[[7]], 1], [[[1, 2], [3, 4]], 64]]
        for _ in range(150):
            n = rng.randrange(1, 9)
            args.append([[[rng.randrange(-10**9, 10**9 + 1) for _ in range(n)] for _ in range(n)], rng.randrange(1, 12)])
    elif uid == O.PRISON:
        args = [[1, 1, [], []], [1, 1, [1], [1]], [3, 3, [1, 2, 3], [2]]]
        for _ in range(250):
            n, m = rng.randrange(1, 12), rng.randrange(1, 12)
            args.append([n, m, rng.sample(range(1, n + 1), rng.randrange(0, n + 1)), rng.sample(range(1, m + 1), rng.randrange(0, m + 1))])
    elif uid == O.ISLAND:
        args = [[[['0']]], [[['1']]], [[['1', '1'], ['1', '1']]]]
        for _ in range(250):
            r, c = rng.randrange(1, 8), rng.randrange(1, 8); p = rng.random()
            args.append([[['1' if rng.random() < p else '0' for _ in range(c)] for _ in range(r)]])
    elif uid == O.INCR:
        args = [[[]], [[5]], [[3, 1]], [[1, 3, 2, 4]], [[3, 1, 0]], [[2, 1, 2, 1, 2]], [[5, 1, 3]]]
        for _ in range(300):
            args.append([[rng.randrange(-4, 7) for _ in range(rng.randrange(0, 9))]])
    elif uid == O.MULTI:
        args = [_ops('MultiStreamReader', [[]], [('read', 3), ('read', 0)]), _ops('MultiStreamReader', [['01234', '', 'ab']], [('read', 2), ('read', 4), ('read', 9), ('read', 1)])]
        for _ in range(200):
            streams = [''.join(rng.choice('abc012') for _ in range(rng.randrange(0, 6))) for _ in range(rng.randrange(0, 5))]
            args.append(_ops('MultiStreamReader', [streams], [('read', rng.randrange(0, 8)) for _ in range(rng.randrange(1, 8))]))
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in _heavy(uid, rng):
            validate_domain(uid, a)
            rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def rng_label(i):
    return i * 7 % 13


def _heavy(uid, rng):
    """Large cases whose expected values are derived analytically or by a cheap independent reference path."""
    O = _o; out = []
    if uid == O.ADS1:
        imps = [[str(i), 'ad' + str(i % 1000)] for i in range(100000)]
        out.append(([imps, 3], ['ad0', 'ad1', 'ad10']))
        out.append(([[[str(i), 'x'] for i in range(100000)], 100000], ['x']))
    if uid == O.ADS2:
        imps = [[str(10**12 - i), 'ad' + str(i % 7)] for i in range(100000)]
        out.append(([imps, 2, 10**12 - 6, 10**12], ['ad0', 'ad1']))
        out.append(([imps, 100000, 0, 10**12], ['ad0', 'ad1', 'ad2', 'ad3', 'ad4', 'ad5', 'ad6']))
    if uid == O.RECT:
        ops = [[0, i + 1, 10**9 - i] for i in range(50000)] + [[1, 50000, 10**9], [1, 10**9, 49999]] * 25000
        out.append(([ops], [True, False] * 25000))
    if uid in (O.GPU1, O.GPU2):
        a = _gpu(rng, 1 if uid == O.GPU1 else 2, O.TRACE_MAX[uid] - 1, ids=O.TRACE_MAX[uid], span=10**6)
        out.append((a, reference(uid, a)))
    if uid in (O.NFT1, O.NFT2):
        traits = [['t' + str(i), ([['v' + str(j), j + 1] for j in range(50)] if uid == O.NFT2 else ['v' + str(j) for j in range(50)])] for i in range(8)]
        randoms = [(i * 2654435761) % 10**15 for i in range(80000)]
        a = [traits, 10000, randoms]
        out.append((a, reference(uid, a)))
    if uid == O.NFT3:
        traits = [['t' + str(i), ['v' + str(j) for j in range(50)]] for i in range(8)]
        a = [traits, 10000, [0] * 10000]  # j == i always: lexicographic first combos
        exp = [['v0'] * 5 + ['v' + str(i // 2500), 'v' + str(i // 50 % 50), 'v' + str(i % 50)] for i in range(10000)]
        out.append((a, exp))
        out.append(([[['a', ['x', 'y']]], 3, [1, 2, 3]], []))
    if uid in (O.LOAN1, O.LOAN2):
        chain = [['co' + str(i), 'co' + str(i + 1)] for i in range(49999)]
        loans = [['L' + str(i), 'co' + str(i)] + ([2] if uid == O.LOAN2 else []) for i in range(50000)]
        exp = [['co49999', sorted('L' + str(i) for i in range(50000))]] if uid == O.LOAN1 else [['co49999', 100000]]
        out.append(([chain, loans], exp))
    if uid == O.SELLER:
        recs = [['s' + str(j) for j in range(20)] for _ in range(2000)]
        out.append(([recs], [[s, sorted(t for t in ('s' + str(j) for j in range(20)) if t != s)] for s in sorted('s' + str(j) for j in range(20))]))
        recs = [['s' + str((i * 7 + j * 13) % 60) for j in range(20)] for i in range(150)]
        out.append(([recs], reference(uid, [recs])))
    if uid == O.AVG:
        sc = [['n' + chr(97 + i % 26), str(10**8 if i % 26 == 3 else -10**8)] for i in range(99999)] + [['nd', '-1']]
        out.append(([sc], reference(uid, [sc])))
    if uid == O.FIREWALL:
        a = _ops('IpFirewall', [_rules(rng, 1000)], [('isAllowed', _ip(rng)) for _ in range(O.TRACE_MAX[uid] - 1)])
        out.append((a, reference(uid, a)))
    if uid == O.IPO:
        bids = [[u, 10**9, 5, u % 3] for u in range(50000)]
        order = sorted(range(50000), key=lambda u: (u % 3, u))
        out.append(([bids, 30000], sorted(order[30000:])))
        out.append(([bids, 10**12], []))
    if uid == O.TREE:
        rel = [[i, i // 2] for i in range(2, 70001)] + [[i, 70001] for i in range(70002, 100002)]
        out.append(([rel], 1))
        rel2 = [[i, 0] for i in range(1, 50001)] + [[i, 50001] for i in range(50002, 100002)]
        out.append(([rel2], 0))
    if uid in (O.FRAUD1, O.FRAUD2):
        calls = []
        for i in range(19999):
            calls.append(('processEvent', ['APPLY', 'a' + str(i % 5000), 'p' + str(i), '', 's' + str(i % 3)]) if i % 2 == 0 else
                         (('getDistinctPIICount',) if uid == O.FRAUD1 or i % 4 == 1 else ('getSharedPIICount',)))
        a = _ops('DistinctPIIValuesCounter', [], calls)
        out.append((a, _fraud_fast(a)))
    if uid in (O.PAY1, O.PAY2):
        invoices = [f'i{j},{j % 100},2026-01-{10 + j % 20}' for j in range(20000)]
        payments = [f'p{j},{j % 100},' + ('paying off:i' + str(j) if j % 2 else 'none') for j in range(20000)]
        out.append(([payments, invoices], _pay_fast([payments, invoices], uid == O.PAY2)))
    if uid == O.TRANSPOSE:
        n = 700
        m = [[i * n + j for j in range(n)] for i in range(n)]
        out.append(([m, 7], [[i * n + j for i in range(n)] for j in range(n)]))
    if uid == O.PRISON:
        out.append(([10**5, 10**5, list(range(1, 10**5 + 1)), list(range(10**5, 0, -2))], (10**5 + 1) * 2))
        out.append(([10**5, 7, list(range(50000, 1, -1)), []], 50000))
    if uid == O.ISLAND:
        g = [['1' if (r // 2 + c // 2) % 2 == 0 else '0' for c in range(500)] for r in range(500)]
        out.append(([g], 8))
        out.append(([[['1'] * 500 for _ in range(500)]], 2000))
        snake = [['1' if r % 2 == 0 or (c == 499 if r % 4 == 1 else c == 0) else '0' for c in range(500)] for r in range(500)]
        out.append(([snake], reference(uid, [snake])))
    if uid == O.INCR:
        arr = [i * 10 for i in range(100000)]
        out.append(([arr], 0))
        out.append(([[5, 4, 3] * 33333 + [0]], -1))
        out.append(([[0, 5] * 50000], 5))
        arr3 = [i * 10 if i % 2 == 0 else i * 10 - 13 for i in range(100000)]
        out.append(([arr3], 3))
    if uid == O.MULTI:
        streams = ['ab' * 50] * 1000 + ['']
        calls = [('read', 7)] * 15000 + [('read', 200000)]
        a = _ops('MultiStreamReader', [streams], calls)
        out.append((a, reference(uid, a)))
    return out


def _fraud_fast(a):
    """Independent incremental path (sets of event indices) used only for large traces."""
    seen, out = {}, [None]
    for k, (op, r) in enumerate(zip(a[0][1:], a[1][1:])):
        if op == 'processEvent':
            for f in range(1, 5):
                if r[0][f] != '': seen.setdefault((f, r[0][f]), set()).add(k)
            out.append(None)
        elif op == 'getDistinctPIICount': out.append(len(seen))
        else: out.append(sum(1 for s in seen.values() if len(s) >= 2))
    return out


def _pay_fast(a, fallback):
    """Independent indexed path for large inputs (sorted candidate lists per amount, linear pointer)."""
    payments, invoices = a
    inv = {i.split(',')[0]: i.split(',') for i in invoices}
    by_amount = {}
    for i in sorted(inv.values(), key=lambda x: (x[2], x[0])): by_amount.setdefault(int(i[1]), []).append(i[0])
    used, out = set(), []
    for p in payments:
        pid, amount, memo = p.split(',', 2)
        m = _o.REF.search(memo); t = m.group(1) if m else None
        match = None
        if t in inv and (not fallback or t not in used): match = t
        elif fallback:
            for c in by_amount.get(int(amount), []):
                if c not in used: match = c; break
        if fallback and match is not None: used.add(match)
        out.append([pid, match])
    return out
