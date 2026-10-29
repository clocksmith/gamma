"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags. None is the official specification.
"""
from collections import Counter
from datetime import date
from fractions import Fraction
import re

H = 'hack2hire:'
WKV = H + '6778936c775a4a31045ead0e'
ALH1 = H + '697c2d6c9731315964cfb048'
ALH2 = H + '697c2f499731315964cfb056'
ALH3 = H + '697c325b9731315964cfb05c'
ALH4 = H + '697c341a9731315964cfb061'
ABT1 = H + '67957d70010c9ed2f849b1f9'
ABT2 = H + '67957d75010c9ed2f849b1fa'
AFS = H + '6a4fae98665efda9311f5607'
BAC1 = H + '6a7f873dd713d873ca7adc2f'
BAC2 = H + '6a7f88b6d713d873ca7adc47'
CSV = H + '696feb8db7afade5b30a39ca'
DASH = H + '678314d4d0faf7ec64cc3ad6'
CAM = H + '6a121534653f4ff494e2c7ea'
CHAT1 = H + '6945c50a2c048134ada834f9'
CHAT2 = H + '6945c7632c048134ada834fb'
COST1 = H + '6973d4f9a0697bac5fdca7ad'
COST2 = H + '69791ddab6043fbfd6027f47'
COST3 = H + '697921bbb6043fbfd6027f52'
CSS1 = H + '689cf810aee746eb1c84ba38'
CSS2 = H + '689e4cd5735253d430dee92d'
CSS3 = H + '689e4cd8735253d430dee92e'
CSS4 = H + '689e4cd9735253d430dee92f'
SNAKE = H + '69e926affbaf3da641828639'
MINE1 = H + '69a8a9fe4b133b6a8f3a5ef3'
MINE2 = H + '69a8acc74b133b6a8f3a5efd'
MINE3 = H + '69ab56434b133b6a8f3a68a2'
FX = H + '678951e8402dc47b67a14951'
CRS1 = H + '6855e42cc201117d348a2630'
CRS2 = H + '69445eb8867a3f9f539ff53d'
C4 = H + '68b93d5483188776facc8ff6'
KVDB = H + '67a19e53b41c4108d8ccb3d4'
INV = H + '677ae48578175fce2ecdfc0a'
IDS = (WKV, ALH1, ALH2, ALH3, ALH4, ABT1, ABT2, AFS, BAC1, BAC2, CSV, DASH, CAM, CHAT1, CHAT2, COST1, COST2, COST3,
       CSS1, CSS2, CSS3, CSS4, SNAKE, MINE1, MINE2, MINE3, FX, CRS1, CRS2, C4, KVDB, INV)

_CSS_L1 = {'addFile': 2, 'copyFile': 2, 'getFilesize': 1}
_CSS_L2 = {**_CSS_L1, 'findFile': 2}
_CSS_L3 = {**_CSS_L2, 'addUser': 2, 'addFileBy': 3, 'mergeUser': 2}
_CSS_L4 = {**_CSS_L3, 'backupUser': 1, 'restoreUser': 1}
_CRS_L1 = {'insert': 1, 'insertWithReferrer': 2, 'getLowestK': 2}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    WKV: ('WindowedKeyValueStore', 2, {'put': 3, 'get': 2}, ('put',)),
    ABT1: ('TransactionSystem', 2, {'getBalance': 1, 'getBalances': 0}, ()),
    ABT2: ('TransactionSystem', 2, {'getBalance': 1, 'getBalances': 0, 'getBalanceAfter': 2}, ()),
    CAM: ('CameraLogServer', 0, {'requestLog': 2, 'pollCommand': 1, 'sendLog': 3, 'pollLog': 0}, ('requestLog', 'sendLog')),
    CSS1: ('CloudStorage', 0, _CSS_L1, ()), CSS2: ('CloudStorage', 0, _CSS_L2, ()),
    CSS3: ('CloudStorage', 0, _CSS_L3, ()), CSS4: ('CloudStorage', 0, _CSS_L4, ()),
    CRS1: ('CustomerRevenueSystem', 0, _CRS_L1, ()),
    CRS2: ('CustomerRevenueSystem', 0, {**_CRS_L1, 'getNestedRevenue': 2}, ()),
    C4: ('ConnectFour', 0, {'play': 1}, ()),
    KVDB: ('InMemoryKVDB', 0, {'set': 2, 'get': 1, 'delete': 1, 'count': 1, 'begin': 0, 'rollback': 0, 'commit': 0},
           ('set', 'delete', 'begin')),
    INV: ('DocumentLibrary', 1, {'search': 1}, ()),
}
WORD = r'[a-z0-9]{1,10}'
NAME = r'[a-z]{1,8}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def strings(a, pattern, minimum=0, maximum=100000, length=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: text(v, pattern, length)


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


def _header_tokens(uid, header):
    # Domain check of the header grammar by a hand-written character scanner (not the candidate's regex).
    if type(header) is not str or not 1 <= len(header) <= 4000: raise ValueError('header')
    tokens = [t.strip(' ') for t in header.split(',')]
    if not 1 <= len(tokens) <= 200: raise ValueError('header token count')
    for t in tokens:
        tag, q = t, None
        if uid == ALH4 and ';' in t:
            tag, q = t.split(';', 1)
            text(q, r'q=(0(\.[0-9]{1,3})?|1(\.0{1,3})?)', 7)
        ok = re.fullmatch(r'[a-z]{2}-[A-Z]{2}', tag) is not None or \
            (uid != ALH1 and re.fullmatch(r'[a-z]{2}', tag) is not None) or (uid in (ALH3, ALH4) and tag == '*')
        if not ok: raise ValueError('language tag')
    return tokens


def _decimal(v, frac):
    text(v, r'(0|[1-9][0-9]{0,5})(\.[0-9]{1,%d})?' % frac, 12)


def _validate_pricing(uid, table):
    if type(table) is not dict or len(table) > 20: raise ValueError('pricing table')
    for region, services in table.items():
        text(region, r'[a-z0-9-]{1,15}', 15)
        if type(services) is not dict or len(services) > 50: raise ValueError('region pricing')
        for service, rate in services.items():
            text(service, r'[a-z0-9.]{1,15}', 15)
            if type(rate) is str: _decimal(rate, 4); continue
            if uid == COST1 or type(rate) is not list or not 1 <= len(rate) <= 6: raise ValueError('rate')
            last = 0
            for i, tier in enumerate(rate):
                if type(tier) is not list or len(tier) != 2: raise ValueError('tier')
                if i == len(rate) - 1:
                    if tier[0] is not None: raise ValueError('last tier unbounded')
                else:
                    integer(tier[0], last + 1, 10**6); last = tier[0]
                _decimal(tier[1], 4)


def _validate_usage(report):
    if type(report) is not dict or set(report) != {'region', 'services'}: raise ValueError('usage report')
    text(report['region'], r'[a-z0-9-]{1,15}', 15)
    if type(report['services']) is not list or len(report['services']) > 2000: raise ValueError('usage services')
    for s in report['services']:
        if type(s) is not dict or set(s) != {'service', 'hours'}: raise ValueError('usage row')
        text(s['service'], r'[a-z0-9.]{1,15}', 15); integer(s['hours'], 0, 10**6)


def _no_arbitrage(rates):
    nodes = sorted({r[0] for r in rates} | {r[1] for r in rates})
    best = {(a, b): Fraction(0) for a in nodes for b in nodes}
    for a, b, r in rates: best[(a, b)] = max(best[(a, b)], Fraction(r))
    for k in nodes:
        for i in nodes:
            if best[(i, k)] == 0: continue
            for j in nodes:
                v = best[(i, k)] * best[(k, j)]
                if v > best[(i, j)]: best[(i, j)] = v
    if any(best[(a, a)] > 1 for a in nodes): raise ValueError('arbitrage cycle')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == WKV:
        ops, rows = trace(uid, args, 20001)
        integer(rows[0][0], 1, 100000); integer(rows[0][1], 1, 10**9)
        last = 0
        for op, row in zip(ops[1:], rows[1:]):
            integer(row[0], 0, 10**9)
            if op == 'put': integer(row[1], 0, 10**9)
            integer(row[-1], last, 10**9); last = row[-1]
    elif uid in (ALH1, ALH2, ALH3, ALH4):
        envelope(args, 2)
        _header_tokens(uid, args[0])
        strings(args[1], r'[a-z]{2}-[A-Z]{2}', 0, 200, 5)
        if len(set(args[1])) != len(args[1]): raise ValueError('duplicate supported tag')
    elif uid in (ABT1, ABT2):
        ops, rows = trace(uid, args, 5001)
        accounts, transactions = rows[0]
        if type(accounts) is not list or not 1 <= len(accounts) <= 1000: raise ValueError('accounts')
        for a in accounts:
            if type(a) is not list or len(a) != 2: raise ValueError('account row')
            text(a[0], NAME, 8); integer(a[1], 0, 10**9)
        names = {a[0] for a in accounts}
        if len(names) != len(accounts): raise ValueError('duplicate account')
        if type(transactions) is not list or len(transactions) > 5000: raise ValueError('transactions')
        for t in transactions:
            if type(t) is not list or len(t) != 3 or t[0] not in names or t[1] not in names or t[0] == t[1]: raise ValueError('transaction')
            integer(t[2], 0, 100)
        for op, row in zip(ops[1:], rows[1:]):
            if op != 'getBalances': text(row[0], NAME, 8)
            if op == 'getBalanceAfter': integer(row[1], 0, len(transactions))
    elif uid == AFS:
        envelope(args, 1); array(args[0], -10**9, 10**9, 0, 100000)
    elif uid == BAC1:
        envelope(args, 1); array(args[0], 1, 10**9, 0, 100000)
    elif uid == BAC2:
        envelope(args, 2); array(args[0], 1, 10**9, 0, 100000); integer(args[1], 1, 1000)
    elif uid == CSV:
        envelope(args, 3)
        strings(args[0], r'[ -~]{0,200}', 1, 10000, 200)
        strings(args[1], WORD, 0, 100, 10); strings(args[2], WORD, 0, 100, 10)
    elif uid == DASH:
        envelope(args, 1)
        recs = args[0]
        if type(recs) is not list or len(recs) > 20000: raise ValueError('records')
        seen = {}
        for r in recs:
            if type(r) is not list or len(r) != 3: raise ValueError('record shape')
            text(r[0], r'[A-Za-z0-9]{1,10}', 10); text(r[1], r'([01][0-9]|2[0-3]):[0-5][0-9]', 5)
            if r[2] not in ('ACCEPTED', 'CANCELED', 'DELIVERED'): raise ValueError('status')
            seen.setdefault(r[0], []).append(r)
        for rs in seen.values():
            acc = [r for r in rs if r[2] == 'ACCEPTED']; end = [r for r in rs if r[2] != 'ACCEPTED']
            if len(acc) != 1 or len(end) > 1: raise ValueError('order lifecycle')
            if end and end[0][1] < acc[0][1]: raise ValueError('terminal before accept')
    elif uid == CAM:
        ops, rows = trace(uid, args, 20001)
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'pollLog': continue
            integer(row[0], 0, 10**9)
            if op in ('requestLog', 'sendLog'): integer(row[1], 0, 10**9)
            if op == 'sendLog': text(row[2], r'[ -~]{0,30}', 30)
    elif uid == CHAT1:
        envelope(args, 2)
        _messages(args[0], 1)
        ids = {m[0] for m in args[0]}
        if type(args[1]) is not list or len(args[1]) > 100000: raise ValueError('queries')
        for q in args[1]:
            if type(q) is not list or len(q) != 3 or type(q[0]) is not int or q[0] not in ids: raise ValueError('query')
            integer(q[1], 0, 100000); integer(q[2], 0, 100000)
    elif uid == CHAT2:
        envelope(args, 1)
        pages = args[0]
        if type(pages) is not list or len(pages) > 2000: raise ValueError('pages')
        content, total = {}, 0
        for p in pages:
            _messages(p, 0); total += len(p)
            for i, c in p:
                if content.setdefault(i, c) != c: raise ValueError('conflicting content')
        if total > 100000: raise ValueError('total messages')
    elif uid in (COST1, COST2, COST3):
        envelope(args, 2); _validate_usage(args[0]); _validate_pricing(uid, args[1])
    elif uid in (CSS1, CSS2, CSS3, CSS4):
        ops, rows = trace(uid, args, 5001)
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'addFile': text(row[0], r'[a-z0-9/._]{1,20}', 20); integer(row[1], 0, 10**9)
            elif op == 'copyFile': text(row[0], r'[a-z0-9/._]{1,20}', 20); text(row[1], r'[a-z0-9/._]{1,20}', 20)
            elif op == 'getFilesize': text(row[0], r'[a-z0-9/._]{1,20}', 20)
            elif op == 'findFile': text(row[0], r'[a-z0-9/._]{0,20}', 20); text(row[1], r'[a-z0-9/._]{0,20}', 20)
            elif op == 'addUser': text(row[0], r'u[a-z0-9]{0,7}', 8); integer(row[1], 0, 10**9)
            elif op == 'addFileBy': text(row[0], r'u[a-z0-9]{0,7}', 8); text(row[1], r'[a-z0-9/._]{1,20}', 20); integer(row[2], 0, 10**9)
            elif op == 'mergeUser': text(row[0], r'u[a-z0-9]{0,7}', 8); text(row[1], r'u[a-z0-9]{0,7}', 8)
            else: text(row[0], r'u[a-z0-9]{0,7}', 8)
    elif uid == SNAKE:
        envelope(args, 1); text(args[0], r'[ -~\n\t]{0,100000}', 100000)
    elif uid in (MINE1, MINE2, MINE3):
        envelope(args, 2)
        txs, block = args
        if type(txs) is not list or len(txs) > 100: raise ValueError('mempool')
        width = 4 if uid == MINE3 else 3
        for t in txs:
            if type(t) is not list or len(t) != width: raise ValueError('transaction')
            text(t[0], r'[a-z0-9]{1,8}', 8); integer(t[1], 1, 10**4); integer(t[2], 0, 10**6)
        ids = [t[0] for t in txs]
        if len(set(ids)) != len(ids): raise ValueError('duplicate id')
        integer(block, 0, 5000 if uid != MINE3 else 2000)
        if uid == MINE3:
            parent = {t[0]: t[3] for t in txs}
            for t in txs:
                if t[3] is not None and (type(t[3]) is not str or t[3] not in parent): raise ValueError('parent')
            for t in txs:  # acyclic: walking parents must end at a root within n steps
                x, steps = t[0], 0
                while x is not None:
                    x = parent[x]; steps += 1
                    if steps > len(txs): raise ValueError('dependency cycle')
    elif uid == FX:
        envelope(args, 3)
        rates, a, b = args
        if type(rates) is not list or len(rates) > 120: raise ValueError('rates')
        pairs = set()
        for r in rates:
            if type(r) is not list or len(r) != 3: raise ValueError('rate row')
            text(r[0], r'[A-Z]{3}', 3); text(r[1], r'[A-Z]{3}', 3)
            text(r[2], r'(0|[1-9][0-9]{0,3})(\.[0-9]{1,4})?', 9)
            if Fraction(r[2]) == 0 or r[0] == r[1] or (r[0], r[1]) in pairs: raise ValueError('rate value or pair')
            pairs.add((r[0], r[1]))
        if len({r[0] for r in rates} | {r[1] for r in rates}) > 30: raise ValueError('currency count')
        text(a, r'[A-Z]{3}', 3); text(b, r'[A-Z]{3}', 3)
        _no_arbitrage(rates)
    elif uid in (CRS1, CRS2):
        ops, rows = trace(uid, args, 3001)
        n = 0
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'insert': integer(row[0], 0, 10**6); n += 1
            elif op == 'insertWithReferrer': integer(row[0], 0, 10**6); integer(row[1], 0, n - 1); n += 1
            elif op == 'getLowestK': integer(row[0], 0, 100); integer(row[1], 0, 10**12)
            else: integer(row[0], 0, n - 1); integer(row[1], 0, 20000)
    elif uid == C4:
        ops, rows = trace(uid, args, 5001)
        for row in rows[1:]: integer(row[0], -1, 7)
    elif uid == KVDB:
        ops, rows = trace(uid, args, 20001)
        for op, row in zip(ops[1:], rows[1:]):
            for v in row: text(v, r'[a-z0-9]{1,8}', 8)
    elif uid == INV:
        ops, rows = trace(uid, args, 2001)
        docs = rows[0][0]
        if type(docs) is not list or len(docs) > 1000: raise ValueError('documents')
        total = 0
        for d in docs:
            if type(d) is not list or len(d) != 2: raise ValueError('document row')
            text(d[0], r'[A-Za-z0-9_-]{1,12}', 12); text(d[1], r'[ -~]{0,2000}', 2000); total += len(d[1])
        if total > 100000 or len({d[0] for d in docs}) != len(docs): raise ValueError('documents size or ids')
        for row in rows[1:]: text(row[0], r'[ -~]{0,200}', 200)


def _messages(m, minimum):
    if type(m) is not list or not minimum <= len(m) <= 100000: raise ValueError('messages')
    last = None
    for row in m:
        if type(row) is not list or len(row) != 2: raise ValueError('message shape')
        integer(row[0], 0, 10**9); text(row[1], r'[ -~]{0,20}', 20)
        if last is not None and row[0] <= last: raise ValueError('ids strictly increasing')
        last = row[0]


# ---------------------------------------------------------------- references

def ref_wkv(ops, rows):
    capacity, window = rows[0]
    order = []  # [key, value, time], least recent first
    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'put':
            key, value, t = row
            hit = [e for e in order if e[0] == key]
            order = [e for e in order if e[0] != key] + [[key, value, t]]
            if not hit and len(order) > capacity: order = order[1:]
            out.append(None)
        else:
            key, t = row
            hit = [e for e in order if e[0] == key]
            if hit and t - hit[0][2] < window:
                order = [e for e in order if e[0] != key] + hit
                out.append(hit[0][1])
            else: out.append(-1)
    return out


def ref_accept(uid, header, supported):
    tokens = [t.strip(' ') for t in header.split(',')]
    parsed = []
    for pos, t in enumerate(tokens):
        q = Fraction(1)
        if ';' in t: t, qs = t.split(';'); q = Fraction(qs[2:])
        parsed.append((pos, t, q))

    def matches(tok, s):
        return tok == s or tok == '*' or (len(tok) == 2 and s[:2] == tok)
    if uid != ALH4:
        out = []
        for _, tok, _ in parsed:
            for s in supported:
                if matches(tok, s) and s not in out: out.append(s)
        return out
    keyed = []
    for idx, s in enumerate(supported):
        hits = [p for p in parsed if matches(p[1], s)]
        if not hits: continue
        rank = lambda tok: 3 if tok == s else 2 if len(tok) == 2 else 1
        top = max(rank(p[1]) for p in hits)
        q = [p for p in hits if rank(p[1]) == top][0][2]
        if q > 0: keyed.append((-q, hits[0][0], idx, s))
    return [k[3] for k in sorted(keyed)]


def ref_abt(uid, ops, rows):
    accounts, transactions = rows[0]

    def replay(k):
        bal = {a: b for a, b in accounts}
        for f, t, p in transactions[:k]:
            amount = bal[f] * p // 100
            bal[f] -= amount; bal[t] += amount
        return bal
    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'getBalances':
            bal = replay(len(transactions)); out.append([[a, bal[a]] for a, _ in accounts])
        elif op == 'getBalance': out.append(replay(len(transactions)).get(row[0], -1))
        else: out.append(replay(row[1]).get(row[0], -1))
    return out


def ref_columns(heights, k):
    cols = [[] for _ in range(k)]; totals = [0] * k
    for i, h in enumerate(heights):
        j = min(range(k), key=lambda c: (totals[c], c))
        cols[j].append(i); totals[j] += h
    return cols


def _words(s):
    out, cur = [], ''
    for ch in s.lower():
        if 'a' <= ch <= 'z' or '0' <= ch <= '9': cur += ch
        else:
            if cur: out.append(cur)
            cur = ''
    if cur: out.append(cur)
    return out


def ref_csv(data, forbidden, ignore):
    forbidden, ignore = set(forbidden), set(ignore)
    good, ids = [], set()
    for idx in range(1, len(data)):
        f = data[idx].split(',')
        if len(f) != 6 or any(x == '' or x != x.strip(' ') for x in f): continue
        if not f[0].isascii() or not f[0].isalnum() or f[0] in ids: continue
        whole, _, cents = f[4].partition('.')
        if not whole.isdigit() or not whole.isascii() or (len(whole) > 1 and whole[0] == '0'): continue
        if '.' in f[4] and not (len(cents) == 2 and cents.isdigit() and cents.isascii()): continue
        try:
            if len(f[5]) != 10 or f[5][4] != '-' or f[5][7] != '-': raise ValueError
            d = date.fromisoformat(f[5])
            if not 1900 <= d.year <= 2099: raise ValueError
        except ValueError: continue
        if any(w in forbidden for c in (1, 2, 3) for w in _words(f[c])): continue
        if [w for w in _words(f[1]) if w not in ignore] == [w for w in _words(f[2]) if w not in ignore]: continue
        good.append(idx); ids.add(f[0])
    return good


def ref_dash(records):
    acc, done = {}, {}
    for oid, ts, st in records:
        m = int(ts[:2]) * 60 + int(ts[3:])
        if st == 'ACCEPTED': acc[oid] = m
        elif st == 'DELIVERED': done[oid] = m
    total = 0
    for minute in range(1440):  # sweep each minute [minute, minute+1)
        total += 30 * sum(1 for o in done if acc[o] <= minute < done[o])
    return total


def ref_cam(ops, rows):
    commands, logs, out = [], [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'requestLog': commands.append(tuple(row)); out.append(None)
        elif op == 'sendLog': logs.append(list(row)); out.append(None)
        elif op == 'pollLog': out.append(logs.pop(0) if logs else None)
        else:
            idx = next((i for i, c in enumerate(commands) if c[0] == row[0]), None)
            out.append(-1 if idx is None else commands.pop(idx)[1])
    return out


def ref_chat_ranges(messages, queries):
    n = len(messages); covered = [False] * n
    pos = {m[0]: i for i, m in enumerate(messages)}
    for t, before, after in queries:
        p = pos[t]
        for i in range(max(0, p - before), min(n - 1, p + after) + 1): covered[i] = True
    out, i = [], 0
    while i < n:
        if covered[i]:
            j = i
            while j + 1 < n and covered[j + 1]: j += 1
            out.append([messages[i][0], messages[j][0]]); i = j + 1
        else: i += 1
    return out


def ref_chat_pages(pages):
    seen = {}
    for p in pages:
        for i, c in p: seen[i] = c
    return [[i, seen[i]] for i in sorted(seen)]


def _tier_cost(rate, hours):
    if type(rate) is str: return Fraction(rate) * hours
    cost = Fraction(0)
    for hour in range(1, hours + 1):  # literal per-hour tier lookup
        for limit, r in rate:
            if limit is None or hour <= limit: cost += Fraction(r); break
    return cost


def _cents(x):
    c = (x * 100 + Fraction(1, 2)).__floor__()
    return f'{c // 100}.{c % 100:02d}'


def ref_cost(uid, report, table):
    region = table.get(report['region'], {})
    hours = {}
    for s in report['services']: hours[s['service']] = hours.get(s['service'], 0) + s['hours']
    if uid == COST1:
        return _cents(sum((Fraction(region[s['service']]) * s['hours'] for s in report['services'] if s['service'] in region), Fraction(0)))
    costs = {name: _tier_cost(region[name], h) for name, h in hours.items() if name in region}
    total = _cents(sum(costs.values(), Fraction(0)))
    if uid == COST2: return total
    return {'total': total, 'services': [[n, _cents(c)] for n, c in sorted(costs.items(), key=lambda kv: (-kv[1], kv[0]))]}


def ref_css(uid, ops, rows):
    files = []  # [name, size, owner]
    users = {}  # id -> capacity
    backups = {}
    out = [None]

    def find(name): return next((f for f in files if f[0] == name), None)

    def used(u): return sum(f[1] for f in files if f[2] == u)
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addFile':
            ok = find(row[0]) is None
            if ok: files.append([row[0], row[1], None])
            out.append(ok)
        elif op == 'copyFile':
            src = find(row[0])
            ok = src is not None and find(row[1]) is None and (src[2] is None or used(src[2]) + src[1] <= users[src[2]])
            if ok: files.append([row[1], src[1], src[2]])
            out.append(ok)
        elif op == 'getFilesize':
            f = find(row[0]); out.append(-1 if f is None else f[1])
        elif op == 'findFile':
            hit = [f for f in files if f[0].startswith(row[0]) and f[0].endswith(row[1])]
            hit.sort(key=lambda f: f[0]); hit.sort(key=lambda f: f[1], reverse=True)
            out.append([f'{f[0]}({f[1]})' for f in hit])
        elif op == 'addUser':
            ok = row[0] not in users
            if ok: users[row[0]] = row[1]
            out.append(ok)
        elif op == 'addFileBy':
            u, name, size = row
            if u in users and find(name) is None and used(u) + size <= users[u]:
                files.append([name, size, u]); out.append(users[u] - used(u))
            else: out.append(-1)
        elif op == 'mergeUser':
            a, b = row
            if a == b or a not in users or b not in users: out.append(-1); continue
            for f in files:
                if f[2] == b: f[2] = a
            users[a] += users.pop(b); backups.pop(b, None)
            out.append(users[a] - used(a))
        elif op == 'backupUser':
            u = row[0]
            if u not in users: out.append(-1); continue
            backups[u] = [(f[0], f[1]) for f in files if f[2] == u]; out.append(len(backups[u]))
        else:
            u = row[0]
            if u not in users: out.append(-1); continue
            files = [f for f in files if f[2] != u]
            n = 0
            for name, size in backups.get(u, []):
                if find(name) is None: files.append([name, size, u]); n += 1
            out.append(n)
    return out


def ref_snake(src):
    out, i = [], 0
    while i < len(src):
        ch = src[i]
        if ch.isascii() and (ch.isalnum() or ch == '_'):
            j = i
            while j < len(src) and src[j].isascii() and (src[j].isalnum() or src[j] == '_'): j += 1
            tok = src[i:j]; core = tok.lstrip('_'); lead = tok[:len(tok) - len(core)]
            parts = core.split('_')
            snake = len(parts) >= 2 and all(p and all(c.islower() or c.isdigit() for c in p) for p in parts) and parts[0][0].islower()
            out.append(lead + parts[0] + ''.join(p[0].upper() + p[1:] for p in parts[1:]) if snake else tok)
            i = j
        else: out.append(ch); i += 1
    return ''.join(out)


def _subsets(n):
    for mask in range(1 << n): yield mask


def ref_mine(uid, txs, block):
    n = len(txs)
    if n > 16: raise ValueError('reference budget')
    best = None
    for mask in _subsets(n):
        chosen = [i for i in range(n) if mask >> i & 1]
        if sum(txs[i][1] for i in chosen) > block: continue
        if uid == MINE3:
            ids = {txs[i][0] for i in chosen}
            if any(txs[i][3] is not None and txs[i][3] not in ids for i in chosen): continue
        key = (sum(txs[i][2] for i in chosen), -sum(txs[i][1] for i in chosen), chosen)
        if best is None or key[0] > best[0] or (key[0] == best[0] and (key[1] > best[1] or (key[1] == best[1] and key[2] < best[2]))):
            best = key
    if uid == MINE2: return [txs[i][0] for i in best[2]]
    return best[0]


def _fmt_fraction(x):
    # x is a Fraction whose denominator divides a power of 10; shortest exact decimal text
    scale = 0
    while 10 ** scale % x.denominator: scale += 1
    s = str(x.numerator * (10 ** scale // x.denominator)).rjust(scale + 1, '0')
    whole, frac = (s[:-scale], s[-scale:].rstrip('0')) if scale else (s, '')
    return whole + ('.' + frac if frac else '')


def ref_fx(rates, a, b):
    if a == b: return '1'
    adj = {}
    for x, y, r in rates: adj.setdefault(x, []).append((y, Fraction(r)))
    best = [None]

    def dfs(node, value, seen):
        if node == b:
            if best[0] is None or value > best[0]: best[0] = value
            return
        for y, r in adj.get(node, []):
            if y not in seen:
                seen.add(y); dfs(y, value * r, seen); seen.discard(y)
    if len(adj) > 9: raise ValueError('reference budget')
    dfs(a, Fraction(1), {a})
    return '-1' if best[0] is None else _fmt_fraction(best[0])


def ref_crs(uid, ops, rows):
    own, parent, out = [], [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'insert': own.append(row[0]); parent.append(None); out.append(len(own) - 1)
        elif op == 'insertWithReferrer': own.append(row[0]); parent.append(row[1]); out.append(len(own) - 1)
        elif op == 'getLowestK':
            k, floor = row
            totals = [(own[i] + sum(own[j] for j in range(len(own)) if parent[j] == i), i) for i in range(len(own))]
            out.append([i for t, i in sorted(x for x in totals if x[0] >= floor)][:k])
        else:
            c, depth = row
            total = 0
            for j in range(len(own)):  # walk each customer's ancestor chain
                d, x = 0, j
                while x is not None and x != c and d <= depth: x = parent[x]; d += 1
                if x == c and d <= depth: total += own[j]
            out.append(total)
    return out


def ref_c4(ops, rows):
    board = [[None] * 7 for _ in range(6)]  # board[row][col], row 0 = bottom
    turn, over, out = 'A', False, [None]

    def winner():
        for r in range(6):
            for c in range(7):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    cells = [(r + k * dr, c + k * dc) for k in range(4)]
                    if all(0 <= rr < 6 and 0 <= cc < 7 for rr, cc in cells):
                        vals = {board[rr][cc] for rr, cc in cells}
                        if len(vals) == 1 and None not in vals: return vals.pop()
        return None
    for row in rows[1:]:
        c = row[0]
        if over or not 0 <= c < 7 or board[5][c] is not None: out.append('INVALID'); continue
        r = min(i for i in range(6) if board[i][c] is None)
        board[r][c] = turn
        w = winner()
        if w: over = True; out.append(w + '_WINS')
        elif all(board[5][i] is not None for i in range(7)): over = True; out.append('DRAW')
        else: out.append('ONGOING')
        turn = 'B' if turn == 'A' else 'A'
    return out


def ref_kvdb(ops, rows):
    stack = [{}]  # full snapshots; top is the live view
    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        cur = stack[-1]
        if op == 'set': cur[row[0]] = row[1]; out.append(None)
        elif op == 'get': out.append(cur.get(row[0]))
        elif op == 'delete': cur.pop(row[0], None); out.append(None)
        elif op == 'count': out.append(sum(1 for v in cur.values() if v == row[0]))
        elif op == 'begin': stack.append(dict(cur)); out.append(None)
        elif op == 'rollback':
            if len(stack) == 1: out.append(False)
            else: stack.pop(); out.append(True)
        else:
            if len(stack) == 1: out.append(False)
            else: stack = [dict(cur)]; out.append(True)
    return out


def ref_inv(ops, rows):
    docs = [(d[0], _words(d[1])) for d in rows[0][0]]
    out = [None]
    for row in rows[1:]:
        p = _words(row[0])
        if not p: out.append([]); continue
        out.append([i for i, w in docs if any(w[s:s + len(p)] == p for s in range(len(w) - len(p) + 1))])
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid == WKV:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_wkv(*args)
    if uid in (ALH1, ALH2, ALH3, ALH4): return ref_accept(uid, *args)
    if uid in (ABT1, ABT2):
        if len(args[0]) * len(args[1][0][1]) > 3 * 10**6: raise ValueError('reference budget')
        return ref_abt(uid, *args)
    if uid == AFS:
        c = Counter(args[0]); return sorted(args[0], key=lambda v: (c[v], v))
    if uid == BAC1:
        if len(args[0]) > 20000: raise ValueError('reference budget')
        return ref_columns(args[0], 2)
    if uid == BAC2:
        if len(args[0]) * args[1] > 3 * 10**6: raise ValueError('reference budget')
        return ref_columns(*args)
    if uid == CSV: return ref_csv(*args)
    if uid == DASH:
        if len(args[0]) > 600: raise ValueError('reference budget')
        return ref_dash(args[0])
    if uid == CAM:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_cam(*args)
    if uid == CHAT1:
        if sum(q[1] + q[2] for q in args[1]) > 3 * 10**6: raise ValueError('reference budget')
        return ref_chat_ranges(*args)
    if uid == CHAT2: return ref_chat_pages(args[0])
    if uid in (COST1, COST2, COST3):
        region = args[1].get(args[0]['region'], {})
        if sum(s['hours'] for s in args[0]['services'] if type(region.get(s['service'])) is list) > 3 * 10**5: raise ValueError('reference budget')
        return ref_cost(uid, *args)
    if uid in (CSS1, CSS2, CSS3, CSS4):
        if len(args[0]) > 1500: raise ValueError('reference budget')
        return ref_css(uid, *args)
    if uid == SNAKE: return ref_snake(args[0])
    if uid in (MINE1, MINE2, MINE3): return ref_mine(uid, *args)
    if uid == FX: return ref_fx(*args)
    if uid in (CRS1, CRS2):
        if len(args[0]) > 800: raise ValueError('reference budget')
        return ref_crs(uid, *args)
    if uid == C4: return ref_c4(*args)
    if uid == KVDB:
        if len(args[0]) > 2000: raise ValueError('reference budget')
        return ref_kvdb(*args)
    if uid == INV:
        if len(args[0]) * sum(len(d[1]) for d in args[1][0][0]) > 2 * 10**7: raise ValueError('reference budget')
        return ref_inv(*args)
    raise ValueError('unknown identity')
