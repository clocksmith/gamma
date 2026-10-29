"""Source-free reference models and domain validation for requested-156-1940-31."""

import bisect
from collections import Counter, defaultdict, deque
import math

PROBLEM_IDS = (
    156, 159, 161, 163, 280, 286, 294, 737, 742, 751,
    755, 758, 772, 774, 903, 911, 1213, 1214, 1215, 1229,
    1230, 1692, 1714, 1740, 1820, 1826, 1908, 1918, 1924, 1933,
    1940,
)

MOD = 10**9 + 7


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


def _tree_to_level(root):
    if root is None:
        return []
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append(node[0])
            q.append(node[1])
            q.append(node[2])
    while out and out[-1] is None:
        out.pop()
    return out


def validate_domain(problem_id: int, *args) -> None:
    if problem_id == 156:
        (root,) = args
        if not isinstance(root, list):
            raise ValueError("invalid 156")
    elif problem_id in (159, 294, 772, 903, 1933):
        (s,) = args
        if not isinstance(s, str) or not s:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 161:
        (s, t) = args
        if not isinstance(s, str) or not isinstance(t, str):
            raise ValueError("invalid 161")
    elif problem_id == 163:
        (nums, lower, upper) = args
        if not isinstance(nums, list) or not _is_int(lower) or not _is_int(upper) or lower > upper:
            raise ValueError("invalid 163")
    elif problem_id in (280, 1908):
        (nums,) = args
        if not isinstance(nums, list) or not nums:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id in (286, 1820, 1924, 1940):
        (grid,) = args
        if not isinstance(grid, list) or not grid:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 737:
        (s1, s2, pairs) = args
        if not isinstance(s1, list) or not isinstance(s2, list) or not isinstance(pairs, list):
            raise ValueError("invalid 737")
    elif problem_id == 742:
        (root, k) = args
        if not isinstance(root, list) or not root or not _is_int(k):
            raise ValueError("invalid 742")
    elif problem_id == 751:
        (ip, n) = args
        if not isinstance(ip, str) or not _is_int(n) or n < 1:
            raise ValueError("invalid 751")
    elif problem_id == 755:
        (heights, volume, k) = args
        if not isinstance(heights, list) or not heights or not _is_int(volume) or not _is_int(k):
            raise ValueError("invalid 755")
    elif problem_id == 758:
        (words, s) = args
        if not isinstance(words, list) or not isinstance(s, str) or not s:
            raise ValueError("invalid 758")
    elif problem_id in (774, 1918):
        (arr, k) = args
        if not isinstance(arr, list) or not arr or not _is_int(k) or k < 1:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 911:
        (ops, arg_lists) = args
        if not isinstance(ops, list) or not ops or ops[0] != "TopVotedCandidate" or len(ops) != len(arg_lists):
            raise ValueError("invalid 911")
    elif problem_id == 1213:
        (a1, a2, a3) = args
        if not (isinstance(a1, list) and isinstance(a2, list) and isinstance(a3, list) and a1):
            raise ValueError("invalid 1213")
    elif problem_id == 1214:
        (r1, r2, target) = args
        if not isinstance(r1, list) or not isinstance(r2, list) or not _is_int(target):
            raise ValueError("invalid 1214")
    elif problem_id == 1215:
        (low, high) = args
        if not _is_int(low) or not _is_int(high) or low < 0 or low > high:
            raise ValueError("invalid 1215")
    elif problem_id == 1229:
        (s1, s2, duration) = args
        if not isinstance(s1, list) or not isinstance(s2, list) or not _is_int(duration) or duration < 1:
            raise ValueError("invalid 1229")
    elif problem_id == 1230:
        (prob, target) = args
        if not isinstance(prob, list) or not prob or not _is_int(target) or not (0 <= target <= len(prob)):
            raise ValueError("invalid 1230")
    elif problem_id == 1692:
        (n, k) = args
        if not _is_int(n) or not _is_int(k) or not (1 <= k <= n <= 1000):
            raise ValueError("invalid 1692")
    elif problem_id == 1714:
        (nums, queries) = args
        if not isinstance(nums, list) or not nums or not isinstance(queries, list) or not queries:
            raise ValueError("invalid 1714")
    elif problem_id == 1740:
        (root, p, q) = args
        if not isinstance(root, list) or not root or not _is_int(p) or not _is_int(q):
            raise ValueError("invalid 1740")
    elif problem_id == 1826:
        (s1, s2) = args
        if not isinstance(s1, list) or not isinstance(s2, list) or len(s1) != len(s2) or len(s1) < 2:
            raise ValueError("invalid 1826")
    else:
        raise KeyError(f"Unknown problem_id: {problem_id}")


def ref_156(root):
    validate_domain(156, root)
    tree = _tree_from_level(root)
    cur = tree
    prev = None
    prev_right = None
    while cur is not None:
        nxt = cur[1]
        cur[1] = prev_right
        prev_right = cur[2]
        cur[2] = prev
        prev = cur
        cur = nxt
    return _tree_to_level(prev)


def ref_159(s: str) -> int:
    validate_domain(159, s)
    cnt = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while len(cnt) > 2:
            lch = s[left]
            cnt[lch] -= 1
            if cnt[lch] == 0:
                del cnt[lch]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


def ref_161(s: str, t: str) -> bool:
    validate_domain(161, s, t)
    if len(s) > len(t):
        s, t = t, s
    if len(t) - len(s) > 1:
        return False
    for i in range(len(s)):
        if s[i] != t[i]:
            if len(s) == len(t):
                return s[i + 1 :] == t[i + 1 :]
            return s[i:] == t[i + 1 :]
    return len(t) == len(s) + 1


def ref_163(nums, lower: int, upper: int):
    validate_domain(163, nums, lower, upper)
    res = []
    prev = lower - 1
    for x in list(nums) + [upper + 1]:
        if x - prev >= 2:
            res.append([prev + 1, x - 1])
        prev = x
    return res


def ref_280(nums):
    validate_domain(280, nums)
    arr = list(nums)
    for i in range(len(arr) - 1):
        if (i % 2 == 0 and arr[i] > arr[i + 1]) or (i % 2 == 1 and arr[i] < arr[i + 1]):
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
    return arr


def ref_286(rooms):
    validate_domain(286, rooms)
    INF = 2147483647
    grid = [list(row) for row in rooms]
    m, n = len(grid), len(grid[0])
    q = deque()
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 0:
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == INF:
                grid[nr][nc] = grid[r][c] + 1
                q.append((nr, nc))
    return grid


def ref_294(currentState: str) -> bool:
    validate_domain(294, currentState)
    runs = []
    cur = 0
    for ch in currentState:
        if ch == "+":
            cur += 1
        else:
            if cur >= 2:
                runs.append(cur)
            cur = 0
    if cur >= 2:
        runs.append(cur)
    if not runs:
        return False
    mx = max(runs)
    g = [0] * (mx + 1)
    for L in range(2, mx + 1):
        seen = {g[i] ^ g[L - 2 - i] for i in range((L - 1) // 2 + 1)}
        mex = 0
        while mex in seen:
            mex += 1
        g[L] = mex
    xor_sum = 0
    for r in runs:
        xor_sum ^= g[r]
    return xor_sum != 0


def ref_737(sentence1, sentence2, similarPairs) -> bool:
    validate_domain(737, sentence1, sentence2, similarPairs)
    if len(sentence1) != len(sentence2):
        return False
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    for a, b in similarPairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return all(w1 == w2 or find(w1) == find(w2) for w1, w2 in zip(sentence1, sentence2))


def ref_742(root, k: int) -> int:
    validate_domain(742, root, k)
    tree = _tree_from_level(root)
    adj = defaultdict(list)
    leaves = set()

    def dfs(node, par):
        if node is None:
            return
        u = node[0]
        if par is not None:
            adj[u].append(par)
            adj[par].append(u)
        if node[1] is None and node[2] is None:
            leaves.add(u)
        dfs(node[1], u)
        dfs(node[2], u)

    dfs(tree, None)
    q = deque([k])
    vis = {k}
    while q:
        u = q.popleft()
        if u in leaves:
            return u
        for v in adj[u]:
            if v not in vis:
                vis.add(v)
                q.append(v)
    return k


def ref_751(ip: str, n: int):
    validate_domain(751, ip, n)
    parts = [int(x) for x in ip.split(".")]
    cur = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
    out = []
    while n > 0:
        step = cur & -cur if cur != 0 else (1 << 32)
        while step > n:
            step >>= 1
        tz = step.bit_length() - 1
        prefix = 32 - tz
        s_ip = f"{(cur >> 24) & 255}.{(cur >> 16) & 255}.{(cur >> 8) & 255}.{cur & 255}/{prefix}"
        out.append(s_ip)
        cur += step
        n -= step
    return out


def ref_755(heights, volume: int, k: int):
    validate_domain(755, heights, volume, k)
    h = list(heights)
    n = len(h)
    for _ in range(volume):
        pos = k
        for i in range(k - 1, -1, -1):
            if h[i] > h[pos]:
                break
            if h[i] < h[pos]:
                pos = i
        if pos == k:
            for i in range(k + 1, n):
                if h[i] > h[pos]:
                    break
                if h[i] < h[pos]:
                    pos = i
        h[pos] += 1
    return h


def ref_758(words, s: str) -> str:
    validate_domain(758, words, s)
    n = len(s)
    bold = [False] * n
    for w in words:
        L = len(w)
        start = s.find(w)
        while start != -1:
            for i in range(start, start + L):
                bold[i] = True
            start = s.find(w, start + 1)
    out = []
    for i, ch in enumerate(s):
        if bold[i] and (i == 0 or not bold[i - 1]):
            out.append("<b>")
        out.append(ch)
        if bold[i] and (i == n - 1 or not bold[i + 1]):
            out.append("</b>")
    return "".join(out)


def ref_772(s: str) -> int:
    validate_domain(772, s)
    idx = 0
    n = len(s)

    def parse_expr():
        nonlocal idx
        stack = []
        num = 0
        op = "+"
        while idx < n:
            ch = s[idx]
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == "(":
                idx += 1
                num = parse_expr()
            if (not ch.isdigit() and ch != " ") or idx == n - 1:
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                elif op == "/":
                    stack.append(int(stack.pop() / num))
                op = ch
                num = 0
                if ch == ")":
                    break
            idx += 1
        return sum(stack)

    return parse_expr()


def ref_774(stations, k: int) -> float:
    validate_domain(774, stations, k)
    gaps = [stations[i + 1] - stations[i] for i in range(len(stations) - 1)]
    lo, hi = 0.0, float(stations[-1] - stations[0])
    for _ in range(60):
        mid = (lo + hi) * 0.5
        need = sum(int((g - 1e-12) // mid) for g in gaps)
        if need <= k:
            hi = mid
        else:
            lo = mid
    return round(hi, 6)


def ref_903(s: str) -> int:
    validate_domain(903, s)
    dp = [1]
    for ch in s:
        if ch == "I":
            cur = 0
            ndp = []
            for x in dp:
                cur = (cur + x) % MOD
                ndp.append(cur)
            dp = ndp
        else:
            cur = 0
            ndp = [0] * (len(dp) + 1)
            for i in range(len(dp) - 1, -1, -1):
                cur = (cur + dp[i]) % MOD
                ndp[i] = cur
            dp = ndp
    return sum(dp) % MOD


def ref_911(ops, arg_lists):
    validate_domain(911, ops, arg_lists)
    persons, times = arg_lists[0]
    counts = defaultdict(int)
    leaders = []
    cur_leader = -1
    max_votes = 0
    for p in persons:
        counts[p] += 1
        if counts[p] >= max_votes:
            max_votes = counts[p]
            cur_leader = p
        leaders.append(cur_leader)
    out = [None]
    for op, args in zip(ops[1:], arg_lists[1:]):
        idx = bisect.bisect_right(times, args[0]) - 1
        out.append(leaders[idx])
    return out


def ref_1213(arr1, arr2, arr3):
    validate_domain(1213, arr1, arr2, arr3)
    s2 = set(arr2)
    s3 = set(arr3)
    return [x for x in arr1 if x in s2 and x in s3]


def ref_1214(root1, root2, target: int) -> bool:
    validate_domain(1214, root1, root2, target)
    s1 = {x for x in root1 if x is not None}
    return any((target - y) in s1 for y in root2 if y is not None)


def ref_1215(low: int, high: int):
    validate_domain(1215, low, high)
    res = [0] if low == 0 else []
    q = deque(range(1, 10))
    while q:
        v = q.popleft()
        if v > high:
            continue
        if v >= low:
            res.append(v)
        last = v % 10
        if last > 0 and v * 10 + last - 1 <= high:
            q.append(v * 10 + last - 1)
        if last < 9 and v * 10 + last + 1 <= high:
            q.append(v * 10 + last + 1)
    return sorted(res)


def ref_1229(slots1, slots2, duration: int):
    validate_domain(1229, slots1, slots2, duration)
    a = sorted(s for s in slots1 if s[1] - s[0] >= duration)
    b = sorted(s for s in slots2 if s[1] - s[0] >= duration)
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if hi - lo >= duration:
            return [lo, lo + duration]
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return []


def ref_1230(prob, target: int) -> float:
    validate_domain(1230, prob, target)
    dp = [0.0] * (target + 1)
    dp[0] = 1.0
    for p in prob:
        for j in range(target, 0, -1):
            dp[j] = dp[j] * (1.0 - p) + dp[j - 1] * p
        dp[0] *= 1.0 - p
    return round(dp[target], 10)


def ref_1692(n: int, k: int) -> int:
    validate_domain(1692, n, k)
    dp = [0] * (k + 1)
    dp[0] = 1
    for _ in range(1, n + 1):
        for j in range(k, 0, -1):
            dp[j] = (dp[j] * j + dp[j - 1]) % MOD
        dp[0] = 0
    return dp[k]


def ref_1714(nums, queries):
    validate_domain(1714, nums, queries)
    n = len(nums)
    B = int(math.isqrt(n)) + 1
    suf = {}
    for y in range(1, B):
        arr = [0] * n
        for i in range(n - 1, -1, -1):
            arr[i] = (nums[i] + (arr[i + y] if i + y < n else 0)) % MOD
        suf[y] = arr
    out = []
    for x, y in queries:
        if y < B:
            out.append(suf[y][x])
        else:
            s = 0
            for i in range(x, n, y):
                s = (s + nums[i]) % MOD
            out.append(s)
    return out


def ref_1740(root, p: int, q: int) -> int:
    validate_domain(1740, root, p, q)
    tree = _tree_from_level(root)
    adj = defaultdict(list)

    def dfs(node, par):
        if node is None:
            return
        u = node[0]
        if par is not None:
            adj[u].append(par)
            adj[par].append(u)
        dfs(node[1], u)
        dfs(node[2], u)

    dfs(tree, None)
    dq = deque([(p, 0)])
    vis = {p}
    while dq:
        u, d = dq.popleft()
        if u == q:
            return d
        for v in adj[u]:
            if v not in vis:
                vis.add(v)
                dq.append((v, d + 1))
    return 0


def ref_1820(grid) -> int:
    validate_domain(1820, grid)
    m, n = len(grid), len(grid[0])
    match = [-1] * n

    def dfs(u: int, vis) -> bool:
        for v in range(n):
            if grid[u][v] and not vis[v]:
                vis[v] = True
                if match[v] == -1 or dfs(match[v], vis):
                    match[v] = u
                    return True
        return False

    ans = 0
    for u in range(m):
        if dfs(u, [False] * n):
            ans += 1
    return ans


def ref_1826(sensor1, sensor2) -> int:
    validate_domain(1826, sensor1, sensor2)
    n = len(sensor1)
    i = 0
    while i < n and sensor1[i] == sensor2[i]:
        i += 1
    if i >= n - 1:
        return -1
    ok1 = sensor1[i : n - 1] == sensor2[i + 1 : n]
    ok2 = sensor2[i : n - 1] == sensor1[i + 1 : n]
    if ok1 and not ok2:
        return 1
    if ok2 and not ok1:
        return 2
    return -1


def ref_1908(piles) -> bool:
    validate_domain(1908, piles)
    xor_sum = 0
    for x in piles:
        xor_sum ^= x
    return xor_sum != 0


def ref_1918(nums, k: int) -> int:
    validate_domain(1918, nums, k)
    lo, hi = min(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        cnt = 0
        cur = 0
        left = 0
        for right, x in enumerate(nums):
            cur += x
            while cur > mid:
                cur -= nums[left]
                left += 1
            cnt += right - left + 1
        if cnt >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def ref_1924(trees):
    validate_domain(1924, trees)
    pts = [tuple(p) for p in dict.fromkeys(tuple(t) for t in trees)]

    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def circle2(a, b):
        return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, dist(a, b) / 2.0)

    def circle3(a, b, c):
        ax, ay = a
        bx, by = b
        cx, cy = c
        d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-12:
            pairs = [circle2(a, b), circle2(b, c), circle2(a, c)]
            return max(pairs, key=lambda item: item[2])
        a2 = ax * ax + ay * ay
        b2 = bx * bx + by * by
        c2 = cx * cx + cy * cy
        ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
        uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
        return (ux, uy, math.hypot(ux - ax, uy - ay))

    c = (pts[0][0], pts[0][1], 0.0)
    for i in range(len(pts)):
        if dist((c[0], c[1]), pts[i]) > c[2] + 1e-9:
            c = (pts[i][0], pts[i][1], 0.0)
            for j in range(i):
                if dist((c[0], c[1]), pts[j]) > c[2] + 1e-9:
                    c = circle2(pts[i], pts[j])
                    for k in range(j):
                        if dist((c[0], c[1]), pts[k]) > c[2] + 1e-9:
                            c = circle3(pts[i], pts[j], pts[k])
    return [round(c[0], 5), round(c[1], 5), round(c[2], 5)]


def ref_1933(s: str) -> bool:
    validate_domain(1933, s)
    twos = 0
    i = 0
    n = len(s)
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        rem = (j - i) % 3
        if rem == 1:
            return False
        if rem == 2:
            twos += 1
        i = j
    return twos == 1


def ref_1940(arrays):
    validate_domain(1940, arrays)
    m = len(arrays)
    cnt = Counter(x for arr in arrays for x in arr)
    return [x for x in arrays[0] if cnt[x] == m]


REFERENCES = {
    156: ref_156, 159: ref_159, 161: ref_161, 163: ref_163, 280: ref_280,
    286: ref_286, 294: ref_294, 737: ref_737, 742: ref_742, 751: ref_751,
    755: ref_755, 758: ref_758, 772: ref_772, 774: ref_774, 903: ref_903,
    911: ref_911, 1213: ref_1213, 1214: ref_1214, 1215: ref_1215, 1229: ref_1229,
    1230: ref_1230, 1692: ref_1692, 1714: ref_1714, 1740: ref_1740, 1820: ref_1820,
    1826: ref_1826, 1908: ref_1908, 1918: ref_1918, 1924: ref_1924, 1933: ref_1933,
    1940: ref_1940,
}
