"""Source-free reference models and domain validation for requested-2753-3359-50."""

from collections import Counter, defaultdict, deque
import heapq
import math

PROBLEM_IDS = (
    2753, 2864, 2930, 2931, 2936, 2946, 2969, 3023, 3037, 3064,
    3094, 3205, 3221, 3245, 3247, 3249, 3250, 3253, 3260, 3263,
    3269, 3275, 3279, 3281, 3282, 3284, 3286, 3288, 3291, 3294,
    3299, 3302, 3306, 3313, 3316, 3319, 3323, 3326, 3329, 3331,
    3339, 3341, 3342, 3344, 3347, 3351, 3353, 3355, 3356, 3359,
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


def validate_domain(problem_id: int, *args) -> None:
    if problem_id == 2753:
        (street, k) = args
        if not isinstance(street, list) or not (1 <= len(street) <= k <= 10**5):
            raise ValueError("invalid 2753")
        if not any(x == 1 for x in street):
            raise ValueError("2753 requires at least one open door")
    elif problem_id == 2864:
        (s,) = args
        if not isinstance(s, str) or not (1 <= len(s) <= 100) or "1" not in s:
            raise ValueError("invalid 2864")
    elif problem_id == 2930:
        (n,) = args
        if not _is_int(n) or not (1 <= n <= 10**5):
            raise ValueError("invalid 2930")
    elif problem_id == 2931:
        (values,) = args
        if not isinstance(values, list) or not values or not values[0]:
            raise ValueError("invalid 2931")
    elif problem_id == 2936:
        (nums,) = args
        if not isinstance(nums, list) or not (1 <= len(nums) <= 10**5):
            raise ValueError("invalid 2936")
    elif problem_id == 2946:
        (mat, k) = args
        if not isinstance(mat, list) or not mat or not _is_int(k) or not (1 <= k <= 50):
            raise ValueError("invalid 2946")
    elif problem_id == 2969:
        (prices,) = args
        if not isinstance(prices, list) or not (1 <= len(prices) <= 10**5):
            raise ValueError("invalid 2969")
    elif problem_id in (3023, 3037):
        (stream, pattern) = args
        if not isinstance(stream, list) or not isinstance(pattern, list) or not pattern:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id in (3064, 3094):
        (n,) = args
        if not _is_int(n) or not (0 <= n < (1 << 30)):
            raise ValueError(f"invalid {problem_id}")
    elif problem_id in (3205, 3221, 3247, 3250, 3282, 3284, 3299, 3326, 3351, 3353):
        (nums,) = args
        if not isinstance(nums, list) or not nums:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3245:
        (colors, queries) = args
        if not isinstance(colors, list) or len(colors) < 3 or not isinstance(queries, list) or not queries:
            raise ValueError("invalid 3245")
    elif problem_id in (3249, 3313):
        (edges,) = args
        if not isinstance(edges, list) or not edges:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3253:
        (target, words, costs) = args
        if not isinstance(target, str) or not isinstance(words, list) or len(words) != len(costs):
            raise ValueError("invalid 3253")
    elif problem_id == 3260:
        (n, k) = args
        if not _is_int(n) or not (1 <= n <= 10**5) or not _is_int(k) or not (1 <= k <= 9):
            raise ValueError("invalid 3260")
    elif problem_id in (3263, 3294):
        (head,) = args
        if not isinstance(head, list) or not head:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3269:
        (nums1, nums2) = args
        if not isinstance(nums1, list) or not isinstance(nums2, list):
            raise ValueError("invalid 3269")
    elif problem_id == 3275:
        (queries, k) = args
        if not isinstance(queries, list) or not queries or not _is_int(k) or k < 1:
            raise ValueError("invalid 3275")
    elif problem_id == 3279:
        (height, positions, directions) = args
        if not _is_int(height) or height < 1 or len(positions) != len(directions):
            raise ValueError("invalid 3279")
    elif problem_id == 3281:
        (start, d) = args
        if not isinstance(start, list) or len(start) < 2 or not _is_int(d) or d < 0:
            raise ValueError("invalid 3281")
    elif problem_id == 3286:
        (grid, health) = args
        if not isinstance(grid, list) or not grid or not _is_int(health) or health < 1:
            raise ValueError("invalid 3286")
    elif problem_id == 3288:
        (coordinates, k) = args
        if not isinstance(coordinates, list) or not (0 <= k < len(coordinates)):
            raise ValueError("invalid 3288")
    elif problem_id == 3291:
        (words, target) = args
        if not isinstance(words, list) or not isinstance(target, str) or not target:
            raise ValueError("invalid 3291")
    elif problem_id == 3302:
        (word1, word2) = args
        if not isinstance(word1, str) or not isinstance(word2, str) or not (1 <= len(word2) <= len(word1)):
            raise ValueError("invalid 3302")
    elif problem_id in (3306, 3329):
        (s, k) = args
        if not isinstance(s, str) or not s or not _is_int(k):
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3316:
        (source, pattern, targetIndices) = args
        if not isinstance(source, str) or not isinstance(pattern, str) or not isinstance(targetIndices, list):
            raise ValueError("invalid 3316")
    elif problem_id == 3319:
        (root, k) = args
        if not isinstance(root, list) or not root or not _is_int(k) or k < 1:
            raise ValueError("invalid 3319")
    elif problem_id == 3323:
        (intervals, k) = args
        if not isinstance(intervals, list) or not intervals or not _is_int(k) or k < 0:
            raise ValueError("invalid 3323")
    elif problem_id == 3331:
        (parent, s) = args
        if not isinstance(parent, list) or not isinstance(s, str) or len(parent) != len(s):
            raise ValueError("invalid 3331")
    elif problem_id == 3339:
        (n, m, k) = args
        if not (_is_int(n) and _is_int(m) and _is_int(k)) or n < 1 or m < 1 or k < 0:
            raise ValueError("invalid 3339")
    elif problem_id in (3341, 3342):
        (moveTime,) = args
        if not isinstance(moveTime, list) or len(moveTime) < 2 or len(moveTime[0]) < 2:
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3344:
        (s,) = args
        if not _is_int(s) or s < 0:
            raise ValueError("invalid 3344")
    elif problem_id == 3347:
        (nums, k, numOperations) = args
        if not isinstance(nums, list) or not nums or not _is_int(k) or not _is_int(numOperations):
            raise ValueError("invalid 3347")
    elif problem_id in (3355, 3356):
        (nums, queries) = args
        if not isinstance(nums, list) or not nums or not isinstance(queries, list):
            raise ValueError(f"invalid {problem_id}")
    elif problem_id == 3359:
        (grid, k) = args
        if not isinstance(grid, list) or not grid or not _is_int(k):
            raise ValueError("invalid 3359")
    else:
        raise KeyError(f"Unknown problem_id: {problem_id}")


def ref_2753(street, k: int) -> int:
    validate_domain(2753, street, k)
    return len(street)


def ref_2864(s: str) -> str:
    validate_domain(2864, s)
    ones = s.count("1")
    zeros = len(s) - ones
    return "1" * (ones - 1) + "0" * zeros + "1"


def ref_2930(n: int) -> int:
    validate_domain(2930, n)
    if n < 4:
        return 0
    p26 = pow(26, n, MOD)
    p25 = pow(25, n - 1, MOD) * (75 + n) % MOD
    p24 = pow(24, n - 1, MOD) * (72 + 2 * n) % MOD
    p23 = pow(23, n - 1, MOD) * (23 + n) % MOD
    return (p26 - p25 + p24 - p23) % MOD


def ref_2931(values) -> int:
    validate_domain(2931, values)
    flat = sorted(x for row in values for x in row)
    return sum((i + 1) * v for i, v in enumerate(flat))


def ref_2936(nums) -> int:
    validate_domain(2936, nums)
    return 1 + sum(1 for i in range(1, len(nums)) if nums[i] != nums[i - 1])


def ref_2946(mat, k: int) -> bool:
    validate_domain(2946, mat, k)
    n = len(mat[0])
    return all(row[j] == row[(j + k) % n] for row in mat for j in range(n))


def ref_2969(prices) -> int:
    validate_domain(2969, prices)
    n = len(prices)
    q = deque([(n + 1, 0)])
    for i in range(n, 0, -1):
        while q and q[0][0] > 2 * i + 1:
            q.popleft()
        cur = prices[i - 1] + q[0][1]
        while q and q[-1][1] >= cur:
            q.pop()
        q.append((i, cur))
    return q[-1][1]


def ref_3023(stream, pattern) -> int:
    validate_domain(3023, stream, pattern)
    m = len(pattern)
    for i in range(len(stream) - m + 1):
        if stream[i : i + m] == pattern:
            return i
    return -1


def ref_3037(stream, pattern) -> int:
    validate_domain(3037, stream, pattern)
    return ref_3023(stream, pattern)


def ref_3064(n: int) -> int:
    validate_domain(3064, n)
    return n


def ref_3094(n: int) -> int:
    validate_domain(3094, n)
    return n


def ref_3205(nums) -> int:
    validate_domain(3205, nums)
    ans = 0
    mx = 0
    for i in range(len(nums) - 1, 0, -1):
        if nums[i] > mx:
            mx = nums[i]
        ans += mx
    return ans


def ref_3221(nums) -> int:
    validate_domain(3221, nums)
    return ref_3205(nums)


def ref_3245(colors, queries):
    validate_domain(3245, colors, queries)
    arr = list(colors)
    n = len(arr)
    out = []
    for q in queries:
        if q[0] == 1:
            sz = q[1]
            cnt = 0
            for start in range(n):
                ok = True
                for d in range(sz - 1):
                    if arr[(start + d) % n] == arr[(start + d + 1) % n]:
                        ok = False
                        break
                if ok:
                    cnt += 1
            out.append(cnt)
        else:
            arr[q[1]] = q[2]
    return out


def ref_3247(nums) -> int:
    validate_domain(3247, nums)
    if any(x & 1 for x in nums):
        return pow(2, len(nums) - 1, MOD)
    return 0


def ref_3249(edges) -> int:
    validate_domain(3249, edges)
    n = len(edges) + 1
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    order = [0]
    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    sz = [1] * n
    good = 0
    for u in reversed(order):
        child_sizes = []
        for v in adj[u]:
            if v != parent[u]:
                sz[u] += sz[v]
                child_sizes.append(sz[v])
        if len(set(child_sizes)) <= 1:
            good += 1
    return good


def ref_3250(nums) -> int:
    validate_domain(3250, nums)
    n = len(nums)
    diff_sum = sum(max(0, nums[i] - nums[i - 1]) for i in range(1, n))
    rem = nums[-1] - diff_sum
    if rem < 0:
        return 0
    return math.comb(rem + n, n) % MOD


def ref_3253(target: str, words, costs) -> int:
    validate_domain(3253, target, words, costs)
    n = len(target)
    best_word = {}
    for w, c in zip(words, costs):
        if w not in best_word or c < best_word[w]:
            best_word[w] = c
    INF = 10**18
    dp = [INF] * (n + 1)
    dp[0] = 0
    for i in range(n):
        if dp[i] == INF:
            continue
        for w, c in best_word.items():
            L = len(w)
            if i + L <= n and target[i : i + L] == w:
                if dp[i] + c < dp[i + L]:
                    dp[i + L] = dp[i] + c
    return -1 if dp[n] == INF else dp[n]


def ref_3260(n: int, k: int) -> str:
    validate_domain(3260, n, k)
    m = (n + 1) // 2
    pow10 = [1] * n
    for i in range(1, n):
        pow10[i] = (pow10[i - 1] * 10) % k
    weights = [0] * m
    for i in range(m):
        j = n - 1 - i
        weights[i] = pow10[i] if i == j else (pow10[i] + pow10[j]) % k
    dp = [[False] * k for _ in range(m + 1)]
    dp[m][0] = True
    for i in range(m - 1, -1, -1):
        w = weights[i]
        lo = 1 if i == 0 else 0
        for r in range(k):
            for d in range(9, lo - 1, -1):
                if dp[i + 1][(r + d * w) % k]:
                    dp[i][r] = True
                    break
    res = ["0"] * m
    r = 0
    for i in range(m):
        w = weights[i]
        lo = 1 if i == 0 else 0
        for d in range(9, lo - 1, -1):
            if dp[i + 1][(r + d * w) % k]:
                res[i] = str(d)
                r = (r + d * w) % k
                break
    left = "".join(res)
    right = left[: n // 2][::-1]
    return left + right


def ref_3263(head):
    validate_domain(3263, head)
    return list(head)


def ref_3269(nums1, nums2) -> int:
    validate_domain(3269, nums1, nums2)
    m, n = len(nums1), len(nums2)
    INF = 10**18
    dp = [INF] * (n + 1)
    dp[0] = 0
    for j in range(1, n + 1):
        p = nums2[j - 1]
        x = dp[j - 1]
        dp[j] = x + 1 + (((x + 1) ^ p) & 1)
    for i in range(1, m + 1):
        p1 = nums1[i - 1]
        ndp = [INF] * (n + 1)
        x = dp[0]
        ndp[0] = x + 1 + (((x + 1) ^ p1) & 1)
        for j in range(1, n + 1):
            p2 = nums2[j - 1]
            v1 = dp[j] + 1 + (((dp[j] + 1) ^ p1) & 1)
            v2 = ndp[j - 1] + 1 + (((ndp[j - 1] + 1) ^ p2) & 1)
            ndp[j] = v1 if v1 < v2 else v2
        dp = ndp
    return dp[n]


def ref_3275(queries, k: int):
    validate_domain(3275, queries, k)
    heap = []
    out = []
    for x, y in queries:
        d = abs(x) + abs(y)
        if len(heap) < k:
            heapq.heappush(heap, -d)
        elif d < -heap[0]:
            heapq.heapreplace(heap, -d)
        out.append(-heap[0] if len(heap) == k else -1)
    return out


def ref_3279(height: int, positions, directions) -> int:
    validate_domain(3279, height, positions, directions)
    period = 2 * height
    delta = [0] * (period + 2)
    cur = sum(positions)
    slope = 0
    for p, d in zip(positions, directions):
        if p == 0:
            d = "U"
        elif p == height:
            d = "D"
        if d == "U":
            slope += 1
            t1 = height - p
            t2 = t1 + height
            delta[t1] -= 2
            delta[t2] += 2
        else:
            slope -= 1
            t1 = p
            t2 = t1 + height
            delta[t1] += 2
            delta[t2] -= 2
    best = cur
    for t in range(1, period + 1):
        cur += slope
        if cur > best:
            best = cur
        slope += delta[t]
    return best


def ref_3281(start, d: int) -> int:
    validate_domain(3281, start, d)
    arr = sorted(start)
    lo, hi = 0, arr[-1] + d - arr[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        prev = arr[0]
        ok = True
        for i in range(1, len(arr)):
            nxt = max(prev + mid, arr[i])
            if nxt > arr[i] + d:
                ok = False
                break
            prev = nxt
        if ok:
            lo = mid
        else:
            hi = mid - 1
    return lo


def ref_3282(nums) -> int:
    validate_domain(3282, nums)
    ans = 0
    mx = 0
    for i in range(len(nums) - 1):
        if nums[i] > mx:
            mx = nums[i]
        ans += mx
    return ans


def ref_3284(nums) -> int:
    validate_domain(3284, nums)
    def run_dir(step: int) -> int:
        total = 0
        cnt = 0
        cur_sum = 0
        prev = None
        for x in nums:
            if prev is not None and x - prev == step:
                cnt += 1
                cur_sum = (cur_sum + cnt * x) % MOD
            else:
                cnt = 1
                cur_sum = x % MOD
            total = (total + cur_sum) % MOD
            prev = x
        return total

    return (run_dir(1) + run_dir(-1) - sum(nums)) % MOD


def ref_3286(grid, health: int) -> bool:
    validate_domain(3286, grid, health)
    m, n = len(grid), len(grid[0])
    INF = 10**9
    dist = [[INF] * n for _ in range(m)]
    dist[0][0] = grid[0][0]
    dq = deque([(0, 0)])
    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                w = grid[nr][nc]
                if d + w < dist[nr][nc]:
                    dist[nr][nc] = d + w
                    if w == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))
    return dist[m - 1][n - 1] < health


def ref_3288(coordinates, k: int) -> int:
    validate_domain(3288, coordinates, k)
    import bisect
    xk, yk = coordinates[k]
    left = [(x, y) for x, y in coordinates if x < xk and y < yk]
    right = [(x, y) for x, y in coordinates if x > xk and y > yk]

    def lis_2d(pts) -> int:
        pts.sort(key=lambda p: (p[0], -p[1]))
        tails = []
        for _, y in pts:
            idx = bisect.bisect_left(tails, y)
            if idx == len(tails):
                tails.append(y)
            else:
                tails[idx] = y
        return len(tails)

    return 1 + lis_2d(left) + lis_2d(right)


def ref_3291(words, target: str) -> int:
    validate_domain(3291, words, target)
    trie = {}
    for w in words:
        node = trie
        for ch in w:
            node = node.setdefault(ch, {})
    n = len(target)
    max_reach = [0] * n
    for i in range(n):
        node = trie
        j = i
        while j < n and target[j] in node:
            node = node[target[j]]
            j += 1
        max_reach[i] = j - i
    steps = 0
    cur_end = 0
    farthest = 0
    for i in range(n):
        if i > farthest:
            return -1
        if i + max_reach[i] > farthest:
            farthest = i + max_reach[i]
        if i == cur_end:
            steps += 1
            cur_end = farthest
            if cur_end >= n:
                return steps
    return steps if cur_end >= n else -1


def ref_3294(node):
    validate_domain(3294, node)
    return list(node)


def ref_3299(nums) -> int:
    validate_domain(3299, nums)
    def calc(step: int) -> int:
        cnt = defaultdict(int)
        tot = defaultdict(int)
        ans = 0
        for x in nums:
            nc = (1 + cnt[x - step]) % MOD
            nt = (tot[x - step] + nc * x) % MOD
            ans = (ans + nt) % MOD
            cnt[x] = (cnt[x] + nc) % MOD
            tot[x] = (tot[x] + nt) % MOD
        return ans

    return (calc(1) + calc(-1) - sum(nums)) % MOD


def ref_3302(word1: str, word2: str):
    validate_domain(3302, word1, word2)
    n, m = len(word1), len(word2)
    last = [-1] * (m + 1)
    last[m] = n
    j = m - 1
    for i in range(n - 1, -1, -1):
        if j >= 0 and word1[i] == word2[j]:
            last[j] = i
            j -= 1
    res = []
    j = 0
    used = False
    for i in range(n):
        if j == m:
            break
        if word1[i] == word2[j]:
            res.append(i)
            j += 1
        elif not used and last[j + 1] > i:
            used = True
            res.append(i)
            j += 1
    return res if len(res) == m else []


def ref_3306(word: str, k: int) -> int:
    validate_domain(3306, word, k)
    vowels = set("aeiou")

    def at_least(limit: int) -> int:
        vcnt = {}
        cons = 0
        left = 0
        ans = 0
        n = len(word)
        for right, ch in enumerate(word):
            if ch in vowels:
                vcnt[ch] = vcnt.get(ch, 0) + 1
            else:
                cons += 1
            while len(vcnt) == 5 and cons >= limit:
                ans += n - right
                lch = word[left]
                if lch in vowels:
                    vcnt[lch] -= 1
                    if vcnt[lch] == 0:
                        del vcnt[lch]
                else:
                    cons -= 1
                left += 1
        return ans

    return at_least(k) - at_least(k + 1)


def ref_3313(edges):
    validate_domain(3313, edges)
    n = len(edges) + 1
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def bfs(start: int):
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        last = start
        while q:
            u = q.popleft()
            last = u
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return last, dist

    a, _ = bfs(0)
    b, da = bfs(a)
    _, db = bfs(b)
    return [a if da[i] >= db[i] else b for i in range(n)]


def ref_3316(source: str, pattern: str, targetIndices) -> int:
    validate_domain(3316, source, pattern, targetIndices)
    m = len(pattern)
    tset = set(targetIndices)
    NEG = -(10**9)
    dp = [NEG] * (m + 1)
    dp[0] = 0
    for i, ch in enumerate(source):
        in_t = 1 if i in tset else 0
        for j in range(m, 0, -1):
            if dp[j] != NEG:
                dp[j] += in_t
            if ch == pattern[j - 1] and dp[j - 1] != NEG and dp[j - 1] > dp[j]:
                dp[j] = dp[j - 1]
        dp[0] += in_t
    return dp[m]


def ref_3319(root, k: int) -> int:
    validate_domain(3319, root, k)
    tree = _tree_from_level(root)
    sizes = []

    def dfs(node):
        if node is None:
            return True, 0
        ok_l, hl = dfs(node[1])
        ok_r, hr = dfs(node[2])
        if ok_l and ok_r and hl == hr:
            h = hl + 1
            sizes.append((1 << h) - 1)
            return True, h
        return False, 0

    dfs(tree)
    sizes.sort(reverse=True)
    return sizes[k - 1] if len(sizes) >= k else -1


def ref_3323(intervals, k: int) -> int:
    validate_domain(3323, intervals, k)
    arr = sorted(intervals)
    merged = []
    for s, e in arr:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        elif e > merged[-1][1]:
            merged[-1][1] = e
    m = len(merged)
    max_bridge = 0
    r = 0
    for l in range(m):
        while r < m and merged[r][0] <= merged[l][1] + k:
            r += 1
        if r - 1 - l > max_bridge:
            max_bridge = r - 1 - l
    return m - max_bridge


def ref_3326(nums) -> int:
    validate_domain(3326, nums)
    def spf(x: int) -> int:
        if x % 2 == 0:
            return 2
        d = 3
        while d * d <= x:
            if x % d == 0:
                return d
            d += 2
        return x

    arr = list(nums)
    ops = 0
    for i in range(len(arr) - 2, -1, -1):
        if arr[i] > arr[i + 1]:
            arr[i] = spf(arr[i])
            ops += 1
            if arr[i] > arr[i + 1]:
                return -1
    return ops


def ref_3329(s: str, k: int) -> int:
    validate_domain(3329, s, k)
    cnt = {}
    left = 0
    ans = 0
    n = len(s)
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while cnt[ch] >= k:
            ans += n - right
            lch = s[left]
            cnt[lch] -= 1
            left += 1
    return ans


def ref_3331(parent, s: str):
    validate_domain(3331, parent, s)
    n = len(parent)
    children = [[] for _ in range(n)]
    for i in range(1, n):
        children[parent[i]].append(i)
    new_parent = list(parent)
    last_seen = {}

    def dfs_reparent(u: int):
        ch = s[u]
        prev = last_seen.get(ch)
        if prev is not None:
            new_parent[u] = prev
        last_seen[ch] = u
        for v in children[u]:
            dfs_reparent(v)
        if prev is None:
            del last_seen[ch]
        else:
            last_seen[ch] = prev

    dfs_reparent(0)
    new_children = [[] for _ in range(n)]
    for i in range(1, n):
        new_children[new_parent[i]].append(i)
    order = [0]
    for u in order:
        for v in new_children[u]:
            order.append(v)
    sz = [1] * n
    for u in reversed(order):
        if u != 0:
            sz[new_parent[u]] += sz[u]
    return sz


def ref_3339(n: int, m: int, k: int) -> int:
    validate_domain(3339, n, m, k)
    even = m // 2
    odd = m - even
    dp0 = [0] * (k + 1)
    dp1 = [0] * (k + 1)
    dp0[0] = even
    dp1[0] = odd
    for _ in range(1, n):
        ndp0 = [0] * (k + 1)
        ndp1 = [0] * (k + 1)
        for c in range(k + 1):
            ways_any = (dp0[c] + dp1[c]) % MOD
            ndp1[c] = (ways_any * odd) % MOD
            ndp0[c] = (dp1[c] * even) % MOD
            if c > 0:
                ndp0[c] = (ndp0[c] + dp0[c - 1] * even) % MOD
        dp0, dp1 = ndp0, ndp1
    return (dp0[k] + dp1[k]) % MOD


def ref_3341(moveTime) -> int:
    validate_domain(3341, moveTime)
    n, m = len(moveTime), len(moveTime[0])
    INF = 10**18
    dist = [[INF] * m for _ in range(n)]
    dist[0][0] = 0
    pq = [(0, 0, 0)]
    while pq:
        t, r, c = heapq.heappop(pq)
        if t > dist[r][c]:
            continue
        if r == n - 1 and c == m - 1:
            return t
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m:
                nt = max(t, moveTime[nr][nc]) + 1
                if nt < dist[nr][nc]:
                    dist[nr][nc] = nt
                    heapq.heappush(pq, (nt, nr, nc))
    return dist[n - 1][m - 1]


def ref_3342(moveTime) -> int:
    validate_domain(3342, moveTime)
    n, m = len(moveTime), len(moveTime[0])
    INF = 10**18
    dist = [[INF] * m for _ in range(n)]
    dist[0][0] = 0
    pq = [(0, 0, 0)]
    while pq:
        t, r, c = heapq.heappop(pq)
        if t > dist[r][c]:
            continue
        if r == n - 1 and c == m - 1:
            return t
        step = 1 + ((r + c) & 1)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m:
                nt = max(t, moveTime[nr][nc]) + step
                if nt < dist[nr][nc]:
                    dist[nr][nc] = nt
                    heapq.heappush(pq, (nt, nr, nc))
    return dist[n - 1][m - 1]


def ref_3344(s: int) -> int:
    validate_domain(3344, s)
    def total_sum(n: int) -> int:
        if n <= 1:
            return 0
        i_sum = (n - 1) * n // 2
        or_sum = 0
        for b in range(12):
            period = 1 << (b + 1)
            half = 1 << b
            full = n // period
            rem = n % period
            zeros = full * half + min(rem, half)
            or_sum += (n * n - zeros * zeros) << b
        return i_sum * or_sum

    lo, hi = 1, 1200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if total_sum(mid) <= s:
            lo = mid
        else:
            hi = mid - 1
    return lo


def ref_3347(nums, k: int, numOperations: int) -> int:
    validate_domain(3347, nums, k, numOperations)
    import bisect
    arr = sorted(nums)
    n = len(arr)
    freq = Counter(arr)
    ans = 0
    r = 0
    for l in range(n):
        while r < n and arr[r] - arr[l] <= 2 * k:
            r += 1
        ans = max(ans, min(r - l, numOperations))
    for v, c in freq.items():
        lo = bisect.bisect_left(arr, v - k)
        hi = bisect.bisect_right(arr, v + k)
        ans = max(ans, min(hi - lo, c + numOperations))
    return ans


def ref_3351(nums) -> int:
    validate_domain(3351, nums)
    cnt = defaultdict(int)
    tot = defaultdict(int)
    for x in nums:
        nc = (1 + cnt[x - 1] + cnt[x + 1]) % MOD
        nt = (tot[x - 1] + tot[x + 1] + nc * x) % MOD
        cnt[x] = (cnt[x] + nc) % MOD
        tot[x] = (tot[x] + nt) % MOD
    return sum(tot.values()) % MOD


def ref_3353(nums) -> int:
    validate_domain(3353, nums)
    return sum(1 for i in range(len(nums) - 1) if nums[i] != nums[i + 1])


def ref_3355(nums, queries) -> bool:
    validate_domain(3355, nums, queries)
    n = len(nums)
    diff = [0] * (n + 1)
    for l, r in queries:
        diff[l] += 1
        diff[r + 1] -= 1
    cur = 0
    for i in range(n):
        cur += diff[i]
        if cur < nums[i]:
            return False
    return True


def ref_3356(nums, queries) -> int:
    validate_domain(3356, nums, queries)
    n = len(nums)
    diff = [0] * (n + 1)
    cur = 0
    k = 0
    for i in range(n):
        while cur + diff[i] < nums[i]:
            if k == len(queries):
                return -1
            l, r, val = queries[k]
            k += 1
            if r >= i:
                diff[max(l, i)] += val
                diff[r + 1] -= val
        cur += diff[i]
    return k


def ref_3359(grid, k: int) -> int:
    validate_domain(3359, grid, k)
    m, n = len(grid), len(grid[0])
    width = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            if grid[r][c] <= k:
                if c > 0 and grid[r][c - 1] <= k and grid[r][c - 1] >= grid[r][c]:
                    width[r][c] = width[r][c - 1] + 1
                else:
                    width[r][c] = 1
    total = 0
    for c in range(n):
        stack = []
        col_sum = 0
        for r in range(m):
            w = width[r][c]
            cnt = 1
            while stack and stack[-1][0] >= w:
                pw, pcnt = stack.pop()
                col_sum -= pw * pcnt
                cnt += pcnt
            stack.append((w, cnt))
            col_sum += w * cnt
            total += col_sum
    return total


REFERENCES = {
    2753: ref_2753, 2864: ref_2864, 2930: ref_2930, 2931: ref_2931,
    2936: ref_2936, 2946: ref_2946, 2969: ref_2969, 3023: ref_3023,
    3037: ref_3037, 3064: ref_3064, 3094: ref_3094, 3205: ref_3205,
    3221: ref_3221, 3245: ref_3245, 3247: ref_3247, 3249: ref_3249,
    3250: ref_3250, 3253: ref_3253, 3260: ref_3260, 3263: ref_3263,
    3269: ref_3269, 3275: ref_3275, 3279: ref_3279, 3281: ref_3281,
    3282: ref_3282, 3284: ref_3284, 3286: ref_3286, 3288: ref_3288,
    3291: ref_3291, 3294: ref_3294, 3299: ref_3299, 3302: ref_3302,
    3306: ref_3306, 3313: ref_3313, 3316: ref_3316, 3319: ref_3319,
    3323: ref_3323, 3326: ref_3326, 3329: ref_3329, 3331: ref_3331,
    3339: ref_3339, 3341: ref_3341, 3342: ref_3342, 3344: ref_3344,
    3347: ref_3347, 3351: ref_3351, 3353: ref_3353, 3355: ref_3355,
    3356: ref_3356, 3359: ref_3359,
}
