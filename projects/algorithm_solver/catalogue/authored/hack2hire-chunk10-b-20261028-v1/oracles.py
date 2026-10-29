"""Independent bounded reference algorithms and inferred-domain validators; no candidate imports.

Every specification here is INFERRED by the claude-opus-5-5 subagent on 2026-10-29 from the public
Hack2Hire group preview, title and tags (see contracts.json). None is the official specification.
References deliberately use different, simpler algorithms than the candidates (one refill epoch at a
time, full rescans of session, assignment and funding histories, per-unit time marking, linear task-id
lookups, window enumeration, regular-expression parsing, per-position deletion, naive subtree maxima,
postfix evaluation with fractions, exact fractions, breadth-first search over sums, split-tree counting,
subarray enumeration, per-day marking, backtracking over every start, literal list simulation) and
refuse inputs above a small budget.
"""
from fractions import Fraction
import itertools
import re

H = 'hack2hire:'
TKL = H + '695d85f19c1c1f40daea73a0'
WMS1 = H + '68a4bbecc11d63d6052ea307'
WMS2 = H + '68a4bbf8c11d63d6052ea308'
WMS3 = H + '68a4bbfac11d63d6052ea309'
WMS4 = H + '68a4bbfbc11d63d6052ea30a'
TAS1 = H + '69efc8ea96981f58ae1f6d74'
TAS2 = H + '69efc92d96981f58ae1f6d75'
TAS3 = H + '69efc94196981f58ae1f6d76'
TAS4 = H + '69efc96396981f58ae1f6d77'
PAG = H + '69026c73d18315042523a913'
ENC = H + '685637ce4d16ce2ead6e1769'
EQF = H + '68d9756679db2fbcd7d7db74'
ESL = H + '68102bc42590daeb41a329e6'
EJT = H + '694f5ef093309f91cc14412f'
F1A = H + '68c32db81f64f4312b0a3e26'
F1B = H + '68c32f681f64f4312b0a3e27'
FLX = H + '6a0226e62608e589a944a229'
FAL1 = H + '6acfb93f2e3a0349b3a8eb2d'
FAL2 = H + '6acfbd2f2e3a0349b3a8eb4e'
FAL3 = H + '6acfd33d2e3a0349b3a8ec32'
FAL4 = H + '6acfd3602e3a0349b3a8ec34'
GPU = H + '695d3f8768e2c0dd046c4aa3'
BPP = H + '69e9376dfbaf3da6418286a5'
CFD1 = H + '680fc0442590daeb41a329b8'
CFD2 = H + '680fc04e2590daeb41a329b9'
CFD3 = H + '680fc04f2590daeb41a329ba'
FCP = H + '690416e84845d25b8e994885'
EOS = H + '67843d1e0e1dbb6a0938577d'

IDS = (TKL, WMS1, WMS2, WMS3, WMS4, TAS1, TAS2, TAS3, TAS4, PAG, ENC, EQF, ESL, EJT, F1A, F1B, FLX,
       FAL1, FAL2, FAL3, FAL4, GPU, BPP, CFD1, CFD2, CFD3, FCP, EOS)
WMS = (WMS1, WMS2, WMS3, WMS4)
TAS = (TAS1, TAS2, TAS3, TAS4)
FAL = (FAL1, FAL2, FAL3, FAL4)

_W = [{'addWorker': 3, 'registerWorker': 2, 'get': 1}, {'topNWorkers': 2}, {'promote': 4, 'calcSalary': 3}, {'setDoublePaid': 2}]
_T = [{'addTask': 3, 'updateTask': 4, 'getTask': 2}, {'searchTasks': 3, 'listTasksSorted': 2},
      {'addUser': 3, 'assignTask': 4, 'getUserTasks': 2}, {'completeTask': 3, 'getOverdueAssignments': 2}]


def _upto(levels, k):
    out = {}
    for d in levels[:k]: out.update(d)
    return out


# uid -> (class name, constructor arity, {method: arity}, void methods)
CLASSES = {
    TKL: ('TokenLimiter', 0, {'setPolicy': 5, 'consume': 3, 'getTokens': 2}, ('setPolicy',)),
    PAG: ('Paginator', 3, {'next': 0, 'prev': 0, 'goTo': 1}, ()),
    ENC: ('Codec', 0, {'encode': 1, 'decode': 1}, ()),
}
for _k, _u in enumerate(WMS, 1):
    CLASSES[_u] = ('WorkerManagementSystem', 0, _upto(_W, _k), ('setDoublePaid',) if _k == 4 else ())
for _k, _u in enumerate(TAS, 1):
    CLASSES[_u] = ('TaskManager', 0, _upto(_T, _k), ())
MAX_OPS = 100001
DIGITS = r'0|[1-9][0-9]{0,12}'


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


def rows_of(a, width, maximum, minimum=0):
    if type(a) is not list or not minimum <= len(a) <= maximum: raise ValueError('row list size')
    for r in a:
        if type(r) is not list or len(r) != width: raise ValueError('row width')


def trace(uid, args, maximum=MAX_OPS):
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


ID = r'[a-z0-9_]{1,20}'
WNAME = r'[A-Za-z ]{1,20}'
TNAME = r'[A-Za-z0-9 ]{1,20}'
TASKID = r'[A-Za-z0-9]{1,15}'
CODE = r'[A-Z]{3}'


# ---------------------------------------------------------------- domains
def tkl_domain(args):
    ops, rows = trace(TKL, args)
    last = 0
    for op, row in zip(ops[1:], rows[1:]):
        text(row[0], ID, 20); integer(row[-1], last, 10**9); last = row[-1]
        if op == 'setPolicy': integer(row[1], 1, 10**9); integer(row[2], 1, 10**6); integer(row[3], 1, 10**9)
        elif op == 'consume': integer(row[1], 1, 10**9)


def wms_domain(uid, args):
    ops, rows = trace(uid, args)
    last, workers, top_cost, sal_cost, doubles, sessions = -1, 0, 0, 0, 0, {}
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'addWorker': text(row[0], WNAME, 20); text(row[1], WNAME, 20); integer(row[2], 1, 10**6); workers += 1
        elif op == 'registerWorker':
            text(row[0], WNAME, 20); integer(row[1], last + 1, 10**9); last = row[1]; sessions[row[0]] = sessions.get(row[0], 0) + 1
        elif op == 'get': text(row[0], WNAME, 20)
        elif op == 'topNWorkers': integer(row[0], 1, 10**5); text(row[1], WNAME, 20); top_cost += workers
        elif op == 'promote': text(row[0], WNAME, 20); text(row[1], WNAME, 20); integer(row[2], 1, 10**6); integer(row[3], 0, 10**9)
        elif op == 'calcSalary':
            text(row[0], WNAME, 20); integer(row[1], 0, 10**9); integer(row[2], row[1], 10**9); sal_cost += sessions.get(row[0], 0)
        else: integer(row[0], 0, 10**9 - 1); integer(row[1], row[0] + 1, 10**9); doubles += 1
    if top_cost > 2 * 10**6 or sal_cost > 2 * 10**6 or doubles > 1000: raise ValueError('query cost bound')


def tas_domain(uid, args):
    ops, rows = trace(uid, args)
    last, tasks, assigned, cost = -1, 0, 0, 0
    for op, row in zip(ops[1:], rows[1:]):
        integer(row[0], last + 1, 10**9); last = row[0]
        if op == 'addTask': text(row[1], TNAME, 20); integer(row[2], -10**9, 10**9); tasks += 1
        elif op == 'updateTask': text(row[1], TASKID, 15); text(row[2], TNAME, 20); integer(row[3], -10**9, 10**9)
        elif op == 'getTask': text(row[1], TASKID, 15)
        elif op == 'searchTasks': text(row[1], TNAME, 20); integer(row[2], 1, 10**5); cost += tasks
        elif op == 'listTasksSorted': integer(row[1], 1, 10**5); cost += tasks
        elif op == 'addUser': text(row[1], ID, 20); integer(row[2], 1, 10**5)
        elif op == 'assignTask': text(row[1], TASKID, 15); text(row[2], ID, 20); integer(row[3], row[0] + 1, 2 * 10**9); assigned += 1
        elif op == 'completeTask': text(row[1], TASKID, 15); text(row[2], ID, 20)
        else: text(row[1], ID, 20); cost += assigned
    if cost > 2 * 10**6: raise ValueError('query cost bound')


def pag_domain(args):
    ops, rows = trace(PAG, args, 10001)
    integer(rows[0][0], 1, 10**9); integer(rows[0][1], 1, 100); integer(rows[0][2], 1, rows[0][0])
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'goTo': integer(row[0], -10**9, 10**9)


RLE = re.compile(r'RLE\[(0|[1-9][0-9]{0,9}), ([1-9][0-9]{0,5})\]')
BP = re.compile(r'BP\[([1-9][0-9]?)((?:, (?:0|[1-9][0-9]{0,9})){1,8})\]')


def enc_domain(args):
    ops, rows = trace(ENC, args, 1001)
    total = 0
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'encode': array(row[0], 0, 10**9); total += len(row[0])
        else:
            strlist(row[0], r'(?:RLE|BP)\[[0-9, ]{1,120}\]', 0, 100000, 125); size = 0
            for run in row[0]:
                m = RLE.fullmatch(run)
                if m:
                    if int(m.group(1)) > 10**9 or int(m.group(2)) > 10**5: raise ValueError('run range')
                    size += int(m.group(2)); continue
                m = BP.fullmatch(run)
                if m is None: raise ValueError('run format')
                width, values = int(m.group(1)), [int(x) for x in m.group(2)[2:].split(', ')]
                if not 1 <= width <= 30 or any(v > 10**9 or v >= 2 ** width for v in values): raise ValueError('bit width')
                size += len(values)
            if size > 10**5: raise ValueError('decoded size')
            total += size
    if total > 2 * 10**5: raise ValueError('total size')


def ejt_domain(node, depth=0):
    """Recursive structural check; returns the exact value (truncating division) to bound every intermediate."""
    if depth > 99: raise ValueError('tree depth')
    if type(node) is not dict or type(node.get('operation')) is not str: raise ValueError('node shape')
    if node['operation'] == 'CONSTANT_NUMBER':
        if set(node) != {'operation', 'value'}: raise ValueError('constant keys')
        integer(node['value'], -10**9, 10**9); return node['value']
    if node['operation'] not in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE') or set(node) != {'operation', 'inputs'}: raise ValueError('operator keys')
    if type(node['inputs']) is not list or len(node['inputs']) != 2: raise ValueError('two inputs')
    a, b = ejt_domain(node['inputs'][0], depth + 1), ejt_domain(node['inputs'][1], depth + 1)
    op = node['operation']
    if op == 'ADD': v = a + b
    elif op == 'SUBTRACT': v = a - b
    elif op == 'MULTIPLY': v = a * b
    else:
        if b == 0: raise ValueError('division by zero')
        v = abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1)
    if abs(v) > 10**15: raise ValueError('intermediate magnitude')
    return v


def ejt_count(node):
    n, stack = 0, [node]
    while stack:
        x = stack.pop(); n += 1
        if n > 40000: raise ValueError('node count')
        if type(x) is dict and type(x.get('inputs')) is list: stack.extend(x['inputs'])
    return n


def f1_domain(drivers, laps):
    strlist(drivers, r'[A-Za-z]{1,20}', 1, 1000, 20)
    if len(set(drivers)) != len(drivers): raise ValueError('unique drivers')
    if type(laps) is not list or len(laps) != len(drivers): raise ValueError('parallel lists')
    width = None
    for row in laps:
        array(row, 1, 10**6, 2, 100000)
        if width is None: width = len(row)
        if len(row) != width: raise ValueError('same lap count')
    if width * len(drivers) > 2 * 10**5: raise ValueError('total laps')


COMMANDS = {'INIT': 2, 'FUND': 4, 'BALANCE': 2, 'WITHDRAW': 3, 'TRANSFER': 4, 'PENDING': 2, 'CANCEL': 2}
ALLOWED = {FAL1: ('FUND', 'BALANCE'), FAL2: ('FUND', 'BALANCE', 'WITHDRAW'), FAL3: ('FUND', 'BALANCE', 'WITHDRAW', 'TRANSFER'),
           FAL4: ('FUND', 'BALANCE', 'WITHDRAW', 'TRANSFER', 'PENDING', 'CANCEL')}


def fal_domain(uid, commands):
    strlist(commands, r'[A-Z]{4,8}(?: [a-z0-9_]{1,20}){2,4}', 0, 100000, 100)
    accounts, started, last = set(), False, 0
    for c in commands:
        f = c.split(' ')
        if f[0] not in COMMANDS or len(f) != COMMANDS[f[0]] + 1: raise ValueError('command arity')
        if f[0] == 'INIT':
            if started or f[1] in accounts: raise ValueError('INIT order or duplicate')
            text(f[1], ID, 20); text(f[2], DIGITS, 13); integer(int(f[2]), 0, 10**9); accounts.add(f[1]); continue
        if f[0] not in ALLOWED[uid]: raise ValueError('command not in this level')
        started = True
        text(f[1], DIGITS, 13); day = int(f[1]); integer(day, last, 10**9); last = day
        text(f[2], ID, 20)
        if f[0] in ('FUND', 'WITHDRAW'): text(f[3], DIGITS, 13); integer(int(f[3]), 1, 10**9)
        if f[0] == 'FUND': text(f[4], DIGITS, 13); integer(int(f[4]), 0, 10**9)
        if f[0] == 'TRANSFER': text(f[3], ID, 20); text(f[4], DIGITS, 13); integer(int(f[4]), 1, 10**9)


def cfd_domain(uid, args):
    envelope(args, 3 if uid == CFD3 else 2)
    blocks = args[0]
    rows_of(blocks, 3, 100000)
    for p, s, e in blocks: integer(p, 0, 10**9); integer(s, 1, 10**9); integer(e, s, 10**9)
    integer(args[1], 1, 10**5 if uid == CFD1 else 10**9)
    if uid == CFD3: integer(args[2], 0, len({b[0] for b in blocks}))


def fcp_domain(tickets):
    rows_of(tickets, 2, 10000, 1)
    out, deg, adj = {}, {}, {}
    for a, b in tickets:
        text(a, CODE, 3); text(b, CODE, 3)
        out[a] = out.get(a, 0) + 1; deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) - 1
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    plus = [v for v in deg if deg[v] == 1]; minus = [v for v in deg if deg[v] == -1]
    if any(abs(d) > 1 for d in deg.values()) or len(plus) != len(minus) or len(plus) > 1: raise ValueError('no Euler path')
    seen, stack = {tickets[0][0]}, [tickets[0][0]]
    while stack:
        for y in adj[stack.pop()]:
            if y not in seen: seen.add(y); stack.append(y)
    if len(seen) != len(adj): raise ValueError('disconnected tickets')


def validate_domain(uid, args):
    if uid not in IDS: raise ValueError('unknown identity')
    if uid == TKL: tkl_domain(args)
    elif uid in WMS: wms_domain(uid, args)
    elif uid in TAS: tas_domain(uid, args)
    elif uid == PAG: pag_domain(args)
    elif uid == ENC: enc_domain(args)
    elif uid == EQF:
        envelope(args, 1); text(args[0], r'[a-z]{1,100000}', 100000)
    elif uid == ESL:
        envelope(args, 2); integer(args[0], 1, 2**17 - 1)
        if args[0] & (args[0] + 1): raise ValueError('perfect tree size')
        array(args[1], 1, 10**9, args[0], args[0])
    elif uid == EJT:
        envelope(args, 1); ejt_count(args[0]); ejt_domain(args[0])
    elif uid in (F1A, F1B):
        envelope(args, 2); f1_domain(*args)
    elif uid == FLX:
        envelope(args, 2); array(args[0], 1, 10**4, 1, 100); integer(args[1], 0, 10**4)
    elif uid in FAL:
        envelope(args, 1); fal_domain(uid, args[0])
    elif uid == GPU:
        envelope(args, 2); integer(args[0], 1, 10**5); array(args[1], 0, args[0] - 1, 0, args[0])
        if len(set(args[1])) != len(args[1]): raise ValueError('distinct bad nodes')
    elif uid == BPP:
        envelope(args, 1); array(args[0], 1, len(args[0]), 1)
        if sorted(args[0]) != list(range(1, len(args[0]) + 1)): raise ValueError('permutation')
    elif uid in (CFD1, CFD2, CFD3): cfd_domain(uid, args)
    elif uid == FCP:
        envelope(args, 1); fcp_domain(args[0])
    elif uid == EOS:
        envelope(args, 1); array(args[0], -10**9, 10**9)
        if len(set(args[0])) != len(args[0]): raise ValueError('unique ids')


# ---------------------------------------------------------------- references
def ref_tkl(ops, rows):
    users, out, epochs = {}, [None], 0
    for op, row in zip(ops[1:], rows[1:]):
        u, t = row[0], row[-1]
        if op == 'setPolicy':
            users[u] = {'cap': row[1], 'amt': row[2], 'iv': row[3], 'tok': row[1], 'next': t + row[3]}; out.append(None); continue
        b = users.get(u)
        if b is None: out.append(False if op == 'consume' else -1); continue
        while b['next'] <= t:  # one refill epoch at a time
            b['tok'] = min(b['cap'], b['tok'] + b['amt']); b['next'] += b['iv']; epochs += 1
            if epochs > 200000: raise ValueError('reference budget')
        if op == 'getTokens': out.append(b['tok'])
        elif b['tok'] >= row[1]: b['tok'] -= row[1]; out.append(True)
        else: out.append(False)
    return out


def ref_wms(ops, rows):
    workers, double, out = {}, [], [None]
    for op, row in zip(ops[1:], rows[1:]):
        w = workers.get(row[0]) if op not in ('topNWorkers', 'setDoublePaid') else None
        if op == 'addWorker':
            if w: out.append(False)
            else: workers[row[0]] = {'pos': row[1], 'comp': row[2], 'done': [], 'open': None, 'pending': None, 'stint': 0}; out.append(True)
        elif op == 'registerWorker':
            if w is None: out.append('invalid_request'); continue
            t = row[1]
            if w['open'] is None:
                if w['pending'] and t >= w['pending'][2]:
                    w['pos'], w['comp'] = w['pending'][0], w['pending'][1]; w['pending'] = None; w['stint'] += 1
                w['open'] = (t, w['comp'], w['stint'])
            else: w['done'].append(w['open'] + (t,)); w['open'] = None
            out.append('registered')
        elif op == 'get': out.append(-1 if w is None else sum(s[3] - s[0] for s in w['done']))
        elif op == 'topNWorkers':
            ranked = []
            for wid in workers:
                x = workers[wid]
                if x['pos'] == row[1]: ranked.append((-sum(s[3] - s[0] for s in x['done'] if s[2] == x['stint']), wid))
            ranked.sort()
            out.append(', '.join('%s(%d)' % (wid, -neg) for neg, wid in ranked[:row[0]]))
        elif op == 'promote':
            if w is None or w['pending'] is not None: out.append('invalid_request')
            else: w['pending'] = (row[1], row[2], row[3]); out.append('success')
        elif op == 'calcSalary':
            if w is None: out.append(-1); continue
            total = 0
            for a, comp, _, b in w['done']:
                for unit in range(max(a, row[1]), min(b, row[2])):  # mark every time unit [unit, unit + 1)
                    total += comp * (2 if any(s <= unit < e for s, e in double) else 1)
            out.append(total)
        else: double.append((row[0], row[1])); out.append(None)
    return out


def ref_tas(ops, rows):
    tasks, users, asg, out = [], {}, [], [None]

    def index(tid):  # linear lookup over every created id
        for i in range(len(tasks)):
            if 'taskId%d' % (i + 1) == tid: return i
        return None

    def mine(u, t): return [a for a in asg if a[0] == u and a[2] > t and a[4] is None]
    for op, row in zip(ops[1:], rows[1:]):
        t = row[0]
        if op == 'addTask': tasks.append([row[1], row[2]]); out.append('taskId%d' % len(tasks))
        elif op == 'updateTask':
            i = index(row[1])
            if i is None: out.append(False)
            else: tasks[i] = [row[2], row[3]]; out.append(True)
        elif op == 'getTask':
            i = index(row[1]); out.append('' if i is None else '%s(%d)' % (tasks[i][0], tasks[i][1]))
        elif op in ('searchTasks', 'listTasksSorted'):
            ids = [i for i in range(len(tasks)) if op == 'listTasksSorted' or row[1] in tasks[i][0]]
            ids = sorted(ids, key=lambda i: (-tasks[i][1], i))[:row[-1]]
            out.append(['taskId%d' % (i + 1) for i in ids])
        elif op == 'addUser':
            if row[1] in users: out.append(False)
            else: users[row[1]] = row[2]; out.append(True)
        elif op == 'assignTask':
            u = row[2]
            if index(row[1]) is None or u not in users: out.append(False); continue
            act = mine(u, t)
            if any(a[1] == row[1] for a in act) or len(act) >= users[u]: out.append(False)
            else: asg.append([u, row[1], row[3], len(asg), None]); out.append(True)
        elif op == 'getUserTasks': out.append([a[1] for a in sorted(mine(row[1], t), key=lambda a: (a[2], a[3]))])
        elif op == 'completeTask':
            hit = [a for a in mine(row[2], t) if a[1] == row[1]]
            if hit: hit[0][4] = t
            out.append(bool(hit))
        else: out.append([a[1] for a in asg if a[0] == row[1] and a[4] is None and a[2] <= t])
    return out


def ref_render(total, visible, cur):
    v = min(visible, total); target = cur - (visible - 1) // 2; best = None
    for s in range(1, total - v + 2):  # every window of v pages that contains cur
        if s <= cur <= s + v - 1 and (best is None or abs(s - target) < abs(best - target)): best = s
    parts = (['<'] if cur > 1 else []) + (['...'] if best > 1 else [])
    parts += ['[%d]' % p if p == cur else str(p) for p in range(best, best + v)]
    parts += (['...'] if best + v - 1 < total else []) + (['>'] if cur < total else [])
    return ' '.join(parts)


def ref_pag(ops, rows):
    total, visible, cur = rows[0]; out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        cur = {'next': cur + 1, 'prev': cur - 1}.get(op, row[0] if row else cur)
        cur = sorted([1, cur, total])[1]
        out.append(ref_render(total, visible, cur))
    return out


def ref_enc(ops, rows):
    out = [None]
    for op, row in zip(ops[1:], rows[1:]):
        if op == 'encode':
            runs, loose = [], []

            def flush():
                for i in range(0, len(loose), 8):
                    chunk = loose[i:i + 8]
                    runs.append('BP[%d%s]' % (max(1, max(chunk).bit_length()), ''.join(', %d' % x for x in chunk)))
                loose.clear()
            for v, grp in itertools.groupby(row[0]):
                k = len(list(grp))
                if k >= 3: flush(); runs.append('RLE[%d, %d]' % (v, k))
                else: loose.extend([v] * k)
            flush(); out.append(runs)
        else:
            seq = []
            for run in row[0]:
                m = RLE.fullmatch(run)
                if m: seq.extend([int(m.group(1))] * int(m.group(2)))
                else: seq.extend(int(x) for x in re.findall(r', ([0-9]+)', run))
            out.append(seq)
    return out


def ref_eqf(s):
    def good(t):
        counts = [t.count(c) for c in set(t)]
        return len(set(counts)) <= 1
    return good(s) or any(good(s[:i] + s[i + 1:]) for i in range(len(s)))


def ref_esl(n, lat):
    def best(v):  # maximum path sum from v down to a leaf, recomputed naively
        if 2 * v + 1 >= n: return lat[v]
        return lat[v] + max(best(2 * v + 1), best(2 * v + 2))
    return sum(best((v - 1) // 2) - lat[(v - 1) // 2] - best(v) for v in range(1, n))


def ref_ejt(root):
    post, stack = [], [(root, False)]  # explicit postfix conversion, then a value stack over fractions
    while stack:
        node, seen = stack.pop()
        if node['operation'] == 'CONSTANT_NUMBER': post.append(Fraction(node['value']))
        elif seen: post.append(node['operation'])
        else: stack += [(node, True), (node['inputs'][1], False), (node['inputs'][0], False)]
    vals = []
    for tok in post:
        if isinstance(tok, Fraction): vals.append(tok); continue
        b = vals.pop(); a = vals.pop()
        vals.append({'ADD': a + b, 'SUBTRACT': a - b, 'MULTIPLY': a * b}.get(tok) if tok != 'DIVIDE' else Fraction(int(a / b)))
    return int(vals[0])


def ref_f1(uid, drivers, laps):
    score = [(-(Fraction(sum(r[:-1]), len(r) - 1) - r[-1]), d) for d, r in zip(drivers, laps)]
    score.sort()
    return score[0][1] if uid == F1A else [d for _, d in score]


def ref_flx(durations, total):
    level, seen, steps = {0}, {0}, 0
    while level:
        if total in level: return steps
        nxt = {s + d for s in level for d in durations if s + d <= total} - seen
        seen |= nxt; level = nxt; steps += 1
    return -1


def ref_fal(commands):
    init, funds, moves, out = {}, [], [], []

    def settled(a, d):
        return init[a] + sum(f[1] for f in funds if f[0] == a and f[2] <= d and not f[3]) + sum(x for b, x in moves if b == a)
    for c in commands:
        f = c.split(' ')
        if f[0] == 'INIT': init[f[1]] = int(f[2]); continue
        d, a = int(f[1]), f[2]
        if f[0] == 'FUND':
            if a in init: funds.append([a, int(f[3]), d + int(f[4]), False])
        elif f[0] == 'BALANCE': out.append(settled(a, d) if a in init else -1)
        elif f[0] == 'WITHDRAW':
            if a in init and int(f[3]) <= settled(a, d): moves.append((a, -int(f[3])))
        elif f[0] == 'TRANSFER':
            b, amt = f[3], int(f[4])
            if a in init and b in init and a != b and amt <= settled(a, d): moves += [(a, -amt), (b, amt)]
        elif f[0] == 'PENDING': out.append(sum(x[1] for x in funds if x[0] == a and x[2] > d and not x[3]) if a in init else -1)
        else:
            for x in reversed(funds):
                if x[0] == a and x[2] > d and not x[3]: x[3] = True; break
    return out


def ref_gpu(n, bad):
    """Count tests from the split tree: the root, plus both halves of every multi-node segment holding a bad node."""
    pref = [0] * (n + 1); marked = set(bad)
    for i in range(n): pref[i + 1] = pref[i] + (i in marked)
    calls, segs = 1, [(0, n)]
    while segs:
        lo, hi = segs.pop()
        if hi - lo > 1:
            if pref[hi] - pref[lo] > 0: calls += 2
            mid = (lo + hi) // 2; segs += [(lo, mid), (mid, hi)]
    return [sorted(bad), calls]


def ref_bpp(p):
    n = len(p)
    return ''.join('1' if any(sorted(p[l:l + k]) == list(range(1, k + 1)) for l in range(n - k + 1)) else '0' for k in range(1, n + 1))


def ref_days(uid, blocks, total, k):
    people = {b[0] for b in blocks}
    free = []
    for day in range(1, total + 1):
        busy = {p for p, s, e in blocks if s <= day <= e}
        free.append(len(people) - len(busy) >= k if uid == CFD3 else not busy)
    if uid == CFD1: return [d + 1 for d in range(total) if free[d]]
    out = []
    for d in range(total):
        if free[d]:
            if out and out[-1][1] == d: out[-1][1] = d + 1
            else: out.append([d + 1, d + 1])
    return out


def ref_fcp(tickets):
    tickets = sorted(tickets, key=lambda t: (t[1], t[0])); used = [False] * len(tickets)

    def go(path):
        if len(path) == len(tickets) + 1: return path
        for i, (a, b) in enumerate(tickets):
            if not used[i] and a == path[-1] and not (i and tickets[i - 1] == tickets[i] and not used[i - 1]):
                used[i] = True
                r = go(path + [b])
                used[i] = False
                if r: return r
        return None
    for start in sorted({a for a, _ in tickets}):  # the first element dominates, so try starts in order
        r = go([start])
        if r: return r


def ref_eos(ids):
    arr, out = list(ids), []
    while arr:
        ok = [arr[i] for i in range(len(arr)) if (i == 0 or arr[i] > arr[i - 1]) and (i == len(arr) - 1 or arr[i] > arr[i + 1])]
        x = min(ok); out.append(x); arr.remove(x)
    return out


def reference(uid, args):
    validate_domain(uid, args)
    if uid in CLASSES:
        if len(args[0]) > 400: raise ValueError('reference budget')
        if uid == TKL: return ref_tkl(*args)
        if uid in WMS:
            if any(type(x) is int and x > 3000 for r in args[1] for x in r): raise ValueError('reference budget')
            return ref_wms(*args)
        if uid in TAS: return ref_tas(*args)
        if uid == PAG:
            if args[1][0][0] > 3000: raise ValueError('reference budget')
            return ref_pag(*args)
        if sum(len(r[0]) for r in args[1][1:]) > 5000: raise ValueError('reference budget')
        return ref_enc(*args)
    if uid == EQF:
        if len(args[0]) > 300: raise ValueError('reference budget')
        return ref_eqf(args[0])
    if uid == ESL:
        if args[0] > 4095: raise ValueError('reference budget')
        return ref_esl(*args)
    if uid == EJT:
        if ejt_count(args[0]) > 2000: raise ValueError('reference budget')
        return ref_ejt(args[0])
    if uid in (F1A, F1B):
        if len(args[0]) * len(args[1][0]) > 5000: raise ValueError('reference budget')
        return ref_f1(uid, *args)
    if uid == FLX:
        if args[1] * len(args[0]) > 200000: raise ValueError('reference budget')
        return ref_flx(*args)
    if uid in FAL:
        if len(args[0]) > 400: raise ValueError('reference budget')
        return ref_fal(args[0])
    if uid == GPU:
        if args[0] > 5000: raise ValueError('reference budget')
        return ref_gpu(*args)
    if uid == BPP:
        if len(args[0]) > 60: raise ValueError('reference budget')
        return ref_bpp(args[0])
    if uid in (CFD1, CFD2, CFD3):
        if args[1] * (len(args[0]) + 1) > 100000: raise ValueError('reference budget')
        return ref_days(uid, args[0], args[1], args[2] if uid == CFD3 else 0)
    if uid == FCP:
        if len(args[0]) > 10: raise ValueError('reference budget')
        return ref_fcp(args[0])
    if len(args[0]) > 300: raise ValueError('reference budget')
    return ref_eos(args[0])
