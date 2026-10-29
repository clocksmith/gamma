"""Private case generation from file-local independent references over INFERRED domains."""
import importlib.util
from pathlib import Path
import random
import zlib
_spec = importlib.util.spec_from_file_location('gamma_h2h06b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain

WORDS = ['x', 'Fix bug', 'Write docs', 'a-b', 'Q_1', 'Deploy', 'Review', 'n']


def _tree(rng, budget, depth):
    node = {'tag': rng.choice(['div', 'p', 'span', 'a', 'ul', 'li', 'h1', 'b']), 'children': []}
    while budget[0] > 0 and depth < 12 and rng.random() < 0.55:
        budget[0] -= 1; node['children'].append(_tree(rng, budget, depth + 1))
    return node


def _task_records(rng, uid):
    n = rng.randrange(0, 14); ids = ['t%d' % i for i in range(n)] + (['A', 'b_2'] if rng.random() < 0.3 else [])
    rng.shuffle(ids); recs, defined = [], []
    for tid in ids:
        name = rng.choice(WORDS)
        if not defined or rng.random() < 0.3: recs.append('%d,task,%s,%s' % (rng.randrange(0, 10**6), tid, name))
        else: recs.append('%d,subtask,%s,%s,%s' % (rng.randrange(0, 10**6), rng.choice(defined), tid, name))
        defined.append(tid)
    if uid == _o.TASK1:
        rng.shuffle(recs); return recs
    extra = []
    for _ in range(rng.randrange(0, 8)):
        pool = ids + ['ghost', 'zz']
        extra.append(rng.choice([
            '%d,task,%s,%s' % (rng.randrange(100), rng.choice(pool), rng.choice(WORDS)),                       # duplicate or new root
            '%d,subtask,%s,%s,%s' % (rng.randrange(100), rng.choice(pool), rng.choice(pool), rng.choice(WORDS)),  # duplicate, orphan or cycle
            '%d,subtask,ghost,orph%d,%s' % (rng.randrange(100), rng.randrange(3), rng.choice(WORDS)),
            '%d,task,,%s' % (rng.randrange(100), rng.choice(WORDS)), '%d,task,q9,' % rng.randrange(100), '1,task,a,b,c', '1,subtask,a,b',
            '1,note,a,b', '', 'garbage', ',,,', '%d,complete,%s' % (rng.randrange(100), rng.choice(pool)), '1,complete,', '1,complete,a,b']))
    recs += extra; rng.shuffle(recs)
    if uid == _o.TASK4:
        recs += ['%d,complete,%s' % (rng.randrange(100), rng.choice(ids + ['ghost'])) for _ in range(rng.randrange(0, 6)) if ids]
        rng.shuffle(recs)
    return recs


def _message(rng):
    toks = []
    for _ in range(rng.randrange(0, 7)):
        k = rng.random()
        if k < 0.35: toks.append('@' + ','.join('id%d' % rng.choice([1, 2, 3, 7, 42, 999, 500]) for _ in range(rng.randrange(1, 4))))
        elif k < 0.42: toks.append('@all')
        elif k < 0.55: toks.append(rng.choice(['appro@ch', 'x@id1', 'mail@id2,id3', 'a@all']))
        else: toks.append(rng.choice(['hi', 'id1', 'ok!', '', 'deal,', 'id7?']))
    return ' '.join(toks)


def _review(rng):
    words = ['San', 'francisco', 'san', 'Francisco', 'bay', 'Bay', 'area', 'sandbox', 'great', 'view', 'NYC', 'nyc2', 'pool']
    seps = [' ', ' ', ' ', ', ', '! ', '?', '-', '  ', '.', "'", '{', '[']
    return ''.join(rng.choice(words) + rng.choice(seps) for _ in range(rng.randrange(0, 12))).rstrip(' ') * 1


MAPPINGS = [['san francisco', 'city'], ['san', 'saint'], ['bay area', 'region'], ['Bay', 'water'], ['great view', 'praise'], ['nyc', 'city'],
            ['pool', 'amenity'], ['SAN', 'dup'], ['francisco bay', 'x'], ['view', 'v']]


def build_cases(uid, include_maximum=False):
    rng = random.Random(zlib.crc32(uid.encode())); args = []
    o = _o
    if uid == o.FLAT:
        args = [[{'tag': 'html', 'children': []}], [{'tag': 'a', 'children': [{'tag': 'b', 'children': []}, {'tag': 'c', 'children': [{'tag': 'b', 'children': []}]}]}]]
        args += [[_tree(rng, [rng.randrange(0, 30)], 0)] for _ in range(250)]
    elif uid in o.TASKS:
        args = [[[]], [['5,task,a,Root']], [['9,subtask,a,b,Child', '1,task,a,Root', '3,subtask,b,c,Leaf', '2,task,z,Other']]]
        if uid != o.TASK1:
            args += [[['1,task,a,A', '2,task,a,Dup', '3,subtask,x,y,Orphan', '4,subtask,y,x,Cycle', '5,subtask,a,a,Self', 'bad', '6,task,,E']]]
        if uid == o.TASK4:
            args += [[['1,task,a,A', '2,subtask,a,b,B', '3,subtask,a,c,C', '4,complete,b', '5,complete,c', '6,task,d,D', '7,complete,d', '8,subtask,d,e,E']]]
        args += [[_task_records(rng, uid)] for _ in range(250)]
    elif uid == o.GAME:
        args = [[[0], [5], 0], [[1], [5], 0], [[3, 1], [-4, 2], 3], [[2, 2, 2], [1, -5, 9], 4], [[0, 0], [-1, -1], 0]]
        for _ in range(250):
            n = rng.randrange(1, 12)
            args.append([[rng.choice([0, 1, 2, 3, 5, 10000]) for _ in range(n)], [rng.randrange(-6, 7) for _ in range(n)], rng.choice([0, 1, 3, 7, 12, 10**9])])
    elif uid == o.GRID:
        args = [[[[9]]], [[[0]]], [[[-1]]], [[[1, 1]]], [[[1, 9, 1]]], [[[1, -1, 1]]], [[[9, 9], [9, 9]]]]
        for _ in range(250):
            m, n = rng.randrange(1, 6), rng.randrange(1, 6)
            w = rng.choice([[9, 9, 9, -1], [9, -1, 1, 0, 9, 9], [9] * 8 + [1]])
            args.append([[[rng.choice(w) for _ in range(n)] for _ in range(m)]])
    elif uid == o.MENTION:
        args = [[[], []], [['id1'], ['@id1 hi @id1,id1']], [['id1', 'id2'], ['appro@ch @id2', '@all', 'x @id3']]]
        for _ in range(250):
            members = rng.sample(['id1', 'id2', 'id3', 'id7', 'id42', 'id999', 'id10'], rng.randrange(0, 6))
            args.append([members, [_message(rng) for _ in range(rng.randrange(0, 6))]])
    elif uid == o.GUESS:
        args = [[s] for s in ['0000', '9999', '0123', '9876', '1111', '0009', '9990', '5555', '1212', '0990']]
        args += [['%04d' % rng.randrange(10000)] for _ in range(240)]
    elif uid == o.GUESS2:
        args = [[t] for t in range(1000)]
    elif uid in (o.DELAY1, o.DELAY2):
        bounds = [(1, 1), (2, 1), (2, 2), (10**9, 1), (10**9, 10**9), (10**9, 500000000), (7, 4)]
        for _ in range(240):
            ub = rng.choice([rng.randrange(1, 20), rng.randrange(1, 10**6), rng.randrange(1, 10**9 + 1)])
            bounds.append((ub, rng.randrange(1, ub + 1)))
        for ub, s in bounds: args.append([ub, s] if uid == o.DELAY1 else [ub, rng.choice([1, 2, 3, 20, rng.randrange(1, 21)]), s])
    elif uid == o.HIGHLIGHT:
        args = [['', []], ['san?', [['san', 'c']]], ['sandbox', [['san', 'c']]], ['San Francisco bay area', MAPPINGS], ['x', []]]
        for _ in range(250):
            args.append([_review(rng), rng.sample(MAPPINGS, rng.randrange(0, len(MAPPINGS) + 1))])
    elif uid in (o.INT1, o.INT2, o.INT3):
        top = {o.INT1: 9, o.INT2: 999, o.INT3: 2**31 - 1}[uid]
        args = [[v] for v in range(min(top, 120) + 1)]
        if uid != o.INT1:
            args += [[v] for v in (top, 100, 101, 110, 115, 120, 999, 900, 990, 909) if v <= top]
            args += [[rng.randrange(0, top + 1)] for _ in range(120)]
        if uid == o.INT3:
            args += [[v] for v in (1000, 1001, 10**6, 10**6 + 1, 10**9, 10**9 + 7, 1000010, 2**31 - 1, 123456789, 1000000000 + 1000)]
            args += [[rng.randrange(0, 10 ** rng.randrange(1, 10))] for _ in range(100)]
    elif uid == o.JOB:
        args = [[[]], [[['J1', '0000', '10']]], [[['J1', '0000', '10'], ['J2', '0005', '5'], ['J3', '0010', '1'], ['J4', '0010', '3']]]]
        for _ in range(250):
            t, jobs = 0, []
            for i in range(rng.randrange(0, 12)):
                t += rng.choice([0, 0, 1, 3, 10, 60]); t = min(t, 1439)
                jobs.append(['J%d' % i, '%02d%02d' % divmod(t, 60), str(rng.choice([1, 2, 5, 10, 60, 10000]))])
            args.append([jobs])
    elif uid == o.KEYS:
        args = [[[['a']], 0, 'a'], [[['a']], 0, 'b'], [[['a', 'b']], 0, 'ab'], [[['a', 'b']], 1, 'abba'], [[['a', 'c', 'b']], 1, 'ab']]
        for _ in range(250):
            m, n = rng.randrange(1, 6), rng.randrange(1, 6); letters = 'abcd'[:rng.randrange(1, 5)]
            kb = [[rng.choice(letters) for _ in range(n)] for _ in range(m)]
            args.append([kb, rng.randrange(0, 6), ''.join(rng.choice(letters if rng.random() < 0.97 else 'e') for _ in range(rng.randrange(1, 12)))])
    elif uid == o.KNIGHT:
        args = [[a, b] for a in range(10) for b in range(10)]
    elif uid == o.PARITY:
        args = [['0'], ['9'], ['10'], ['1234'], ['65875'], ['247'], ['0000'], ['13579'], ['97531']]
        args += [[''.join(rng.choice('0123456789') for _ in range(rng.randrange(1, 15)))] for _ in range(250)]
    elif uid == o.LATENCY:
        args = [[[], 1, 1], [[1], 1, 1], [[1, 2, 3], 1, 2], [[5, 10, 10, 19, 20, 100], 10, 3], [[10**9], 10**9, 100000]]
        for _ in range(250):
            args.append([sorted(rng.randrange(1, 60) for _ in range(rng.randrange(0, 12))), rng.choice([1, 2, 5, 10, 100]), rng.randrange(1, 8)])
    elif uid == o.CIRC:
        args = [[[0], 0], [[0], 1], [[1], 0], [[1, 0, 1], 0], [[1, 1, 0, 1, 1], 0], [[0, 0, 0], 2]]
        for _ in range(250):
            n = rng.randrange(1, 14)
            args.append([[rng.choice([0, 1, 1]) for _ in range(n)], rng.randrange(0, n + 1)])
    rows = [{'args': a, 'expected': reference(uid, a), 'category': 'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a, expected in maximum_rows(uid):
            validate_domain(uid, a); rows.append({'args': a, 'expected': expected, 'category': 'analytic-maximum', 'isolate': True})
    return rows


def _chain_records(roots, depth, prefix='r'):
    """roots chains of `depth` tasks each; records listed child-first (reverse) to exercise forward references."""
    recs = []
    for r in range(roots):
        chain = ['%s%d_%d' % (prefix, r, d) for d in range(depth)]
        recs.append('7,task,%s,N%d' % (chain[0], r))
        recs += ['7,subtask,%s,%s,N%d' % (chain[d - 1], chain[d], r) for d in range(depth - 1, 0, -1)]
    return recs


def maximum_rows(uid):
    """Large inputs whose expected values follow analytically from their construction."""
    o = _o; out = []
    if uid == o.FLAT:
        node = leaf_parent = {'tag': 'deep', 'children': []}
        for _ in range(88): node = {'tag': 'deep', 'children': [node]}
        leaf_parent['children'] = [{'tag': 'li', 'children': []} for _ in range(19911)]
        out.append(([node], ['<deep>'] * 89 + ['<li>', '</li>'] * 19911 + ['</deep>'] * 89))
        wide = {'tag': 'ul', 'children': [{'tag': 'li', 'children': [{'tag': 'b', 'children': []}]} for _ in range(9999)]}
        out.append(([wide], ['<ul>'] + ['<li>', '<b>', '</b>', '</li>'] * 9999 + ['</ul>']))
    elif uid in o.TASKS:
        recs = _chain_records(200, 100)
        if uid == o.TASK1:
            out.append(([recs], ['  ' * d + 'N%d' % r for r in range(200) for d in range(100)]))
        else:
            recs = _chain_records(100, 100)
            noise = ['1,task,r%d_0,Dup' % (i % 100) for i in range(3000)] + ['1,subtask,ghost%d,o%d,Orph' % (i, i) for i in range(3000)] + \
                    ['bad,record'] * 2000 + ['1,subtask,c%d,c%d,Cyc' % (i + 1, i) for i in range(1000)] + ['1,subtask,c0,c999,Cyc']
            marks = ['2,complete,r%d_99' % r for r in range(0, 100, 2)] if uid == o.TASK4 else []
            rows = recs + noise + marks
            exp = []
            for r in range(100):
                num = str(r + 1)
                for d in range(100):
                    box = ('[x] ' if r % 2 == 0 else '[ ] ') if uid == o.TASK4 else ''
                    exp.append('  ' * d + (num + ' ' + box if uid != o.TASK2 else '') + 'N%d' % r)
                    num += '.1'
            out.append(([rows], exp))
    elif uid == o.GAME:
        n = 100000
        out.append(([[1] * n, [1] * n, 50000], 50000))
        out.append(([[0] * n, [-1] * 50000 + [1] * 50000, 0], 50000))
        out.append(([[10000] * n, [10000] * n, 10**9], 10**9))
    elif uid == o.GRID:
        out.append(([[[9] * 316 for _ in range(316)]], [[1 ^ ((r + c) & 1) for c in range(316)] for r in range(316)]))
        g = [[9] * 100000]; g[0][99999] = 0
        out.append(([g], [[(c & 1) ^ 1 for c in range(100000)]]))
        g = [[9 if c % 2 == 0 else -1 for c in range(300)] for _ in range(333)]; g[0][0] = 0; g[2][0] = 1
        out.append(([g], []))
    elif uid == o.MENTION:
        members = ['id%d' % i for i in range(1, 1000)]
        msgs = ['@all hello @' + ','.join('id%d' % i for i in range(1, 40)) + ' x@id5 ' + 'z' * 80] * 10000
        out.append(([members, msgs], [10000] * 999))
        msgs = ['@id%d @id%d ok' % (1 + i % 999, 1 + i % 999) for i in range(9990)]
        out.append(([members, msgs], [10] * 999))
    elif uid == o.HIGHLIGHT:
        mapping = [['abc', 'one'], ['abc abc', 'two']] + [['w%d' % i, 'c%d' % i] for i in range(498)]
        out.append((['abc ' * 4999 + 'abc', mapping], ' '.join(['[two]{abc abc}'] * 2500)))
        out.append((['abd ' * 5000, mapping], 'abd ' * 5000))
    elif uid == o.JOB:
        n = 100000
        out.append(([[['J%d' % i, '0000', '1'] for i in range(n)]], [['J%d' % i, 'M%d' % (i + 1)] for i in range(n)]))
        jobs = [['J%d' % i, '%02d%02d' % divmod(i // 70, 60), '1'] for i in range(n)]
        out.append(([jobs], [['J%d' % i, 'M%d' % (i % 70 + 1)] for i in range(n)]))
    elif uid == o.KEYS:
        kb = [['c'] * 30 for _ in range(30)]; kb[0][0] = 'a'; kb[29][29] = 'b'
        out.append(([kb, 58, 'ab' * 500], True))
        out.append(([kb, 57, 'ab' * 500], False))
        out.append(([[['a'] * 30 for _ in range(30)], 0, 'a' * 1000], True))
        kb2 = [['a' if (r + c) % 2 == 0 else 'b' for c in range(30)] for r in range(30)]
        out.append(([kb2, 1, 'ab' * 499 + 'aa'], True))
        out.append(([kb2, 0, 'ab' * 500], False))
    elif uid == o.PARITY:
        out.append((['0123456789' * 10000], '0123456789' * 10000))
        out.append((['2468' * 25000], '8' * 25000 + '6' * 25000 + '4' * 25000 + '2' * 25000))
        out.append((['1' * 50000 + '0' + '3' * 49999], '1' * 50000 + '0' + '3' * 49999))
    elif uid == o.LATENCY:
        lat = list(range(1, 100001))
        out.append(([lat, 1000, 50], [999] + [1000] * 48 + [51001]))
        out.append(([lat, 1, 100000], [0] + [1] * 99998 + [2]))
    elif uid == o.CIRC:
        n = 100000
        out.append(([[1, 0] * (n // 2), 10], 21))
        out.append(([[0] + [1] * (n - 1), 0], n - 1))
        out.append(([[0] * n, n], n))
        out.append(([[1] * 49999 + [0] * 2 + [1] * 49999, 1], 99999))
    return out
