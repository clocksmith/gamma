"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags. None is the official specification.
"""
from bisect import bisect_right
from fractions import Fraction
import re

H = 'hack2hire:'
ADS = H + '6a19fed3c81f779dc6a2370d'
CAM1 = H + '6a08df61bd4165b6d480ff97'
CAM2 = H + '6a08e02abd4165b6d480ffa1'
PACK = H + '69ff9cd5574d87bc49006f98'
CRAWL = H + '692f515ecd79766b0b310123'
MENU = H + '6782bd403cd890ccd3798fc3'
ISLAND = H + '6933ae8be8ebbb1c53caf339'
FLIP = H + '6a18ebdbc81f779dc6a23112'
FOREST1 = H + '6a7ce081d713d873ca7ac76a'
FOREST2 = H + '6a7ceda7d713d873ca7ac7f8'
DELIVERY1 = H + '69178d9a10632c00111ca20d'
DELIVERY2 = H + '6917944e10632c00111ca217'
DELIVERY3 = H + '6917944f10632c00111ca218'
DEPLOY1 = H + '6acd79422e3a0349b3a8d5be'
DEPLOY2 = H + '6acd79662e3a0349b3a8d5c0'
BANK1 = H + '687c3a5eaa2b26b0b64b39e5'
BANK2 = H + '687c4741aa2b26b0b64b39ee'
BANK3 = H + '687c4e56024483ac76db8c9b'
BANK4 = H + '687c5c0b024483ac76db8ca2'
CARD1 = H + '697d94b4b8c468a441586147'
CARD2 = H + '6986db08fedd959e9aa443ca'
CARD3 = H + '6986df8bfedd959e9aa443d6'
CONNECT = H + '69c19a8521f6ab4226964bf7'
DOC1 = H + '69d16c5617b72775cc49bf93'
DOC2 = H + '69d1730e17b72775cc49bfc6'
DOC3 = H + '69d1735f17b72775cc49bfc7'
TENNIS1 = H + '6941be52b9d646bec48c68cc'
TENNIS2 = H + '6941c912e79fe20cf9ff4435'
FIND1 = H + '683e86418d3dfb7c9bd756ab'
FIND2 = H + '683f1dc68d3dfb7c9bd756da'
IDS = (ADS, CAM1, CAM2, PACK, CRAWL, MENU, ISLAND, FLIP, FOREST1, FOREST2, DELIVERY1, DELIVERY2, DELIVERY3,
       DEPLOY1, DEPLOY2, BANK1, BANK2, BANK3, BANK4, CARD1, CARD2, CARD3, CONNECT, DOC1, DOC2, DOC3,
       TENNIS1, TENNIS2, FIND1, FIND2)

_BANK_L1 = {'createAccount': 2, 'deposit': 3, 'transfer': 4}
_BANK_L2 = {**_BANK_L1, 'topSpenders': 2}
_BANK_L3 = {**_BANK_L2, 'pay': 3, 'getPaymentStatus': 3}
_BANK_L4 = {**_BANK_L3, 'mergeAccounts': 3, 'getBalance': 3}
_DEL_L1 = {'addDriver': 2, 'addDelivery': 3, 'getTotalCost': 0}
_DEL_L2 = {**_DEL_L1, 'payUpTo': 1, 'getTotalCostUnpaid': 0}
_DEL_L3 = {**_DEL_L2, 'getMaxActiveDriversInLast24Hours': 1}
_DOC_L1 = {'setProperty': 3, 'getProperty': 2, 'undo': 0}
_DOC_L2 = {**_DOC_L1, 'redo': 0}
_DOC_L3 = {**_DOC_L2, 'removeProperty': 2, 'getProperties': 1}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    BANK1: ('BankingSystem', 0, _BANK_L1, ()), BANK2: ('BankingSystem', 0, _BANK_L2, ()),
    BANK3: ('BankingSystem', 0, _BANK_L3, ()), BANK4: ('BankingSystem', 0, _BANK_L4, ()),
    DELIVERY1: ('DeliverySystem', 0, _DEL_L1, ('addDriver', 'addDelivery')),
    DELIVERY2: ('DeliverySystem', 0, _DEL_L2, ('addDriver', 'addDelivery', 'payUpTo')),
    DELIVERY3: ('DeliverySystem', 0, _DEL_L3, ('addDriver', 'addDelivery', 'payUpTo')),
    CONNECT: ('ConnectKGame', 1, {'placePiece': 2}, ()),
    DOC1: ('Document', 0, _DOC_L1, ('setProperty',)), DOC2: ('Document', 0, _DOC_L2, ('setProperty',)),
    DOC3: ('Document', 0, _DOC_L3, ('setProperty',)),
    TENNIS1: ('TennisGame', 0, {'pointTo': 1, 'getPoints': 0, 'getScore': 0, 'getWinner': 0}, ('pointTo',)),
    TENNIS2: ('TennisSet', 0, {'pointTo': 1, 'getGames': 0, 'getGameScore': 0, 'getWinner': 0}, ('pointTo',)),
    FIND1: ('FileSystem', 0, {'addFile': 2, 'find': 2}, ('addFile',)),
    FIND2: ('FileSystem', 0, {'addFile': 2, 'find': 2}, ('addFile',)),
}
SUITS = ('CLUBS', 'DIAMONDS', 'HEARTS', 'SPADES')
RANKS = ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')
WEEK = 10080
DAY_MS = 86400000
DAY_S = 86400


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def trace(uid, args, maximum):
    name, ctor, methods, _ = CLASSES[uid]
    envelope(args, 2)
    ops, rows = args
    if type(ops) is not list or type(rows) is not list or not 1 <= len(ops) <= maximum or len(ops) != len(rows):
        raise ValueError('trace shape')
    if ops[0] != name or type(rows[0]) is not list or len(rows[0]) != ctor: raise ValueError('initial constructor')
    for op, row in zip(ops[1:], rows[1:]):
        if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
            raise ValueError('method or arity')
    return ops, rows


ACCOUNT = r'[a-z0-9]{1,8}'
URL = r'http://[a-z0-9]+(\.[a-z0-9]+)*(/[a-z0-9._-]*)*'
COMPONENT = r'[a-z0-9_]+(\.[a-z0-9_]+)*'
PATH = r'(/' + COMPONENT + r')+'


def card(c):
    if type(c) is not list or len(c) != 2 or c[0] not in SUITS or c[1] not in RANKS: raise ValueError('card')
    return (c[0], c[1])


def validate_deck(deck):
    if type(deck) is not list or len(deck) != 52 or len({card(c) for c in deck}) != 52: raise ValueError('deck permutation')


def validate_menu(node, budget):
    stack = [node]
    while stack:
        n = stack.pop(); budget[0] -= 1
        if budget[0] < 0: raise ValueError('menu size')
        if type(n) is not dict or set(n) != {'key', 'value', 'active', 'children'}: raise ValueError('menu node shape')
        text(n['key'], r'[A-Za-z0-9 _-]{1,20}', 20); text(n['value'], r'[A-Za-z0-9 _.$-]{0,20}', 20)
        if type(n['active']) is not bool or type(n['children']) is not list: raise ValueError('menu node fields')
        stack.extend(n['children'])


def validate_filter(f, nested, depth=0):
    if depth > 20 or type(f) is not list or not f or type(f[0]) is not str: raise ValueError('filter shape')
    kind = f[0]
    if kind == 'sizeGreaterThan' and len(f) == 2: integer(f[1], 0, 10**9); return
    if kind == 'extension' and len(f) == 2: text(f[1], r'[a-z0-9_]{0,10}', 10); return
    if kind == 'namePrefix' and len(f) == 2: text(f[1], r'[a-z0-9_.]{0,10}', 10); return
    if nested and kind in ('and', 'or') and len(f) == 2 and type(f[1]) is list and len(f[1]) <= 10:
        for g in f[1]: validate_filter(g, nested, depth + 1)
        return
    if nested and kind == 'not' and len(f) == 2: validate_filter(f[1], nested, depth + 1); return
    raise ValueError('unknown filter')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == ADS:
        envelope(args, 4)
        positions, ads, state, indices = args
        if type(positions) is not list or not 0 <= len(positions) <= 2000: raise ValueError('positions')
        for p in positions: text(p, r'[A-Za-z0-9_-]{1,20}', 20)
        if len(set(positions)) != len(positions): raise ValueError('duplicate position')
        if type(ads) is not list or len(ads) > 2000: raise ValueError('ads')
        for ad in ads:
            if type(ad) is not dict or set(ad) != {'adId', 'maxDisplay'}: raise ValueError('ad shape')
            text(ad['adId'], r'[A-Za-z0-9_-]{1,20}', 20); integer(ad['maxDisplay'], 0, 10**9)
        if len({ad['adId'] for ad in ads}) != len(ads): raise ValueError('duplicate ad')
        if type(state) is not dict or len(state) > 4000: raise ValueError('state')
        for k, v in state.items(): text(k, r'[A-Za-z0-9_-]{1,20}', 20); integer(v, 0, 10**9)
        array(indices, 0, 2**31 - 1, len(positions), len(positions))
    elif uid in (CAM1, CAM2):
        envelope(args, 3 if uid == CAM1 else 5)
        cameras = [args[0:2]] if uid == CAM1 else [args[0:2], args[2:4]]
        for times, values in cameras:
            array(times, 0, 10**9); array(values, 0, 10**9, len(times), len(times))
            if any(a >= b for a, b in zip(times, times[1:])): raise ValueError('times strictly increasing')
        integer(args[-1], 0, 10**9)
    elif uid == PACK:
        envelope(args, 1); array(args[0], 0, 100000, 1, 100000)
    elif uid == CRAWL:
        envelope(args, 2)
        text(args[0], URL, 200)
        if type(args[1]) is not dict or len(args[1]) > 5000: raise ValueError('link map')
        total = 0
        for k, v in args[1].items():
            text(k, URL, 200)
            if type(v) is not list: raise ValueError('link list')
            total += len(v)
            for u in v: text(u, URL, 200)
        if total > 50000: raise ValueError('link count')
    elif uid == MENU:
        envelope(args, 1); validate_menu(args[0], [20000])
    elif uid == ISLAND:
        envelope(args, 1)
        grid = args[0]
        if type(grid) is not list or not 1 <= len(grid) <= 300: raise ValueError('grid rows')
        for row in grid:
            if type(row) is not list or len(row) != len(grid[0]) or not 1 <= len(row) <= 300 or any(c not in ('0', '1') for c in row):
                raise ValueError('grid row')
    elif uid == FLIP:
        envelope(args, 2)
        s, requests = args
        text(s, r'[01]{1,100000}', 100000)
        if type(requests) is not list or len(requests) > 100000: raise ValueError('requests')
        for r in requests:
            if r == 'flip': continue
            text(r, r'count:(0|[1-9][0-9]*)', 20)
            if int(r[6:]) >= len(s): raise ValueError('count index')
    elif uid in (FOREST1, FOREST2):
        envelope(args, 2)
        parent = args[0]
        array(parent, 0, 99999, 1, 100000)
        n = len(parent)
        for p in parent:
            if p >= n: raise ValueError('parent index')
        color = [0] * n  # acyclicity: every parent chain must reach a self-parent root
        for i in range(n):
            path, j = [], i
            while color[j] == 0:
                color[j] = 1; path.append(j)
                if parent[j] == j: break
                j = parent[j]
            if color[j] == 1 and parent[j] != j: raise ValueError('cycle')
            for x in path: color[x] = 2
        if uid == FOREST1: integer(args[1], 0, n - 1)
        else: array(args[1], 0, n - 1, 0, 100000)
    elif uid in (DELIVERY1, DELIVERY2, DELIVERY3):
        ops, rows = trace(uid, args, 5001)
        drivers = set()
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'addDriver':
                integer(row[0], 0, 10**9); integer(row[1], 1, 100000)
                if row[0] in drivers: raise ValueError('duplicate driver')
                drivers.add(row[0])
            elif op == 'addDelivery':
                if type(row[0]) is not int or row[0] not in drivers: raise ValueError('unknown driver')
                integer(row[1], 0, 10**9); integer(row[2], row[1] + 1, min(10**9, row[1] + DAY_S))
            elif op in ('payUpTo', 'getMaxActiveDriversInLast24Hours'):
                integer(row[0], 0, 10**9)
    elif uid in (DEPLOY1, DEPLOY2):
        envelope(args, 1)
        if type(args[0]) is not list or len(args[0]) > 20000: raise ValueError('records')
        for r in args[0]:
            text(r, r'(0|[1-9][0-9]{0,4}),(0|[1-9][0-9]{0,4}),(allowed|freeze)', 40)
            a, b, _ = r.split(',')
            if not 0 <= int(a) < int(b) <= WEEK: raise ValueError('window bounds')
    elif uid in (BANK1, BANK2, BANK3, BANK4):
        ops, rows = trace(uid, args, 5001)
        last = 0
        for op, row in zip(ops[1:], rows[1:]):
            integer(row[0], last + 1, 10**12); last = row[0]
            if op == 'createAccount': text(row[1], ACCOUNT, 8)
            elif op in ('deposit', 'pay'): text(row[1], ACCOUNT, 8); integer(row[2], 1, 10**6)
            elif op == 'transfer': text(row[1], ACCOUNT, 8); text(row[2], ACCOUNT, 8); integer(row[3], 1, 10**6)
            elif op == 'topSpenders': integer(row[1], 1, 1000)
            elif op == 'getPaymentStatus': text(row[1], ACCOUNT, 8); text(row[2], r'payment[1-9][0-9]{0,5}', 20)
            elif op == 'mergeAccounts': text(row[1], ACCOUNT, 8); text(row[2], ACCOUNT, 8)
            elif op == 'getBalance': text(row[1], ACCOUNT, 8); integer(row[2], 1, row[0])
    elif uid in (CARD1, CARD2, CARD3):
        envelope(args, 1 if uid == CARD1 else 2)
        validate_deck(args[0])
        if uid != CARD1: integer(args[1], 1, 52)
    elif uid == CONNECT:
        ops, rows = trace(uid, args, 401)
        integer(rows[0][0], 1, 20)
        for row in rows[1:]:
            if row[0] not in ('B', 'R'): raise ValueError('player')
            integer(row[1], -10**9, 10**9)
    elif uid in (DOC1, DOC2, DOC3):
        ops, rows = trace(uid, args, 5001)
        for op, row in zip(ops[1:], rows[1:]):
            if row: integer(row[0], 0, 10**9)
            if len(row) >= 2: text(row[1], r'[a-z]{1,10}', 10)
            if len(row) == 3: text(row[2], r'[A-Za-z0-9#]{0,10}', 10)
    elif uid in (TENNIS1, TENNIS2):
        ops, rows = trace(uid, args, 5001)
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'pointTo' and row[0] not in ('A', 'B'): raise ValueError('player')
    elif uid in (FIND1, FIND2):
        ops, rows = trace(uid, args, 3001)
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'addFile': text(row[0], PATH, 200); integer(row[1], 0, 10**9)
            else:
                if row[0] != '/': text(row[0], PATH, 200)
                if uid == FIND1:
                    if type(row[1]) is not list or len(row[1]) > 10: raise ValueError('filter list')
                    for f in row[1]: validate_filter(f, False)
                else: validate_filter(row[1], True)


# ---------------------------------------------------------------- references

def ref_ads(positions, ads, state, indices):
    # Literal re-filtering of the whole candidate list for every position.
    used, out = set(), []
    for i, _ in enumerate(positions):
        eligible = [ad['adId'] for ad in ads if ad['adId'] not in used and state.get(ad['adId'], 0) < ad['maxDisplay']]
        if not eligible: out.append(None); continue
        chosen = eligible[indices[i] % len(eligible)]
        used.add(chosen); out.append(chosen)
    return out


def periods(times, values, threshold):
    # Label each reading with the index of its run start, then group labels.
    labels, out = {}, []
    for i, v in enumerate(values):
        if v >= threshold: labels[i] = labels.get(i - 1, i)
    starts = sorted(set(labels.values()))
    for s in starts:
        last = max(i for i, l in labels.items() if l == s)
        out.append([times[s], times[last]])
    return out


def ref_pack(cards):
    top = max(cards)
    if top > 3000 or len(cards) > 200: raise ValueError('reference budget')
    return min(sum((-c) % p for c in cards) for p in range(2, max(top, 2) + 2))


def host(url): return url[7:].split('/', 1)[0]


def ref_crawl(start, links):
    found = {start}
    while True:
        grown = found | {u for v in found for u in links.get(v, []) if host(u) == host(start)}
        if grown == found: return sorted(found)
        found = grown


def ref_menu(node):
    if not node['active']: return None
    kids = [ref_menu(c) for c in node['children']]
    return {'key': node['key'], 'value': node['value'], 'active': True, 'children': [k for k in kids if k is not None]}


def ref_island(grid):
    m, n = len(grid), len(grid[0])
    root = list(range(m * n))
    def find(x):
        while root[x] != x: x = root[x]
        return x
    for r in range(m):
        for c in range(n):
            if grid[r][c] == '1':
                for rr, cc in ((r + 1, c), (r, c + 1)):
                    if rr < m and cc < n and grid[rr][cc] == '1': root[find(rr * n + cc)] = find(r * n + c)
    stats, order = {}, []
    for r in range(m):
        for c in range(n):
            if grid[r][c] != '1': continue
            k = find(r * n + c)
            if k not in stats: stats[k] = [0, 0]; order.append(k)
            stats[k][0] += 1
            stats[k][1] += sum(1 for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                               if 0 <= rr < m and 0 <= cc < n and grid[rr][cc] == '0')
    return [stats[k] for k in order]


def ref_flip(s, requests):
    if len(s) * len(requests) > 2 * 10**6: raise ValueError('reference budget')
    out, cur = [], s
    for r in requests:
        if r == 'flip': cur = ''.join('1' if ch == '0' else '0' for ch in cur)
        else: out.append(cur[:int(r[6:]) + 1].count('1'))
    return out


def ref_forest(parent, targets):
    if len(parent) > 3000: raise ValueError('reference budget')
    dead = set()
    for t in targets:
        if t in dead: continue
        for i in range(len(parent)):  # ancestor walk from every node
            j = i
            while True:
                if j == t: dead.add(i); break
                if parent[j] == j: break
                j = parent[j]
    return [-1 if i in dead else p for i, p in enumerate(parent)]


def dollars(total_cents):
    cents = int(total_cents + Fraction(1, 2)) if total_cents >= 0 else 0  # half-up of a nonnegative rational
    return f'{cents // 100}.{cents % 100:02d}'


def ref_delivery(ops, rows):
    rate, deliveries, paid, out = {}, [], [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addDriver': rate[row[0]] = row[1]; out.append(None)
        elif op == 'addDelivery': deliveries.append(tuple(row)); paid.append(False); out.append(None)
        elif op == 'payUpTo':
            for i, d in enumerate(deliveries):
                if d[2] <= row[0]: paid[i] = True
            out.append(None)
        elif op in ('getTotalCost', 'getTotalCostUnpaid'):
            out.append(dollars(sum((Fraction(rate[d] * (e - s), 3600) for (d, s, e), p in zip(deliveries, paid)
                                    if op == 'getTotalCost' or not p), Fraction(0))))
        else:
            now = row[0]; low = now - DAY_S
            instants = {low} | {s for _, s, _ in deliveries if low <= s <= now}
            out.append(max(len({d for d, s, e in deliveries if s <= t < e}) for t in instants))
    return out


def ref_deploy_minutes(records):
    allowed, freeze = set(), set()
    for r in records:
        a, b, kind = r.split(',')
        (allowed if kind == 'allowed' else freeze).update(range(int(a), int(b)))
    return allowed - freeze


def ref_deploy_windows(records):
    # Interval algebra: merge allowed, merge freeze, subtract.
    def merged(kind):
        spans = sorted((int(a), int(b)) for a, b, k in (r.split(',') for r in records) if k == kind)
        out = []
        for a, b in spans:
            if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
            else: out.append([a, b])
        return out
    result = []
    for a, b in merged('allowed'):
        pieces = [[a, b]]
        for fa, fb in merged('freeze'):
            nxt = []
            for pa, pb in pieces:
                if fb <= pa or fa >= pb: nxt.append([pa, pb]); continue
                if pa < fa: nxt.append([pa, fa])
                if fb < pb: nxt.append([fb, pb])
            pieces = nxt
        result.extend(pieces)
    return result


def ref_bank(uid, ops, rows):
    """Event sourcing: each answer replays the whole log of earlier successful events from scratch."""
    if len(ops) > 400: raise ValueError('reference budget')
    log = []  # (time, kind, data)

    def replay(until):
        acct, out_total, pay, pcount = {}, {}, {}, 0
        cash = []  # (due, payment id)
        for t, kind, data in log:
            if t > until: break
            # cashbacks due at or before this event fire first
            for due, pid in sorted(cash):
                if due <= t and pay[pid][2] == 'IN_PROGRESS':
                    owner = pay[pid][0]; acct[owner] += pay[pid][1] * 2 // 100; pay[pid][2] = 'CASHBACK_RECEIVED'
            if kind == 'create': acct[data] = 0; out_total[data] = 0
            elif kind == 'deposit': acct[data[0]] += data[1]
            elif kind == 'transfer':
                acct[data[0]] -= data[2]; acct[data[1]] += data[2]; out_total[data[0]] += data[2]
            elif kind == 'pay':
                pcount += 1; pid = 'payment' + str(pcount)
                acct[data[0]] -= data[1]; out_total[data[0]] += data[1]
                pay[pid] = [data[0], data[1], 'IN_PROGRESS']; cash.append((t + DAY_MS, pid))
            elif kind == 'merge':
                a, b = data
                acct[a] += acct.pop(b); out_total[a] += out_total.pop(b)
                for p in pay.values():
                    if p[0] == b: p[0] = a
        for due, pid in sorted(cash):
            if due <= until and pay[pid][2] == 'IN_PROGRESS':
                owner = pay[pid][0]; acct[owner] += pay[pid][1] * 2 // 100; pay[pid][2] = 'CASHBACK_RECEIVED'
        return acct, out_total, pay, pcount

    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        t = row[0]
        acct, out_total, pay, pcount = replay(t)
        if op == 'createAccount':
            ok = row[1] not in acct
            if ok: log.append((t, 'create', row[1]))
            out.append(ok)
        elif op == 'deposit':
            if row[1] not in acct: out.append(-1); continue
            log.append((t, 'deposit', (row[1], row[2]))); out.append(acct[row[1]] + row[2])
        elif op == 'transfer':
            s, d, amt = row[1], row[2], row[3]
            if s == d or s not in acct or d not in acct or acct[s] < amt: out.append(-1); continue
            log.append((t, 'transfer', (s, d, amt))); out.append(acct[s] - amt)
        elif op == 'topSpenders':
            ranked = sorted(out_total.items(), key=lambda kv: (-kv[1], kv[0]))[:row[1]]
            out.append([f'{k}({v})' for k, v in ranked])
        elif op == 'pay':
            if row[1] not in acct or acct[row[1]] < row[2]: out.append(None); continue
            log.append((t, 'pay', (row[1], row[2]))); out.append('payment' + str(pcount + 1))
        elif op == 'getPaymentStatus':
            p = pay.get(row[2])
            out.append(p[2] if row[1] in acct and p is not None and p[0] == row[1] else None)
        elif op == 'mergeAccounts':
            a, b = row[1], row[2]
            ok = a != b and a in acct and b in acct
            if ok: log.append((t, 'merge', (a, b)))
            out.append(ok)
        elif op == 'getBalance':
            acct_at = replay(row[2])[0]
            out.append(acct_at.get(row[1], -1))
    return out


def full_deck():
    return [[s, r] for s in SUITS for r in RANKS]


def ref_hands(deck, players):
    order = full_deck()
    size = 52 // players
    return [sorted([list(c) for c in deck[p:players * size:players]], key=order.index) for p in range(players)]


def ref_card_game(deck, players):
    hands = [list(h) for h in ref_hands(deck, players)]
    strength = lambda c: (RANKS.index(c[1]), SUITS.index(c[0]))
    wins = [0] * players
    while hands[0]:
        played = []
        for h in hands:
            best = max(h, key=strength); h.remove(best); played.append(best)
        wins[max(range(players), key=lambda i: strength(played[i]))] += 1
    return wins


def ref_connect(ops, rows):
    if len(ops) > 120: raise ValueError('reference budget')
    k = rows[0][0]
    cols, out = {}, [None]
    for row in rows[1:]:
        player, column = row
        cols[column] = [player] + cols.get(column, [])  # index = height
        grid = {(c, y): v for c, col in cols.items() for y, v in enumerate(col)}
        win = False
        for (c, y), v in grid.items():
            if v != player: continue
            for dc, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                cells = [(c + i * dc, y + i * dy) for i in range(k)]
                if all(grid.get(cell) == player for cell in cells) and any(cc == column for cc, _ in cells): win = True
        out.append(win)
    return out


def ref_document(uid, ops, rows):
    changes, cursor, out = [], 0, [None]
    def state():
        props = {}
        for kind, layer, key, value in changes[:cursor]:
            if kind == 'set': props[(layer, key)] = value
            else: props.pop((layer, key))
        return props
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'setProperty':
            del changes[cursor:]; changes.append(('set', row[0], row[1], row[2])); cursor += 1; out.append(None)
        elif op == 'removeProperty':
            if (row[0], row[1]) not in state(): out.append(False); continue
            del changes[cursor:]; changes.append(('remove', row[0], row[1], None)); cursor += 1; out.append(True)
        elif op == 'getProperty': out.append(state().get((row[0], row[1])))
        elif op == 'getProperties': out.append(sorted([k, v] for (layer, k), v in state().items() if layer == row[0]))
        elif op == 'undo':
            out.append(cursor > 0); cursor = max(cursor - 1, 0)
        elif op == 'redo':
            out.append(cursor < len(changes)); cursor = min(cursor + 1, len(changes))
    return out


CALLS = ('Love', '15', '30', '40')


def game_state(points):
    """Score one game from its literal point log; returns (winner or '', score text)."""
    x = y = 0
    for p in points:
        if p == 'A': x += 1
        else: y += 1
        if (x >= 4 or y >= 4) and abs(x - y) >= 2:
            w = 'A' if x > y else 'B'
            return w, 'Game ' + w
    if x >= 3 and y >= 3: return '', 'Deuce' if x == y else 'Advantage ' + ('A' if x > y else 'B')
    return '', CALLS[x] + '-' + CALLS[y]


def ref_tennis1(ops, rows):
    log, out = [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        winner = game_state(log)[0]
        if op == 'pointTo':
            if not winner: log.append(row[0])
            out.append(None)
        elif op == 'getPoints': out.append([log.count('A'), log.count('B')])
        elif op == 'getScore': out.append(game_state(log)[1])
        else: out.append(winner)
    return out


def set_state(log):
    """Replay the whole set point log: returns games, current-game text, set winner."""
    games, current, tie = [0, 0], [], False
    for p in log:
        if (games[0] >= 6 or games[1] >= 6) and abs(games[0] - games[1]) >= 2 or 7 in games: break
        current.append(p)
        if tie:
            x, y = current.count('A'), current.count('B')
            if max(x, y) >= 7 and abs(x - y) >= 2: games['AB'.index(p)] += 1; current = []
        elif game_state(current)[0]:
            games['AB'.index(p)] += 1; current = []
        tie = games == [6, 6]
    winner = ''
    if (max(games) >= 6 and abs(games[0] - games[1]) >= 2) or 7 in games: winner = 'A' if games[0] > games[1] else 'B'
    if winner: text_ = 'Set ' + winner
    elif tie: text_ = f'Tiebreak {current.count("A")}-{current.count("B")}'
    else: text_ = game_state(current)[1]
    return games, text_, winner


def ref_tennis2(ops, rows):
    log, out = [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'pointTo': log.append(row[0]); out.append(None)
        else:
            games, txt, winner = set_state(log)
            out.append(list(games) if op == 'getGames' else txt if op == 'getGameScore' else winner)
    return out


def match_filter(f, path, size):
    name = path.rsplit('/', 1)[1]
    ext = name.rsplit('.', 1)[1] if '.' in name else ''
    kind = f[0]
    if kind == 'sizeGreaterThan': return size > f[1]
    if kind == 'extension': return ext == f[1]
    if kind == 'namePrefix': return name.startswith(f[1])
    if kind == 'and': return all(match_filter(g, path, size) for g in f[1])
    if kind == 'or': return any(match_filter(g, path, size) for g in f[1])
    return not match_filter(f[1], path, size)


def ref_find(uid, ops, rows):
    files, out = {}, [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addFile': files[row[0]] = row[1]; out.append(None); continue
        prefix = '/' if row[0] == '/' else row[0] + '/'
        test = (lambda p, s: all(match_filter(f, p, s) for f in row[1])) if uid == FIND1 else (lambda p, s: match_filter(row[1], p, s))
        out.append(sorted(p for p, s in files.items() if p.startswith(prefix) and test(p, s)))
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == ADS: return ref_ads(*args)
    if uid == CAM1: return periods(*args)
    if uid == CAM2:
        a, b = periods(args[0], args[1], args[4]), periods(args[2], args[3], args[4])
        if len(a) * len(b) > 10**6: raise ValueError('reference budget')
        return sorted([max(x[0], y[0]), min(x[1], y[1])] for x in a for y in b if max(x[0], y[0]) <= min(x[1], y[1]))
    if uid == PACK: return ref_pack(args[0])
    if uid == CRAWL: return ref_crawl(*args)
    if uid == MENU:
        if len(repr(args[0])) > 200000: raise ValueError('reference budget')
        return ref_menu(args[0])
    if uid == ISLAND: return ref_island(args[0])
    if uid == FLIP: return ref_flip(*args)
    if uid == FOREST1: return ref_forest(args[0], [args[1]])
    if uid == FOREST2: return ref_forest(args[0], args[1])
    if uid in (DELIVERY1, DELIVERY2, DELIVERY3):
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_delivery(*args)
    if uid == DEPLOY1: return len(ref_deploy_minutes(args[0]))
    if uid == DEPLOY2: return ref_deploy_windows(args[0])
    if uid in (BANK1, BANK2, BANK3, BANK4): return ref_bank(uid, *args)
    if uid == CARD1: return ref_hands(args[0], 4)
    if uid == CARD2: return ref_hands(*args)
    if uid == CARD3: return ref_card_game(*args)
    if uid == CONNECT: return ref_connect(*args)
    if uid in (DOC1, DOC2, DOC3):
        if len(args[0]) > 600: raise ValueError('reference budget')
        return ref_document(uid, *args)
    if uid == TENNIS1:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_tennis1(*args)
    if uid == TENNIS2:
        if len(args[0]) > 600: raise ValueError('reference budget')
        return ref_tennis2(*args)
    if len(args[0]) > 600: raise ValueError('reference budget')
    return ref_find(uid, *args)


def _second_deploy_check(records):
    """Cross-check of the two deploy references (minutes vs windows)."""
    minutes = ref_deploy_minutes(records)
    return sorted(minutes) == [m for a, b in ref_deploy_windows(records) for m in range(a, b)]
