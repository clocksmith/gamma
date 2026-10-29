"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-28 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (literal replay,
snapshots, exhaustive enumeration, quadratic scans).
"""
from fractions import Fraction
from itertools import product
import re
import sys

H = 'hack2hire:'
RATE = H + '68ac41b61bf7d2097f647ef1'
MOD1 = H + '694af9676e481a4b09cbc77d'
MOD2 = H + '694b056e6e481a4b09cbc7e4'
MOD3 = H + '694b08dc6e481a4b09cbc807'
RECT1 = H + '6ac95215339e3a32c154ddc3'
RECT2 = H + '6ac95252339e3a32c154ddc8'
RECT3 = H + '6ac95279339e3a32c154ddca'
RECT4 = H + '6ac952f0339e3a32c154ddd2'
SHEET1 = H + '69f78c6830f41dfd539fc6dc'
SHEET2 = H + '69f78ced30f41dfd539fc6e1'
DIAG = H + '6a330d046849fecc81440a2f'
EXP1 = H + '691f8b9d9abeeebe6fae3eb5'
EXP2 = H + '6920bd4a94b324049c3251a5'
WQ1 = H + '6ab32819e74ebb7457a3f0f5'
WQ2 = H + '6ab328bbe74ebb7457a3f0fc'
PERM = H + '69d184ef17b72775cc49c04e'
FILL = H + '67c76f386c89e288437c3031'
MEET = H + '68fd342247bea664c0bba313'
FREE1 = H + '6a7cd372d713d873ca7ac6ef'
FREE2 = H + '6a7cd38bd713d873ca7ac6f0'
IPV4 = H + '6a0b74fac84b6e8a3be18c83'
TILE = H + '6a21c269d5c5b3e5f9c34546'
FRAC = H + '67d793931989183df53824a0'
FRIEND = H + '68fd2f6247bea664c0bba309'
PROF1 = H + '69308197cd79766b0b310225'
PROF2 = H + '69308714cd79766b0b310228'
PROF3 = H + '69308716cd79766b0b310229'
HOTEL1 = H + '697bdcee9731315964cfaf6f'
HOTEL2 = H + '697bdf679731315964cfaf77'
HOTEL3 = H + '697bdf8c9731315964cfaf78'
DIFF1 = H + '69bd5fda1cbff60a929be96f'
DIFF2 = H + '69eb97bffbaf3da6418293cf'
DIFF3 = H + '69eb97f0fbaf3da6418293d1'

IDS = (RATE, MOD1, MOD2, MOD3, RECT1, RECT2, RECT3, RECT4, SHEET1, SHEET2, DIAG, EXP1, EXP2, WQ1, WQ2, PERM,
       FILL, MEET, FREE1, FREE2, IPV4, TILE, FRAC, FRIEND, PROF1, PROF2, PROF3, HOTEL1, HOTEL2, HOTEL3,
       DIFF1, DIFF2, DIFF3)

_MOD_L1 = {'canRemove': 2}
_MOD_L2 = {**_MOD_L1, 'getModerators': 0}
_MOD_L3 = {**_MOD_L2, 'canRemoveAt': 3, 'getModeratorsAt': 1}
_RECT_L1 = {'addRectangle': 4, 'getTopRectangle': 2}
_RECT_L2 = {**_RECT_L1, 'removeRectangle': 1}
_RECT_L3 = {**_RECT_L2, 'bringToFront': 1}
_RECT_L4 = {**_RECT_L3, 'undo': 0}
_SHEET = {'setCell': 2, 'getCell': 1, 'resetCell': 1}
_WQ = {'reserve': 1, 'complete': 2, 'fail': 2, 'getDeadLetters': 1}
# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    MOD1: ('ModSystem', 1, _MOD_L1, ()), MOD2: ('ModSystem', 1, _MOD_L2, ()), MOD3: ('ModSystem', 1, _MOD_L3, ()),
    RECT1: ('RectangleBoard', 2, _RECT_L1, ()), RECT2: ('RectangleBoard', 2, _RECT_L2, ()),
    RECT3: ('RectangleBoard', 2, _RECT_L3, ()), RECT4: ('RectangleBoard', 2, _RECT_L4, ()),
    SHEET1: ('Spreadsheet', 0, _SHEET, ('setCell', 'resetCell')), SHEET2: ('Spreadsheet', 0, _SHEET, ('resetCell',)),
    WQ1: ('WorkQueue', 3, _WQ, ()), WQ2: ('WorkQueue', 4, _WQ, ()),
}
SAFE = 2**53 - 1
NAME = r'[a-z][a-z0-9_]{0,11}'


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def text(v, pattern, maximum=100):
    if type(v) is not str or not len(v) <= maximum or re.fullmatch(pattern, v) is None: raise ValueError('string domain')


def array(a, lo, hi, minimum=0, maximum=100000):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('array size')
    for v in a: integer(v, lo, hi)


def envelope(args, n):
    if type(args) is not list or len(args) != n: raise ValueError('argument envelope')


def strlist(a, pattern, minimum=0, maximum=100000, width=100):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('list size')
    for v in a: text(v, pattern, width)


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


def cents(s, dollars_ok=False):
    """Exact decimal with at most two fractional digits -> integer hundredths."""
    m = re.fullmatch(r'(0|[1-9][0-9]{0,8})(\.[0-9]{1,2})?', s)
    if m is None: raise ValueError('decimal domain')
    return int(Fraction(s) * 100)


CELL = r'[A-Z](100|[1-9][0-9]?)'
EXP_FIELDS = ('expense_id', 'trip_id', 'amount', 'expense_type', 'vendor_type', 'vendor_name')
OPERATORS = ('<', '<=', '>', '>=', '==', '!=')
HHMM = r'([01][0-9]|2[0-3]):[0-5][0-9]'


def minute(s): return int(s[:2]) * 60 + int(s[3:])


def walk_tree(node, budget, kind):
    """Validate an IPv4 filesystem tree (kind='ip') or a permissions forest node (kind='perm')."""
    stack = [(node, 0)]
    while stack:
        n, depth = stack.pop()
        budget[0] -= 1
        if budget[0] < 0 or depth > 200: raise ValueError('tree budget (depth <= 200 keeps recursive JSON and deepcopy transports within default limits)')
        if type(n) is not dict: raise ValueError('node shape')
        if kind == 'ip':
            if set(n) != {'name', 'isFile', 'lines', 'children'} or type(n['isFile']) is not bool: raise ValueError('node keys')
            text(n['name'], r'[A-Za-z0-9._-]{1,20}', 20)
            if type(n['lines']) is not list or type(n['children']) is not list: raise ValueError('node lists')
            if n['isFile'] and n['children'] or not n['isFile'] and n['lines']: raise ValueError('file/dir shape')
            for line in n['lines']:
                text(line, r'[ -~]{0,200}', 200)
                budget[1] -= len(line) + 1
            if budget[1] < 0: raise ValueError('text budget')
        else:
            if set(n) != {'uuid', 'type', 'userIds', 'children'} or n['type'] not in ('TEAM', 'FOLDER', 'FILE'): raise ValueError('node keys')
            if (n['type'] == 'TEAM') != (depth == 0): raise ValueError('teams only at top level')
            text(n['uuid'], r'[a-z0-9-]{1,36}', 36)
            strlist(n['userIds'], r'u[0-9]{1,6}', 0, 100, 7)
            if type(n['children']) is not list or n['type'] == 'FILE' and n['children']: raise ValueError('children')
            budget[1].append(n['uuid'])
        for c in n['children']: stack.append((c, depth + 1))


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == RATE:
        envelope(args, 3)
        array(args[0], 0, 10**9, 0, 100000); integer(args[1], 1, 10**9); integer(args[2], 1, 100000)
        if any(a > b for a, b in zip(args[0], args[0][1:])): raise ValueError('timestamps non-decreasing')
    elif uid in (MOD1, MOD2, MOD3):
        ops, rows = trace(uid, args, 20001)
        logs = rows[0][0]
        if type(logs) is not list or len(logs) > 20000: raise ValueError('logs')
        last = 0
        for rec in logs:
            if type(rec) is not list or len(rec) != 3: raise ValueError('log record')
            integer(rec[0], last, 10**9); last = rec[0]; text(rec[1], NAME, 12)
            if rec[2] not in ('ADD', 'REMOVE'): raise ValueError('action')
        for op, row in zip(ops[1:], rows[1:]):
            if op in ('canRemoveAt', 'getModeratorsAt'): integer(row[0], 0, 10**9)
            for v in (row[1:] if op == 'canRemoveAt' else row if op == 'canRemove' else []): text(v, NAME, 12)
    elif uid in (RECT1, RECT2, RECT3, RECT4):
        ops, rows = trace(uid, args, 5001)
        integer(rows[0][0], 1, 10**9); integer(rows[0][1], 1, 10**9)
        w, h = rows[0]
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'addRectangle':
                integer(row[0], 0, w - 1); integer(row[2], row[0], w - 1); integer(row[1], 0, h - 1); integer(row[3], row[1], h - 1)
            elif op == 'getTopRectangle': integer(row[0], 0, w - 1); integer(row[1], 0, h - 1)
            elif op in ('removeRectangle', 'bringToFront'): integer(row[0], -10**9, 10**9)
    elif uid in (SHEET1, SHEET2):
        ops, rows = trace(uid, args, 3001)
        for op, row in zip(ops[1:], rows[1:]):
            text(row[0], CELL, 4)
            if op == 'setCell':
                v = row[1]
                if type(v) is not str or len(v) > 400: raise ValueError('cell content')
                term = r'(' + CELL + r'|0|[1-9][0-9]{0,6})'
                if re.fullmatch(r'0|[1-9][0-9]{0,6}', v) is None and re.fullmatch('=' + term + r'(\+' + term + '){0,19}', v) is None:
                    raise ValueError('cell content grammar')
                for lit in re.findall(r'(?<![A-Z0-9])[0-9]+', v):
                    if int(lit) > 10**6: raise ValueError('literal range')
        ref_sheet(uid, ops, rows)  # rejects v1 cycles and unsafe magnitudes
    elif uid == DIAG:
        envelope(args, 2)
        locs, recs = args
        if type(locs) is not list or not 1 <= len(locs) <= 100000: raise ValueError('locations')
        for p in locs:
            if type(p) is not list or len(p) != 2: raise ValueError('point')
            integer(p[0], -10**9, 10**9); integer(p[1], -10**9, 10**9)
        if len({tuple(p) for p in locs}) != len(locs): raise ValueError('unique locations')
        array(recs, 1, 4, 0, 100000)
    elif uid in (EXP1, EXP2):
        envelope(args, 2)
        rules, expenses = args
        if type(rules) is not list or len(rules) > 200 or type(expenses) is not list or len(expenses) > 5000: raise ValueError('sizes')
        for e in expenses:
            if type(e) is not list or len(e) != 6: raise ValueError('expense row')
            text(e[0], r'E[0-9]{1,6}', 7); text(e[1], r'T[0-9]{1,6}', 7); cents(e[2])
            for v in e[3:]: text(v, r'[a-z_]{1,16}', 16)
        if len({e[0] for e in expenses}) != len(expenses): raise ValueError('unique expense ids')
        for r in rules:
            if type(r) is not list or len(r) != 7: raise ValueError('rule row')
            if r[0] not in (('expense',) if uid == EXP1 else ('expense', 'trip')): raise ValueError('rule type')
            text(r[1], r'R[0-9]{1,4}', 5)
            if r[2] not in EXP_FIELDS[2:] or r[0] == 'trip' and r[2] != 'amount': raise ValueError('rule field')
            if r[3] not in (OPERATORS if r[2] == 'amount' else ('==', '!=')): raise ValueError('operator')
            if r[2] == 'amount': cents(r[4])
            else: text(r[4], r'[a-z_]{1,16}', 16)
            if r[5] == '':
                if r[6] != '': raise ValueError('empty conditional')
            else:
                if r[5] not in EXP_FIELDS[3:]: raise ValueError('conditional field')
                text(r[6], r'[a-z_]{1,16}', 16)
        if len({r[1] for r in rules}) != len(rules): raise ValueError('unique rule ids')
    elif uid in (WQ1, WQ2):
        ops, rows = trace(uid, args, 20001)
        ctor = rows[0]
        task_ids = ctor[0]
        array(task_ids, 0, 10**9, 0, 20000)
        if len(set(task_ids)) != len(task_ids): raise ValueError('unique tasks')
        integer(ctor[-2], 1, 10**9); integer(ctor[-1], 1, 1000)
        if uid == WQ2:
            deps = ctor[1]
            if type(deps) is not list or len(deps) > 40000: raise ValueError('dependencies')
            known = set(task_ids); seen = set(); indeg = {t: 0 for t in task_ids}; out = {t: [] for t in task_ids}
            for d in deps:
                if type(d) is not list or len(d) != 2 or d[0] not in known or d[1] not in known or d[0] == d[1]: raise ValueError('dependency')
                if tuple(d) in seen: raise ValueError('duplicate dependency')
                seen.add(tuple(d)); indeg[d[1]] += 1; out[d[0]].append(d[1])
            frontier = [t for t in task_ids if indeg[t] == 0]; count = 0
            while frontier:
                t = frontier.pop(); count += 1
                for u in out[t]:
                    indeg[u] -= 1
                    if indeg[u] == 0: frontier.append(u)
            if count != len(task_ids): raise ValueError('dependency cycle')
        last = 0
        for op, row in zip(ops[1:], rows[1:]):
            integer(row[0], last, 2 * 10**9); last = row[0]
            if op in ('complete', 'fail'): integer(row[1], 0, 10**9)
    elif uid == PERM:
        envelope(args, 2)
        teams, queries = args
        if type(teams) is not list or len(teams) > 1000: raise ValueError('teams')
        budget = [100000, []]
        for t in teams: walk_tree(t, budget, 'perm')
        if len(set(budget[1])) != len(budget[1]): raise ValueError('unique uuids')
        if type(queries) is not list or len(queries) > 100000: raise ValueError('queries')
        for q in queries:
            if type(q) is not list or len(q) != 2: raise ValueError('query')
            text(q[0], r'u[0-9]{1,6}', 7); text(q[1], r'[a-z0-9-]{1,36}', 36)
    elif uid == FILL:
        envelope(args, 1)
        text(args[0], r'(0|[1-9][0-9]?)( (0|[1-9][0-9]?)){0,6} = (0|[1-9][0-9]{0,14})', 64)
    elif uid == MEET:
        envelope(args, 2)
        strlist(args[0], NAME + ' [a-z]{1,12} ' + HHMM + ' ' + HHMM, 0, 20000, 50)
        for e in args[0]:
            parts = e.split(' ')
            if minute(parts[2]) > minute(parts[3]): raise ValueError('start after end')
        integer(args[1], 1, 1440)
    elif uid in (FREE1, FREE2):
        envelope(args, 1 if uid == FREE1 else 2)
        ranges = args[0]
        if type(ranges) is not list or len(ranges) > 1000: raise ValueError('ranges')
        used = set()
        for r in ranges:
            if type(r) is not list or len(r) != 3: raise ValueError('range row')
            text(r[0], r'[a-z][a-z0-9_-]{0,15}', 16)
            for v in r[1:]: text(v, r'0|[1-9][0-9]{0,2}', 3)
            a, b = int(r[1]), int(r[2])
            if a > b: raise ValueError('reversed range')
            span = set(range(a, b + 1))
            if span & used: raise ValueError('overlapping allocation')
            used |= span
        if uid == FREE2: integer(args[1], 1, 1000)
    elif uid == IPV4:
        envelope(args, 1)
        walk_tree(args[0], [20000, 2000000], 'ip')
    elif uid == TILE:
        envelope(args, 2)
        strlist(args[0], r'[RB_]', 1, 12, 1); strlist(args[1], r'[RB_]', len(args[0]), len(args[0]), 1)
    elif uid == FRAC:
        envelope(args, 2)
        orders, inventory = args
        if type(orders) is not list or len(orders) > 100000 or type(inventory) is not list or len(inventory) > 1000: raise ValueError('sizes')
        sym = r'[A-Z]{1,5}'
        for o in orders:
            if type(o) is not list or len(o) != 4 or o[1] not in ('B', 'S'): raise ValueError('order')
            text(o[0], sym, 5); text(o[3], r'[1-9][0-9]{0,7}', 8)
            if type(o[2]) is not str: raise ValueError('quantity')
            if o[2].startswith('$'): cents(o[2][1:])
            else:
                if cents(o[2]) > 10**8: raise ValueError('share quantity')
        if [o[0] for o in orders] != sorted(o[0] for o in orders): raise ValueError('orders sorted by symbol')
        for it in inventory:
            if type(it) is not list or len(it) != 2: raise ValueError('inventory row')
            text(it[0], sym, 5); text(it[1], r'0|[1-9][0-9]?', 2)
        names = [it[0] for it in inventory]
        if names != sorted(set(names)): raise ValueError('inventory sorted unique')
    elif uid == FRIEND:
        envelope(args, 2)
        integer(args[0], 1, 1000)
        edges = args[1]
        if type(edges) is not list or len(edges) > 5000: raise ValueError('edges')
        seen = set()
        for e in edges:
            if type(e) is not list or len(e) != 2: raise ValueError('edge')
            integer(e[0], 0, args[0] - 1); integer(e[1], 0, args[0] - 1)
            key = (min(e), max(e))
            if e[0] == e[1] or key in seen: raise ValueError('self or duplicate friendship')
            seen.add(key)
    elif uid in (PROF1, PROF2, PROF3):
        envelope(args, 2 if uid == PROF2 else 1)
        samples = args[0]
        strlist(samples, r'(0|[1-9][0-9]{0,8}):(' + NAME + r'(->' + NAME + r')*)?', 0, 20000, 2000)
        times = [int(s.split(':', 1)[0]) for s in samples]
        if any(a >= b for a, b in zip(times, times[1:])): raise ValueError('times strictly increasing')
        if sum(len(s) for s in samples) > 2000000: raise ValueError('text budget')
        if uid == PROF2: integer(args[1], 1, 20000)
    elif uid in (HOTEL1, HOTEL2, HOTEL3):
        envelope(args, 2)
        res, tps = args
        if type(res) is not list or len(res) > 5000 or type(tps) is not dict or len(tps) > 20: raise ValueError('sizes')
        for r in res:
            if type(r) is not dict or set(r) != {'guest_name', 'room_type', 'check_in_day', 'stay_length'}: raise ValueError('reservation')
            text(r['guest_name'], r'[A-Z][a-z]{0,11}', 12); text(r['room_type'], r'[a-z]{1,12}', 12)
            integer(r['check_in_day'], 0, 10**6); integer(r['stay_length'], 1, 365)
        for name, tp in tps.items():
            text(name, r'[a-z][a-z_]{0,19}', 20)
            if uid == HOTEL1: integer(tp, -365, 365)
            else:
                keys = {'anchor', 'offset'} | ({'room_types'} if uid == HOTEL3 and type(tp) is dict and 'room_types' in tp else set())
                if type(tp) is not dict or set(tp) != keys or tp['anchor'] not in ('check_in', 'check_out'): raise ValueError('touchpoint')
                integer(tp['offset'], -365, 365)
                if 'room_types' in tp: strlist(tp['room_types'], r'[a-z]{1,12}', 0, 10, 12)
    elif uid in (DIFF1, DIFF2, DIFF3):
        envelope(args, 2)
        limit = 2000 if uid == DIFF3 else 100000
        for lines in args: strlist(lines, r'[ -~]{0,40}', 0, limit, 40)


# ---------------------------------------------------------------- references

def ref_rate(ts, window, limit):
    if len(ts) > 3000: raise ValueError('reference budget')
    allowed, out = [], []
    for t in ts:
        ok = sum(1 for a in allowed if t - window + 1 <= a <= t) + 1 <= limit
        out.append(ok)
        if ok: allowed.append(t)
    return out


def mod_state(logs):
    """Literal replay -> list of (user, sequence) in hierarchy order."""
    active = []
    for seq, (_, user, action) in enumerate(logs):
        names = [u for u, _ in active]
        if action == 'ADD' and user not in names: active.append((user, seq))
        if action == 'REMOVE' and user in names: active.pop(names.index(user))
    return [u for u, _ in active]


def mod_can(order, actor, target):
    return actor in order and target in order and order.index(actor) < order.index(target)


def ref_mod(ops, rows):
    logs = rows[0][0]
    if len(logs) * len(ops) > 4 * 10**6: raise ValueError('reference budget')
    now = mod_state(logs); out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'canRemove': out.append(mod_can(now, *row))
        elif op == 'getModerators': out.append(list(now))
        else:
            past = mod_state([r for r in logs if r[0] <= row[0]])
            out.append(mod_can(past, row[1], row[2]) if op == 'canRemoveAt' else past)
    return out


def ref_rect(ops, rows):
    if len(ops) > 1200: raise ValueError('reference budget')
    rects, order, history, out, nxt = {}, [], [], [None], 1
    for op, row in zip(ops[1:], rows[1:]):
        snap = (dict(rects), list(order))
        if op == 'addRectangle':
            rects[nxt] = tuple(row); order.append(nxt); out.append(nxt); nxt += 1; history.append(snap)
        elif op == 'getTopRectangle':
            x, y = row; hit = -1
            for rid in order:
                x1, y1, x2, y2 = rects[rid]
                if x1 <= x <= x2 and y1 <= y <= y2: hit = rid
            out.append(hit)
        elif op == 'removeRectangle':
            ok = row[0] in order
            if ok: order.remove(row[0]); history.append(snap)
            out.append(ok)
        elif op == 'bringToFront':
            ok = row[0] in order
            if ok: order.remove(row[0]); order.append(row[0]); history.append(snap)
            out.append(ok)
        else:
            if history: rects, order = history.pop(); rects, order = dict(rects), list(order); out.append(True)
            else: out.append(False)
    return out


def sheet_value(cells, cell, memo, depth=0):
    if depth > 3000: raise ValueError('reference depth')
    if cell in memo:
        if memo[cell] is None: raise ValueError('cycle')
        return memo[cell]
    memo[cell] = None
    content = cells.get(cell, '0')
    if content.startswith('='):
        total = 0
        for term in content[1:].split('+'):
            total += int(term) if term[0].isdigit() else sheet_value(cells, term, memo, depth + 1)
    else: total = int(content)
    memo[cell] = total
    return total


def ref_sheet(uid, ops, rows):
    old = sys.getrecursionlimit(); sys.setrecursionlimit(max(old, 10000))
    try:
        cells, out = {}, [None]
        for op, row in zip(ops[1:], rows[1:]):
            if op == 'setCell':
                trial = dict(cells); trial[row[0]] = row[1]
                try:
                    memo = {}
                    for c in trial: sheet_value(trial, c, memo)
                    ok = True
                except ValueError as e:
                    if str(e) != 'cycle': raise
                    if uid == SHEET1: raise ValueError('cycle outside inferred v1 domain')
                    ok = False
                if ok: cells = trial
                out.append(None if uid == SHEET1 else ok)
            elif op == 'resetCell': cells.pop(row[0], None); out.append(None)
            else:
                v = sheet_value(cells, row[0], {})
                if v > SAFE: raise ValueError('magnitude outside inferred domain')
                out.append(v)
        return out
    finally: sys.setrecursionlimit(old)


def ref_diag(locs, recs):
    if len(locs) * len(recs) > 4 * 10**6: raise ValueError('reference budget')
    sx, sy = {1: (1, 1), 2: (1, -1), 3: (-1, 1), 4: (-1, -1)}, None
    a, b = locs[0]
    for d in recs:
        dx, dy = sx[d]; best = None
        for x, y in locs:
            z = (x - a) * dx
            if z >= 1 and (y - b) * dy == z and (best is None or z < best[0]): best = (z, x, y)
        if best: a, b = best[1], best[2]
    return [a, b]


def ref_expense(rules, expenses):
    def value(e, f): return Fraction(e[EXP_FIELDS.index(f)]) if f == 'amount' else e[EXP_FIELDS.index(f)]

    def holds(lhs, op, rhs): return {'<': lhs < rhs, '<=': lhs <= rhs, '>': lhs > rhs, '>=': lhs >= rhs, '==': lhs == rhs, '!=': lhs != rhs}[op]
    out = []
    for r in rules:
        rhs = Fraction(r[4]) if r[2] == 'amount' else r[4]
        hits = [e for e in expenses if r[5] == '' or value(e, r[5]) == r[6]]
        if r[0] == 'expense':
            out += [[r[1], e[0]] for e in hits if not holds(value(e, r[2]), r[3], rhs)]
        else:
            trips = []
            for e in hits:
                if e[1] not in trips: trips.append(e[1])
            out += [[r[1], t] for t in trips if not holds(sum(Fraction(e[2]) for e in hits if e[1] == t), r[3], rhs)]
    return out


def ref_queue(uid, ops, rows):
    if len(ops) > 1500: raise ValueError('reference budget')
    ctor = rows[0]
    tasks, lease, cap = ctor[0], ctor[-2], ctor[-1]
    deps = ctor[1] if uid == WQ2 else []
    status = {t: 'waiting' for t in tasks}  # waiting|ready|reserved|done|dead
    attempts = {t: 0 for t in tasks}; ready = []; dead = []; holds = []  # holds: [deadline, seq, task]
    pos = {t: i for i, t in enumerate(tasks)}
    prereq = {t: [a for a, b in deps if b == t] for t in tasks}
    for t in tasks:
        if not prereq[t]: status[t] = 'ready'; ready.append(t)
    seq = 0

    def kill(t):
        status[t] = 'dead'; dead.append(t); queue = [t]
        while queue:
            x = queue.pop(0)
            for u in sorted((b for a, b in deps if a == x), key=pos.get):
                if status[u] != 'dead': status[u] = 'dead'; dead.append(u); queue.append(u)

    def release(t):
        if attempts[t] < cap: status[t] = 'ready'; ready.append(t)
        else: kill(t)

    def expire(now):
        for h in sorted(holds):
            if h[0] <= now: holds.remove(h); release(h[2])
    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        expire(row[0])
        if op == 'reserve':
            if ready:
                t = ready.pop(0); attempts[t] += 1; status[t] = 'reserved'; seq += 1; holds.append([row[0] + lease, seq, t]); out.append(t)
            else: out.append(-1)
        elif op in ('complete', 'fail'):
            h = [h for h in holds if h[2] == row[1]]
            if not h: out.append(False); continue
            holds.remove(h[0])
            if op == 'fail': release(row[1])
            else:
                status[row[1]] = 'done'
                for u in tasks:
                    if status[u] == 'waiting' and prereq[u] and all(status[p] == 'done' for p in prereq[u]): status[u] = 'ready'; ready.append(u)
            out.append(True)
        else: out.append(list(dead))
    return out


def ref_perm(teams, queries):
    if len(queries) > 2000: raise ValueError('reference budget')
    out = []
    for user, target in queries:
        reach = set(); stack = [(t, False) for t in teams]
        while stack:
            n, granted = stack.pop()
            granted = granted or user in n['userIds']
            if granted: reach.add(n['uuid'])
            stack += [(c, granted) for c in n['children']]
        out.append(target in reach)
    return out


def ref_fill(equation):
    left, target = equation.split(' = ')
    nums = [int(x) for x in left.split(' ')]
    if len(nums) > 7: raise ValueError('reference budget')

    def trees(i, j):
        if i == j: return [('n', nums[i])]
        return [(op, a, b) for k in range(i, j) for a in trees(i, k) for b in trees(k + 1, j) for op in '+*']

    def ev(t): return t[1] if t[0] == 'n' else ev(t[1]) + ev(t[2]) if t[0] == '+' else ev(t[1]) * ev(t[2])

    def show(t):
        if t[0] == 'n': return str(t[1])
        a, b = show(t[1]), show(t[2])
        if t[0] == '*':
            if t[1][0] == '+': a = '(' + a + ')'
            if t[2][0] == '+': b = '(' + b + ')'
            return a + '*' + b
        return a + '+' + b
    return sorted({show(t) for t in trees(0, len(nums) - 1) if ev(t) == int(target)})


def ref_meet(events, k):
    busy = [False] * 1440
    for e in events:
        _, _, a, b = e.split(' ')
        for m in range(minute(a), minute(b) + 1): busy[m] = True
    for t in range(0, 1440 - k + 1):
        if not any(busy[t:t + k]): return '%02d:%02d' % divmod(t, 60)
    return '-1'


def ref_free(ranges, size=1):
    used = [False] * 1000
    for _, a, b in ranges:
        for i in range(int(a), int(b) + 1): used[i] = True
    out, i = [], 0
    while i < 1000:
        if used[i]: i += 1; continue
        j = i
        while j + 1 < 1000 and not used[j + 1]: j += 1
        if j - i + 1 >= size: out.append([str(i), str(j)])
        i = j + 1
    return out


IP_RUN = re.compile(r'[0-9.]+')
OCTET = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])'
IP_EXACT = re.compile(OCTET + r'(\.' + OCTET + r'){3}')


def ref_ipv4(root):
    found = set(); stack = [root]
    while stack:
        n = stack.pop()
        for line in n['lines']:
            for m in IP_RUN.finditer(line):
                if IP_EXACT.fullmatch(m.group()): found.add(m.group())
        stack += n['children']
    return sorted(found)


def tile_prev(board):
    """Reverse moves: all boards b' such that one legal forward move turns b' into board."""
    out, n = [], len(board)
    for i, c in enumerate(board):
        if c == 'R':
            for step in (1, 2):
                j = i - step
                if j >= 0 and board[j] == '_' and (step == 1 or board[i - 1] == 'B'):
                    b = list(board); b[i], b[j] = '_', 'R'; out.append(tuple(b))
        if c == 'B':
            for step in (1, 2):
                j = i + step
                if j < n and board[j] == '_' and (step == 1 or board[i + 1] == 'R'):
                    b = list(board); b[i], b[j] = '_', 'B'; out.append(tuple(b))
    return out


def ref_tile(start, target):
    if sorted(start) != sorted(target): return False
    goal, seen, frontier = tuple(start), {tuple(target)}, [tuple(target)]
    while frontier:
        b = frontier.pop()
        if b == goal: return True
        for p in tile_prev(b):
            if p not in seen: seen.add(p); frontier.append(p)
    return False


def ref_frac(orders, inventory):
    inv = {s: Fraction(int(v), 100) for s, v in inventory}
    for sym, kind, qty, price in orders:
        shares = Fraction(int(Fraction(qty[1:]) * 100) * 100 // int(price), 100) if qty.startswith('$') else Fraction(qty)
        have = inv.get(sym, Fraction(0))
        if kind == 'B':
            while have < shares: have += 1
            have -= shares
        else:
            have += shares
            while have >= 1: have -= 1
        inv[sym] = have
    return [[s, str(int(inv[s] * 100))] for s in sorted(inv)]


def ref_friend(n, edges):
    if n > 300: raise ValueError('reference budget')
    adj = [[False] * n for _ in range(n)]
    for a, b in edges: adj[a][b] = adj[b][a] = True
    out = []
    for u in range(n):
        best, pick = 0, -1
        for v in range(n):
            if v == u or adj[u][v]: continue
            m = sum(1 for w in range(n) if adj[u][w] and adj[v][w])
            if m > best: best, pick = m, v
        out.append(pick)
    return out


def parse_samples(samples):
    rows = []
    for s in samples:
        t, st = s.split(':', 1)
        rows.append((int(t), st.split('->') if st else []))
    return rows


def frame_runs(samples):
    """Every frame instance as (depth, name, first sample index, last sample index, open-at-end)."""
    rows = parse_samples(samples); runs = []
    for i, (_, st) in enumerate(rows):
        for d, name in enumerate(st):
            if i > 0 and len(rows[i - 1][1]) > d and rows[i - 1][1][:d + 1] == st[:d + 1]: continue
            j = i
            while j + 1 < len(rows) and rows[j + 1][1][:d + 1] == st[:d + 1]: j += 1
            runs.append((d, name, i, j, j == len(rows) - 1))
    return rows, runs


def ref_prof_events(samples, minimum=1):
    if len(samples) > 1500: raise ValueError('reference budget')
    rows, runs = frame_runs(samples); ev = []
    for d, name, i, j, open_end in runs:
        if j - i + 1 < minimum: continue
        ev.append((rows[i][0], 1, d, ['start', name, rows[i][0]]))
        if not open_end: ev.append((rows[j + 1][0], 0, -d, ['end', name, rows[j + 1][0]]))
    return [e[3] for e in sorted(ev, key=lambda e: e[:3])]


def ref_prof_exclusive(samples):
    rows = parse_samples(samples); total = {}
    for _, st in rows:
        for name in st: total.setdefault(name, 0)
    for (t, st), (u, _) in zip(rows, rows[1:]):
        if st: total[st[-1]] += u - t
    return [[k, total[k]] for k in sorted(total)]


def ref_hotel(uid, res, tps):
    out = []
    for r in res:
        for name, tp in tps.items():
            if uid == HOTEL1: day = r['check_in_day'] + tp
            else:
                if uid == HOTEL3 and 'room_types' in tp and r['room_type'] not in tp['room_types']: continue
                base = r['check_in_day'] + (r['stay_length'] if tp['anchor'] == 'check_out' else 0)
                day = base + tp['offset']
            out.append([day, r['guest_name'], name])
    return sorted(out)


def unique_pairs(a, b):
    return [[i, b.index(x)] for i, x in enumerate(a) if a.count(x) == 1 and b.count(x) == 1]


def best_chain(pairs):
    """Longest strictly increasing-in-j chain over pairs sorted by i; lexicographically smallest i list."""
    best = [None] * len(pairs)
    for k in range(len(pairs) - 1, -1, -1):
        cand = [pairs[k]]
        for m in range(k + 1, len(pairs)):
            if pairs[m][1] > pairs[k][1]:
                c = [pairs[k]] + best[m]
                if len(c) > len(cand) or len(c) == len(cand) and [p[0] for p in c] < [p[0] for p in cand]: cand = c
        best[k] = cand
    out = []
    for c in best:
        if len(c) > len(out) or len(c) == len(out) and [p[0] for p in c] < [p[0] for p in out]: out = c
    return out


def ref_diff(a, b):
    if a == b: return ['  ' + x for x in a]
    p = 0
    while p < len(a) and p < len(b) and a[p] == b[p]: p += 1
    s = 0
    while s < len(a) - p and s < len(b) - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]: s += 1
    ma, mb = a[p:len(a) - s], b[p:len(b) - s]
    chain = best_chain(unique_pairs(ma, mb))
    mid = []
    if not chain: mid = ['- ' + x for x in ma] + ['+ ' + x for x in mb]
    else:
        pi = pj = 0
        for i, j in chain:
            mid += ref_diff(ma[pi:i], mb[pj:j]) + ['  ' + ma[i]]; pi, pj = i + 1, j + 1
        mid += ref_diff(ma[pi:], mb[pj:])
    return ['  ' + x for x in a[:p]] + mid + ['  ' + x for x in a[len(a) - s:]]


def reference(uid, args):
    validate_domain(uid, args)
    if uid == RATE: return ref_rate(*args)
    if uid in (MOD1, MOD2, MOD3): return ref_mod(*args)
    if uid in (RECT1, RECT2, RECT3, RECT4): return ref_rect(*args)
    if uid in (SHEET1, SHEET2):
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_sheet(uid, *args)
    if uid == DIAG: return ref_diag(*args)
    if uid in (EXP1, EXP2):
        if len(args[0]) * len(args[1]) > 200000: raise ValueError('reference budget')
        return ref_expense(*args)
    if uid in (WQ1, WQ2): return ref_queue(uid, *args)
    if uid == PERM: return ref_perm(*args)
    if uid == FILL: return ref_fill(args[0])
    if uid == MEET: return ref_meet(*args)
    if uid in (FREE1, FREE2): return ref_free(*args)
    if uid == IPV4: return ref_ipv4(args[0])
    if uid == TILE: return ref_tile(*args)
    if uid == FRAC:
        if len(args[0]) > 3000: raise ValueError('reference budget')
        return ref_frac(*args)
    if uid == FRIEND: return ref_friend(*args)
    if uid == PROF1: return ref_prof_events(args[0])
    if uid == PROF2: return ref_prof_events(args[0], args[1])
    if uid == PROF3: return ref_prof_exclusive(args[0])
    if uid in (HOTEL1, HOTEL2, HOTEL3): return ref_hotel(uid, *args)
    if max(len(args[0]), len(args[1])) > (60 if uid == DIFF3 else 400): raise ValueError('reference budget')
    pairs = unique_pairs(*args)
    if uid == DIFF1: return pairs[0] if pairs else [-1, -1]
    if uid == DIFF2: return best_chain(pairs)
    return ref_diff(*args)


def diff_reconstructs(a, b, out):
    """Independent property: the diff applied to lines1 yields lines2."""
    return [x[2:] for x in out if x[:2] in ('  ', '- ')] == a and [x[2:] for x in out if x[:2] in ('  ', '+ ')] == b
