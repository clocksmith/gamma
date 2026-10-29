"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h10b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


def wid(i):
    """Fixed-length letter id; lexicographic order equals numeric order."""
    return ''.join(chr(65 + (i // 26 ** k) % 26) for k in (3, 2, 1, 0))


def code(i):
    return ''.join(chr(65 + (i // 26 ** k) % 26) for k in (2, 1, 0))


def _tkl(rng):
    calls, t = [], 0
    for _ in range(rng.randrange(1, 25)):
        t += rng.choice([0, 0, 1, 2, 3, 7, 20])
        u = rng.choice(['a', 'b', 'u_1'])
        r = rng.random()
        if r < 0.25: calls.append(('setPolicy', u, rng.choice([1, 3, 5, 10]), rng.choice([1, 2, 4]), rng.choice([1, 2, 5, 10]), t))
        elif r < 0.75: calls.append(('consume', u, rng.choice([1, 1, 2, 3, 6, 11]), t))
        else: calls.append(('getTokens', u, t))
    return _ops('TokenLimiter', [], calls)


def _wms(rng, level):
    names = ['Ann', 'Bo Li', 'Cy', 'ann']; pos = ['Dev', 'QA', 'Dev Ops']
    calls, t = [('addWorker', 'Ann', 'Dev', 5), ('addWorker', 'Cy', rng.choice(pos), 3)][:rng.randrange(0, 3)], 0
    for _ in range(rng.randrange(1, 30)):
        r = rng.random(); w = rng.choice(names)
        if r < 0.2: calls.append(('addWorker', w, rng.choice(pos), rng.choice([1, 2, 5, 100])))
        elif r < 0.55: t += rng.choice([1, 1, 2, 3, 7]); calls.append(('registerWorker', w, t))
        elif r < 0.65: calls.append(('get', w))
        elif level >= 2 and r < 0.75: calls.append(('topNWorkers', rng.choice([1, 2, 3, 10]), rng.choice(pos)))
        elif level >= 3 and r < 0.85: calls.append(('promote', w, rng.choice(pos), rng.choice([1, 3, 50]), rng.choice([0, t, t + 2, t + 5, t + 30])))
        elif level >= 3 and r < 0.95:
            a = rng.randrange(0, t + 3); calls.append(('calcSalary', w, a, a + rng.choice([0, 1, 3, 10, 100])))
        elif level >= 4:
            a = rng.randrange(0, t + 10); calls.append(('setDoublePaid', a, a + rng.choice([1, 2, 5, 20])))
        else: calls.append(('get', w))
    return _ops('WorkerManagementSystem', [], calls)


def _tas(rng, level):
    calls, t, made = [], 0, 0
    for _ in range(rng.randrange(1, 30)):
        t += rng.choice([1, 1, 2, 3])
        r = rng.random()
        tid = 'taskId%d' % rng.randrange(0, made + 2) if rng.random() < 0.9 else rng.choice(['x', 'taskid1'])
        if r < 0.25: calls.append(('addTask', t, rng.choice(['fix bug', 'Bug', 'write docs', 'bugfix', 'a']), rng.choice([-5, 0, 1, 3, 3, 10**9]))); made += 1
        elif r < 0.35: calls.append(('updateTask', t, tid, rng.choice(['bug', 'docs', 'X 1']), rng.choice([0, 2, 3, -10**9])))
        elif r < 0.45: calls.append(('getTask', t, tid))
        elif level >= 2 and r < 0.55: calls.append(('searchTasks', t, rng.choice(['bug', 'Bug', 'o', 'z', ' ']), rng.choice([1, 2, 5])))
        elif level >= 2 and r < 0.6: calls.append(('listTasksSorted', t, rng.choice([1, 3, 10])))
        elif level >= 3 and r < 0.68: calls.append(('addUser', t, rng.choice(['u', 'v', 'w_2']), rng.choice([1, 2, 3])))
        elif level >= 3 and r < 0.82: calls.append(('assignTask', t, tid, rng.choice(['u', 'v', 'w_2', 'z']), t + rng.choice([1, 2, 3, 5, 10])))
        elif level >= 3 and r < 0.9: calls.append(('getUserTasks', t, rng.choice(['u', 'v', 'z'])))
        elif level >= 4 and r < 0.95: calls.append(('completeTask', t, tid, rng.choice(['u', 'v'])))
        elif level >= 4: calls.append(('getOverdueAssignments', t, rng.choice(['u', 'v', 'z'])))
        else: calls.append(('getTask', t, tid))
    return _ops('TaskManager', [], calls)


def _pag(rng):
    total = rng.choice([1, 2, 3, 5, 7, 10, 30]); vis = rng.choice([1, 2, 3, 4, 5, 7, 40])
    calls = []
    for _ in range(rng.randrange(1, 12)):
        r = rng.random()
        if r < 0.4: calls.append(('next',))
        elif r < 0.7: calls.append(('prev',))
        else: calls.append(('goTo', rng.choice([-3, 0, 1, 2, total, total + 1, rng.randrange(1, total + 1)])))
    return _ops('Paginator', [total, vis, rng.randrange(1, total + 1)], calls)


def _enc(rng):
    calls = []
    for _ in range(rng.randrange(1, 5)):
        if rng.random() < 0.6:
            seq = []
            for _ in range(rng.randrange(0, 8)): seq += [rng.choice([0, 1, 2, 7, 255, 256, 10**9])] * rng.choice([1, 1, 2, 3, 4, 9])
            calls.append(('encode', seq))
        else:
            runs = []
            for _ in range(rng.randrange(0, 5)):
                if rng.random() < 0.5: runs.append('RLE[%d, %d]' % (rng.choice([0, 3, 10**9]), rng.choice([1, 2, 5])))
                else:
                    vals = [rng.choice([0, 1, 5, 6, 7]) for _ in range(rng.randrange(1, 9))]
                    runs.append('BP[%d%s]' % (rng.choice([3, 4, 30]), ''.join(', %d' % v for v in vals)))
            calls.append(('decode', runs))
    return _ops('Codec', [], calls)


def _fal(rng, uid):
    level = _o.FAL.index(uid) + 1
    accts = ['a', 'b', 'c_1'][:rng.randrange(1, 4)]
    cmds = ['INIT %s %d' % (a, rng.choice([0, 5, 100, 10**9])) for a in accts]
    day = 0
    for _ in range(rng.randrange(0, 16)):
        day += rng.choice([0, 0, 1, 2, 5]); a = rng.choice(accts + ['zz'])
        r = rng.random()
        if r < 0.35: cmds.append('FUND %d %s %d %d' % (day, a, rng.choice([1, 7, 50, 10**9]), rng.choice([0, 0, 1, 2, 5, 10**9])))
        elif r < 0.6: cmds.append('BALANCE %d %s' % (day, a))
        elif level >= 2 and r < 0.72: cmds.append('WITHDRAW %d %s %d' % (day, a, rng.choice([1, 5, 50, 100, 10**9])))
        elif level >= 3 and r < 0.84: cmds.append('TRANSFER %d %s %s %d' % (day, a, rng.choice(accts + ['zz']), rng.choice([1, 5, 50, 10**9])))
        elif level >= 4 and r < 0.92: cmds.append('PENDING %d %s' % (day, a))
        elif level >= 4: cmds.append('CANCEL %d %s' % (day, a))
        else: cmds.append('BALANCE %d %s' % (day, a))
    return [cmds]


def _tree(rng, depth):
    if depth == 0 or rng.random() < 0.3: return {'operation': 'CONSTANT_NUMBER', 'value': rng.choice([-7, -2, -1, 0, 1, 2, 3, 5, 10**9])}
    return {'operation': rng.choice(['ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE']), 'inputs': [_tree(rng, depth - 1), _tree(rng, depth - 1)]}


def _ejt(rng):
    while True:
        t = _tree(rng, rng.randrange(0, 5))
        try: validate_domain(_o.EJT, [t]); return [t]
        except ValueError: pass


def _fcp(rng):
    nodes = ['AAA', 'BBB', 'CCC', 'JFK', 'SFO'][:rng.randrange(2, 6)]
    while True:
        k = rng.randrange(1, 9); path = [rng.choice(nodes)]
        for _ in range(k): path.append(rng.choice([x for x in nodes if x != path[-1]] if rng.random() < 0.9 else nodes))
        tickets = [[a, b] for a, b in zip(path, path[1:])]; rng.shuffle(tickets)
        return [tickets]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.TKL:
        args = [_ops('TokenLimiter', [], [('consume', 'a', 1, 0), ('getTokens', 'a', 0)]),
                _ops('TokenLimiter', [], [('setPolicy', 'a', 5, 2, 3, 0), ('consume', 'a', 4, 1), ('consume', 'a', 2, 2), ('consume', 'a', 2, 3),
                                          ('getTokens', 'a', 8), ('getTokens', 'a', 9), ('setPolicy', 'a', 1, 1, 1, 9), ('getTokens', 'a', 9)])]
        args += [_tkl(rng) for _ in range(250)]
    elif uid in o.WMS:
        level = o.WMS.index(uid) + 1
        args = [_ops('WorkerManagementSystem', [], [('get', 'Ann')]),
                _ops('WorkerManagementSystem', [], [('addWorker', 'Ann', 'Dev', 10), ('addWorker', 'Ann', 'QA', 1), ('registerWorker', 'Ann', 5), ('get', 'Ann'),
                                                    ('registerWorker', 'Ann', 9), ('registerWorker', 'Bob', 10), ('registerWorker', 'Ann', 12), ('get', 'Ann'), ('get', 'Bob')])]
        args += [_wms(rng, level) for _ in range(250)]
    elif uid in o.TAS:
        level = o.TAS.index(uid) + 1
        args = [_ops('TaskManager', [], [('getTask', 1, 'taskId1')]),
                _ops('TaskManager', [], [('addTask', 1, 'a', 3), ('addTask', 2, 'a', 3), ('updateTask', 3, 'taskId2', 'b', -1), ('updateTask', 4, 'taskId3', 'c', 0),
                                         ('getTask', 5, 'taskId2'), ('getTask', 6, 'taskId1')])]
        args += [_tas(rng, level) for _ in range(250)]
    elif uid == o.PAG:
        args = [_ops('Paginator', [1, 1, 1], [('next',)]), _ops('Paginator', [10, 5, 5], [('next',), ('goTo', 10), ('prev',), ('goTo', 1), ('goTo', 99)]),
                _ops('Paginator', [3, 7, 2], [('prev',), ('prev',)]), _ops('Paginator', [10, 4, 1], [('goTo', 5), ('goTo', 6)])]
        args += [_pag(rng) for _ in range(250)]
    elif uid == o.ENC:
        args = [_ops('Codec', [], [('encode', [])]), _ops('Codec', [], [('decode', [])]),
                _ops('Codec', [], [('encode', [1, 1, 2, 2, 2]), ('encode', [0] * 3 + list(range(10)) + [9, 9]), ('decode', ['RLE[5, 2]', 'BP[3, 1, 2]'])])]
        args += [_enc(rng) for _ in range(250)]
    elif uid == o.EQF:
        args = [['a'], ['ab'], ['aab'], ['aabb'], ['abac'], ['aabbccc'], ['aaabbbcc'], ['aabbcd'], ['abcc'], ['aaaabb'], ['zzzzz']]
        args += [[''.join(rng.choice('aabbcz'[:rng.randrange(1, 7)]) for _ in range(rng.randrange(1, 12)))] for _ in range(250)]
    elif uid == o.ESL:
        args = [[1, [5]], [3, [1, 2, 3]], [3, [4, 7, 7]], [7, [1, 1, 1, 1, 2, 3, 4]], [7, [1, 5, 1, 1, 1, 2, 9]]]
        for _ in range(250):
            n = rng.choice([1, 3, 7, 15, 31]); args.append([n, [rng.choice([1, 2, 3, 10, 10**9]) for _ in range(n)]])
    elif uid == o.EJT:
        c = lambda v: {'operation': 'CONSTANT_NUMBER', 'value': v}
        args = [[c(7)], [{'operation': 'DIVIDE', 'inputs': [c(-7), c(2)]}], [{'operation': 'SUBTRACT', 'inputs': [c(3), {'operation': 'MULTIPLY', 'inputs': [c(4), c(5)]}]}]]
        args += [_ejt(rng) for _ in range(250)]
    elif uid in (o.F1A, o.F1B):
        args = [[['Max'], [[90, 80]]], [['Lewis', 'Max'], [[90, 92, 85], [91, 91, 86]]], [['b', 'a'], [[10, 10, 10], [12, 8, 10]]]]
        for _ in range(250):
            n, laps = rng.randrange(1, 6), rng.randrange(2, 6)
            names = rng.sample(['Ann', 'Bo', 'Cy', 'ann', 'Zed', 'Al', 'Bob'], n)
            args.append([names, [[rng.choice([1, 2, 3, 59, 60, 61, 10**6]) for _ in range(laps)] for _ in range(n)]])
    elif uid == o.FLX:
        args = [[[1], 0], [[2], 3], [[1, 2, 5], 11], [[3, 7], 5], [[5, 5, 2], 9], [[10000], 10000]]
        args += [[[rng.randrange(1, 15) for _ in range(rng.randrange(1, 5))], rng.randrange(0, 60)] for _ in range(250)]
    elif uid in o.FAL:
        args = [[[]], [['INIT a 5']], [['INIT a 5', 'FUND 1 a 10 2', 'BALANCE 2 a', 'BALANCE 3 a', 'FUND 3 a 4 0', 'BALANCE 3 a', 'BALANCE 3 zz']]]
        args += [_fal(rng, uid) for _ in range(250)]
    elif uid == o.GPU:
        args = [[1, []], [1, [0]], [2, [1]], [5, [0, 4]], [8, [3]], [7, [6, 0, 3]]]
        for _ in range(250):
            n = rng.randrange(1, 40); args.append([n, rng.sample(range(n), min(n, rng.choice([0, 1, 1, 2, 3, n // 2, n])))])
    elif uid == o.BPP:
        args = [[[1]], [[2, 1]], [[1, 2]], [[2, 1, 3]], [[3, 1, 2]], [[1, 3, 2]], [[4, 1, 3, 2, 5]]]
        for _ in range(250):
            p = list(range(1, rng.randrange(2, 14))); rng.shuffle(p); args.append([p])
    elif uid in (o.CFD1, o.CFD2, o.CFD3):
        args = [[[], 1], [[[1, 1, 3]], 5], [[[1, 2, 2], [2, 4, 6], [1, 5, 5]], 8], [[[7, 1, 100]], 10]]
        if uid == o.CFD3: args = [a + [len({b[0] for b in a[0]})] for a in args] + [[[[1, 1, 4], [1, 3, 6], [2, 2, 2]], 9, 1], [[], 4, 0]]
        for _ in range(250):
            total = rng.randrange(1, 25)
            blocks = []
            for _ in range(rng.randrange(0, 6)):
                s = rng.randrange(1, total + 4); blocks.append([rng.choice([0, 1, 2, 10**9]), s, s + rng.choice([0, 0, 1, 3, 9])])
            a = [blocks, total]
            if uid == o.CFD3: a.append(rng.randrange(0, len({b[0] for b in blocks}) + 1))
            args.append(a)
    elif uid == o.FCP:
        args = [[[['JFK', 'SFO']]], [[['JFK', 'ATL'], ['ATL', 'JFK'], ['JFK', 'SFO']]], [[['BBB', 'AAA'], ['AAA', 'BBB']]],
                [[['MUC', 'LHR'], ['JFK', 'MUC'], ['SFO', 'SJC'], ['LHR', 'SFO']]], [[['AAA', 'BBB'], ['AAA', 'CCC'], ['CCC', 'AAA']]]]
        args += [_fcp(rng) for _ in range(250)]
    elif uid == o.EOS:
        args = [[[]], [[5]], [[1, 2]], [[2, 1]], [[3, 1, 2]], [[2, 1, 4, 3]], [[1, 5, 2, 4, 3]]]
        for _ in range(250):
            n = rng.randrange(0, 12); args.append([rng.sample([-10**9, -5, -1, 0, 1, 2, 3, 4, 7, 9, 12, 40, 10**9], n)])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _wms_common():
    out = []
    m = 25000
    calls = [('addWorker', wid(i), 'Eng', 1) for i in range(m)]
    for i in range(m): calls += [('registerWorker', wid(i), 4 * i), ('registerWorker', wid(i), 4 * i + i % 3 + 1)]
    calls += [('get', wid(i)) for i in range(m)]
    out.append((_ops('WorkerManagementSystem', [], calls), [None] + [True] * m + ['registered'] * (2 * m) + [i % 3 + 1 for i in range(m)]))
    calls = [('addWorker', 'Solo', 'Eng', 7)] + [('registerWorker', 'Solo', i) for i in range(99996)] + [('get', 'Solo'), ('get', 'Nobody'), ('registerWorker', 'Nobody', 10**9)]
    out.append((_ops('WorkerManagementSystem', [], calls), [None, True] + ['registered'] * 99996 + [49998, -1, 'invalid_request']))
    return out


def _tas_common():
    out = []
    m = 50000
    calls = [('addTask', i + 1, 'T%d' % i, i % 100) for i in range(m)] + [('getTask', m + 1 + i, 'taskId%d' % (i + 1)) for i in range(m)]
    out.append((_ops('TaskManager', [], calls), [None] + ['taskId%d' % (i + 1) for i in range(m)] + ['T%d(%d)' % (i, i % 100) for i in range(m)]))
    calls = [('addTask', 1, 'x', 0)]; exp = [None, 'taskId1']
    for j in range(49998):
        calls += [('updateTask', 2 * j + 2, 'taskId1', 'N%d' % j, j), ('updateTask', 2 * j + 3, 'taskId2', 'y', 1)]; exp += [True, False]
    calls.append(('getTask', 10**9, 'taskId1')); exp.append('N49997(49997)')
    out.append((_ops('TaskManager', [], calls), exp))
    return out


def _fal_common():
    out = []
    cmds = ['INIT x 0']; exp = []
    for i in range(49999): cmds += ['FUND %d x 1 0' % i, 'BALANCE %d x' % i]; exp.append(i + 1)
    out.append(([cmds], exp))
    m = 49998
    cmds = ['INIT x 1000000000'] + ['FUND 0 x 1000000000 1000000000'] * m + ['BALANCE 999999999 x', 'BALANCE 1000000000 x', 'BALANCE 1000000000 nobody']
    out.append(([cmds], [10**9, 10**9 + m * 10**9, -1]))
    return out


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []; n = 100000
    if uid == o.TKL:
        m = 33333
        calls = [('setPolicy', 'u%d' % i, 10, 1, 1000, 0) for i in range(m)] + [('consume', 'u%d' % i, 10, 1) for i in range(m)] + [('getTokens', 'u%d' % i, 1000) for i in range(m)]
        out.append((_ops('TokenLimiter', [], calls), [None] * (m + 1) + [True] * m + [1] * m))
        calls = [('setPolicy', 'w', 10**9, 10**6, 1, 0)]
        for j in range(49999): calls += [('consume', 'w', 10**9, 1000 * j), ('consume', 'w', 1, 1000 * j)]
        out.append((_ops('TokenLimiter', [], calls), [None, None] + [True, False] * 49999))
        calls = [('setPolicy', 'w', 10**9, 10**6, 1, 0), ('consume', 'w', 10**9, 0), ('getTokens', 'w', 10**9), ('getTokens', 'zz', 10**9)]
        out.append((_ops('TokenLimiter', [], calls), [None, None, True, 10**9, -1]))
    elif uid in o.WMS:
        level = o.WMS.index(uid) + 1
        out += _wms_common()
        if level >= 2:
            k = 1000; calls, t = [], 0
            for i in range(k):
                calls += [('addWorker', wid(i), 'Dev', 1), ('registerWorker', wid(i), t), ('registerWorker', wid(i), t + i + 1)]; t += i + 2
            top = ', '.join('%s(%d)' % (wid(i), i + 1) for i in reversed(range(k)))
            calls += [('topNWorkers', 100000, 'Dev')] * 999 + [('topNWorkers', 3, 'QA')]
            out.append((_ops('WorkerManagementSystem', [], calls), [None] + [True, 'registered', 'registered'] * k + [top] * 999 + ['']))
            calls = [('addWorker', wid(i), 'Ops', 1) for i in range(1000)] + [('topNWorkers', 2, 'Ops')] * 1000
            out.append((_ops('WorkerManagementSystem', [], calls), [None] + [True] * 1000 + ['AAAA(0), AAAB(0)'] * 1000))
        if level >= 3:
            m = 16666; calls, exp, t = [], [None], 0
            for i in range(m):
                calls += [('addWorker', wid(i), 'Dev', 10), ('promote', wid(i), 'Lead', 20, 0), ('promote', wid(i), 'CTO', 30, 0),
                          ('registerWorker', wid(i), t), ('registerWorker', wid(i), t + 5), ('calcSalary', wid(i), t + 1, t + 3) if i % 2 else ('calcSalary', wid(i), 0, 10**9)]
                exp += [True, 'success', 'invalid_request', 'registered', 'registered', 40 if i % 2 else 100]; t += 6
            out.append((_ops('WorkerManagementSystem', [], calls), exp))
            calls = [('addWorker', 'Solo', 'Dev', 10**6)] + [('registerWorker', 'Solo', i) for i in range(2000)] + [('calcSalary', 'Solo', 0, 10**9)] * 1000
            out.append((_ops('WorkerManagementSystem', [], calls), [None, True] + ['registered'] * 2000 + [1000 * 10**6] * 1000))
        if level >= 4:
            calls = [('setDoublePaid', 2000 * k, 2000 * k + 1000) for k in range(1000)] + [('addWorker', 'Solo', 'Dev', 10**6)]
            for j in range(1000): calls += [('registerWorker', 'Solo', 2000 * j + 500), ('registerWorker', 'Solo', 2000 * j + 1500)]
            calls += [('calcSalary', 'Solo', 0, 10**9)] * 998 + [('calcSalary', 'Solo', 500, 1000), ('calcSalary', 'Solo', 1000, 1500)]
            exp = [None] * 1001 + [True] + ['registered'] * 2000 + [1500 * 10**9] * 998 + [10**9, 500 * 10**6]
            out.append((_ops('WorkerManagementSystem', [], calls), exp))
            calls = [('setDoublePaid', 0, 10**9)] * 2 + [('addWorker', 'Ann', 'Dev', 7)]
            calls += [('registerWorker', 'Ann', 4 * j + 1) for j in range(40000)]
            calls += [('calcSalary', 'Ann', 0, 10**9)] * 50
            out.append((_ops('WorkerManagementSystem', [], calls), [None, None, None, True] + ['registered'] * 40000 + [20000 * 4 * 14] * 50))
    elif uid in o.TAS:
        level = o.TAS.index(uid) + 1
        out += _tas_common()
        if level >= 2:
            k = 2000
            calls = [('addTask', i + 1, 'job%d' % i, i % 7) for i in range(k)]
            calls += [('searchTasks', k + 1 + j, 'job1', 10) if j % 2 else ('listTasksSorted', k + 1 + j, 100000) for j in range(999)]
            hits = sorted((i for i in range(k) if str(i).startswith('1')), key=lambda i: (-(i % 7), i))[:10]
            every = sorted(range(k), key=lambda i: (-(i % 7), i))
            exp = [None] + ['taskId%d' % (i + 1) for i in range(k)] + [['taskId%d' % (i + 1) for i in (hits if j % 2 else every)] for j in range(999)]
            out.append((_ops('TaskManager', [], calls), exp))
        if level >= 3:
            m = 30000
            calls = [('addUser', 1, 'u', 100000)] + [('addTask', 2 + i, 'T', 0) for i in range(m)]
            calls += [('assignTask', 2 + m + i, 'taskId%d' % (i + 1), 'u', 5 * 10**8 + i) for i in range(m)] + [('getUserTasks', 5 * 10**8 - 1, 'u'), ('getUserTasks', 5 * 10**8 + m, 'u')]
            out.append((_ops('TaskManager', [], calls), [None, True] + ['taskId%d' % (i + 1) for i in range(m)] + [True] * m + [['taskId%d' % (i + 1) for i in range(m)], []]))
            calls = [('addUser', 1, 'q', 1), ('addTask', 2, 'T', 0), ('addTask', 3, 'U', 0)]
            calls += [('assignTask', 4 + j, 'taskId%d' % (1 + j % 2), 'q', 4 + j + 2) for j in range(90000)]
            out.append((_ops('TaskManager', [], calls), [None, True, 'taskId1', 'taskId2'] + [j % 2 == 0 for j in range(90000)]))
        if level >= 4:
            calls = [('addUser', 1, 'u', 1), ('addTask', 2, 'T', 0)]; exp = [None, True, 'taskId1']; t = 3
            for _ in range(33000):
                calls += [('assignTask', t, 'taskId1', 'u', t + 5), ('completeTask', t + 1, 'taskId1', 'u'), ('completeTask', t + 2, 'taskId1', 'u')]; exp += [True, True, False]; t += 3
            calls.append(('getOverdueAssignments', t, 'u')); exp.append([])
            out.append((_ops('TaskManager', [], calls), exp))
            m = 30000
            calls = [('addUser', 1, 'v', 100000)] + [('addTask', 2 + i, 'T', 0) for i in range(m)]
            calls += [('assignTask', 2 + m + i, 'taskId%d' % (i + 1), 'v', 3 + m + i) for i in range(m)]
            calls += [('completeTask', 10**8 + i, 'taskId%d' % (i + 1), 'v') for i in range(100)] + [('getOverdueAssignments', 10**9, 'v')]
            out.append((_ops('TaskManager', [], calls), [None, True] + ['taskId%d' % (i + 1) for i in range(m)] + [True] * m + [False] * 100 + [['taskId%d' % (i + 1) for i in range(m)]]))
    elif uid == o.PAG:
        def view(c):
            s = max(1, c - 49)
            return ' '.join((['<'] if c > 1 else []) + (['...'] if s > 1 else []) + ['[%d]' % p if p == c else str(p) for p in range(s, s + 100)] + ['...', '>'])
        out.append((_ops('Paginator', [10**9, 100, 1], [('next',)] * 10000), [None] + [view(c) for c in range(2, 10002)]))
        out.append((_ops('Paginator', [1, 1, 1], [('goTo', 10**9), ('goTo', -10**9), ('next',), ('prev',)] * 2500), [None] + ['[1]'] * 10000))
        tail = ' '.join(['<', '...'] + [str(p) for p in range(10**9 - 99, 10**9)] + ['[%d]' % 10**9])
        out.append((_ops('Paginator', [10**9, 100, 10**9], [('goTo', 10**9)] * 10000), [None] + [tail] * 10000))
    elif uid == o.ENC:
        out.append((_ops('Codec', [], [('encode', [7] * n), ('decode', ['RLE[7, 100000]'])]), [None, ['RLE[7, 100000]'], [7] * n]))
        alt = [i % 2 for i in range(n)]; chunk = 'BP[1, 0, 1, 0, 1, 0, 1, 0, 1]'
        out.append((_ops('Codec', [], [('encode', alt), ('decode', [chunk] * 12500)]), [None, [chunk] * 12500, alt]))
        mix = [10**9, 10**9, 3, 3, 3] * 20000; runs = ['BP[30, 1000000000, 1000000000]', 'RLE[3, 3]'] * 20000
        out.append((_ops('Codec', [], [('encode', mix), ('decode', runs)]), [None, runs, mix]))
    elif uid == o.EQF:
        out += [(['a' * n], True), (['ab' * 50000], True), (['abc' * 33333 + 'a'], True), (['a' * 50000 + 'b' * 49998 + 'cc'], False),
                (['a' * 99999 + 'b'], True), (['a' * 50001 + 'b' * 49999], False)]
    elif uid == o.ESL:
        m = 2**17 - 1
        out.append(([m, [1] * m], 0))
        out.append(([m, [1] * (2**16 - 1) + [1 + (i % 2 == 0) for i in range(2**16 - 1, m)]], 2**15))
        lat = [1] * m
        for v in range(m):
            u = v
            while u > 2: u = (u - 1) // 2
            if u == 2: lat[v] = 10**9
        out.append(([m, lat], 16 * 10**9 - 16))
    elif uid == o.EJT:
        def bal(d):
            return {'operation': 'CONSTANT_NUMBER', 'value': 10**9} if d == 0 else {'operation': 'ADD', 'inputs': [bal(d - 1), bal(d - 1)]}
        out.append(([bal(14)], 2**14 * 10**9))
        node = {'operation': 'CONSTANT_NUMBER', 'value': 1}
        for _ in range(99): node = {'operation': 'SUBTRACT', 'inputs': [node, {'operation': 'CONSTANT_NUMBER', 'value': 1}]}
        out.append(([node], -98))
        node, val = {'operation': 'CONSTANT_NUMBER', 'value': -10**9}, -10**9
        for k in range(99):
            if k % 2 == 0: node = {'operation': 'MULTIPLY', 'inputs': [node, {'operation': 'CONSTANT_NUMBER', 'value': 7}]}; val *= 7
            else: node = {'operation': 'DIVIDE', 'inputs': [node, {'operation': 'CONSTANT_NUMBER', 'value': 6}]}; val = -((-val) // 6)
        out.append(([node], val))
    elif uid in (o.F1A, o.F1B):
        names = [wid(i) for i in range(1000)]
        laps = [[1000] * 199 + [1000 - i % 500] for i in range(1000)]
        out.append(([names, laps], names[499] if uid == o.F1A else [names[v + d] for v in range(499, -1, -1) for d in (0, 500)]))
        laps2 = [[10**6] * 99999 + [1], [1] * 99999 + [10**6]]
        out.append(([['Zed', 'Ann'], laps2], 'Zed' if uid == o.F1A else ['Zed', 'Ann']))
        out.append(([names, [[60, 60] for _ in names]], names[0] if uid == o.F1A else names))
    elif uid == o.FLX:
        best = min(a + (10000 - 7 * a) // 3 for a in range(0, 10000 // 7 + 1) if (10000 - 7 * a) % 3 == 0)
        out += [([[3, 7], 10000], best), ([[2] * 100, 9999], -1), ([list(range(1, 101)), 10000], 100), ([[10000 - i for i in range(100)], 0], 0),
                ([list(range(9901, 10001)), 10000], 1), ([[9999, 2] + [9997] * 98, 10000], 5000)]
    elif uid in o.FAL:
        level = o.FAL.index(uid) + 1
        out += _fal_common()
        if level >= 2:
            cmds = ['INIT x 0']; exp = []
            for i in range(33333): cmds += ['FUND %d x 2 0' % i, 'WITHDRAW %d x 1' % i, 'BALANCE %d x' % i]; exp.append(i + 1)
            out.append(([cmds], exp))
            out.append(([['INIT x 0'] + ['WITHDRAW %d x 1' % i for i in range(99998)] + ['BALANCE 99998 x']], [0]))
        if level >= 3:
            cmds = ['INIT a 1000000000', 'INIT b 0']; exp = []
            for i in range(49997): cmds += ['TRANSFER %d a b 1' % i, 'BALANCE %d b' % i]; exp.append(i + 1)
            cmds += ['TRANSFER 50000 b b 1', 'TRANSFER 50000 b a 49999', 'BALANCE 50000 a']; exp.append(10**9 - 49997)
            out.append(([cmds], exp))
        if level >= 4:
            cmds = ['INIT x 0']; exp = []
            for i in range(33333): cmds += ['FUND %d x 7 1000000' % i, 'PENDING %d x' % i, 'BALANCE %d x' % i]; exp += [7 * (i + 1), 0]
            out.append(([cmds], exp))
            cmds = ['INIT x 0']; exp = []
            for i in range(24999): cmds += ['FUND %d x 3 5' % i, 'FUND %d x 4 0' % i, 'CANCEL %d x' % i, 'PENDING %d x' % i]; exp.append(0)
            cmds.append('BALANCE 1000000000 x'); exp.append(4 * 24999)
            out.append(([cmds], exp))
    elif uid == o.GPU:
        out.append(([n, []], [[], 1]))
        out.append(([n, list(range(n - 1, -1, -1))], [list(range(n)), 1 + 2 * (n - 1)]))
        size, chain = n, 0
        while size > 1: chain += 1; size //= 2
        out.append(([n, [0]], [[0], 1 + 2 * chain]))
    elif uid == o.BPP:
        out.append(([list(range(1, n + 1))], '1' * n))
        out.append(([list(range(n, 0, -1))], '1' * n))
        out.append(([list(range(1, n, 2)) + list(range(2, n + 1, 2))], '1' + '0' * (n - 3) + '11'))
    elif uid in (o.CFD1, o.CFD2, o.CFD3):
        T = 10**5 if uid == o.CFD1 else 10**9
        if uid == o.CFD1:
            out.append(([[[1, 1, T]], T], []))
            out.append(([[[i % 9, 2 * i, 2 * i] for i in range(1, T // 2 + 1)], T], list(range(1, T + 1, 2))))
            out.append(([[], T], list(range(1, T + 1))))
            out.append(([[[3, 5, 10**9]] * n, T], [1, 2, 3, 4]))
        elif uid == o.CFD2:
            out.append(([[[i % 7, 10 * i + 1, 10 * i + 5] for i in range(n)], T], [[10 * i + 6, 10 * i + 10] for i in range(n - 1)] + [[999996, T]]))
            out.append(([[[1, 1 + j, 10**9 - j] for j in range(n)], T], []))
            out.append(([[[2, 500000001 + j, 500000001 + j] for j in range(n)], T], [[1, 500000000], [500100001, T]]))
        else:
            blocks = [[p, 1000 * p + 1 + j, 1000 * p + 1000 - j] for p in range(1000) for j in range(100)]
            out.append(([blocks, T, 1000], [[1000001, T]]))
            out.append(([blocks, T, 999], [[1, T]]))
            out.append(([blocks, T, 0], [[1, T]]))
            out.append(([[[p, 1, 10**9] for p in range(n)], T, 1], []))
    elif uid == o.FCP:
        order = list(range(10001)); random.Random(7).shuffle(order)
        tickets = [[code(order[i]), code(order[i + 1])] for i in range(10000)]
        random.Random(8).shuffle(tickets)
        out.append(([tickets], [code(x) for x in order]))
        star = []
        for i in range(1, 5000): star += [['AAA', code(i)], [code(i), 'AAA']]
        out.append(([star[::-1]], ['AAA'] + [x for i in range(1, 5000) for x in (code(i), 'AAA')]))
        out.append(([[['BBB', 'AAA'], ['AAA', 'BBB']] * 5000], ['AAA', 'BBB'] * 5000 + ['AAA']))
    elif uid == o.EOS:
        out.append(([list(range(1, n + 1))], list(range(n, 0, -1))))
        out.append(([list(range(n, 0, -1))], list(range(n, 0, -1))))
        out.append(([[i + 2 if i % 2 == 0 else i for i in range(n)]], list(range(2, n + 1, 2)) + list(range(n - 1, 0, -2))))
    return out
