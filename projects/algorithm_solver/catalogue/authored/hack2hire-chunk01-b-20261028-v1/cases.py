"""Private case generation from file-local independent references; inferred domains only, no source examples."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec = importlib.util.spec_from_file_location('gamma_h2h_c01b_case_oracles', Path(__file__).with_name('oracles.py'))
_o = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_o)
reference, validate_domain = _o.reference, _o.validate_domain


def _seed(pid):
    return int(_o.vid(pid)[-8:], 16)


def _tree(rng, budget, make_file):
    """Random directory tree with at most `budget` nodes (directories + files)."""
    count = [1]
    def build(depth, name):
        node = {'name': name, 'directories': [], 'files': []}
        for i in range(rng.randrange(0, 5)):
            if count[0] >= budget: break
            count[0] += 1
            if depth < 3 and rng.random() < 0.4: node['directories'].append(build(depth + 1, f'd{i}'))
            else: node['files'].append(make_file(rng, f'f{i}'))
        return node
    return build(0, 'root')


def _grid(rng, rows, cols, alphabet):
    return [''.join(rng.choice(alphabet) for _ in range(cols)) for _ in range(rows)]


def _small(pid, rng):
    args = []
    if pid == _o.BUF:
        for _ in range(250):
            names, rows = ['BufferedFile'], [[rng.randrange(1, 6)]]
            for _ in range(rng.randrange(0, 9)):
                if rng.random() < 0.7: names.append('write'); rows.append([[rng.randrange(-128, 128) for _ in range(rng.randrange(0, 8))]])
                else: names.append('flush'); rows.append([])
            args.append([names, rows])
        args.append([['BufferedFile', 'write', 'flush', 'flush'], [[1], [[-128, 127]], [], []]])
    elif pid in (_o.ENC1, _o.ENC2):
        budget = 14 if pid == _o.ENC1 else 9
        f = lambda r, n: {'name': n, 'isEncrypted': r.random() < 0.6}
        args = [[_tree(rng, rng.randrange(1, budget + 1), f)] for _ in range(250)]
        args.append([{'name': 'root', 'directories': [], 'files': []}])
        args.append([{'name': 'root', 'directories': [{'name': 'e', 'directories': [], 'files': []}], 'files': [{'name': 'x', 'isEncrypted': True}]}])
    elif pid == _o.FANCY:
        args = [[n] for n in range(1, 400)] + [[4**k + d] for k in range(1, 15) for d in (-1, 0, 1) if 1 <= 4**k + d <= 10**9]
        args += [[rng.randrange(1, 10**9 + 1)] for _ in range(80)] + [[10**9]]
    elif pid in (_o.FILT1, _o.FILT2):
        for _ in range(250):
            msgs = [[f'u{i}', ''.join(rng.choice('ab ') for _ in range(rng.randrange(0, 9)))] for i in range(rng.randrange(0, 6))]
            words = [''.join(rng.choice('ab') for _ in range(rng.randrange(1, 4))) for _ in range(rng.randrange(0, 4))]
            args.append([msgs, words])
    elif pid == _o.CAM:
        users, groups, cams = ['u0', 'u1', 'u2', 'u3'], ['g0', 'g1', 'g2', 'g3'], ['c0', 'c1', 'c2']
        for _ in range(300):
            perms = []
            for _ in range(rng.randrange(0, 12)):
                rel = rng.choice(_o.RELATIONS)
                a = rng.choice(users if rel in ('cameraOwner', 'groupMember') else groups)
                b = rng.choice(cams if rel in ('cameraOwner', 'groupCameraOwner') else groups)
                perms.append([a, rel, b])
            args.append([perms, rng.choice(cams + ['c9'])])
    elif pid == _o.DASH:
        for _ in range(250):
            r, c = rng.randrange(1, 6), rng.randrange(1, 6)
            city = _grid(rng, r, c, '  DXX ')
            args.append([city, [[i, j] for i in range(r) for j in range(c)]])
        args.append([['X'], [[0, 0]]]); args.append([[' '], []])
    elif pid in (_o.MODE, _o.MED):
        for _ in range(300):
            k, n = rng.randrange(1, 5), rng.randrange(1, 14)
            spread = rng.choice([2, 4, 10**9])
            flat = [rng.randrange(-spread, spread + 1) for _ in range(n)]
            args.append([[flat[i::k] for i in range(k)]])
        args += [[[[10**9], [-10**9]]], [[[10**9, 10**9 - 1]]], [[[-10**9]]], [[[1, 2], [3], [4]]]]
    elif pid in (_o.DEST1, _o.DEST2):
        for _ in range(300):
            nodes = rng.randrange(1, 8)
            if pid == _o.DEST1:
                edges = [[u, rng.randrange(nodes)] for u in range(nodes) if rng.random() < 0.7]
                rng.shuffle(edges)
            else:
                edges = [[rng.randrange(nodes), rng.randrange(nodes)] for _ in range(rng.randrange(0, 12))]
            args.append([edges, rng.randrange(nodes + 1)])
        args += [[[], 10**9], [[[0, 10**9]], 0]]
    elif pid in (_o.DUP1, _o.DUP2):
        pool = [[], [0], [255], [1, 2], [1, 2, 3], [2, 1], [0, 0]]
        def f(r, n):
            content = list(r.choice(pool))
            if pid == _o.DUP1: return {'name': n, 'content': content}
            chunks, i = [], 0
            while i < len(content) or (not chunks and r.random() < 0.5):
                step = r.randrange(0, 3); chunks.append(content[i:i + step]); i += step
            return {'name': n, 'chunks': chunks}
        args = [[_tree(rng, rng.randrange(4, 25), f)] for _ in range(300)]
    elif pid == _o.TRADE:
        for _ in range(300):
            args.append([[[rng.randrange(1, 6), rng.randrange(1, 5), rng.choice(['buy', 'sell'])] for _ in range(rng.randrange(0, 12))]])
        args.append([[[10**9, 10**9, 'sell'], [10**9, 10**9, 'buy'], [1, 1, 'buy']]])
    elif pid == _o.SHOP:
        for _ in range(300):
            n = rng.randrange(1, 9)
            args.append([[[rng.randrange(1, 6), rng.randrange(0, 11)] for _ in range(n)], rng.randrange(0, 13)])
        args += [[[[10000, 10**9]], 10000], [[[10000, 0]], 9999], [[[1, 0], [1, 0]], 0]]
    elif pid == _o.MISS:
        for _ in range(300):
            words = [rng.choice('abc') for _ in range(rng.randrange(1, 9))]
            keep = sorted(rng.sample(range(len(words)), rng.randrange(0, len(words) + 1)))
            args.append([' '.join(words), ' '.join(words[i] for i in keep)])
        args += [['Hello World', 'World'], ['a A a', 'a']]
    elif pid in (_o.COM1, _o.COM2):
        for _ in range(300):
            k = rng.randrange(1, 4)
            r, c = rng.randrange(2, 7), rng.randrange(2, 7)
            cells = [[rng.choice('X' + ''.join(str(d) for d in range(1, k + 1)) * 2) for _ in range(c)] for _ in range(r)]
            spots = rng.sample([(i, j) for i in range(r) for j in range(c)], 2)
            cells[spots[0][0]][spots[0][1]] = 'S'; cells[spots[1][0]][spots[1][1]] = 'D'
            modes = ['Walk', 'Bike', 'Car'][:k]
            args.append([[''.join(row) for row in cells], modes, [rng.randrange(1, 5) for _ in range(k)], [rng.randrange(0, 5) for _ in range(k)]])
    elif pid == _o.ROBOT:
        for _ in range(300):
            r, c = rng.randrange(1, 6), rng.randrange(1, 6)
            board = [[rng.choice('OEEX') for _ in range(c)] for _ in range(r)]
            want = [rng.randrange(1, 4) for _ in range(4)]
            robots = [(i, j) for i in range(r) for j in range(c) if board[i][j] == 'O']
            if robots and rng.random() < 0.7:
                i, j = rng.choice(robots); want = []
                for di, dj in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    s = 1
                    while 0 <= i + s * di < r and 0 <= j + s * dj < c and board[i + s * di][j + s * dj] != 'X': s += 1
                    want.append(s)
            args.append([board, want])
    elif pid == _o.STOP1:
        for _ in range(300):
            args.append([''.join(rng.choice('ab ') for _ in range(rng.randrange(0, 11))),
                         [''.join(rng.choice('ab') for _ in range(rng.randrange(1, 4))) for _ in range(rng.randrange(0, 4))]])
        args += [['', ['a']], ['abc', []], ['Stop', ['stop']]]
    elif pid == _o.STOP2:
        for _ in range(400):
            args.append([[''.join(rng.choice('ab') for _ in range(rng.randrange(0, 5))) for _ in range(rng.randrange(0, 6))],
                         [''.join(rng.choice('ab') for _ in range(rng.randrange(1, 5))) for _ in range(rng.randrange(0, 4))]])
        args += [[[], ['a']], [['ab', 'c'], ['abc', 'b']], [['xa', 'bx'], ['ab', 'abz']]]
    elif pid in (_o.SOCK1, _o.SOCK2):
        for _ in range(300):
            n = rng.randrange(0, 11)
            ids = rng.sample(list(range(-20, 21)) + [-10**9, 10**9], n)
            args.append([ids, [rng.choice(['red', 'g']) for _ in range(n)], [rng.choice(['left', 'right']) for _ in range(n)]])
    return args


def _maximum(pid):
    """Domain-bound rows with expected values fixed by construction (analytic) or a linear-time reference."""
    if pid == _o.BUF:
        a = [['BufferedFile'] + ['write'] * 20 + ['flush'], [[9999]] + [[[(i * 7 + j) % 256 - 128 for j in range(10000)]] for i in range(20)] + [[]]]
        b = [['BufferedFile'] + ['write'] * 10000, [[1]] + [[[i % 256 - 128] * 20] for i in range(10000)]]
        c = [['BufferedFile', 'write', 'flush'], [[10000], [[5] * 10000], []]]
        return [(x, reference(pid, x)) for x in (a, b, c)]
    if pid in (_o.ENC1, _o.ENC2):
        flat_all = {'name': 'root', 'directories': [], 'files': [{'name': f'f{i}', 'isEncrypted': True} for i in range(99999)]}
        flat_alt = {'name': 'root', 'directories': [], 'files': [{'name': f'f{i}', 'isEncrypted': i % 2 == 0} for i in range(99999)]}
        chain = None
        for i in reversed(range(200)):
            chain = {'name': f'd{i}', 'directories': [chain] if chain else [], 'files': [{'name': 'f', 'isEncrypted': i < 199}]}
        v1 = pid == _o.ENC1
        return [([flat_all], 1), ([flat_alt], 50000), ([chain], 199 if v1 else 2)]
    if pid == _o.FANCY:
        return [([10**9], reference(pid, [10**9])), ([1], 0), ([4**14 + 1], 2**14)]
    if pid in (_o.FILT1, _o.FILT2):
        msgs = [[f'u{i}', 'ab' * 10] for i in range(10000)]
        words = [''.join(w) for w in itertools.islice(itertools.product('cdefg', repeat=5), 999)]
        return [([msgs, words], msgs), ([msgs, words + ['ba']], msgs if pid == _o.FILT1 else [])]
    if pid == _o.CAM:
        chain = [['u0', 'groupMember', 'g0']] + [[f'g{i}', 'subgroupMember', f'g{i + 1}'] for i in range(99998)] + [['g99998', 'groupCameraOwner', 'cam']]
        chain = chain[:100000]
        fan = [[f'u{i}', 'groupMember', 'g'] for i in range(99999)] + [['g', 'groupCameraOwner', 'cam']]
        return [([chain, 'cam'], ['u0'] if chain[-1][1] == 'groupCameraOwner' else []), ([fan, 'cam'], sorted(f'u{i}' for i in range(99999)))]
    if pid == _o.DASH:
        city = ['D' + ' ' * 315] + [' ' * 316] * 315
        locs = [[i, j] for i in range(316) for j in range(316)]
        return [([city, locs], [i + j for i, j in locs]), ([[' ' * 316] * 316, locs], [-1] * len(locs))]
    if pid in (_o.MODE, _o.MED):
        a = [[[(i * 2000 + j) % 1000 for j in range(2000)] for i in range(100)]]
        b = [[[10**9 - (i * 2000 + j) for j in range(2000)] for i in range(100)]]
        return [(a, reference(pid, a)), (b, reference(pid, b))]
    if pid == _o.DEST1:
        return [([[[i, i + 1] for i in range(100000)], 0], 100000), ([[[i, (i + 1) % 100000] for i in range(100000)], 5], -1)]
    if pid == _o.DEST2:
        return [([[[0, i] for i in range(1, 100001)], 0], list(range(1, 100001))), ([[[i, i + 1] for i in range(100000)], 0], [100000]),
                ([[[i, (i + 1) % 100000] for i in range(100000)], 0], [])]
    if pid in (_o.DUP1, _o.DUP2):
        def file(i, content):
            if pid == _o.DUP1: return {'name': f'f{i}', 'content': content}
            s = i % 5 + 1
            return {'name': f'f{i}', 'chunks': [content[j:j + s] for j in range(0, len(content), s)]}
        wide = {'name': 'root', 'directories': [], 'files': [file(i, [i % 100] * 20) for i in range(9999)]}
        groups = {}
        for i in range(9999): groups.setdefault(i % 100, []).append(f'/f{i}')
        chain, path = None, []
        for i in reversed(range(200)):
            chain = {'name': f'd{i}', 'directories': [chain] if chain else [], 'files': [file(i, [7] * 999)]}
        paths = ['/'.join([''] + [f'd{j}' for j in range(1, i + 1)] + [f'f{i}']) for i in range(200)]
        return [([wide], sorted(sorted(g) for g in groups.values())), ([chain], [sorted(paths)])]
    if pid == _o.TRADE:
        a = [[p, 10**9, 'sell'] for p in range(1, 50001)] + [[10**9, 10**9, 'buy'] for _ in range(50000)]
        b = [[1, 10**9, 'buy'] for _ in range(50000)] + [[2, 10**9, 'sell'] for _ in range(50000)]
        return [([a], 5 * 10**13), ([b], 0)]
    if pid == _o.SHOP:
        same = [[10000, 0] for _ in range(10000)]
        spaced = [[10000, i * 10000] for i in range(10000)]
        return [([same, 10000], 10000), ([same, 0], -1), ([spaced, 10000], 1), ([same, 10**9], 1)]
    if pid == _o.MISS:
        return [([' '.join(['ab'] * 33333), ' '.join(['ab'] * 16666)], ['ab'] * 16667), ([' '.join(['ab'] * 33333), ''], ['ab'] * 33333)]
    if pid in (_o.COM1, _o.COM2):
        modes, times, costs = ['A', 'B', 'C'], [10000, 3, 2], [10000, 0, 1]
        open_grid = ['S' + '1' * 99] + ['1' * 100] * 98 + ['1' * 99 + 'D']
        walled = ['S' + '1' * 99, 'X' * 100] + ['1' * 100] * 97 + ['1' * 99 + 'D']
        v1 = pid == _o.COM1
        return [([open_grid, modes, times, costs], 'A' if v1 else [197 * 10000, 197 * 10000]),
                ([walled, modes, times, costs], '' if v1 else [-1, -1])]
    if pid == _o.ROBOT:
        full = [['O'] * 316 for _ in range(316)]
        return [([full, [1, 1, 316, 316]], [[0, 0]]), ([full, [158, 158, 159, 159]], [[157, 157]]), ([[['E'] * 316 for _ in range(316)], [1, 1, 1, 1]], [])]
    if pid == _o.STOP1:
        words = ['a' * 49 + chr(99 + i % 24) for i in range(100)]
        return [(['a' * 100000, words], 'a' * 100000), (['a' * 99999 + 'b', words[:99] + ['ab']], 'a' * 99998)]
    if pid == _o.STOP2:
        return [([['a' * 100] * 1000, ['a' * 49 + 'b']], ['a' * 51] + ['a' * 100] * 999 + ['a' * 49]),
                ([['abcdefghij'] * 10000, ['jab']], ['abcdefghi'] + [''] * 10000)]
    if pid in (_o.SOCK1, _o.SOCK2):
        ids = list(range(100000)); ids[0], ids[1], ids[99998], ids[99999] = -10**9, -10**9 + 1, 10**9 - 1, 10**9
        colors = [chr(97 + (i // 2) % 26) for i in range(100000)]
        feet = ['left' if i % 2 == 0 else 'right' for i in range(100000)]
        return [([ids, colors, feet], 50000 if pid == _o.SOCK1 else [[ids[2 * j], ids[2 * j + 1]] for j in sorted(range(50000), key=lambda j: ids[2 * j])])]
    return []


def build_cases(pid, include_maximum=False):
    rng = random.Random(_seed(pid))
    rows = [{'args': a, 'expected': reference(pid, a), 'category': 'independent-bounded-reference'} for a in _small(pid, rng)]
    if include_maximum:
        for a, expected in _maximum(pid):
            validate_domain(pid, a)
            rows.append({'args': a, 'expected': expected, 'category': 'analytic-or-linear-reference-maximum', 'isolate': True})
    return rows
