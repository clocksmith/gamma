"""Source-free reference models and domain validation for requested-243-370-35."""

from collections import Counter, defaultdict, deque
import heapq
import math

PROBLEM_IDS = (
    243, 245, 246, 247, 248, 249, 250, 254, 255, 256,
    259, 265, 267, 269, 270, 272, 276, 296, 298, 302,
    311, 314, 317, 320, 325, 333, 340, 351, 356, 358,
    360, 361, 366, 369, 370,
)


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _tree_from_level(values):
    if not values or values[0] is None:
        return None
    nodes = [None if v is None else [v, None, None] for v in values]
    kids = nodes[::-1]
    root = kids.pop()
    for node in nodes:
        if node is not None:
            if kids:
                node[1] = kids.pop()
            if kids:
                node[2] = kids.pop()
    return root


def validate_domain(problem_id: int, *args) -> None:
    if problem_id in (243, 245):
        (wordsDict, word1, word2) = args
        if not isinstance(wordsDict, list) or len(wordsDict) < 2 or not isinstance(word1, str) or not isinstance(word2, str):
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 246:
        (num,) = args
        if not isinstance(num, str) or not (1 <= len(num) <= 50):
            raise ValueError("invalid 246")
    elif problem_id == 247:
        (n,) = args
        if not _is_int(n) or not (1 <= n <= 14):
            raise ValueError("invalid 247")
    elif problem_id == 248:
        (low, high) = args
        if not isinstance(low, str) or not isinstance(high, str) or int(low) > int(high):
            raise ValueError("invalid 248")
    elif problem_id == 249:
        (strings,) = args
        if not isinstance(strings, list) or not strings:
            raise ValueError("invalid 249")
    elif problem_id in (250, 298, 314, 333, 366):
        (root,) = args
        if not isinstance(root, list):
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 254:
        (n,) = args
        if not _is_int(n) or not (1 <= n <= 10**7):
            raise ValueError("invalid 254")
    elif problem_id == 255:
        (preorder,) = args
        if not isinstance(preorder, list) or not preorder:
            raise ValueError("invalid 255")
    elif problem_id in (256, 265):
        (costs,) = args
        if not isinstance(costs, list) or not costs or not costs[0]:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 259:
        (nums, target) = args
        if not isinstance(nums, list) or not _is_int(target):
            raise ValueError("invalid 259")
    elif problem_id == 267:
        (s,) = args
        if not isinstance(s, str) or not (1 <= len(s) <= 16):
            raise ValueError("invalid 267")
    elif problem_id == 269:
        (words,) = args
        if not isinstance(words, list) or not words:
            raise ValueError("invalid 269")
    elif problem_id == 270:
        (root, target) = args
        if not isinstance(root, list) or not root or not isinstance(target, (int, float)):
            raise ValueError("invalid 270")
    elif problem_id == 272:
        (root, target, k) = args
        if not isinstance(root, list) or not root or not isinstance(target, (int, float)) or not _is_int(k):
            raise ValueError("invalid 272")
    elif problem_id == 276:
        (n, k) = args
        if not _is_int(n) or not _is_int(k) or n < 1 or k < 1:
            raise ValueError("invalid 276")
    elif problem_id in (296, 317, 361):
        (grid,) = args
        if not isinstance(grid, list) or not grid or not grid[0]:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 302:
        (image, x, y) = args
        if not isinstance(image, list) or not image or not _is_int(x) or not _is_int(y):
            raise ValueError("invalid 302")
    elif problem_id == 311:
        (mat1, mat2) = args
        if not isinstance(mat1, list) or not isinstance(mat2, list) or len(mat1[0]) != len(mat2):
            raise ValueError("invalid 311")
    elif problem_id == 320:
        (word,) = args
        if not isinstance(word, str) or not (1 <= len(word) <= 15):
            raise ValueError("invalid 320")
    elif problem_id == 325:
        (nums, k) = args
        if not isinstance(nums, list) or not nums or not _is_int(k):
            raise ValueError("invalid 325")
    elif problem_id in (340, 358):
        (s, k) = args
        if not isinstance(s, str) or not s or not _is_int(k) or k < 0:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 351:
        (m, n) = args
        if not _is_int(m) or not _is_int(n) or not (1 <= m <= n <= 9):
            raise ValueError("invalid 351")
    elif problem_id == 356:
        (points,) = args
        if not isinstance(points, list) or not points:
            raise ValueError("invalid 356")
    elif problem_id == 360:
        (nums, a, b, c) = args
        if not isinstance(nums, list) or not nums:
            raise ValueError("invalid 360")
    elif problem_id == 369:
        (head,) = args
        if not isinstance(head, list) or not head:
            raise ValueError("invalid 369")
    elif problem_id == 370:
        (length, updates) = args
        if not _is_int(length) or length < 1 or not isinstance(updates, list):
            raise ValueError("invalid 370")
    else:
        raise KeyError(f"Unknown problem_id: {problem_id}")


def ref_243(wordsDict, word1: str, word2: str) -> int:
    validate_domain(243, wordsDict, word1, word2)
    i1 = i2 = -1
    ans = len(wordsDict)
    for i, w in enumerate(wordsDict):
        if w == word1:
            i1 = i
            if i2 != -1:
                ans = min(ans, i1 - i2)
        elif w == word2:
            i2 = i
            if i1 != -1:
                ans = min(ans, i2 - i1)
    return ans


def ref_245(wordsDict, word1: str, word2: str) -> int:
    validate_domain(245, wordsDict, word1, word2)
    same = word1 == word2
    i1 = i2 = -1
    ans = len(wordsDict)
    for i, w in enumerate(wordsDict):
        if same:
            if w == word1:
                if i1 != -1:
                    ans = min(ans, i - i1)
                i1 = i
        else:
            if w == word1:
                i1 = i
                if i2 != -1:
                    ans = min(ans, i1 - i2)
            elif w == word2:
                i2 = i
                if i1 != -1:
                    ans = min(ans, i2 - i1)
    return ans


def ref_246(num: str) -> bool:
    validate_domain(246, num)
    mp = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    l, r = 0, len(num) - 1
    while l <= r:
        if num[l] not in mp or mp[num[l]] != num[r]:
            return False
        l += 1
        r -= 1
    return True


def ref_247(n: int):
    validate_domain(247, n)
    pairs = (("0", "0"), ("1", "1"), ("6", "9"), ("8", "8"), ("9", "6"))

    def build(rem: int, total: int):
        if rem == 0:
            return [""]
        if rem == 1:
            return ["0", "1", "8"]
        mids = build(rem - 2, total)
        res = []
        for s in mids:
            for a, b in pairs:
                if rem == total and a == "0":
                    continue
                res.append(a + s + b)
        return sorted(res)

    return build(n, n)


def ref_248(low: str, high: str) -> int:
    validate_domain(248, low, high)
    pairs = (("0", "0"), ("1", "1"), ("6", "9"), ("8", "8"), ("9", "6"))
    ln_lo, ln_hi = len(low), len(high)
    count = 0
    for length in range(ln_lo, ln_hi + 1):
        cur = [""] if length % 2 == 0 else ["0", "1", "8"]
        rem = length - (length % 2)
        while rem > 0:
            is_outer = rem == 2
            nxt = []
            for s in cur:
                for a, b in pairs:
                    if is_outer and length > 1 and a == "0":
                        continue
                    nxt.append(a + s + b)
            cur = nxt
            rem -= 2
        for s in cur:
            if (len(s) > ln_lo or s >= low) and (len(s) < ln_hi or s <= high):
                count += 1
    return count


def ref_249(strings):
    validate_domain(249, strings)
    groups = defaultdict(list)
    for s in strings:
        base = ord(s[0])
        key = tuple((ord(c) - base) % 26 for c in s)
        groups[key].append(s)
    return list(groups.values())


def ref_250(root) -> int:
    validate_domain(250, root)
    tree = _tree_from_level(root)
    cnt = 0

    def dfs(node):
        nonlocal cnt
        if node is None:
            return True
        ok_l = dfs(node[1])
        ok_r = dfs(node[2])
        if not (ok_l and ok_r):
            return False
        if node[1] is not None and node[1][0] != node[0]:
            return False
        if node[2] is not None and node[2][0] != node[0]:
            return False
        cnt += 1
        return True

    dfs(tree)
    return cnt


def ref_254(n: int):
    validate_domain(254, n)
    res = []
    path = []

    def dfs(rem: int, start: int):
        d = start
        while d * d <= rem:
            if rem % d == 0:
                res.append(path + [d, rem // d])
                path.append(d)
                dfs(rem // d, d)
                path.pop()
            d += 1

    dfs(n, 2)
    return res


def ref_255(preorder) -> bool:
    validate_domain(255, preorder)
    stack = []
    low = -(10**18)
    for x in preorder:
        if x < low:
            return False
        while stack and stack[-1] < x:
            low = stack.pop()
        stack.append(x)
    return True


def ref_256(costs) -> int:
    validate_domain(256, costs)
    r, b, g = 0, 0, 0
    for c0, c1, c2 in costs:
        r, b, g = c0 + min(b, g), c1 + min(r, g), c2 + min(r, b)
    return min(r, b, g)


def ref_259(nums, target: int) -> int:
    validate_domain(259, nums, target)
    arr = sorted(nums)
    n = len(arr)
    ans = 0
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            if arr[i] + arr[lo] + arr[hi] < target:
                ans += hi - lo
                lo += 1
            else:
                hi -= 1
    return ans


def ref_265(costs) -> int:
    validate_domain(265, costs)
    k = len(costs[0])
    dp = list(costs[0])
    for row in costs[1:]:
        min1 = min2 = 10**18
        idx1 = -1
        for j, v in enumerate(dp):
            if v < min1:
                min2 = min1
                min1 = v
                idx1 = j
            elif v < min2:
                min2 = v
        dp = [row[j] + (min2 if j == idx1 else min1) for j in range(k)]
    return min(dp)


def ref_267(s: str):
    validate_domain(267, s)
    cnt = Counter(s)
    odds = [ch for ch, c in cnt.items() if c & 1]
    if len(odds) > 1:
        return []
    mid = odds[0] if odds else ""
    half = sorted(ch for ch, c in cnt.items() for _ in range(c // 2))
    m = len(half)
    used = [False] * m
    res = []
    cur = []

    def backtrack():
        if len(cur) == m:
            left = "".join(cur)
            res.append(left + mid + left[::-1])
            return
        for i in range(m):
            if used[i]:
                continue
            if i > 0 and half[i] == half[i - 1] and not used[i - 1]:
                continue
            used[i] = True
            cur.append(half[i])
            backtrack()
            cur.pop()
            used[i] = False

    backtrack()
    return res


def ref_269(words) -> str:
    validate_domain(269, words)
    chars = sorted({ch for w in words for ch in w})
    adj = {c: set() for c in chars}
    indeg = {c: 0 for c in chars}
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if len(w1) > len(w2) and w1.startswith(w2):
            return ""
        for a, b in zip(w1, w2):
            if a != b:
                if b not in adj[a]:
                    adj[a].add(b)
                    indeg[b] += 1
                break
    heap = [c for c in chars if indeg[c] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        u = heapq.heappop(heap)
        out.append(u)
        for v in sorted(adj[u]):
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, v)
    return "".join(out) if len(out) == len(chars) else ""


def ref_270(root, target: float) -> int:
    validate_domain(270, root, target)
    tree = _tree_from_level(root)
    best = tree[0]
    cur = tree
    while cur is not None:
        v = cur[0]
        if abs(v - target) < abs(best - target) or (abs(v - target) == abs(best - target) and v < best):
            best = v
        cur = cur[1] if target < v else cur[2]
    return best


def ref_272(root, target: float, k: int):
    validate_domain(272, root, target, k)
    tree = _tree_from_level(root)
    vals = []

    def inorder(node):
        if node is None:
            return
        inorder(node[1])
        vals.append(node[0])
        inorder(node[2])

    inorder(tree)
    lo = 0
    for i in range(k, len(vals)):
        if abs(vals[i] - target) < abs(vals[lo] - target):
            lo += 1
        else:
            break
    return vals[lo : lo + k]


def ref_276(n: int, k: int) -> int:
    validate_domain(276, n, k)
    if n == 1:
        return k
    same = k
    diff = k * (k - 1)
    for _ in range(3, n + 1):
        same, diff = diff, (same + diff) * (k - 1)
    return same + diff


def ref_296(grid) -> int:
    validate_domain(296, grid)
    rows = [r for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 1]
    cols = [c for c in range(len(grid[0])) for r in range(len(grid)) if grid[r][c] == 1]

    def dist_1d(arr) -> int:
        l, r = 0, len(arr) - 1
        s = 0
        while l < r:
            s += arr[r] - arr[l]
            l += 1
            r -= 1
        return s

    return dist_1d(rows) + dist_1d(cols)


def ref_298(root) -> int:
    validate_domain(298, root)
    tree = _tree_from_level(root)
    if tree is None:
        return 0
    best = 0

    def dfs(node, parent_val, cur_len):
        nonlocal best
        if node is None:
            return
        ln = cur_len + 1 if parent_val is not None and node[0] == parent_val + 1 else 1
        if ln > best:
            best = ln
        dfs(node[1], node[0], ln)
        dfs(node[2], node[0], ln)

    dfs(tree, None, 0)
    return best


def ref_302(image, x: int, y: int) -> int:
    validate_domain(302, image, x, y)
    r_lo = r_hi = x
    c_lo = c_hi = y
    for r, row in enumerate(image):
        for c, ch in enumerate(row):
            if ch == "1" or ch == 1:
                if r < r_lo:
                    r_lo = r
                if r > r_hi:
                    r_hi = r
                if c < c_lo:
                    c_lo = c
                if c > c_hi:
                    c_hi = c
    return (r_hi - r_lo + 1) * (c_hi - c_lo + 1)


def ref_311(mat1, mat2):
    validate_domain(311, mat1, mat2)
    m, k, n = len(mat1), len(mat1[0]), len(mat2[0])
    res = [[0] * n for _ in range(m)]
    for i in range(m):
        for p in range(k):
            v1 = mat1[i][p]
            if v1 != 0:
                for j in range(n):
                    if mat2[p][j] != 0:
                        res[i][j] += v1 * mat2[p][j]
    return res


def ref_314(root):
    validate_domain(314, root)
    tree = _tree_from_level(root)
    if tree is None:
        return []
    cols = defaultdict(list)
    q = deque([(tree, 0)])
    min_c = max_c = 0
    while q:
        node, c = q.popleft()
        cols[c].append(node[0])
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c
        if node[1] is not None:
            q.append((node[1], c - 1))
        if node[2] is not None:
            q.append((node[2], c + 1))
    return [cols[c] for c in range(min_c, max_c + 1)]


def ref_317(grid) -> int:
    validate_domain(317, grid)
    m, n = len(grid), len(grid[0])
    total_dist = [[0] * n for _ in range(m)]
    reach = [[0] * n for _ in range(m)]
    buildings = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                buildings += 1
                q = deque([(r, c, 0)])
                vis = [[False] * n for _ in range(m)]
                vis[r][c] = True
                while q:
                    cr, cc, d = q.popleft()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < m and 0 <= nc < n and not vis[nr][nc] and grid[nr][nc] == 0:
                            vis[nr][nc] = True
                            total_dist[nr][nc] += d + 1
                            reach[nr][nc] += 1
                            q.append((nr, nc, d + 1))
    INF = 10**18
    ans = INF
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 0 and reach[r][c] == buildings and total_dist[r][c] < ans:
                ans = total_dist[r][c]
    return -1 if ans == INF else ans


def ref_320(word: str):
    validate_domain(320, word)
    n = len(word)
    out = []
    for mask in range(1 << n):
        parts = []
        cnt = 0
        for i in range(n):
            if (mask >> i) & 1:
                cnt += 1
            else:
                if cnt > 0:
                    parts.append(str(cnt))
                    cnt = 0
                parts.append(word[i])
        if cnt > 0:
            parts.append(str(cnt))
        out.append("".join(parts))
    return out


def ref_325(nums, k: int) -> int:
    validate_domain(325, nums, k)
    first = {0: -1}
    cur = 0
    best = 0
    for i, x in enumerate(nums):
        cur += x
        if cur - k in first:
            best = max(best, i - first[cur - k])
        if cur not in first:
            first[cur] = i
    return best


def ref_333(root) -> int:
    validate_domain(333, root)
    tree = _tree_from_level(root)
    INF = 10**18

    def dfs(node):
        if node is None:
            return True, INF, -INF, 0
        ok_l, mn_l, mx_l, sz_l = dfs(node[1])
        ok_r, mn_r, mx_r, sz_r = dfs(node[2])
        if ok_l and ok_r and mx_l < node[0] < mn_r:
            return True, min(mn_l, node[0]), max(mx_r, node[0]), sz_l + sz_r + 1
        return False, -INF, INF, max(sz_l, sz_r)

    return dfs(tree)[3]


def ref_340(s: str, k: int) -> int:
    validate_domain(340, s, k)
    if k == 0:
        return 0
    cnt = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while len(cnt) > k:
            lch = s[left]
            cnt[lch] -= 1
            if cnt[lch] == 0:
                del cnt[lch]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


def ref_351(m: int, n: int) -> int:
    validate_domain(351, m, n)
    skip = [[0] * 10 for _ in range(10)]
    skip[1][3] = skip[3][1] = 2
    skip[1][7] = skip[7][1] = 4
    skip[3][9] = skip[9][3] = 6
    skip[7][9] = skip[9][7] = 8
    skip[1][9] = skip[9][1] = skip[2][8] = skip[8][2] = skip[3][7] = skip[7][3] = skip[4][6] = skip[6][4] = 5

    def dfs(vis: int, cur: int, rem: int) -> int:
        if rem == 0:
            return 1
        vis |= 1 << cur
        total = 0
        for nxt in range(1, 10):
            mid = skip[cur][nxt]
            if not ((vis >> nxt) & 1) and (mid == 0 or ((vis >> mid) & 1)):
                total += dfs(vis, nxt, rem - 1)
        return total

    ans = 0
    for length in range(m, n + 1):
        ans += dfs(0, 1, length - 1) * 4
        ans += dfs(0, 2, length - 1) * 4
        ans += dfs(0, 5, length - 1)
    return ans


def ref_356(points) -> bool:
    validate_domain(356, points)
    pts = {(x, y) for x, y in points}
    xs = [x for x, _ in pts]
    sum_x = min(xs) + max(xs)
    return all((sum_x - x, y) in pts for x, y in pts)


def ref_358(s: str, k: int) -> str:
    validate_domain(358, s, k)
    if k <= 1:
        return s
    cnt = Counter(s)
    heap = [(-c, ord(ch), ch) for ch, c in cnt.items()]
    heapq.heapify(heap)
    q = deque()
    res = []
    while heap:
        neg_c, code, ch = heapq.heappop(heap)
        res.append(ch)
        q.append((neg_c + 1, code, ch))
        if len(q) >= k:
            item = q.popleft()
            if item[0] < 0:
                heapq.heappush(heap, item)
    return "".join(res) if len(res) == len(s) else ""


def ref_360(nums, a: int, b: int, c: int):
    validate_domain(360, nums, a, b, c)
    return sorted(a * x * x + b * x + c for x in nums)


def ref_361(grid) -> int:
    validate_domain(361, grid)
    m, n = len(grid), len(grid[0])
    row_hits = 0
    col_hits = [0] * n
    best = 0
    for r in range(m):
        for c in range(n):
            if c == 0 or grid[r][c - 1] == "W":
                row_hits = 0
                k = c
                while k < n and grid[r][k] != "W":
                    if grid[r][k] == "E":
                        row_hits += 1
                    k += 1
            if r == 0 or grid[r - 1][c] == "W":
                col_hits[c] = 0
                k = r
                while k < m and grid[k][c] != "W":
                    if grid[k][c] == "E":
                        col_hits[c] += 1
                    k += 1
            if grid[r][c] == "0":
                best = max(best, row_hits + col_hits[c])
    return best


def ref_366(root):
    validate_domain(366, root)
    tree = _tree_from_level(root)
    res = []

    def dfs(node) -> int:
        if node is None:
            return -1
        h = 1 + max(dfs(node[1]), dfs(node[2]))
        if h == len(res):
            res.append([])
        res[h].append(node[0])
        return h

    dfs(tree)
    return res


def ref_369(head):
    validate_domain(369, head)
    num = int("".join(str(d) for d in head)) + 1
    return [int(ch) for ch in str(num)]


def ref_370(length: int, updates):
    validate_domain(370, length, updates)
    diff = [0] * (length + 1)
    for l, r, inc in updates:
        diff[l] += inc
        diff[r + 1] -= inc
    res = [0] * length
    cur = 0
    for i in range(length):
        cur += diff[i]
        res[i] = cur
    return res


REFERENCES = {
    243: ref_243, 245: ref_245, 246: ref_246, 247: ref_247, 248: ref_248,
    249: ref_249, 250: ref_250, 254: ref_254, 255: ref_255, 256: ref_256,
    259: ref_259, 265: ref_265, 267: ref_267, 269: ref_269, 270: ref_270,
    272: ref_272, 276: ref_276, 296: ref_296, 298: ref_298, 302: ref_302,
    311: ref_311, 314: ref_314, 317: ref_317, 320: ref_320, 325: ref_325,
    333: ref_333, 340: ref_340, 351: ref_351, 356: ref_356, 358: ref_358,
    360: ref_360, 361: ref_361, 366: ref_366, 369: ref_369, 370: ref_370,
}
