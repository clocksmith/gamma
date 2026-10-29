"""Independent bounded reference algorithms and INFERRED-domain validators; no candidate imports.

Every domain below is an inference (claude-opus-5-5 subagent, 2026-10-28) from partial Hack2Hire
previews, titles and tags. It is not an official specification. See contracts.json.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import re
from bisect import bisect_left

P = 'hack2hire:'
BUF = P + '695aed975242f618a4d2fa2f'
ENC1 = P + '6aa303f10ca9cc4e1c7901af'
ENC2 = P + '6aa304120ca9cc4e1c7901b3'
FANCY = P + '69c0a3ed21f6ab42269647c2'
FILT1 = P + '6a21945a8b879849ebc11fd4'
FILT2 = P + '6a2194828b879849ebc11fd5'
CAM = P + '6a0b5e8dc84b6e8a3be18bbb'
DASH = P + '689bcb111126a03aace65e51'
MODE = P + '6935ba921553144e303f676a'
MED = P + '69361ab01553144e303f6805'
DEST1 = P + '67fab475ba41b3368f4e5861'
DEST2 = P + '67fac1b6ba41b3368f4e5865'
DUP1 = P + '6934db665f306485cc5f08ba'
DUP2 = P + '6934e59f5f306485cc5f08be'
TRADE = P + '67e8af3a7131f7c901ffd7a1'
SHOP = P + '688102fcf96758aa78e1d67a'
MISS = P + '6a7921edd713d873ca7aa5eb'
COM1 = P + '68523a801af0034b322764d9'
COM2 = P + '6944670d867a3f9f539ff548'
ROBOT = P + '6789faf811318cc872dd83f3'
STOP1 = P + '69dfe86895e80ae213e5c79a'
STOP2 = P + '69dfee0f95e80ae213e5c7bc'
SOCK1 = P + '68dee4164b499ddb216af5ec'
SOCK2 = P + '68e1734e0fdcf62632c38cdc'
IDS = (BUF, ENC1, ENC2, FANCY, FILT1, FILT2, CAM, DASH, MODE, MED, DEST1, DEST2, DUP1, DUP2,
       TRADE, SHOP, MISS, COM1, COM2, ROBOT, STOP1, STOP2, SOCK1, SOCK2)
CLASSES = {BUF: 'BufferedFile'}
ARITY = {BUF: 2, ENC1: 1, ENC2: 1, FANCY: 1, FILT1: 2, FILT2: 2, CAM: 2, DASH: 2, MODE: 1, MED: 1,
         DEST1: 2, DEST2: 2, DUP1: 1, DUP2: 1, TRADE: 1, SHOP: 2, MISS: 2, COM1: 4, COM2: 4,
         ROBOT: 2, STOP1: 2, STOP2: 2, SOCK1: 3, SOCK2: 3}
# Every positive integer whose base-4 digits are 0/1, from the binary spelling of each mask (enumeration, not digit DP).
FANCY_VALUES = sorted(int(bin(mask)[2:], 4) for mask in range(1, 1 << 16))
RELATIONS = ('cameraOwner', 'groupMember', 'subgroupMember', 'groupCameraOwner')


def vid(uid):
    return uid[len(P):]


def integer(v, lo, hi):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('integer domain')


def string(s, lo, hi, pattern):
    if type(s) is not str or not lo <= len(s) <= hi or re.fullmatch(pattern, s) is None: raise ValueError('string domain')


def array(a, lo, hi):
    if type(a) is not list or not lo <= len(a) <= hi: raise ValueError('array size')


def tree(root, file_check, max_nodes, max_depth):
    """Iterative directory-tree validator; returns (node count, total file payload)."""
    if type(root) is not dict: raise ValueError('root directory required')
    stack, nodes, payload = [(root, 0)], 0, 0
    while stack:
        node, depth = stack.pop()
        if depth > max_depth: raise ValueError('depth')
        if type(node) is not dict or set(node) != {'name', 'directories', 'files'}: raise ValueError('directory shape')
        string(node['name'], 1, 30, r'[A-Za-z0-9._-]+')
        array(node['directories'], 0, max_nodes); array(node['files'], 0, max_nodes)
        names = [d['name'] if type(d) is dict else None for d in node['directories']] + \
                [f['name'] if type(f) is dict else None for f in node['files']]
        if len(set(names)) != len(names): raise ValueError('sibling names unique')
        for f in node['files']:
            payload += file_check(f); nodes += 1
        nodes += 1
        if nodes > max_nodes: raise ValueError('node budget')
        for child in node['directories']: stack.append((child, depth + 1))
    return nodes, payload


def enc_file(f):
    if type(f) is not dict or set(f) != {'name', 'isEncrypted'} or type(f['isEncrypted']) is not bool: raise ValueError('file shape')
    string(f['name'], 1, 30, r'[A-Za-z0-9._-]+')
    return 0


def byte_list(a, hi):
    array(a, 0, hi)
    for v in a: integer(v, 0, 255)
    return len(a)


def dup1_file(f):
    if type(f) is not dict or set(f) != {'name', 'content'}: raise ValueError('file shape')
    string(f['name'], 1, 30, r'[A-Za-z0-9._-]+')
    return byte_list(f['content'], 200000)


def dup2_file(f):
    if type(f) is not dict or set(f) != {'name', 'chunks'}: raise ValueError('file shape')
    string(f['name'], 1, 30, r'[A-Za-z0-9._-]+')
    array(f['chunks'], 0, 200000)
    return sum(byte_list(c, 200000) for c in f['chunks'])


def char_grid(rows, alphabet, max_area):
    array(rows, 1, max_area)
    if type(rows[0]) is not str or not rows[0]: raise ValueError('grid row')
    for row in rows:
        if type(row) is not str or len(row) != len(rows[0]) or set(row) - set(alphabet): raise ValueError('grid row')
    if len(rows) * len(rows[0]) > max_area: raise ValueError('grid area')


def validate_domain(pid, args):
    if pid not in ARITY or type(args) is not list or len(args) != ARITY[pid]: raise ValueError('argument envelope')
    if pid == BUF:
        names, rows = args
        array(names, 1, 10001); array(rows, len(names), len(names))
        if names[0] != 'BufferedFile' or type(rows[0]) is not list or len(rows[0]) != 1: raise ValueError('constructor')
        integer(rows[0][0], 1, 10000)
        total = 0
        for name, row in zip(names[1:], rows[1:]):
            if name == 'write' and type(row) is list and len(row) == 1:
                array(row[0], 0, 10000)
                for v in row[0]: integer(v, -128, 127)
                total += len(row[0])
            elif not (name == 'flush' and row == []): raise ValueError('method or arity')
        if total > 200000: raise ValueError('total bytes')
    elif pid in (ENC1, ENC2): tree(args[0], enc_file, 100000, 200)
    elif pid == FANCY: integer(args[0], 1, 10**9)
    elif pid in (FILT1, FILT2):
        messages, words = args
        array(messages, 0, 10000); array(words, 0, 1000)
        total = 0
        for m in messages:
            if type(m) is not list or len(m) != 2: raise ValueError('message pair')
            string(m[0], 1, 20, r'[a-z0-9_]+'); string(m[1], 0, 1000, r'[a-z ]*'); total += len(m[1])
        if total > 200000: raise ValueError('total text')
        for w in words: string(w, 1, 20, r'[a-z]+')
    elif pid == CAM:
        perms, camera = args
        array(perms, 0, 100000)
        users, groups, cameras = set(), set(), set()
        for p in perms:
            if type(p) is not list or len(p) != 3 or p[1] not in RELATIONS: raise ValueError('triple')
            string(p[0], 1, 20, r'[A-Za-z0-9_]+'); string(p[2], 1, 20, r'[A-Za-z0-9_]+')
            subject = users if p[1] in ('cameraOwner', 'groupMember') else groups
            target = cameras if p[1] in ('cameraOwner', 'groupCameraOwner') else groups
            subject.add(p[0]); target.add(p[2])
        if users & groups or users & cameras or groups & cameras: raise ValueError('entity roles must be disjoint')
        string(camera, 1, 20, r'[A-Za-z0-9_]+')
        if camera in users or camera in groups: raise ValueError('camera role')
    elif pid == DASH:
        city, locations = args
        char_grid(city, 'D X', 100000)
        array(locations, 0, 100000)
        for loc in locations:
            if type(loc) is not list or len(loc) != 2: raise ValueError('location')
            integer(loc[0], 0, len(city) - 1); integer(loc[1], 0, len(city[0]) - 1)
    elif pid in (MODE, MED):
        slices = args[0]
        array(slices, 1, 100)
        sizes = []
        for s in slices:
            array(s, 0, 200000)
            for v in s: integer(v, -10**9, 10**9)
            sizes.append(len(s))
        if sum(sizes) < 1 or sum(sizes) > 200000 or max(sizes) - min(sizes) > 1: raise ValueError('even partition')
    elif pid in (DEST1, DEST2):
        edges, start = args
        array(edges, 0, 100000)
        sources = set()
        for e in edges:
            if type(e) is not list or len(e) != 2: raise ValueError('edge')
            integer(e[0], 0, 10**9); integer(e[1], 0, 10**9)
            if pid == DEST1 and e[0] in sources: raise ValueError('out-degree at most one')
            sources.add(e[0])
        integer(start, 0, 10**9)
    elif pid == DUP1:
        _, total = tree(args[0], dup1_file, 10000, 200)
        if total > 200000: raise ValueError('total bytes')
    elif pid == DUP2:
        _, total = tree(args[0], dup2_file, 10000, 200)
        if total > 200000: raise ValueError('total bytes')
    elif pid == TRADE:
        array(args[0], 0, 100000)
        for o in args[0]:
            if type(o) is not list or len(o) != 3 or o[2] not in ('buy', 'sell'): raise ValueError('order')
            integer(o[0], 1, 10**9); integer(o[1], 1, 10**9)
    elif pid == SHOP:
        orders, target = args
        array(orders, 1, 10000)
        for o in orders:
            if type(o) is not list or len(o) != 2: raise ValueError('order')
            integer(o[0], 1, 10000); integer(o[1], 0, 10**9)
        integer(target, 0, 10**9)
    elif pid == MISS:
        s, t = args
        string(s, 1, 100000, r'[A-Za-z]+( [A-Za-z]+)*'); string(t, 0, 100000, r'([A-Za-z]+( [A-Za-z]+)*)?')
        words, i = s.split(' '), 0
        for w in (t.split(' ') if t else []):
            while i < len(words) and words[i] != w: i += 1
            if i == len(words): raise ValueError('t words must be a subsequence of s words')
            i += 1
    elif pid in (COM1, COM2):
        grid, modes, times, costs = args
        array(modes, 1, 9); array(times, len(modes), len(modes)); array(costs, len(modes), len(modes))
        for m in modes: string(m, 1, 10, r'[A-Za-z]+')
        if len(set(modes)) != len(modes): raise ValueError('distinct modes')
        for v in times: integer(v, 1, 10000)
        for v in costs: integer(v, 0, 10000)
        array(grid, 1, 100)
        char_grid(grid, 'SDX' + ''.join(str(d) for d in range(1, len(modes) + 1)), 10000)
        if len(grid[0]) > 100: raise ValueError('grid width')
        joined = ''.join(grid)
        if joined.count('S') != 1 or joined.count('D') != 1: raise ValueError('one S and one D')
    elif pid == ROBOT:
        board, distances = args
        array(board, 1, 100000)
        if type(board[0]) is not list or not board[0]: raise ValueError('board row')
        for row in board:
            if type(row) is not list or len(row) != len(board[0]): raise ValueError('board row')
            for c in row:
                if c not in ('O', 'E', 'X') or type(c) is not str: raise ValueError('board cell')
        if len(board) * len(board[0]) > 100000: raise ValueError('board area')
        array(distances, 4, 4)
        for d in distances: integer(d, 1, 100001)
    elif pid in (STOP1, STOP2):
        source, words = args
        if pid == STOP1: string(source, 0, 100000, r'[ -~]*')
        else:
            array(source, 0, 10000)
            for c in source: string(c, 0, 100, r'[ -~]*')
            if sum(len(c) for c in source) > 100000: raise ValueError('total stream')
        array(words, 0, 100)
        for w in words: string(w, 1, 50, r'[ -~]+')
    elif pid in (SOCK1, SOCK2):
        ids, colors, feet = args
        array(ids, 0, 100000); array(colors, len(ids), len(ids)); array(feet, len(ids), len(ids))
        for v in ids: integer(v, -10**9, 10**9)
        if len(set(ids)) != len(ids): raise ValueError('distinct ids')
        for c in colors: string(c, 1, 10, r'[a-z]+')
        for f in feet:
            if f not in ('left', 'right') or type(f) is not str: raise ValueError('foot')


def walk(root, path_of_root='/'):
    """Yield (path, file) for every file; paths joined with '/', root shown as '/'."""
    out, stack = [], [(root, '')]
    while stack:
        node, prefix = stack.pop()
        for f in node['files']: out.append((prefix + '/' + f['name'], f))
        for d in node['directories']: stack.append((d, prefix + '/' + d['name']))
    return out


def all_nodes(root):
    """Pre-order list of (kind, node, parent index)."""
    nodes, stack = [], [(root, -1)]
    while stack:
        node, parent = stack.pop()
        nodes.append(('dir', node, parent)); me = len(nodes) - 1
        for f in node['files']: nodes.append(('file', f, me))
        for d in reversed(node['directories']): stack.append((d, me))
    return nodes


def reference(pid, args):
    validate_domain(pid, args)
    if pid == BUF:
        # Stream-offset model: disk length after each op is the largest whole-capacity prefix (write) or the whole stream (flush).
        names, rows = args
        capacity, stream, disk, out = rows[0][0], [], 0, [None]
        for name, row in zip(names[1:], rows[1:]):
            if name == 'write':
                stream.extend(row[0]); new = disk + (len(stream) - disk) // capacity * capacity
            else: new = len(stream)
            out.append(stream[disk:new]); disk = new
        return out
    if pid in (ENC1, ENC2):
        nodes = all_nodes(args[0])
        if len(nodes) > (14 if pid == ENC1 else 9): raise ValueError('reference budget')
        target = [n[1]['isEncrypted'] if n[0] == 'file' else None for n in nodes]
        files = [i for i, n in enumerate(nodes) if n[0] == 'file']
        best = None
        for ops in product(*[((0, 1) if pid == ENC1 else (0, 1, 2)) for _ in nodes]):
            state = [False] * len(nodes)
            for i, n in enumerate(nodes):  # parents precede children in pre-order
                inherited = False if n[2] < 0 else state[n[2]]
                if pid == ENC1: state[i] = inherited or ops[i] == 1
                else: state[i] = inherited if ops[i] == 0 else ops[i] == 1
            if all(state[i] == target[i] for i in files):
                used = sum(1 for o in ops if o)
                best = used if best is None else min(best, used)
        return best
    if pid == FANCY:
        return bisect_left(FANCY_VALUES, args[0])
    if pid in (FILT1, FILT2):
        messages, words = args
        if pid == FILT1: unsafe = lambda text: any(w in text.split() for w in words)
        else: unsafe = lambda text: any(w in text for w in words)
        return [[m[0], m[1]] for m in messages if not unsafe(m[1])]
    if pid == CAM:
        perms, camera = args
        if len(perms) > 80: raise ValueError('reference budget')
        users = {p[0] for p in perms if p[1] in ('cameraOwner', 'groupMember')}
        admins = []
        for u in sorted(users):
            reach, changed = {u}, True
            while changed:  # forward closure by fixpoint over every triple
                changed = False
                for a, rel, b in perms:
                    if a in reach and b not in reach: reach.add(b); changed = True
            if camera in reach: admins.append(u)
        return admins
    if pid == DASH:
        city, locations = args
        if len(city) * len(city[0]) > 400: raise ValueError('reference budget')
        out = []
        for r, c in locations:
            if city[r][c] == 'X': out.append(-1); continue
            frontier, seen, dist, found = {(r, c)}, {(r, c)}, 0, -1
            while frontier and found < 0:
                if any(city[a][b] == 'D' for a, b in frontier): found = dist; break
                nxt = set()
                for a, b in frontier:
                    for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= x < len(city) and 0 <= y < len(city[0]) and city[x][y] != 'X' and (x, y) not in seen:
                            seen.add((x, y)); nxt.add((x, y))
                frontier, dist = nxt, dist + 1
            out.append(found)
        return out
    if pid == MODE:
        flat = sorted(v for s in args[0] for v in s)
        best, best_count, i = None, 0, 0
        while i < len(flat):
            j = i
            while j < len(flat) and flat[j] == flat[i]: j += 1
            if j - i > best_count: best, best_count = flat[i], j - i
            i = j
        return best
    if pid == MED:
        flat = sorted(v for s in args[0] for v in s)
        n = len(flat)
        value = Fraction(flat[(n - 1) // 2] + flat[n // 2], 2)
        return int(value) if value.denominator == 1 else float(value)
    if pid == DEST1:
        edges, start = args
        nxt = {u: v for u, v in edges}
        node = start
        for _ in range(len(edges) + 1):
            if node not in nxt: return node
            node = nxt[node]
        return -1
    if pid == DEST2:
        edges, start = args
        if len(edges) > 300: raise ValueError('reference budget')
        reach, changed = {start}, True
        while changed:
            changed = False
            for u, v in edges:
                if u in reach and v not in reach: reach.add(v); changed = True
        sources = {u for u, _ in edges}
        return sorted(x for x in reach if x not in sources)
    if pid in (DUP1, DUP2):
        files = walk(args[0])
        if len(files) > 300: raise ValueError('reference budget')
        content = [f['content'] if pid == DUP1 else [b for c in f['chunks'] for b in c] for _, f in files]
        parent = list(range(len(files)))
        def find(x):
            while parent[x] != x: x = parent[x]
            return x
        for i, j in combinations(range(len(files)), 2):
            if content[i] == content[j]: parent[find(i)] = find(j)
        groups = {}
        for i, (path, _) in enumerate(files): groups.setdefault(find(i), []).append(path)
        return sorted(sorted(g) for g in groups.values() if len(g) > 1)
    if pid == TRADE:
        orders = args[0]
        if len(orders) > 400: raise ValueError('reference budget')
        buys, sells, traded = [], [], 0
        for price, qty, kind in orders:
            book, mine = (sells, buys) if kind == 'buy' else (buys, sells)
            while qty:
                ok = [i for i, (p, _) in enumerate(book) if (p <= price if kind == 'buy' else p >= price)]
                if not ok: break
                i = min(ok, key=lambda k: book[k][0]) if kind == 'buy' else max(ok, key=lambda k: book[k][0])
                take = min(qty, book[i][1]); traded += take; qty -= take
                book[i] = (book[i][0], book[i][1] - take)
                if book[i][1] == 0: book.pop(i)
            if qty: mine.append((price, qty))
        return traded
    if pid == SHOP:
        orders, target = args
        if len(orders) > 60: raise ValueError('reference budget')
        seq = sorted(range(len(orders)), key=lambda i: (orders[i][1], i))
        for k in range(1, len(orders) + 1):
            free, total = [0] * k, 0
            for i in seq:
                d, a = orders[i]
                s = min(range(k), key=lambda x: free[x])
                free[s] = max(free[s], a) + d; total += free[s] - a
            if Fraction(total, len(orders)) <= target: return k
        return -1
    if pid == MISS:
        s, t = args[0].split(' '), (args[1].split(' ') if args[1] else [])
        if len(s) > 16: raise ValueError('reference budget')
        for chosen in combinations(range(len(s)), len(t)):  # lexicographic order: leftmost embedding first
            if [s[i] for i in chosen] == t:
                keep = set(chosen)
                return [w for i, w in enumerate(s) if i not in keep]
        raise ValueError('not a subsequence')
    if pid in (COM1, COM2):
        grid, modes, times, costs = args
        cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))]
        if len(cells) > 150: raise ValueError('reference budget')
        (sr, sc), = [x for x in cells if grid[x[0]][x[1]] == 'S']
        def relax(allowed):
            # Bellman-Ford over (time, cost) pairs; cost of a step = charge of the cell being left.
            inf = None; dist = {x: inf for x in cells}; dist[(sr, sc)] = (0, 0)
            for _ in range(len(cells)):
                for (r, c) in cells:
                    if dist[(r, c)] is None or grid[r][c] in 'XD' or not allowed(grid[r][c]): continue
                    ch = grid[r][c]
                    step = (0, 0) if ch == 'S' else (times[int(ch) - 1], costs[int(ch) - 1])
                    cand = (dist[(r, c)][0] + step[0], dist[(r, c)][1] + step[1])
                    for x, y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= x < len(grid) and 0 <= y < len(grid[0]) and grid[x][y] != 'X' and allowed(grid[x][y]):
                            if dist[(x, y)] is None or cand < dist[(x, y)]: dist[(x, y)] = cand
            (dr, dc), = [x for x in cells if grid[x[0]][x[1]] == 'D']
            return dist[(dr, dc)]
        if pid == COM2:
            got = relax(lambda ch: True)
            return [-1, -1] if got is None else [got[0], got[1]]
        best = None
        for m in range(len(modes)):
            got = relax(lambda ch, m=m: ch in 'SD' or ch == str(m + 1))
            if got is not None and (best is None or (got[0], got[1], m) < best): best = (got[0], got[1], m)
        return '' if best is None else modes[best[2]]
    if pid == ROBOT:
        board, want = args
        out = []
        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] != 'O': continue
                got = []
                for dr, dc in ((0, -1), (-1, 0), (1, 0), (0, 1)):  # left, top, bottom, right
                    k = 1
                    while 0 <= r + k * dr < len(board) and 0 <= c + k * dc < len(board[0]) and board[r + k * dr][c + k * dc] != 'X': k += 1
                    got.append(k)
                if got == want: out.append([r, c])
        return out
    if pid == STOP1:
        text, words = args
        for i in range(len(text) + 1):
            if any(text.startswith(w, i) for w in words): return text[:i]
        return text
    if pid == STOP2:
        chunks, words = args
        if sum(len(c) for c in chunks) > 3000: raise ValueError('reference budget')
        def safe(text, final):
            for i in range(len(text) + 1):
                if any(text.startswith(w, i) for w in words): return i, True
                if not final and any(len(text) - i < len(w) and w.startswith(text[i:]) and i < len(text) for w in words): return i, False
            return len(text), False
        out, emitted, text, stopped = [], 0, '', False
        for c in chunks + [None]:
            if stopped: out.append(''); continue
            final = c is None
            if not final: text += c
            pos, stopped = safe(text, final)
            out.append(text[emitted:pos]); emitted = pos
        return out
    if pid in (SOCK1, SOCK2):
        ids, colors, feet = args
        if len(ids) > 200: raise ValueError('reference budget')
        pool = sorted(zip(ids, colors, feet))
        pairs = []
        while True:  # repeatedly pair the globally smallest unpaired left id with the smallest same-colour right id
            lefts = [x for x in pool if x[2] == 'left' and any(y[2] == 'right' and y[1] == x[1] for y in pool)]
            if not lefts: break
            l = lefts[0]
            r = min(y for y in pool if y[2] == 'right' and y[1] == l[1])
            pairs.append([l[0], r[0]]); pool.remove(l); pool.remove(r)
        return len(pairs) if pid == SOCK1 else sorted(pairs)
    raise ValueError('unknown identity')
