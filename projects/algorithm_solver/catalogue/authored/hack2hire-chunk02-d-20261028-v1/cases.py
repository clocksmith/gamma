"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h02d_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _ops(name, ctor, calls):
    return [[name] + [c[0] for c in calls], [list(ctor)] + [list(c[1:]) for c in calls]]


USERS = ['al', 'bo', 'cy', 'di', 'ed']


def _mod(rng, level, n):
    logs, t = [], 0
    for _ in range(rng.randrange(0, 15)):
        t += rng.choice([0, 0, 1, 5]); logs.append([t, rng.choice(USERS), rng.choice(['ADD', 'ADD', 'REMOVE'])])
    names = ['canRemove'] + (['getModerators'] if level >= 2 else []) + (['canRemoveAt', 'getModeratorsAt'] if level >= 3 else [])
    calls = []
    for _ in range(n):
        op = rng.choice(names)
        if op == 'canRemove': calls.append((op, rng.choice(USERS), rng.choice(USERS)))
        elif op == 'getModerators': calls.append((op,))
        elif op == 'canRemoveAt': calls.append((op, rng.randrange(0, t + 3), rng.choice(USERS), rng.choice(USERS)))
        else: calls.append((op, rng.randrange(0, t + 3)))
    return _ops('ModSystem', [logs], calls)


def _rect(rng, level, n):
    w, h = rng.randrange(1, 6), rng.randrange(1, 6)
    names = ['addRectangle', 'getTopRectangle', 'getTopRectangle'] + (['removeRectangle'] if level >= 2 else []) + \
        (['bringToFront'] if level >= 3 else []) + (['undo', 'undo'] if level >= 4 else [])
    calls, made = [], 0
    for _ in range(n):
        op = rng.choice(names)
        if op == 'addRectangle':
            x1, y1 = rng.randrange(w), rng.randrange(h); calls.append((op, x1, y1, rng.randrange(x1, w), rng.randrange(y1, h))); made += 1
        elif op == 'getTopRectangle': calls.append((op, rng.randrange(w), rng.randrange(h)))
        elif op == 'undo': calls.append((op,))
        else: calls.append((op, rng.randrange(-1, made + 2)))
    return _ops('RectangleBoard', [w, h], calls)


CELLS = ['A1', 'A2', 'B1', 'B2', 'C3', 'Z100']


def _sheet(rng, level, n):
    calls, cells = [], {}
    for _ in range(n):
        op = rng.choice(['setCell', 'setCell', 'getCell', 'getCell', 'resetCell'])
        c = rng.choice(CELLS)
        if op == 'setCell':
            if rng.random() < 0.4: v = str(rng.choice([0, 1, 7, 10**6, rng.randrange(1000)]))
            else: v = '=' + '+'.join(rng.choice(CELLS + ['3', '0']) for _ in range(rng.randrange(1, 4)))
            trial = dict(cells); trial[c] = v
            if level == 1:
                try: _acyclic(trial)
                except ValueError: continue
                cells = trial
            calls.append((op, c, v))
        elif op == 'resetCell':
            cells.pop(c, None); calls.append((op, c))
        else: calls.append((op, c))
    return _ops('Spreadsheet', [], calls)


def _acyclic(cells):
    memo = {}
    for c in cells: _o.sheet_value(cells, c, memo)


def _wq(rng, level, n):
    tasks = rng.sample(range(0, 30), rng.randrange(0, 7))
    deps = []
    if level == 2:
        for _ in range(rng.randrange(0, 6)):
            if len(tasks) >= 2:
                i, j = sorted(rng.sample(range(len(tasks)), 2))
                if [tasks[i], tasks[j]] not in deps: deps.append([tasks[i], tasks[j]])
    lease, cap = rng.randrange(1, 6), rng.randrange(1, 4)
    calls, t = [], 0
    for _ in range(n):
        t += rng.choice([0, 1, 1, 2, 5]); op = rng.choice(['reserve', 'reserve', 'complete', 'fail', 'getDeadLetters'])
        if op in ('complete', 'fail'): calls.append((op, t, rng.choice(tasks + [99]) if tasks else 99))
        else: calls.append((op, t))
    return _ops('WorkQueue', [tasks, deps, lease, cap] if level == 2 else [tasks, lease, cap], calls)


def _perm_tree(rng, depth, counter):
    kind = 'TEAM' if depth == 0 else rng.choice(['FOLDER', 'FILE'])
    counter[0] += 1
    node = {'uuid': 'n' + str(counter[0]), 'type': kind, 'userIds': rng.sample(['u1', 'u2', 'u3', 'u4'], rng.choice([0, 0, 1, 2])), 'children': []}
    if kind != 'FILE' and depth < 4:
        node['children'] = [_perm_tree(rng, depth + 1, counter) for _ in range(rng.randrange(0, 3))]
    return node


def _ip_tree(rng, depth):
    if depth >= 3 or rng.random() < 0.4:
        lines = []
        for _ in range(rng.randrange(0, 4)):
            parts = [rng.choice(['ip', 'x=', ' ', '.', 'a1', '9', '.1', '1.2.3.4', '255.255.255.255', '256.1.1.1', '01.2.3.4', '0.0.0.0',
                                 '10.0.0.1.', '1.2.3', str(rng.randrange(300)), '192.168.1.' + str(rng.randrange(260)), ':']) for _ in range(rng.randrange(0, 6))]
            lines.append(''.join(parts)[:200])
        return {'name': 'f' + str(rng.randrange(99)), 'isFile': True, 'lines': lines, 'children': []}
    return {'name': 'd' + str(rng.randrange(99)), 'isFile': False, 'lines': [], 'children': [_ip_tree(rng, depth + 1) for _ in range(rng.randrange(0, 4))]}


def _samples(rng, n):
    out, t = [], rng.randrange(0, 3)
    stack = []
    for _ in range(n):
        r = rng.random()
        if r < 0.3 and stack: stack = stack[:rng.randrange(len(stack))]
        elif r < 0.7 and len(stack) < 5: stack = stack + [rng.choice(['main', 'f', 'g', 'h'])]
        elif r < 0.8 and stack: stack = stack[:-1] + [rng.choice(['f', 'g'])]
        out.append(str(t) + ':' + '->'.join(stack)); t += rng.randrange(1, 4)
    return out


def _lines(rng, n, alphabet):
    return [rng.choice(alphabet) for _ in range(n)]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.RATE:
        args = [[[], 1, 1], [[5], 1, 1], [[0, 0, 0], 1, 2], [[0, 10**9], 10**9, 1]]
        for _ in range(250):
            ts = sorted(rng.randrange(0, 20) for _ in range(rng.randrange(0, 12)))
            args.append([ts, rng.randrange(1, 8), rng.randrange(1, 4)])
    elif uid in (o.MOD1, o.MOD2, o.MOD3):
        level = (o.MOD1, o.MOD2, o.MOD3).index(uid) + 1
        args = [_ops('ModSystem', [[]], [('canRemove', 'al', 'al')]), _ops('ModSystem', [[[0, 'al', 'ADD'], [0, 'bo', 'ADD']]], [('canRemove', 'al', 'bo'), ('canRemove', 'bo', 'al')])]
        args += [_mod(rng, level, rng.randrange(1, 12)) for _ in range(200)]
    elif uid in (o.RECT1, o.RECT2, o.RECT3, o.RECT4):
        level = (o.RECT1, o.RECT2, o.RECT3, o.RECT4).index(uid) + 1
        args = [_ops('RectangleBoard', [1, 1], [('getTopRectangle', 0, 0)]), _ops('RectangleBoard', [10**9, 10**9], [('addRectangle', 0, 0, 10**9 - 1, 10**9 - 1), ('getTopRectangle', 10**9 - 1, 0)])]
        args += [_rect(rng, level, rng.randrange(1, 25)) for _ in range(250)]
    elif uid in (o.SHEET1, o.SHEET2):
        level = 1 if uid == o.SHEET1 else 2
        args = [_ops('Spreadsheet', [], [('getCell', 'Z100')])]
        if level == 2: args.append(_ops('Spreadsheet', [], [('setCell', 'A1', '=A1'), ('setCell', 'A1', '=B1'), ('setCell', 'B1', '=A1+1'), ('getCell', 'A1')]))
        args += [_sheet(rng, level, rng.randrange(1, 20)) for _ in range(250)]
    elif uid == o.DIAG:
        args = [[[[0, 0]], []], [[[0, 0]], [1, 2, 3, 4]], [[[0, 0], [2, 2], [1, 1]], [1, 1, 4, 4, 4]]]
        for _ in range(250):
            pts = rng.sample([[x, y] for x in range(-3, 4) for y in range(-3, 4)], rng.randrange(1, 15))
            args.append([pts, [rng.randrange(1, 5) for _ in range(rng.randrange(0, 10))]])
    elif uid in (o.EXP1, o.EXP2):
        kinds = ['expense'] if uid == o.EXP1 else ['expense', 'trip']
        args = [[[], []], [[['expense', 'R1', 'amount', '<=', '75', 'expense_type', 'meals']], [['E1', 'T1', '75.00', 'meals', 'restaurant', 'joes']]]]
        for _ in range(250):
            exps = [['E' + str(i), 'T' + str(rng.randrange(3)), rng.choice(['0', '10', '10.5', '49.99', '50', '75.01', '120', str(rng.randrange(200))]),
                     rng.choice(['meals', 'travel', 'gift']), rng.choice(['restaurant', 'airline', 'shop']), rng.choice(['joes', 'acme'])] for i in range(rng.randrange(0, 8))]
            rules = []
            for i in range(rng.randrange(0, 5)):
                kind = rng.choice(kinds); field = 'amount' if kind == 'trip' or rng.random() < 0.6 else rng.choice(['expense_type', 'vendor_type', 'vendor_name'])
                op = rng.choice(o.OPERATORS if field == 'amount' else ('==', '!='))
                value = rng.choice(['0', '10.50', '50', '75', '100', '200']) if field == 'amount' else rng.choice(['meals', 'airline', 'acme', 'shop'])
                cond = rng.choice([['', ''], ['expense_type', 'meals'], ['vendor_type', 'airline'], ['vendor_name', 'acme']])
                rules.append([kind, 'R' + str(i), field, op, value] + cond)
            args.append([rules, exps])
    elif uid in (o.WQ1, o.WQ2):
        level = 1 if uid == o.WQ1 else 2
        args = [_ops('WorkQueue', [[], [], 1, 1] if level == 2 else [[], 1, 1], [('reserve', 0), ('getDeadLetters', 0)])]
        args.append(_ops('WorkQueue', [[1, 2], [[1, 2]], 5, 1] if level == 2 else [[1, 2], 5, 1],
                         [('reserve', 0), ('reserve', 1), ('fail', 2, 1), ('reserve', 3), ('getDeadLetters', 9)]))
        args += [_wq(rng, level, rng.randrange(1, 25)) for _ in range(250)]
    elif uid == o.PERM:
        args = [[[], [['u1', 'x']]]]
        for _ in range(200):
            counter = [0]; teams = [_perm_tree(rng, 0, counter) for _ in range(rng.randrange(1, 3))]
            args.append([teams, [[rng.choice(['u1', 'u2', 'u3', 'u4', 'u5']), 'n' + str(rng.randrange(1, counter[0] + 2))] for _ in range(rng.randrange(0, 10))]])
    elif uid == o.FILL:
        args = [['0 = 0'], ['5 = 6'], ['2 3 4 = 14'], ['2 3 4 = 20'], ['1 1 1 1 = 4'], ['0 0 0 = 0'], ['1 2 3 4 5 6 7 = 28']]
        for _ in range(120):
            nums = [rng.choice([0, 1, 1, 2, 3, 5, 9, 12, 99]) for _ in range(rng.randrange(1, 6))]
            target = rng.choice([0, 1, sum(nums), rng.randrange(0, 40)])
            args.append([' '.join(map(str, nums)) + ' = ' + str(target)])
        for _ in range(10):
            nums = [rng.randrange(0, 10) for _ in range(7)]; args.append([' '.join(map(str, nums)) + ' = ' + str(sum(nums) + rng.randrange(0, 30))])
    elif uid == o.MEET:
        args = [[[], 1], [[], 1440], [['al busy 00:00 23:59'], 1], [['al busy 00:01 23:59'], 1], [['al busy 00:00 23:58'], 2]]
        for _ in range(250):
            evs = []
            for _ in range(rng.randrange(0, 6)):
                a = rng.randrange(0, 1440); b = min(1439, a + rng.randrange(0, 400))
                evs.append(f'{rng.choice(USERS)} {rng.choice(["meeting", "busy", "lunch"])} {a // 60:02d}:{a % 60:02d} {b // 60:02d}:{b % 60:02d}')
            args.append([evs, rng.choice([1, 2, 30, 60, 300, rng.randrange(1, 1441)])])
    elif uid in (o.FREE1, o.FREE2):
        args = [[[]], [[['all', '0', '999']]], [[['a', '0', '0'], ['b', '999', '999']]]]
        for _ in range(250):
            pts = sorted(rng.sample(range(0, 1000), 2 * rng.randrange(0, 6)))
            if rng.random() < 0.5: pts = sorted(rng.sample(range(0, 40), 2 * rng.randrange(0, 6)))
            rows = [[rng.choice(['x', 'y', 'z']), str(pts[i]), str(pts[i + 1])] for i in range(0, len(pts), 2)]
            rng.shuffle(rows); args.append([rows])
        if uid == o.FREE2: args = [a + [rng.choice([1, 1, 2, 5, 100, 1000])] for a in args]
    elif uid == o.IPV4:
        args = [[{'name': 'r', 'isFile': False, 'lines': [], 'children': []}], [{'name': 'r', 'isFile': True, 'lines': ['1.1.1.1 1.1.1.1', '0.0.0.0'], 'children': []}]]
        args += [[_ip_tree(rng, 0)] for _ in range(250)]
    elif uid == o.TILE:
        args = [[['_'], ['_']], [['R', '_'], ['_', 'R']], [['_', 'R'], ['R', '_']], [['R', 'B', '_'], ['_', 'B', 'R']], [['R', 'B', '_'], ['B', '_', 'R']]]
        for _ in range(300):
            n = rng.randrange(1, 9); s = [rng.choice('RB__') for _ in range(n)]
            t = list(s) if rng.random() < 0.3 else [rng.choice('RB__') for _ in range(n)]
            if rng.random() < 0.6:  # random walk to a reachable target
                t = list(s)
                for _ in range(rng.randrange(0, 6)):
                    nxt = [list(b) for b in _forward(t)]
                    if nxt: t = rng.choice(nxt)
            args.append([s, t])
    elif uid == o.FRAC:
        args = [[[], []], [[['AAPL', 'B', '0.5', '15000']], []], [[['AAPL', 'S', '0.5', '15000']], [['AAPL', '60']]]]
        for _ in range(250):
            orders = []
            for _ in range(rng.randrange(0, 8)):
                q = rng.choice(['0.01', '0.25', '0.5', '0.99', '1', '1.5', '2.75', '$1', '$10.50', '$100', '$0.01'])
                orders.append([rng.choice(['AAPL', 'GOOG', 'TSLA']), rng.choice('BS'), q, str(rng.choice([1, 99, 100, 333, 15000, rng.randrange(1, 50000)]))])
            orders.sort(key=lambda r: r[0])
            inv = [[s, str(rng.randrange(100))] for s in ['AAPL', 'MSFT', 'TSLA'] if rng.random() < 0.5]
            args.append([orders, inv])
    elif uid == o.FRIEND:
        args = [[1, []], [2, [[0, 1]]], [3, [[0, 1], [1, 2]]], [4, [[0, 1], [0, 2], [3, 1], [3, 2]]]]
        for _ in range(250):
            n = rng.randrange(1, 12); pairs = [[a, b] for a in range(n) for b in range(a + 1, n)]
            es = rng.sample(pairs, rng.randrange(0, len(pairs) + 1)); es = [e if rng.random() < 0.5 else e[::-1] for e in es]
            args.append([n, es])
    elif uid in (o.PROF1, o.PROF2, o.PROF3):
        args = [[[]], [['5:']], [['1:main', '2:main->f', '4:main->f->f', '6:main', '9:']], [['0:a->b', '3:a->c', '5:b->c']]]
        args += [[_samples(rng, rng.randrange(0, 15))] for _ in range(250)]
        if uid == o.PROF2: args = [a + [rng.choice([1, 1, 2, 3, 5])] for a in args]
    elif uid in (o.HOTEL1, o.HOTEL2, o.HOTEL3):
        args = [[[], {}]]
        for _ in range(250):
            res = [{'guest_name': rng.choice(['Ann', 'Bob', 'Cy']), 'room_type': rng.choice(['suite', 'king', 'twin']),
                    'check_in_day': rng.randrange(0, 20), 'stay_length': rng.randrange(1, 6)} for _ in range(rng.randrange(0, 5))]
            tps = {}
            for name in rng.sample(['welcome', 'reminder', 'survey', 'upsell'], rng.randrange(0, 4)):
                off = rng.randrange(-5, 6)
                if uid == o.HOTEL1: tps[name] = off
                else:
                    tps[name] = {'anchor': rng.choice(['check_in', 'check_out']), 'offset': off}
                    if uid == o.HOTEL3 and rng.random() < 0.5: tps[name]['room_types'] = rng.sample(['suite', 'king', 'twin'], rng.randrange(0, 3))
            args.append([res, tps])
    elif uid in (o.DIFF1, o.DIFF2, o.DIFF3):
        args = [[[], []], [['a'], ['a']], [['a', 'a'], ['a']], [['a', 'b'], ['b', 'a']], [['x', 'a', 'b', 'c', 'y'], ['a', 'q', 'b', 'c']]]
        for _ in range(250):
            alpha = rng.choice([['a', 'b'], ['a', 'b', 'c', 'd', 'e'], [chr(97 + i) for i in range(12)], ['', ' x', 'line']])
            args.append([_lines(rng, rng.randrange(0, 12), alpha), _lines(rng, rng.randrange(0, 12), alpha)])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _forward(board):
    """Forward moves (used only to pick reachable targets for case generation)."""
    out, n = [], len(board)
    for i, c in enumerate(board):
        if c == 'R':
            if i + 1 < n and board[i + 1] == '_': b = list(board); b[i], b[i + 1] = '_', 'R'; out.append(b)
            if i + 2 < n and board[i + 1] == 'B' and board[i + 2] == '_': b = list(board); b[i], b[i + 2] = '_', 'R'; out.append(b)
        if c == 'B':
            if i - 1 >= 0 and board[i - 1] == '_': b = list(board); b[i], b[i - 1] = '_', 'B'; out.append(b)
            if i - 2 >= 0 and board[i - 1] == 'R' and board[i - 2] == '_': b = list(board); b[i], b[i - 2] = '_', 'B'; out.append(b)
    return out


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.RATE:
        n = 100000; ts = [i // 2 for i in range(n)]  # two requests per tick; window 5 holds exactly 10 -> all allowed
        out.append(([ts, 5, 10], [True] * n))
        out.append(([[7] * n, 1, 3], [True] * 3 + [False] * (n - 3)))
    elif uid in (o.MOD1, o.MOD2, o.MOD3):
        n = 20000; logs = [[i, 'u' + str(i % 5000), 'ADD' if i < 5000 else ('REMOVE' if i % 2 else 'ADD')] for i in range(n)]
        # first 5000 ADD u0..u4999; i in 5000..9999: odd i removes odd-index user, even i re-ADD of an active user is a no-op;
        # later rounds are all no-ops -> active = even-index users in original order, unchanged after time 9999.
        state = ['u' + str(i) for i in range(0, 5000, 2)]
        calls = [('canRemove', 'u0', 'u2')] * 5000
        exp = [None] + [o.mod_can(state, 'u0', 'u2')] * 5000
        if uid != o.MOD1:
            calls += [('getModerators',)] * 20; exp += [state] * 20
        if uid == o.MOD3:
            past = state
            calls += [('getModeratorsAt', 12345)] * 20 + [('canRemoveAt', 12345, 'u0', 'u4')] * 4000
            exp += [past] * 20 + [o.mod_can(past, 'u0', 'u4')] * 4000
        out.append((_ops('ModSystem', [logs], calls), exp))
    elif uid in (o.RECT1, o.RECT2, o.RECT3, o.RECT4):
        calls = [('addRectangle', i, i, 10**9 - 1, 10**9 - 1) for i in range(1500)] + [('getTopRectangle', 0, 0)] * 1500
        out.append((_ops('RectangleBoard', [10**9, 10**9], calls), [None] + list(range(1, 1501)) + [1] * 1500))
    elif uid in (o.SHEET1, o.SHEET2):
        cols = [chr(65 + i) for i in range(26)]
        cells = [c + str(r) for r in range(1, 101) for c in cols][:600]
        calls = [('setCell', cells[0], '1')] + [('setCell', cells[i], '=' + cells[i - 1] + '+1') for i in range(1, len(cells))]
        calls += [('getCell', cells[-1])] * 100
        exp = [None] + [None if uid == o.SHEET1 else True] * len(cells) + [len(cells)] * 100
        out.append((_ops('Spreadsheet', [], calls), exp))
    elif uid == o.DIAG:
        n = 100000; locs = [[i, i] for i in range(n)]
        out.append(([locs, [1] * 99999 + [4]], [n - 2, n - 2]))
        out.append(([locs, [2, 3] * 50000], [0, 0]))
    elif uid in (o.EXP1, o.EXP2):
        exps = [['E' + str(i), 'T' + str(i % 100), '100.00', 'meals', 'restaurant', 'joes'] for i in range(5000)]
        rules = [['expense', 'R' + str(i), 'amount', '<=', '99.99', '', ''] for i in range(40)]
        exp = [['R' + str(i), 'E' + str(j)] for i in range(40) for j in range(5000)]
        if uid == o.EXP2:
            rules += [['trip', 'R9' + str(i), 'amount', '<', '5000', 'expense_type', 'meals'] for i in range(10)]
            exp += [['R9' + str(i), 'T' + str(t)] for i in range(10) for t in range(100)]
        out.append(([rules, exps], exp))
    elif uid in (o.WQ1, o.WQ2):
        n = 10000; tasks = list(range(n))
        calls = [('reserve', i) for i in range(n)] + [('getDeadLetters', 10**9)]
        ctor = [tasks, [[i, i + 1] for i in range(n - 1)], 1, 1] if uid == o.WQ2 else [tasks, 1, 1]
        if uid == o.WQ1:
            exp = [None] + tasks + [tasks]
        else:  # chain: only task 0 ready; it expires at t=1 -> dead, cascade kills all
            exp = [None, 0] + [-1] * (n - 1) + [tasks]
        out.append((_ops('WorkQueue', ctor, calls), exp))
    elif uid == o.PERM:
        node = {'uuid': 'leaf', 'type': 'FILE', 'userIds': [], 'children': []}
        for i in range(199): node = {'uuid': 'd' + str(i), 'type': 'FOLDER', 'userIds': [], 'children': [node]}
        root = {'uuid': 'root', 'type': 'TEAM', 'userIds': ['u1'], 'children': [node]}
        out.append(([[root], [['u1', 'leaf'], ['u2', 'leaf']] * 10000], [True, False] * 10000))
    elif uid == o.FILL:
        out.append((['1 1 1 1 1 1 1 = 999'], []))
    elif uid == o.MEET:
        evs = [f'p{i % 50} busy {m // 60:02d}:{m % 60:02d} {m // 60:02d}:{m % 60:02d}' for i, m in enumerate(range(0, 1440, 2))]
        out.append(([evs * 27, 1], '00:01'))
        out.append(([evs * 27, 2], '-1'))
    elif uid in (o.FREE1, o.FREE2):
        rows = [['b' + str(i % 7), str(i), str(i)] for i in range(0, 1000, 2)]
        exp = [[str(i), str(i)] for i in range(1, 1000, 2)]
        out.append(([rows[::-1]] + ([1] if uid == o.FREE2 else []), exp))
        if uid == o.FREE2: out.append(([rows, 2], []))
    elif uid == o.IPV4:
        files = [{'name': 'f' + str(i), 'isFile': True, 'lines': ['ip 10.0.%d.%d and 300.1.1.1' % (i % 256, j) for j in range(100)], 'children': []} for i in range(200)]
        root = {'name': 'root', 'isFile': False, 'lines': [], 'children': files}
        out.append(([root], sorted({'10.0.%d.%d' % (i % 256, j) for i in range(200) for j in range(100)})))
    elif uid == o.TILE:
        for s, t in [('RRRRR__BBBBB', 'BBBBB__RRRRR'), ('RRRRRR______', '______RRRRRR'), ('RRRR_B_B_BBB', 'BBBB_R_R_RRR'), ('RRRRR_BBBBBB', 'BBBBBB_RRRRR')]:
            out.append(([list(s), list(t)], o.ref_tile(list(s), list(t))))
    elif uid == o.FRAC:
        orders = [['AAPL', 'B', '0.01', '100']] * 100000
        out.append(([orders, []], [['AAPL', '0']]))
    elif uid == o.FRIEND:
        n = 1000; es = [[0, i] for i in range(1, n)] + [[i, i + 1] for i in range(1, 4000) if i + 1 < n]
        out.append(([n, es], _friend_star(n, es)))
    elif uid in (o.PROF1, o.PROF2, o.PROF3):
        samples = ['%d:%s' % (i, '->'.join(['f'] * 50)) for i in range(10000)]
        a = [samples] + ([10000] if uid == o.PROF2 else [])
        if uid == o.PROF3: exp = [['f', 9999]]
        else: exp = [['start', 'f', 0]] * 50
        out.append((a, exp))
    elif uid in (o.HOTEL1, o.HOTEL2, o.HOTEL3):
        res = [{'guest_name': 'G' + chr(97 + i % 26), 'room_type': 'suite', 'check_in_day': i, 'stay_length': 1} for i in range(5000)]
        tps = {'t' + chr(97 + k): (k if uid == o.HOTEL1 else {'anchor': 'check_in', 'offset': k}) for k in range(20)}
        out.append(([res, tps], sorted([i + k, 'G' + chr(97 + i % 26), 't' + chr(97 + k)] for i in range(5000) for k in range(20))))
    elif uid in (o.DIFF1, o.DIFF2, o.DIFF3):
        n = 100000 if uid != o.DIFF3 else 2000
        a = ['l' + str(i) for i in range(n)]; b = a[::-1]
        if uid == o.DIFF1: out.append(([a, b], [0, n - 1]))
        elif uid == o.DIFF2: out.append(([a, b], [[0, n - 1]]))
        else: out.append(([a, b], ['+ ' + x for x in b[:-1]] + ['  ' + a[0]] + ['- ' + x for x in a[1:]]))
    return out


def _friend_star(n, es):
    """Analytic: hub 0 adjacent to all; path 1..n-1. User 0 has no non-friends -> -1.
    Leaf i (path neighbours i-1,i+1) shares hub 0 with every other leaf, and shares two mutuals (0 and i+-1)
    with i-2 / i+2; smallest such id wins; leaves with no distance-2 path neighbour pick the smallest non-friend."""
    adj = [set() for _ in range(n)]
    for a, b in es: adj[a].add(b); adj[b].add(a)
    out = [-1]
    for u in range(1, n):
        best = [v for v in (u - 2, u + 2) if 1 <= v < n]
        if best: out.append(min(best)); continue
        out.append(min(v for v in range(1, n) if v != u and v not in adj[u]))
    return out
