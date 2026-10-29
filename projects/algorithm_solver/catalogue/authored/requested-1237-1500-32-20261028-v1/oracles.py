"""Independent brute-force and reference models; never import or execute candidate sources."""
from collections import Counter, deque
from functools import lru_cache

IDS = (
    1237, 1244, 1245, 1246, 1261, 1265, 1273, 1274,
    1278, 1286, 1302, 1315, 1348, 1352, 1357, 1367,
    1379, 1381, 1396, 1428, 1429, 1430, 1448, 1457,
    1469, 1472, 1474, 1476, 1483, 1485, 1490, 1500,
)

TRACE_CLASSES = {
    1244: ('Leaderboard', {'addScore': 2, 'top': 1, 'reset': 1}),
    1261: ('FindElements', {'find': 1}),
    1286: ('CombinationIterator', {'next': 0, 'hasNext': 0}),
    1348: ('TweetCounts', {'recordTweet': 2, 'getTweetCountsPerFrequency': 4}),
    1352: ('ProductOfNumbers', {'add': 1, 'getProduct': 1}),
    1357: ('Cashier', {'getBill': 2}),
    1381: ('CustomStack', {'push': 1, 'pop': 0, 'increment': 2}),
    1396: ('UndergroundSystem', {'checkIn': 3, 'checkOut': 3, 'getAverageTime': 2}),
    1429: ('FirstUnique', {'showFirstUnique': 0, 'add': 1}),
    1472: ('BrowserHistory', {'visit': 1, 'back': 1, 'forward': 1}),
    1476: ('SubrectangleQueries', {'updateSubrectangle': 5, 'getValue': 2}),
    1483: ('TreeAncestor', {'getKthAncestor': 2}),
    1500: ('FileSharing', {'join': 1, 'leave': 1, 'request': 2}),
}


def _is_int(v, low=None, high=None):
    if type(v) is not int:
        return False
    if low is not None and v < low:
        return False
    if high is not None and v > high:
        return False
    return True


def _build_bintree(arr, low=-10**5, high=10**5, max_nodes=10000):
    if type(arr) is not list:
        raise ValueError('tree must be list')
    if not arr:
        return None, 0
    if arr[0] is None or not _is_int(arr[0], low, high):
        raise ValueError('invalid root')
    root = {'val': arr[0], 'left': None, 'right': None}
    q = deque([root])
    i = 1
    count = 1
    while q and i < len(arr):
        node = q.popleft()
        for side in ('left', 'right'):
            if i < len(arr):
                v = arr[i]
                i += 1
                if v is not None:
                    if not _is_int(v, low, high):
                        raise ValueError('invalid node val')
                    child = {'val': v, 'left': None, 'right': None}
                    node[side] = child
                    q.append(child)
                    count += 1
                    if count > max_nodes:
                        raise ValueError('node limit exceeded')
    if i < len(arr):
        raise ValueError('dangling tree entries')
    return root, count


def _parse_nary(arr, max_nodes=10000):
    if type(arr) is not list:
        raise ValueError('nary must be list')
    if not arr:
        return None, 0
    if arr[0] is None or not _is_int(arr[0], 0, 10000):
        raise ValueError('invalid nary root')
    if len(arr) > 1 and arr[1] is not None:
        raise ValueError('missing null after nary root')
    root = {'val': arr[0], 'children': []}
    q = deque([root])
    i = 2
    count = 1
    while q and i < len(arr):
        parent = q.popleft()
        while i < len(arr) and arr[i] is not None:
            v = arr[i]
            if not _is_int(v, 0, 10000):
                raise ValueError('invalid nary val')
            child = {'val': v, 'children': []}
            parent['children'].append(child)
            q.append(child)
            count += 1
            if count > max_nodes:
                raise ValueError('too many nary nodes')
            i += 1
        i += 1
    return root, count


def _custom_f(fid, x, y):
    if fid == 1:
        return x + y
    if fid == 2:
        return x * y
    if fid == 3:
        return x * x + y
    if fid == 4:
        return x + y * y
    if fid == 5:
        return x * x + y * y
    if fid == 6:
        return (x + y) * (x + y)
    if fid == 7:
        return x * x * x + y * y * y
    if fid == 8:
        return x * x * y
    return x * y * y


def validate_domain(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:
        raise ValueError('invalid pid or args')

    if pid in TRACE_CLASSES:
        if len(args) != 2:
            raise ValueError('trace requires [ops, rows]')
        ops, rows = args
        cls_name, methods = TRACE_CLASSES[pid]
        if (type(ops) is not list or type(rows) is not list or not ops or
                len(ops) != len(rows) or ops[0] != cls_name or type(rows[0]) is not list):
            raise ValueError('invalid trace header')
        for op, row in zip(ops[1:], rows[1:]):
            if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
                raise ValueError(f'invalid op {op} for {pid}')
        if pid == 1244:
            if rows[0] != []:
                raise ValueError('1244 init empty')
            active = set()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addScore':
                    if not (_is_int(row[0], 1, 10000) and _is_int(row[1], 1, 100)):
                        raise ValueError('1244 invalid addScore')
                    active.add(row[0])
                elif op == 'top':
                    if not _is_int(row[0], 1, max(1, len(active))):
                        raise ValueError('1244 invalid top K')
                else:
                    if row[0] not in active:
                        raise ValueError('1244 reset unknown player')
        elif pid == 1261:
            if len(rows[0]) != 1:
                raise ValueError('1261 requires [root]')
            r, _ = _build_bintree(rows[0][0], -1, 10**6, 10000)
            if r is None:
                raise ValueError('1261 root non-empty')
            for op, row in zip(ops[1:], rows[1:]):
                if not _is_int(row[0], 0, 10**6):
                    raise ValueError('1261 invalid target')
        elif pid == 1286:
            if len(rows[0]) != 2:
                raise ValueError('1286 requires [characters, combinationLength]')
            chars, k = rows[0]
            if (type(chars) is not str or not (1 <= len(chars) <= 15) or
                    list(chars) != sorted(set(chars)) or not _is_int(k, 1, len(chars))):
                raise ValueError('1286 invalid init')
        elif pid == 1348:
            if rows[0] != []:
                raise ValueError('1348 empty init')
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'recordTweet':
                    if type(row[0]) is not str or not row[0] or not _is_int(row[1], 0, 10**9):
                        raise ValueError('1348 invalid recordTweet')
                else:
                    freq, name, st, et = row
                    if (freq not in ('minute', 'hour', 'day') or type(name) is not str or
                            not _is_int(st, 0, 10**9) or not _is_int(et, st, min(10**9, st + 10**4))):
                        raise ValueError('1348 invalid query')
        elif pid == 1352:
            if rows[0] != []:
                raise ValueError('1352 empty init')
            count = 0
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'add':
                    if not _is_int(row[0], 0, 100):
                        raise ValueError('1352 invalid add')
                    count += 1
                else:
                    if not _is_int(row[0], 1, count):
                        raise ValueError('1352 invalid k')
        elif pid == 1357:
            if len(rows[0]) != 4:
                raise ValueError('1357 requires [n, discount, products, prices]')
            n, disc, prods, prices = rows[0]
            if (not _is_int(n, 1, 10**4) or not _is_int(disc, 0, 100) or
                    type(prods) is not list or type(prices) is not list or
                    not (1 <= len(prods) <= 200) or len(prods) != len(prices)):
                raise ValueError('1357 invalid init')
        elif pid == 1381:
            if len(rows[0]) != 1 or not _is_int(rows[0][0], 1, 1000):
                raise ValueError('1381 invalid maxSize')
        elif pid == 1396:
            if rows[0] != []:
                raise ValueError('1396 empty init')
        elif pid == 1429:
            if (len(rows[0]) != 1 or type(rows[0][0]) is not list or
                    not (1 <= len(rows[0][0]) <= 10**5) or
                    not all(_is_int(x, 1, 10**8) for x in rows[0][0])):
                raise ValueError('1429 invalid init')
        elif pid == 1472:
            if len(rows[0]) != 1 or type(rows[0][0]) is not str or not (1 <= len(rows[0][0]) <= 20):
                raise ValueError('1472 invalid homepage')
        elif pid == 1476:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 100):
                raise ValueError('1476 invalid rectangle')
        elif pid == 1483:
            if len(rows[0]) != 2:
                raise ValueError('1483 requires [n, parent]')
            n, parent = rows[0]
            if not _is_int(n, 1, 50000) or type(parent) is not list or len(parent) != n or parent[0] != -1:
                raise ValueError('1483 invalid tree')
        elif pid == 1500:
            if len(rows[0]) != 1 or not _is_int(rows[0][0], 1, 100):
                raise ValueError('1500 invalid m')
        return

    if pid == 1237:
        if len(args) != 2 or not _is_int(args[0], 1, 9) or not _is_int(args[1], 1, 100):
            raise ValueError('1237 invalid function_id or z')
    elif pid == 1245:
        if len(args) != 1 or type(args[0]) is not list or len(args[0]) > 10000:
            raise ValueError('1245 invalid edges')
        n = len(args[0]) + 1
        for e in args[0]:
            if type(e) is not list or len(e) != 2 or not (_is_int(e[0], 0, n - 1) and _is_int(e[1], 0, n - 1)):
                raise ValueError('1245 invalid edge')
    elif pid == 1246:
        if (len(args) != 1 or type(args[0]) is not list or
                not (1 <= len(args[0]) <= 100) or not all(_is_int(x, 1, 20) for x in args[0])):
            raise ValueError('1246 invalid arr')
    elif pid == 1265:
        if (len(args) != 1 or type(args[0]) is not list or
                not (1 <= len(args[0]) <= 1000) or not all(_is_int(x, -1000, 1000) for x in args[0])):
            raise ValueError('1265 invalid head')
    elif pid == 1273:
        if len(args) != 3:
            raise ValueError('1273 requires [nodes, parent, value]')
        nodes, parent, value = args
        if (not _is_int(nodes, 1, 10000) or type(parent) is not list or type(value) is not list or
                len(parent) != nodes or len(value) != nodes or parent[0] != -1):
            raise ValueError('1273 invalid args')
    elif pid == 1274:
        if len(args) != 3:
            raise ValueError('1274 requires [ships, topRight, bottomLeft]')
        ships, tr, bl = args
        if (type(ships) is not list or len(ships) > 10 or
                type(tr) is not list or type(bl) is not list or len(tr) != 2 or len(bl) != 2 or
                not (0 <= bl[0] <= tr[0] <= 1000 and 0 <= bl[1] <= tr[1] <= 1000)):
            raise ValueError('1274 invalid bounds')
    elif pid == 1278:
        if (len(args) != 2 or type(args[0]) is not str or not (1 <= len(args[0]) <= 100) or
                not _is_int(args[1], 1, len(args[0]))):
            raise ValueError('1278 invalid s, k')
    elif pid in (1302, 1315, 1448, 1457, 1469):
        if len(args) != 1:
            raise ValueError(f'{pid} requires [root]')
        low, high = (-10**4, 10**4) if pid == 1448 else ((1, 9) if pid == 1457 else (1, 10000))
        r, _ = _build_bintree(args[0], low, high, 100000)
        if r is None:
            raise ValueError(f'{pid} tree must be non-empty')
    elif pid == 1367:
        if len(args) != 2 or type(args[0]) is not list or not (1 <= len(args[0]) <= 100):
            raise ValueError('1367 invalid head')
        r, _ = _build_bintree(args[1], 1, 100, 2500)
        if r is None:
            raise ValueError('1367 empty root')
    elif pid == 1379:
        if len(args) != 2:
            raise ValueError('1379 requires [tree, target]')
        r, _ = _build_bintree(args[0], 1, 10**5, 10000)
        if r is None or not _is_int(args[1], 1, 10**5):
            raise ValueError('1379 invalid args')
    elif pid == 1428:
        if len(args) != 1 or type(args[0]) is not list or not (1 <= len(args[0]) <= 100):
            raise ValueError('1428 invalid mat')
        mat = args[0]
        cols = len(mat[0])
        for row in mat:
            if type(row) is not list or len(row) != cols or row != sorted(row) or not all(x in (0, 1) for x in row):
                raise ValueError('1428 row must be non-decreasing binary')
    elif pid == 1430:
        if len(args) != 2 or type(args[1]) is not list or not (1 <= len(args[1]) <= 5000):
            raise ValueError('1430 invalid args')
        r, _ = _build_bintree(args[0], 0, 9, 5000)
        if r is None:
            raise ValueError('1430 empty tree')
    elif pid == 1474:
        if (len(args) != 3 or type(args[0]) is not list or not (1 <= len(args[0]) <= 10000) or
                not _is_int(args[1], 1, 1000) or not _is_int(args[2], 1, 1000)):
            raise ValueError('1474 invalid args')
    elif pid == 1485:
        if len(args) != 1 or type(args[0]) is not list or len(args[0]) > 1000:
            raise ValueError('1485 invalid tree')
        for item in args[0]:
            if item is not None:
                if (type(item) is not list or len(item) != 2 or
                        not _is_int(item[0], 1, 10**6) or
                        (item[1] is not None and not _is_int(item[1], 0, len(args[0]) - 1))):
                    raise ValueError('1485 invalid node entry')
    elif pid == 1490:
        if len(args) != 1:
            raise ValueError('1490 requires [root]')
        _parse_nary(args[0], 10000)


def reference(pid, args):
    validate_domain(pid, args)

    if pid in TRACE_CLASSES:
        ops, rows = args
        out = [None]
        if pid == 1244:
            scores = Counter()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addScore':
                    scores[row[0]] += row[1]
                    out.append(None)
                elif op == 'top':
                    out.append(sum(sorted(scores.values(), reverse=True)[:row[0]]))
                else:
                    scores.pop(row[0], None)
                    out.append(None)
            return out
        if pid == 1261:
            root, _ = _build_bintree(rows[0][0], -1, 10**6, 10000)
            vals = set()
            def recover(n, v):
                if n is not None:
                    vals.add(v)
                    recover(n['left'], 2 * v + 1)
                    recover(n['right'], 2 * v + 2)
            recover(root, 0)
            for op, row in zip(ops[1:], rows[1:]):
                out.append(row[0] in vals)
            return out
        if pid == 1286:
            import itertools
            chars, k = rows[0]
            combos = [''.join(c) for c in itertools.combinations(chars, k)]
            idx = 0
            for op in ops[1:]:
                if op == 'next':
                    out.append(combos[idx])
                    idx += 1
                else:
                    out.append(idx < len(combos))
            return out
        if pid == 1348:
            tweets = {}
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'recordTweet':
                    tweets.setdefault(row[0], []).append(row[1])
                    out.append(None)
                else:
                    freq, name, st, et = row
                    delta = {'minute': 60, 'hour': 3600, 'day': 86400}[freq]
                    buckets = [0] * (((et - st) // delta) + 1)
                    for t in tweets.get(name, ()):
                        if st <= t <= et:
                            buckets[(t - st) // delta] += 1
                    out.append(buckets)
            return out
        if pid == 1352:
            nums = []
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'add':
                    nums.append(row[0])
                    out.append(None)
                else:
                    p = 1
                    for v in nums[-row[0]:]:
                        p *= v
                    out.append(p)
            return out
        if pid == 1357:
            n, disc, prods, prices = rows[0]
            price_map = dict(zip(prods, prices))
            cnt = 0
            for op, row in zip(ops[1:], rows[1:]):
                cnt += 1
                prod, amt = row
                total = sum(price_map[p] * a for p, a in zip(prod, amt))
                if cnt % n == 0:
                    total = total * (100 - disc) / 100.0
                else:
                    total = float(total)
                out.append(total)
            return out
        if pid == 1381:
            cap = rows[0][0]
            stk = []
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'push':
                    if len(stk) < cap:
                        stk.append(row[0])
                    out.append(None)
                elif op == 'pop':
                    out.append(stk.pop() if stk else -1)
                else:
                    k, val = row
                    for i in range(min(k, len(stk))):
                        stk[i] += val
                    out.append(None)
            return out
        if pid == 1396:
            cin = {}
            stats = {}
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'checkIn':
                    cin[row[0]] = (row[1], row[2])
                    out.append(None)
                elif op == 'checkOut':
                    st, t0 = cin.pop(row[0])
                    pair = stats.setdefault((st, row[1]), [0, 0])
                    pair[0] += row[2] - t0
                    pair[1] += 1
                    out.append(None)
                else:
                    tot, cnt = stats[(row[0], row[1])]
                    out.append(tot / float(cnt))
            return out
        if pid == 1429:
            counts = Counter(rows[0][0])
            order = list(rows[0][0])
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'add':
                    counts[row[0]] += 1
                    order.append(row[0])
                    out.append(None)
                else:
                    ans = -1
                    for v in order:
                        if counts[v] == 1:
                            ans = v
                            break
                    out.append(ans)
            return out
        if pid == 1472:
            hist = [rows[0][0]]
            cur = 0
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'visit':
                    hist = hist[:cur + 1] + [row[0]]
                    cur += 1
                    out.append(None)
                elif op == 'back':
                    cur = max(0, cur - row[0])
                    out.append(hist[cur])
                else:
                    cur = min(len(hist) - 1, cur + row[0])
                    out.append(hist[cur])
            return out
        if pid == 1476:
            mat = [list(r) for r in rows[0][0]]
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'updateSubrectangle':
                    r1, c1, r2, c2, v = row
                    for r in range(r1, r2 + 1):
                        for c in range(c1, c2 + 1):
                            mat[r][c] = v
                    out.append(None)
                else:
                    out.append(mat[row[0]][row[1]])
            return out
        if pid == 1483:
            n, parent = rows[0]
            for op, row in zip(ops[1:], rows[1:]):
                curr, k = row
                while curr != -1 and k > 0:
                    curr = parent[curr]
                    k -= 1
                out.append(curr)
            return out
        if pid == 1500:
            m = rows[0][0]
            user_chunks = {}
            active_ids = set()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'join':
                    uid = 1
                    while uid in active_ids:
                        uid += 1
                    active_ids.add(uid)
                    user_chunks[uid] = set(row[0])
                    out.append(uid)
                elif op == 'leave':
                    active_ids.discard(row[0])
                    user_chunks.pop(row[0], None)
                    out.append(None)
                else:
                    uid, cid = row
                    owners = sorted(u for u, chs in user_chunks.items() if cid in chs)
                    if owners:
                        user_chunks[uid].add(cid)
                    out.append(owners)
            return out

    if pid == 1237:
        fid, z = args
        return [[x, y] for x in range(1, 1001) for y in range(1, 1001) if _custom_f(fid, x, y) == z]

    if pid == 1245:
        edges = args[0]
        if not edges:
            return 0
        n = len(edges) + 1
        adj = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        def bfs(start):
            dist = [-1] * n
            dist[start] = 0
            q = deque([start])
            far = start
            while q:
                u = q.popleft()
                if dist[u] > dist[far]:
                    far = u
                for v in adj[u]:
                    if dist[v] == -1:
                        dist[v] = dist[u] + 1
                        q.append(v)
            return far, dist[far]
        u, _ = bfs(0)
        _, diam = bfs(u)
        return diam

    if pid == 1246:
        arr = tuple(args[0])
        @lru_cache(None)
        def dp(i, j):
            if i > j:
                return 0
            if i == j:
                return 1
            res = 1 + dp(i + 1, j)
            if arr[i] == arr[i + 1]:
                res = min(res, 1 + dp(i + 2, j))
            for k in range(i + 2, j + 1):
                if arr[i] == arr[k]:
                    res = min(res, dp(i + 1, k - 1) + dp(k + 1, j))
            return res
        return dp(0, len(arr) - 1)

    if pid == 1265:
        return list(reversed(args[0]))

    if pid == 1273:
        nodes, parent, value = args
        children = [[] for _ in range(nodes)]
        for i in range(1, nodes):
            children[parent[i]].append(i)
        def dfs(u):
            total_sum = value[u]
            total_cnt = 1
            for v in children[u]:
                s, c = dfs(v)
                total_sum += s
                total_cnt += c
            return (0, 0) if total_sum == 0 else (total_sum, total_cnt)
        return dfs(0)[1]

    if pid == 1274:
        ships, tr, bl = args
        return sum(bl[0] <= x <= tr[0] and bl[1] <= y <= tr[1] for x, y in ships)

    if pid == 1278:
        s, k = args
        n = len(s)
        @lru_cache(None)
        def solve_dp(idx, rem):
            if rem == 1:
                sub = s[idx:]
                return sum(sub[i] != sub[-1 - i] for i in range(len(sub) // 2))
            best = n
            for end in range(idx + 1, n - rem + 2):
                sub = s[idx:end]
                c = sum(sub[i] != sub[-1 - i] for i in range(len(sub) // 2))
                best = min(best, c + solve_dp(end, rem - 1))
            return best
        return solve_dp(0, k)

    if pid == 1302:
        root, _ = _build_bintree(args[0], 1, 10000, 100000)
        q = deque([root])
        last_sum = 0
        while q:
            last_sum = sum(n['val'] for n in q)
            for _ in range(len(q)):
                node = q.popleft()
                if node['left']:
                    q.append(node['left'])
                if node['right']:
                    q.append(node['right'])
        return last_sum

    if pid == 1315:
        root, _ = _build_bintree(args[0], 1, 10000, 100000)
        def walk(n, p, gp):
            if n is None:
                return 0
            cur = n['val'] if gp is not None and gp % 2 == 0 else 0
            return cur + walk(n['left'], n['val'], p) + walk(n['right'], n['val'], p)
        return walk(root, None, None)

    if pid == 1367:
        head, tree_arr = args
        root, _ = _build_bintree(tree_arr, 1, 100, 2500)
        def match(node, idx):
            if idx == len(head):
                return True
            if node is None or node['val'] != head[idx]:
                return False
            return match(node['left'], idx + 1) or match(node['right'], idx + 1)
        def visit(node):
            if node is None:
                return False
            return match(node, 0) or visit(node['left']) or visit(node['right'])
        return visit(root)

    if pid == 1379:
        return args[1]

    if pid == 1428:
        mat = args[0]
        best = -1
        for c in range(len(mat[0])):
            if any(row[c] == 1 for row in mat):
                return c
        return best

    if pid == 1430:
        tree_arr, seq = args
        root, _ = _build_bintree(tree_arr, 0, 9, 5000)
        def check(node, idx):
            if node is None or idx >= len(seq) or node['val'] != seq[idx]:
                return False
            if node['left'] is None and node['right'] is None:
                return idx == len(seq) - 1
            return check(node['left'], idx + 1) or check(node['right'], idx + 1)
        return check(root, 0)

    if pid == 1448:
        root, _ = _build_bintree(args[0], -10**4, 10**4, 100000)
        def dfs(node, mx):
            if node is None:
                return 0
            good = 1 if node['val'] >= mx else 0
            nmx = max(mx, node['val'])
            return good + dfs(node['left'], nmx) + dfs(node['right'], nmx)
        return dfs(root, root['val'])

    if pid == 1457:
        root, _ = _build_bintree(args[0], 1, 9, 100000)
        def dfs(node, mask):
            if node is None:
                return 0
            mask ^= 1 << node['val']
            if node['left'] is None and node['right'] is None:
                return 1 if (mask & (mask - 1)) == 0 else 0
            return dfs(node['left'], mask) + dfs(node['right'], mask)
        return dfs(root, 0)

    if pid == 1469:
        root, _ = _build_bintree(args[0], 1, 10000, 100000)
        out = []
        def dfs(node):
            if node is None:
                return
            if node['left'] is not None and node['right'] is None:
                out.append(node['left']['val'])
            elif node['right'] is not None and node['left'] is None:
                out.append(node['right']['val'])
            dfs(node['left'])
            dfs(node['right'])
        dfs(root)
        return out

    if pid == 1474:
        head, m, n = args
        out = []
        i = 0
        while i < len(head):
            out.extend(head[i:i + m])
            i += m + n
        return out

    if pid == 1485:
        return [None if item is None else [item[0], item[1]] for item in args[0]]

    if pid == 1490:
        return list(args[0])
