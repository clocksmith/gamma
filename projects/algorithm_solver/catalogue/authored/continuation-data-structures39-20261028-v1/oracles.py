"""Independent brute-force and reference models; never import or execute candidate sources."""
from collections import Counter, deque
from functools import lru_cache
import itertools
import json
import math

IDS = (
    295, 297, 303, 304, 307, 321, 328, 341, 352, 355,
    374, 380, 381, 382, 384, 385, 398, 420, 427, 429,
    430, 432, 449, 460, 466, 470, 478, 479, 480, 483,
    488, 497, 519, 528, 535, 558, 559, 572, 587,
)

TRACE_CLASSES = {
    295: ('MedianFinder', {'addNum': 1, 'findMedian': 0}),
    303: ('NumArray', {'sumRange': 2}),
    304: ('NumMatrix', {'sumRegion': 4}),
    307: ('NumArray', {'update': 2, 'sumRange': 2}),
    341: ('NestedIterator', {'next': 0, 'hasNext': 0}),
    352: ('SummaryRanges', {'addNum': 1, 'getIntervals': 0}),
    355: ('Twitter', {'postTweet': 2, 'getNewsFeed': 1, 'follow': 2, 'unfollow': 2}),
    380: ('RandomizedSet', {'insert': 1, 'remove': 1, 'getRandom': 0}),
    381: ('RandomizedCollection', {'insert': 1, 'remove': 1, 'getRandom': 0}),
    382: ('Solution', {'getRandom': 0}),
    384: ('Solution', {'reset': 0, 'shuffle': 0}),
    398: ('Solution', {'pick': 1}),
    432: ('AllOne', {'inc': 1, 'dec': 1, 'getMaxKey': 0, 'getMinKey': 0}),
    460: ('LFUCache', {'get': 1, 'put': 2}),
    478: ('Solution', {'randPoint': 0}),
    497: ('Solution', {'pick': 0}),
    519: ('Solution', {'flip': 0, 'reset': 0}),
    528: ('Solution', {'pickIndex': 0}),
}


class _LCG:
    def __init__(self, seed=0x9E3779B9):
        self.state = seed & 0xFFFFFFFF

    def next_u32(self):
        self.state = (self.state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.state

    def randrange(self, n):
        return self.next_u32() % n

    def random(self):
        return self.next_u32() / 4294967296.0


def _is_int(v, low=None, high=None):
    if type(v) is not int:
        return False
    if low is not None and v < low:
        return False
    if high is not None and v > high:
        return False
    return True


def _is_num(v, low=None, high=None):
    if type(v) not in (int, float) or isinstance(v, bool):
        return False
    if low is not None and v < low:
        return False
    if high is not None and v > high:
        return False
    return True


def _validate_nested_list(item, allow_top_empty=False):
    if type(item) is int:
        if not (-10**6 <= item <= 10**6):
            raise ValueError('nested integer out of range')
        return 1
    if type(item) is list:
        total = 0
        for sub in item:
            total += _validate_nested_list(sub, allow_top_empty=True)
        return total
    raise ValueError('invalid nested list element')


def _build_bintree(arr, low=-1000, high=1000, max_nodes=10000):
    if type(arr) is not list:
        raise ValueError('tree array must be list')
    if not arr:
        return None, 0
    if arr[0] is None or not _is_int(arr[0], low, high):
        raise ValueError('invalid root value')
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
                        raise ValueError('invalid tree node value')
                    child = {'val': v, 'left': None, 'right': None}
                    node[side] = child
                    q.append(child)
                    count += 1
                    if count > max_nodes:
                        raise ValueError('too many tree nodes')
    if i < len(arr):
        raise ValueError('dangling tree values')
    return root, count


def _serialize_bintree(root):
    if root is None:
        return []
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append(node['val'])
            q.append(node['left'])
            q.append(node['right'])
    while out and out[-1] is None:
        out.pop()
    return out


def _is_valid_bst(node, low, high):
    if node is None:
        return True
    if not (low < node['val'] < high):
        return False
    return _is_valid_bst(node['left'], low, node['val']) and _is_valid_bst(node['right'], node['val'], high)


def _parse_nary(arr, max_nodes=10000):
    if type(arr) is not list:
        raise ValueError('nary tree must be list')
    if not arr:
        return None, 0
    if arr[0] is None or not _is_int(arr[0], 0, 10000):
        raise ValueError('invalid nary root')
    if len(arr) > 1 and arr[1] is not None:
        raise ValueError('missing separator after nary root')
    root = {'val': arr[0], 'children': []}
    q = deque([root])
    i = 2
    count = 1
    while q and i < len(arr):
        parent = q.popleft()
        while i < len(arr) and arr[i] is not None:
            v = arr[i]
            if not _is_int(v, 0, 10000):
                raise ValueError('invalid nary value')
            child = {'val': v, 'children': []}
            parent['children'].append(child)
            q.append(child)
            count += 1
            if count > max_nodes:
                raise ValueError('nary node limit exceeded')
            i += 1
        i += 1
    if i < len(arr):
        raise ValueError('dangling nary entries')
    return root, count


def _parse_multilevel(arr):
    if type(arr) is not list:
        raise ValueError('multilevel list must be list')
    if not arr:
        return []
    for v in arr:
        if v is not None and not _is_int(v, 1, 10**5):
            raise ValueError('invalid multilevel value')
    nodes = []
    i = 0
    n = len(arr)
    while i < n and arr[i] is not None:
        nodes.append({'val': arr[i], 'next': None, 'child': None})
        i += 1
    if not nodes:
        raise ValueError('leading null in multilevel list')
    for j in range(len(nodes) - 1):
        nodes[j]['next'] = nodes[j + 1]
    curr = nodes[0]
    i += 1
    total = len(nodes)
    while i < n:
        while i < n and arr[i] is None:
            if curr is None:
                raise ValueError('null advance past end of level')
            curr = curr['next']
            i += 1
        if i >= n:
            break
        if curr is None:
            raise ValueError('child attached to missing node')
        chain = []
        while i < n and arr[i] is not None:
            chain.append({'val': arr[i], 'next': None, 'child': None})
            i += 1
        total += len(chain)
        if total > 1000:
            raise ValueError('too many multilevel nodes')
        for j in range(len(chain) - 1):
            chain[j]['next'] = chain[j + 1]
        curr['child'] = chain[0]
        curr = chain[0]
        i += 1
    return nodes[0]


def _deserialize_quadtree(data):
    if type(data) is not list or not data:
        raise ValueError('quadtree must be non-empty list')
    def make_node(item):
        if (type(item) is not list or len(item) != 2 or
                item[0] not in (0, 1) or item[1] not in (0, 1) or
                type(item[0]) is not int or type(item[1]) is not int):
            raise ValueError('invalid quadtree entry')
        return {'isLeaf': item[0] == 1, 'val': item[1] == 1, 'tl': None, 'tr': None, 'bl': None, 'br': None}
    root = make_node(data[0])
    q = deque([root])
    i = 1
    while q and i < len(data):
        curr = q.popleft()
        for side in ('tl', 'tr', 'bl', 'br'):
            if i < len(data):
                item = data[i]
                i += 1
                if item is not None:
                    if curr['isLeaf']:
                        raise ValueError('leaf cannot have children in quadtree')
                    child = make_node(item)
                    curr[side] = child
                    q.append(child)
    if i < len(data):
        raise ValueError('dangling quadtree nodes')
    def check_complete(node, depth=0):
        if depth > 6:
            raise ValueError('quadtree depth exceeded')
        if node['isLeaf']:
            return 0
        sub = []
        for side in ('tl', 'tr', 'bl', 'br'):
            if node[side] is None:
                raise ValueError('internal quadtree node missing child')
            sub.append(check_complete(node[side], depth + 1))
        return 1 + max(sub)
    depth = check_complete(root)
    return root, depth


def _serialize_quadtree(root):
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append([1 if node['isLeaf'] else 0, 1 if node['val'] else 0])
            q.append(node['tl'])
            q.append(node['tr'])
            q.append(node['bl'])
            q.append(node['br'])
    while out and out[-1] is None:
        out.pop()
    return out


def _quadtree_from_grid(grid, r0, c0, size):
    first = grid[r0][c0]
    uniform = True
    for r in range(r0, r0 + size):
        for c in range(c0, c0 + size):
            if grid[r][c] != first:
                uniform = False
                break
        if not uniform:
            break
    if uniform:
        return {'isLeaf': True, 'val': first == 1, 'tl': None, 'tr': None, 'bl': None, 'br': None}
    half = size // 2
    return {
        'isLeaf': False,
        'val': True,
        'tl': _quadtree_from_grid(grid, r0, c0, half),
        'tr': _quadtree_from_grid(grid, r0, c0 + half, half),
        'bl': _quadtree_from_grid(grid, r0 + half, c0, half),
        'br': _quadtree_from_grid(grid, r0 + half, c0 + half, half),
    }


def _quadtree_to_grid(node, size):
    if node['isLeaf']:
        v = 1 if node['val'] else 0
        return [[v] * size for _ in range(size)]
    half = size // 2
    tl = _quadtree_to_grid(node['tl'], half)
    tr = _quadtree_to_grid(node['tr'], half)
    bl = _quadtree_to_grid(node['bl'], half)
    br = _quadtree_to_grid(node['br'], half)
    grid = []
    for r in range(half):
        grid.append(tl[r] + tr[r])
    for r in range(half):
        grid.append(bl[r] + br[r])
    return grid


def validate_domain(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:
        raise ValueError('invalid pid or args container')

    if pid in TRACE_CLASSES:
        if len(args) != 2:
            raise ValueError('trace problem requires [operation_names, argument_lists]')
        ops, rows = args
        cls_name, methods = TRACE_CLASSES[pid]
        if (type(ops) is not list or type(rows) is not list or
                not ops or len(ops) != len(rows) or ops[0] != cls_name or type(rows[0]) is not list):
            raise ValueError('invalid trace header')
        for op, row in zip(ops[1:], rows[1:]):
            if type(op) is not str or op not in methods or type(row) is not list or len(row) != methods[op]:
                raise ValueError(f'invalid method call {op} for {pid}')

        if pid == 295:
            if rows[0] != [] or len(ops) > 50001:
                raise ValueError('invalid 295 constructor or length')
            added = 0
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addNum':
                    if not _is_int(row[0], -10**5, 10**5):
                        raise ValueError('295 addNum out of range')
                    added += 1
                elif added == 0:
                    raise ValueError('295 findMedian on empty stream')
        elif pid == 303:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 10**4):
                raise ValueError('303 invalid nums')
            nums = rows[0][0]
            if not all(_is_int(x, -10**5, 10**5) for x in nums) or len(ops) > 10001:
                raise ValueError('303 nums elements out of range')
            for op, row in zip(ops[1:], rows[1:]):
                if not (_is_int(row[0], 0, len(nums) - 1) and _is_int(row[1], row[0], len(nums) - 1)):
                    raise ValueError('303 sumRange bounds invalid')
        elif pid == 304:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 200):
                raise ValueError('304 invalid matrix')
            mat = rows[0][0]
            m = len(mat)
            if type(mat[0]) is not list or not (1 <= len(mat[0]) <= 200):
                raise ValueError('304 invalid cols')
            n = len(mat[0])
            for r in mat:
                if type(r) is not list or len(r) != n or not all(_is_int(x, -10**4, 10**4) for x in r):
                    raise ValueError('304 invalid row')
            for op, row in zip(ops[1:], rows[1:]):
                r1, c1, r2, c2 = row
                if not (_is_int(r1, 0, m - 1) and _is_int(r2, r1, m - 1) and
                        _is_int(c1, 0, n - 1) and _is_int(c2, c1, n - 1)):
                    raise ValueError('304 sumRegion bounds invalid')
        elif pid == 307:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 30000):
                raise ValueError('307 invalid nums')
            nums = rows[0][0]
            if not all(_is_int(x, -100, 100) for x in nums) or len(ops) > 30001:
                raise ValueError('307 element range invalid')
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'update':
                    if not (_is_int(row[0], 0, len(nums) - 1) and _is_int(row[1], -100, 100)):
                        raise ValueError('307 update bounds invalid')
                else:
                    if not (_is_int(row[0], 0, len(nums) - 1) and _is_int(row[1], row[0], len(nums) - 1)):
                        raise ValueError('307 sumRange bounds invalid')
        elif pid == 341:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 500):
                raise ValueError('341 invalid nestedList')
            flat = []
            def collect(items):
                for x in items:
                    if type(x) is int:
                        if not (-10**6 <= x <= 10**6):
                            raise ValueError('341 int out of bounds')
                        flat.append(x)
                    elif type(x) is list:
                        collect(x)
                    else:
                        raise ValueError('341 invalid item')
            collect(rows[0][0])
            idx = 0
            for op in ops[1:]:
                if op == 'next':
                    if idx >= len(flat):
                        raise ValueError('341 next past end')
                    idx += 1
        elif pid == 352:
            if rows[0] != [] or len(ops) > 30001:
                raise ValueError('352 invalid header')
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addNum' and not _is_int(row[0], 0, 10**4):
                    raise ValueError('352 value out of range')
        elif pid == 355:
            if rows[0] != [] or len(ops) > 30001:
                raise ValueError('355 invalid header')
            tweets = set()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'postTweet':
                    if not (_is_int(row[0], 1, 500) and _is_int(row[1], 0, 10**4)) or row[1] in tweets:
                        raise ValueError('355 invalid postTweet')
                    tweets.add(row[1])
                elif op == 'getNewsFeed':
                    if not _is_int(row[0], 1, 500):
                        raise ValueError('355 invalid userId')
                else:
                    if not (_is_int(row[0], 1, 500) and _is_int(row[1], 1, 500)) or row[0] == row[1]:
                        raise ValueError('355 invalid follow/unfollow')
        elif pid in (380, 381):
            if rows[0] != [] or len(ops) > 200001:
                raise ValueError('380/381 invalid header')
            counts = Counter()
            total = 0
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'insert':
                    if not _is_int(row[0], -2**31, 2**31 - 1):
                        raise ValueError('insert val out of bounds')
                    if pid == 380:
                        if counts[row[0]] == 0:
                            counts[row[0]] = 1
                            total += 1
                    else:
                        counts[row[0]] += 1
                        total += 1
                elif op == 'remove':
                    if not _is_int(row[0], -2**31, 2**31 - 1):
                        raise ValueError('remove val out of bounds')
                    if counts[row[0]] > 0:
                        counts[row[0]] -= 1
                        total -= 1
                elif total == 0:
                    raise ValueError('getRandom on empty collection')
        elif pid == 382:
            if (len(rows[0]) != 1 or type(rows[0][0]) is not list or
                    not (1 <= len(rows[0][0]) <= 10**4) or
                    not all(_is_int(x, -10**4, 10**4) for x in rows[0][0])):
                raise ValueError('382 invalid head')
        elif pid == 384:
            if (len(rows[0]) != 1 or type(rows[0][0]) is not list or
                    not (1 <= len(rows[0][0]) <= 50) or
                    not all(_is_int(x, -10**6, 10**6) for x in rows[0][0]) or
                    len(set(rows[0][0])) != len(rows[0][0])):
                raise ValueError('384 invalid nums')
        elif pid == 398:
            if (len(rows[0]) != 1 or type(rows[0][0]) is not list or
                    not (1 <= len(rows[0][0]) <= 20000) or
                    not all(_is_int(x, -2**31, 2**31 - 1) for x in rows[0][0])):
                raise ValueError('398 invalid nums')
            present = set(rows[0][0])
            for op, row in zip(ops[1:], rows[1:]):
                if not _is_int(row[0], -2**31, 2**31 - 1) or row[0] not in present:
                    raise ValueError('398 target not in nums')
        elif pid == 432:
            if rows[0] != [] or len(ops) > 50001:
                raise ValueError('432 invalid header')
            counts = Counter()
            for op, row in zip(ops[1:], rows[1:]):
                if op in ('inc', 'dec'):
                    k = row[0]
                    if type(k) is not str or not (1 <= len(k) <= 10) or not all('a' <= c <= 'z' for c in k):
                        raise ValueError('432 invalid key')
                    if op == 'inc':
                        counts[k] += 1
                    else:
                        if counts[k] <= 0:
                            raise ValueError('432 dec on missing key')
                        counts[k] -= 1
        elif pid == 460:
            if len(rows[0]) != 1 or not _is_int(rows[0][0], 1, 10**4) or len(ops) > 200001:
                raise ValueError('460 invalid capacity')
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'get':
                    if not _is_int(row[0], 0, 10**5):
                        raise ValueError('460 invalid get key')
                else:
                    if not (_is_int(row[0], 0, 10**5) and _is_int(row[1], 0, 10**9)):
                        raise ValueError('460 invalid put args')
        elif pid == 478:
            if (len(rows[0]) != 3 or not _is_num(rows[0][0], 1e-9, 10**8) or
                    not _is_num(rows[0][1], -10**7, 10**7) or not _is_num(rows[0][2], -10**7, 10**7)):
                raise ValueError('478 invalid circle params')
        elif pid == 497:
            if len(rows[0]) != 1 or type(rows[0][0]) is not list or not (1 <= len(rows[0][0]) <= 100):
                raise ValueError('497 invalid rects')
            rects = rows[0][0]
            for r in rects:
                if (type(r) is not list or len(r) != 4 or
                        not all(_is_int(x, -10**9, 10**9) for x in r) or r[0] > r[2] or r[1] > r[3]):
                    raise ValueError('497 invalid rect')
        elif pid == 519:
            if len(rows[0]) != 2 or not (_is_int(rows[0][0], 1, 10**4) and _is_int(rows[0][1], 1, 10**4)):
                raise ValueError('519 invalid m, n')
            cap = rows[0][0] * rows[0][1]
            used = 0
            for op in ops[1:]:
                if op == 'flip':
                    used += 1
                    if used > cap:
                        raise ValueError('519 flip exceeds matrix size')
                else:
                    used = 0
        elif pid == 528:
            if (len(rows[0]) != 1 or type(rows[0][0]) is not list or
                    not (1 <= len(rows[0][0]) <= 10**4) or
                    not all(_is_int(x, 1, 10**5) for x in rows[0][0])):
                raise ValueError('528 invalid weights')
        return

    if pid == 297:
        if len(args) != 1:
            raise ValueError('297 requires [root]')
        _build_bintree(args[0], -1000, 1000, 10000)
    elif pid == 321:
        if len(args) != 3:
            raise ValueError('321 requires [nums1, nums2, k]')
        nums1, nums2, k = args
        if (type(nums1) is not list or type(nums2) is not list or
                not (1 <= len(nums1) <= 500) or not (1 <= len(nums2) <= 500) or
                not all(_is_int(x, 0, 9) for x in nums1) or
                not all(_is_int(x, 0, 9) for x in nums2) or
                not _is_int(k, 1, len(nums1) + len(nums2))):
            raise ValueError('321 invalid domain')
    elif pid == 328:
        if (len(args) != 1 or type(args[0]) is not list or len(args[0]) > 10**4 or
                not all(_is_int(x, -10**6, 10**6) for x in args[0])):
            raise ValueError('328 invalid head')
    elif pid == 374:
        if len(args) != 2 or not _is_int(args[0], 1, 2**31 - 1) or not _is_int(args[1], 1, args[0]):
            raise ValueError('374 invalid n, pick')
    elif pid == 385:
        if len(args) != 1 or type(args[0]) is not str or not (1 <= len(args[0]) <= 50000):
            raise ValueError('385 invalid string')
        try:
            parsed = json.loads(args[0])
        except Exception as exc:
            raise ValueError('385 invalid json syntax') from exc
        _validate_nested_list(parsed)
    elif pid == 420:
        if len(args) != 1 or type(args[0]) is not str or not (1 <= len(args[0]) <= 50):
            raise ValueError('420 invalid password length')
        for ch in args[0]:
            if not (ch.isalnum() or ch in '.!'):
                raise ValueError('420 invalid char')
    elif pid == 427:
        if len(args) != 1 or type(args[0]) is not list or not args[0]:
            raise ValueError('427 invalid grid')
        grid = args[0]
        n = len(grid)
        if n not in (1, 2, 4, 8, 16, 32, 64):
            raise ValueError('427 grid size must be power of 2 in 1..64')
        for row in grid:
            if type(row) is not list or len(row) != n or not all(type(x) is int and x in (0, 1) for x in row):
                raise ValueError('427 invalid grid row')
    elif pid in (429, 559):
        if len(args) != 1:
            raise ValueError('429/559 requires [root]')
        _parse_nary(args[0], 10000)
    elif pid == 430:
        if len(args) != 1:
            raise ValueError('430 requires [head]')
        _parse_multilevel(args[0])
    elif pid == 449:
        if len(args) != 1:
            raise ValueError('449 requires [root]')
        root, _ = _build_bintree(args[0], 0, 10000, 10000)
        if not _is_valid_bst(root, -1, 10001):
            raise ValueError('449 input is not a valid BST')
    elif pid == 466:
        if len(args) != 4:
            raise ValueError('466 requires [s1, n1, s2, n2]')
        s1, n1, s2, n2 = args
        if (type(s1) is not str or type(s2) is not str or
                not (1 <= len(s1) <= 100) or not (1 <= len(s2) <= 100) or
                not all('a' <= c <= 'z' for c in s1) or not all('a' <= c <= 'z' for c in s2) or
                not _is_int(n1, 1, 10**6) or not _is_int(n2, 1, 10**6)):
            raise ValueError('466 invalid domain')
    elif pid == 470:
        if (len(args) != 1 or type(args[0]) is not list or len(args[0]) < 2 or len(args[0]) % 2 != 0 or
                len(args[0]) > 10**5 or not all(_is_int(x, 1, 7) for x in args[0])):
            raise ValueError('470 invalid rand7 stream')
        stream = args[0]
        if not any((stream[i] - 1) * 7 + stream[i + 1] <= 40 for i in range(0, len(stream), 2)):
            raise ValueError('470 stream has no accepted rejection-sampling pair')
    elif pid == 479:
        if len(args) != 1 or not _is_int(args[0], 1, 8):
            raise ValueError('479 invalid n')
    elif pid == 480:
        if len(args) != 2 or type(args[0]) is not list:
            raise ValueError('480 requires [nums, k]')
        nums, k = args
        if (not (1 <= len(nums) <= 10**5) or not _is_int(k, 1, len(nums)) or
                not all(_is_int(x, -2**31, 2**31 - 1) for x in nums)):
            raise ValueError('480 invalid domain')
    elif pid == 483:
        if len(args) != 1 or type(args[0]) is not str or not args[0].isdigit():
            raise ValueError('483 requires digit string')
        v = int(args[0])
        if not (3 <= v <= 10**18) or str(v) != args[0]:
            raise ValueError('483 value out of range')
    elif pid == 488:
        if len(args) != 2 or type(args[0]) is not str or type(args[1]) is not str:
            raise ValueError('488 requires [board, hand]')
        board, hand = args
        if (not (1 <= len(board) <= 16) or not (1 <= len(hand) <= 5) or
                not all(c in 'RYBGW' for c in board) or not all(c in 'RYBGW' for c in hand)):
            raise ValueError('488 invalid board or hand')
    elif pid == 535:
        if len(args) != 1 or type(args[0]) is not str or not (1 <= len(args[0]) <= 10**4):
            raise ValueError('535 invalid url')
    elif pid == 558:
        if len(args) != 2:
            raise ValueError('558 requires [quadTree1, quadTree2]')
        _deserialize_quadtree(args[0])
        _deserialize_quadtree(args[1])
    elif pid == 572:
        if len(args) != 2:
            raise ValueError('572 requires [root, subRoot]')
        r1, c1 = _build_bintree(args[0], -10**4, 10**4, 2000)
        r2, c2 = _build_bintree(args[1], -10**4, 10**4, 1000)
        if r1 is None or r2 is None:
            raise ValueError('572 trees must be non-empty')
    elif pid == 587:
        if len(args) != 1 or type(args[0]) is not list or not (1 <= len(args[0]) <= 3000):
            raise ValueError('587 invalid trees')
        seen = set()
        for pt in args[0]:
            if (type(pt) is not list or len(pt) != 2 or
                    not (_is_int(pt[0], 0, 100) and _is_int(pt[1], 0, 100)) or
                    (pt[0], pt[1]) in seen):
                raise ValueError('587 invalid or duplicate point')
            seen.add((pt[0], pt[1]))


def reference(pid, args):
    validate_domain(pid, args)

    if pid in TRACE_CLASSES:
        ops, rows = args
        out = [None]
        if pid == 295:
            stream = []
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addNum':
                    stream.append(row[0])
                    out.append(None)
                else:
                    s = sorted(stream)
                    m = len(s)
                    out.append(float(s[m // 2]) if m % 2 == 1 else (s[m // 2 - 1] + s[m // 2]) / 2.0)
            return out
        if pid == 303:
            nums = list(rows[0][0])
            for op, row in zip(ops[1:], rows[1:]):
                out.append(sum(nums[row[0]:row[1] + 1]))
            return out
        if pid == 304:
            mat = [list(r) for r in rows[0][0]]
            for op, row in zip(ops[1:], rows[1:]):
                r1, c1, r2, c2 = row
                out.append(sum(mat[r][c] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)))
            return out
        if pid == 307:
            nums = list(rows[0][0])
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'update':
                    nums[row[0]] = row[1]
                    out.append(None)
                else:
                    out.append(sum(nums[row[0]:row[1] + 1]))
            return out
        if pid == 341:
            flat = []
            def flatten(items):
                for x in items:
                    if type(x) is int:
                        flat.append(x)
                    else:
                        flatten(x)
            flatten(rows[0][0])
            cursor = 0
            for op in ops[1:]:
                if op == 'hasNext':
                    out.append(cursor < len(flat))
                else:
                    out.append(flat[cursor])
                    cursor += 1
            return out
        if pid == 352:
            seen = set()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'addNum':
                    seen.add(row[0])
                    out.append(None)
                else:
                    vals = sorted(seen)
                    intervals = []
                    for v in vals:
                        if not intervals or intervals[-1][1] + 1 < v:
                            intervals.append([v, v])
                        else:
                            intervals[-1][1] = v
                    out.append(intervals)
            return out
        if pid == 355:
            posts = []
            follows = set()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'postTweet':
                    posts.append((row[0], row[1]))
                    out.append(None)
                elif op == 'follow':
                    follows.add((row[0], row[1]))
                    out.append(None)
                elif op == 'unfollow':
                    follows.discard((row[0], row[1]))
                    out.append(None)
                else:
                    u = row[0]
                    feed = [tid for author, tid in reversed(posts) if author == u or (u, author) in follows][:10]
                    out.append(feed)
            return out
        if pid == 380:
            rng = _LCG()
            vals = []
            pos = {}
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'insert':
                    v = row[0]
                    if v in pos:
                        out.append(False)
                    else:
                        pos[v] = len(vals)
                        vals.append(v)
                        out.append(True)
                elif op == 'remove':
                    v = row[0]
                    if v not in pos:
                        out.append(False)
                    else:
                        idx = pos.pop(v)
                        last = vals.pop()
                        if idx < len(vals):
                            vals[idx] = last
                            pos[last] = idx
                        out.append(True)
                else:
                    out.append(vals[rng.randrange(len(vals))])
            return out
        if pid == 381:
            rng = _LCG()
            vals = []
            pos = {}
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'insert':
                    v = row[0]
                    bucket = pos.setdefault(v, [])
                    is_new = len(bucket) == 0
                    bucket.append(len(vals))
                    vals.append([v, len(bucket) - 1])
                    out.append(is_new)
                elif op == 'remove':
                    v = row[0]
                    bucket = pos.get(v)
                    if not bucket:
                        out.append(False)
                    else:
                        idx = bucket.pop()
                        last_val, last_slot = vals.pop()
                        if idx < len(vals):
                            vals[idx] = [last_val, last_slot]
                            pos[last_val][last_slot] = idx
                        out.append(True)
                else:
                    out.append(vals[rng.randrange(len(vals))][0])
            return out
        if pid == 382:
            rng = _LCG()
            vals = list(rows[0][0])
            for _ in ops[1:]:
                out.append(vals[rng.randrange(len(vals))])
            return out
        if pid == 384:
            rng = _LCG()
            orig = list(rows[0][0])
            for op in ops[1:]:
                if op == 'reset':
                    out.append(list(orig))
                else:
                    arr = list(orig)
                    for i in range(len(arr) - 1, 0, -1):
                        j = rng.randrange(i + 1)
                        arr[i], arr[j] = arr[j], arr[i]
                    out.append(arr)
            return out
        if pid == 398:
            rng = _LCG()
            indices = {}
            for idx, v in enumerate(rows[0][0]):
                indices.setdefault(v, []).append(idx)
            for op, row in zip(ops[1:], rows[1:]):
                bucket = indices[row[0]]
                out.append(bucket[rng.randrange(len(bucket))])
            return out
        if pid == 432:
            counts = Counter()
            for op, row in zip(ops[1:], rows[1:]):
                if op == 'inc':
                    counts[row[0]] += 1
                    out.append(None)
                elif op == 'dec':
                    counts[row[0]] -= 1
                    if counts[row[0]] == 0:
                        del counts[row[0]]
                    out.append(None)
                elif op == 'getMaxKey':
                    if not counts:
                        out.append('')
                    else:
                        m = max(counts.values())
                        out.append(min(k for k, c in counts.items() if c == m))
                else:
                    if not counts:
                        out.append('')
                    else:
                        m = min(counts.values())
                        out.append(min(k for k, c in counts.items() if c == m))
            return out
        if pid == 460:
            cap = rows[0][0]
            store = {}
            tick = 0
            for op, row in zip(ops[1:], rows[1:]):
                tick += 1
                if op == 'get':
                    k = row[0]
                    if k not in store:
                        out.append(-1)
                    else:
                        val, freq, _ = store[k]
                        store[k] = (val, freq + 1, tick)
                        out.append(val)
                else:
                    k, val = row
                    if k in store:
                        _, freq, _ = store[k]
                        store[k] = (val, freq + 1, tick)
                    else:
                        if len(store) == cap:
                            victim = min(store.items(), key=lambda kv: (kv[1][1], kv[1][2]))[0]
                            del store[victim]
                        store[k] = (val, 1, tick)
                    out.append(None)
            return out
        if pid == 478:
            rng = _LCG()
            radius, xc, yc = rows[0]
            for _ in ops[1:]:
                while True:
                    dx = 2.0 * rng.random() - 1.0
                    dy = 2.0 * rng.random() - 1.0
                    if dx * dx + dy * dy <= 1.0:
                        out.append([xc + radius * dx, yc + radius * dy])
                        break
            return out
        if pid == 497:
            rng = _LCG()
            rects = rows[0][0]
            prefix = []
            total = 0
            for x1, y1, x2, y2 in rects:
                total += (x2 - x1 + 1) * (y2 - y1 + 1)
                prefix.append(total)
            for _ in ops[1:]:
                t = rng.randrange(total)
                idx = 0
                while prefix[idx] <= t:
                    idx += 1
                base = 0 if idx == 0 else prefix[idx - 1]
                offset = t - base
                x1, y1, x2, y2 = rects[idx]
                w = x2 - x1 + 1
                out.append([x1 + offset % w, y1 + offset // w])
            return out
        if pid == 519:
            rng = _LCG()
            m, n = rows[0]
            total = m * n
            swapped = {}
            for op in ops[1:]:
                if op == 'flip':
                    r = rng.randrange(total)
                    total -= 1
                    idx = swapped.get(r, r)
                    swapped[r] = swapped.get(total, total)
                    out.append([idx // n, idx % n])
                else:
                    total = m * n
                    swapped.clear()
                    out.append(None)
            return out
        if pid == 528:
            rng = _LCG()
            prefix = []
            total = 0
            for w in rows[0][0]:
                total += w
                prefix.append(total)
            for _ in ops[1:]:
                target = rng.randrange(total) + 1
                idx = 0
                while prefix[idx] < target:
                    idx += 1
                out.append(idx)
            return out

    if pid in (297, 449):
        root, _ = _build_bintree(args[0], -1000 if pid == 297 else 0, 1000 if pid == 297 else 10000, 10000)
        return _serialize_bintree(root)

    if pid == 321:
        nums1, nums2, k = args
        m, n = len(nums1), len(nums2)
        @lru_cache(None)
        def dp(i, j, rem):
            if rem == 0:
                return ()
            if (m - i) + (n - j) < rem:
                return None
            best = None
            if i < m:
                skip1 = dp(i + 1, j, rem)
                if skip1 is not None and (best is None or skip1 > best):
                    best = skip1
                sub1 = dp(i + 1, j, rem - 1)
                if sub1 is not None:
                    cand1 = (nums1[i],) + sub1
                    if best is None or cand1 > best:
                        best = cand1
            if j < n:
                skip2 = dp(i, j + 1, rem)
                if skip2 is not None and (best is None or skip2 > best):
                    best = skip2
                sub2 = dp(i, j + 1, rem - 1)
                if sub2 is not None:
                    cand2 = (nums2[j],) + sub2
                    if best is None or cand2 > best:
                        best = cand2
            return best
        return list(dp(0, 0, k))

    if pid == 328:
        head = args[0]
        return [head[i] for i in range(0, len(head), 2)] + [head[i] for i in range(1, len(head), 2)]

    if pid == 374:
        return args[1]

    if pid == 385:
        return json.loads(args[0])

    if pid == 420:
        s = args[0]
        n = len(s)
        has_lower = any('a' <= c <= 'z' for c in s)
        has_upper = any('A' <= c <= 'Z' for c in s)
        has_digit = any('0' <= c <= '9' for c in s)
        missing = (0 if has_lower else 1) + (0 if has_upper else 1) + (0 if has_digit else 1)
        runs = []
        i = 0
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            if j - i >= 3:
                runs.append(j - i)
            i = j
        if n < 6:
            return max(6 - n, missing)
        if n <= 20:
            return max(missing, sum(r // 3 for r in runs))
        deletes = n - 20
        rem = deletes
        for mod in (0, 1, 2):
            for idx in range(len(runs)):
                if rem <= 0:
                    break
                if runs[idx] < 3 or runs[idx] % 3 != mod:
                    continue
                need = 1 if mod == 0 else (2 if mod == 1 else 3)
                if mod < 2:
                    if rem >= need:
                        runs[idx] -= need
                        rem -= need
                else:
                    while runs[idx] >= 3 and rem >= 3:
                        runs[idx] -= 3
                        rem -= 3
        for idx in range(len(runs)):
            while runs[idx] >= 3 and rem >= 3:
                runs[idx] -= 3
                rem -= 3
        return deletes + max(missing, sum(r // 3 for r in runs if r >= 3))

    if pid == 427:
        grid = args[0]
        return _serialize_quadtree(_quadtree_from_grid(grid, 0, 0, len(grid)))

    if pid == 429:
        root, _ = _parse_nary(args[0], 10000)
        if root is None:
            return []
        levels = []
        def dfs(node, d):
            if d == len(levels):
                levels.append([])
            levels[d].append(node['val'])
            for ch in node['children']:
                dfs(ch, d + 1)
        dfs(root, 0)
        return levels

    if pid == 430:
        head = _parse_multilevel(args[0])
        if not head:
            return []
        out = []
        def walk(node):
            while node is not None:
                out.append(node['val'])
                if node['child'] is not None:
                    walk(node['child'])
                node = node['next']
        walk(head)
        return out

    if pid == 466:
        s1, n1, s2, n2 = args
        if not set(s2).issubset(set(s1)):
            return 0
        if len(s1) * n1 <= 20000:
            j = 0
            for _ in range(n1):
                for ch in s1:
                    if ch == s2[j % len(s2)]:
                        j += 1
            return (j // len(s2)) // n2
        seen = {}
        history = []
        j = 0
        for block in range(1, n1 + 1):
            for ch in s1:
                if ch == s2[j % len(s2)]:
                    j += 1
            rem = j % len(s2)
            history.append(j)
            if rem in seen:
                prev_block = seen[rem]
                prev_j = history[prev_block - 1]
                cycle_blocks = block - prev_block
                cycle_j = j - prev_j
                remaining = n1 - block
                full_cycles = remaining // cycle_blocks
                tail = remaining % cycle_blocks
                total_j = j + full_cycles * cycle_j + (history[prev_block - 1 + tail] - prev_j)
                return (total_j // len(s2)) // n2
            seen[rem] = block
        return (j // len(s2)) // n2

    if pid == 470:
        stream = args[0]
        for i in range(0, len(stream), 2):
            idx = (stream[i] - 1) * 7 + stream[i + 1]
            if idx <= 40:
                return (idx - 1) % 10 + 1
        raise ValueError('no accepted sample')

    if pid == 479:
        n = args[0]
        if n == 1:
            return 9
        upper = 10**n - 1
        lower = 10**(n - 1)
        for left in range(upper, lower - 1, -1):
            s = str(left)
            pal = int(s + s[::-1])
            d = upper
            while d * d >= pal:
                if pal % d == 0 and lower <= pal // d <= upper:
                    return pal % 1337
                d -= 1
        raise ValueError('palindrome not found')

    if pid == 480:
        nums, k = args
        out = []
        for i in range(len(nums) - k + 1):
            w = sorted(nums[i:i + k])
            out.append((w[k // 2] + w[(k - 1) // 2]) / 2.0)
        return out

    if pid == 483:
        N = int(args[0])
        if N <= 200000:
            for k in range(2, N):
                tmp = N
                ok = True
                while tmp > 0:
                    if tmp % k != 1:
                        ok = False
                        break
                    tmp //= k
                if ok:
                    return str(k)
            return str(N - 1)
        max_m = N.bit_length()
        for m in range(max_m, 1, -1):
            k = int(round(N ** (1.0 / m)))
            for cand in (k - 1, k, k + 1):
                if cand >= 2 and (cand**(m + 1) - 1) == N * (cand - 1):
                    return str(cand)
        return str(N - 1)

    if pid == 488:
        board0, hand0 = args
        def collapse(s):
            changed = True
            while changed:
                changed = False
                i = 0
                while i < len(s):
                    j = i
                    while j < len(s) and s[j] == s[i]:
                        j += 1
                    if j - i >= 3:
                        s = s[:i] + s[j:]
                        changed = True
                        break
                    i = j
            return s
        start_hand = ''.join(sorted(hand0))
        q = deque([(collapse(board0), start_hand, 0)])
        visited = {(collapse(board0), start_hand)}
        while q:
            b, h, steps = q.popleft()
            if not b:
                return steps
            if not h:
                continue
            for hi, ch in enumerate(h):
                if hi > 0 and h[hi] == h[hi - 1]:
                    continue
                nh = h[:hi] + h[hi + 1:]
                for bi in range(len(b) + 1):
                    if bi > 0 and b[bi - 1] == ch:
                        continue
                    pick = False
                    if bi < len(b) and b[bi] == ch:
                        pick = True
                    elif 0 < bi < len(b) and b[bi - 1] == b[bi] and b[bi] != ch:
                        pick = True
                    if not pick:
                        continue
                    nb = collapse(b[:bi] + ch + b[bi:])
                    if not nb:
                        return steps + 1
                    state = (nb, nh)
                    if state not in visited:
                        visited.add(state)
                        q.append((nb, nh, steps + 1))
        return -1

    if pid == 535:
        return args[0]

    if pid == 558:
        q1, d1 = _deserialize_quadtree(args[0])
        q2, d2 = _deserialize_quadtree(args[1])
        size = 1 << max(d1, d2)
        g1 = _quadtree_to_grid(q1, size)
        g2 = _quadtree_to_grid(q2, size)
        merged = [[g1[r][c] | g2[r][c] for c in range(size)] for r in range(size)]
        return _serialize_quadtree(_quadtree_from_grid(merged, 0, 0, size))

    if pid == 559:
        root, _ = _parse_nary(args[0], 10000)
        if root is None:
            return 0
        def depth(node):
            return 1 + max((depth(ch) for ch in node['children']), default=0)
        return depth(root)

    if pid == 572:
        r1, _ = _build_bintree(args[0], -10**4, 10**4, 2000)
        r2, _ = _build_bintree(args[1], -10**4, 10**4, 1000)
        def same(a, b):
            if a is None or b is None:
                return a is b
            return a['val'] == b['val'] and same(a['left'], b['left']) and same(a['right'], b['right'])
        def has_sub(node):
            if node is None:
                return False
            return same(node, r2) or has_sub(node['left']) or has_sub(node['right'])
        return has_sub(r1)

    if pid == 587:
        pts = sorted(tuple(p) for p in args[0])
        if len(pts) <= 3:
            return [list(p) for p in pts]
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        if all(cross(pts[0], pts[1], r) == 0 for r in pts):
            return [list(p) for p in pts]
        hull = set()
        for i, a in enumerate(pts):
            for j, b in enumerate(pts):
                if i == j:
                    continue
                if all(cross(a, b, r) >= 0 for r in pts):
                    for r in pts:
                        if cross(a, b, r) == 0:
                            hull.add(r)
        return [list(p) for p in sorted(hull)]
