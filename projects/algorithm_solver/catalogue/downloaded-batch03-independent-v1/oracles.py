"""Independent definition-based references for downloaded batch 03 (88 problems)."""
from collections import Counter, defaultdict, deque
from bisect import bisect_left
from functools import lru_cache
from itertools import combinations, permutations, product
import heapq
import math
import re

IDS = (
    11, 15, 22, 26, 27, 31, 33, 34, 36, 38, 39, 40, 41, 42, 43, 45, 46, 48, 49, 50,
    52, 53, 54, 55, 56, 57, 59, 60, 62, 63, 64, 71, 72, 73, 74, 75, 76, 77, 78, 79,
    80, 81, 84, 88, 89, 90, 91, 93, 96, 97, 115, 120, 122, 123, 127, 128, 130, 131,
    134, 135, 136, 137, 139, 152, 154, 164, 165, 166, 174, 186, 187, 200, 201, 207,
    210, 216, 223, 227, 239, 241, 310, 331, 332, 347, 373, 375, 388, 400
)

FUNCTIONAL_ADAPTER_IDS = (26, 27, 31, 48, 73, 75, 80, 88, 130, 186)

MANDATORY_FAILURES = {
    (41, 'python'): 'Allocated set of input values violates mandatory O(1) auxiliary space',
    (41, 'javascript'): 'Allocated Set of input values violates mandatory O(1) auxiliary space',
    (164, 'python'): 'Comparison sort violates mandatory linear runtime complexity',
    (164, 'javascript'): 'Comparison sort violates mandatory linear runtime complexity',
    (373, 'python'): 'Materializing all len(nums1)*len(nums2) pairs violates subquadratic memory and time bounds',
    (373, 'javascript'): 'Materializing all len(nums1)*len(nums2) pairs violates subquadratic memory and time bounds',
}


def expected(pid, a):
    x = a[0]
    if pid == 11:
        # Container With Most Water
        return max((j - i) * min(x[i], x[j]) for i in range(len(x)) for j in range(i + 1, len(x))) if len(x) >= 2 else 0
    if pid == 15:
        # 3Sum: unique triplets that sum to 0
        triplets = set()
        n = len(x)
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    if x[i] + x[j] + x[k] == 0:
                        triplets.add(tuple(sorted([x[i], x[j], x[k]])))
        return sorted(list(t) for t in triplets)
    if pid == 22:
        # Generate Parentheses
        res = []
        def gen(s, open_c, close_c):
            if len(s) == 2 * x:
                res.append(s)
                return
            if open_c < x:
                gen(s + '(', open_c + 1, close_c)
            if close_c < open_c:
                gen(s + ')', open_c, close_c + 1)
        gen('', 0, 0)
        return sorted(res)
    if pid == 26:
        # Remove Duplicates from Sorted Array (functional adapter)
        res = []
        for v in x:
            if not res or res[-1] != v:
                res.append(v)
        return res
    if pid == 27:
        # Remove Element (functional adapter)
        return [v for v in x if v != a[1]]
    if pid == 31:
        # Next Permutation (functional adapter)
        nums = list(x)
        i = len(nums) - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1
        if i >= 0:
            j = len(nums) - 1
            while nums[j] <= nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        nums[i + 1:] = reversed(nums[i + 1:])
        return nums
    if pid == 33:
        # Search in Rotated Sorted Array
        return x.index(a[1]) if a[1] in x else -1
    if pid == 34:
        # Find First and Last Position of Element in Sorted Array
        target = a[1]
        if target not in x:
            return [-1, -1]
        return [x.index(target), len(x) - 1 - x[::-1].index(target)]
    if pid == 36:
        # Valid Sudoku
        for r in range(9):
            row = [c for c in x[r] if c != '.']
            if len(row) != len(set(row)):
                return False
        for c in range(9):
            col = [x[r][c] for r in range(9) if x[r][c] != '.']
            if len(col) != len(set(col)):
                return False
        for br in range(3):
            for bc in range(3):
                blk = [x[r][c] for r in range(br * 3, (br + 1) * 3) for c in range(bc * 3, (bc + 1) * 3) if x[r][c] != '.']
                if len(blk) != len(set(blk)):
                    return False
        return True
    if pid == 38:
        # Count and Say
        cur = '1'
        for _ in range(x - 1):
            nxt = []
            i = 0
            while i < len(cur):
                j = i
                while j < len(cur) and cur[j] == cur[i]:
                    j += 1
                nxt.append(str(j - i) + cur[i])
                i = j
            cur = ''.join(nxt)
        return cur
    if pid == 39:
        # Combination Sum
        cands = sorted(set(x))
        target = a[1]
        res = []
        def dfs(idx, cur, rem):
            if rem == 0:
                res.append(cur)
                return
            for i in range(idx, len(cands)):
                if cands[i] > rem:
                    break
                dfs(i, cur + [cands[i]], rem - cands[i])
        dfs(0, [], target)
        return sorted(res)
    if pid == 40:
        # Combination Sum II
        cands = sorted(x)
        target = a[1]
        res = []
        def dfs(idx, cur, rem):
            if rem == 0:
                res.append(cur)
                return
            for i in range(idx, len(cands)):
                if i > idx and cands[i] == cands[i - 1]:
                    continue
                if cands[i] > rem:
                    break
                dfs(i + 1, cur + [cands[i]], rem - cands[i])
        dfs(0, [], target)
        return sorted(res)
    if pid == 41:
        # First Missing Positive
        s = set(x)
        v = 1
        while v in s:
            v += 1
        return v
    if pid == 42:
        # Trapping Rain Water
        n = len(x)
        if n < 3:
            return 0
        l_max = [0] * n
        r_max = [0] * n
        l_max[0] = x[0]
        for i in range(1, n):
            l_max[i] = max(l_max[i - 1], x[i])
        r_max[-1] = x[-1]
        for i in range(n - 2, -1, -1):
            r_max[i] = max(r_max[i + 1], x[i])
        return sum(max(0, min(l_max[i], r_max[i]) - x[i]) for i in range(n))
    if pid == 43:
        # Multiply Strings
        return str(int(x) * int(a[1]))
    if pid == 45:
        # Jump Game II
        n = len(x)
        if n <= 1:
            return 0
        jumps, cur_end, farthest = 0, 0, 0
        for i in range(n - 1):
            farthest = max(farthest, i + x[i])
            if i == cur_end:
                jumps += 1
                cur_end = farthest
        return jumps
    if pid == 46:
        # Permutations
        return sorted(list(p) for p in permutations(x))
    if pid == 48:
        # Rotate Image (functional adapter)
        n = len(x)
        return [[x[n - 1 - r][c] for r in range(n)] for c in range(n)]
    if pid == 49:
        # Group Anagrams
        groups = defaultdict(list)
        for s in x:
            groups[''.join(sorted(s))].append(s)
        return sorted(sorted(g) for g in groups.values())
    if pid == 50:
        # Pow(x, n)
        return float(x ** a[1])
    if pid == 52:
        # N-Queens II
        n = x
        cols, diag1, diag2 = set(), set(), set()
        count = 0
        def backtrack(r):
            nonlocal count
            if r == n:
                count += 1
                return
            for c in range(n):
                if c not in cols and (r - c) not in diag1 and (r + c) not in diag2:
                    cols.add(c)
                    diag1.add(r - c)
                    diag2.add(r + c)
                    backtrack(r + 1)
                    cols.remove(c)
                    diag1.remove(r - c)
                    diag2.remove(r + c)
        backtrack(0)
        return count
    if pid == 53:
        # Maximum Subarray
        cur = best = x[0]
        for v in x[1:]:
            cur = max(v, cur + v)
            best = max(best, cur)
        return best
    if pid == 54:
        # Spiral Matrix
        if not x or not x[0]:
            return []
        res = []
        top, bottom, left, right = 0, len(x) - 1, 0, len(x[0]) - 1
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                res.append(x[top][c])
            top += 1
            for r in range(top, bottom + 1):
                res.append(x[r][right])
            right -= 1
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    res.append(x[bottom][c])
                bottom -= 1
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    res.append(x[r][left])
                left += 1
        return res
    if pid == 55:
        # Jump Game
        farthest = 0
        for i, v in enumerate(x):
            if i > farthest:
                return False
            farthest = max(farthest, i + v)
        return True
    if pid == 56:
        # Merge Intervals
        if not x:
            return []
        intervals = sorted(x, key=lambda iv: iv[0])
        res = [intervals[0]]
        for iv in intervals[1:]:
            if iv[0] <= res[-1][1]:
                res[-1] = [res[-1][0], max(res[-1][1], iv[1])]
            else:
                res.append(iv)
        return res
    if pid == 57:
        # Insert Interval
        intervals = list(x) + [a[1]]
        return expected(56, [intervals])
    if pid == 59:
        # Spiral Matrix II
        n = x
        mat = [[0] * n for _ in range(n)]
        val = 1
        top, bottom, left, right = 0, n - 1, 0, n - 1
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                mat[top][c] = val
                val += 1
            top += 1
            for r in range(top, bottom + 1):
                mat[r][right] = val
                val += 1
            right -= 1
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    mat[bottom][c] = val
                    val += 1
                bottom -= 1
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    mat[r][left] = val
                    val += 1
                left += 1
        return mat
    if pid == 60:
        # Permutation Sequence
        n, k = x, a[1]
        nums = list(range(1, n + 1))
        fact = [1] * (n + 1)
        for i in range(1, n + 1):
            fact[i] = fact[i - 1] * i
        k -= 1
        res = []
        for i in range(n, 0, -1):
            idx = k // fact[i - 1]
            k %= fact[i - 1]
            res.append(str(nums.pop(idx)))
        return ''.join(res)
    if pid == 62:
        # Unique Paths
        return math.comb(x + a[1] - 2, x - 1)
    if pid == 63:
        # Unique Paths II
        m, n = len(x), len(x[0])
        dp = [0] * n
        dp[0] = 1 if x[0][0] == 0 else 0
        for r in range(m):
            for c in range(n):
                if x[r][c] == 1:
                    dp[c] = 0
                elif c > 0:
                    dp[c] += dp[c - 1]
        return dp[-1]
    if pid == 64:
        # Minimum Path Sum
        m, n = len(x), len(x[0])
        dp = [0] * n
        dp[0] = x[0][0]
        for c in range(1, n):
            dp[c] = dp[c - 1] + x[0][c]
        for r in range(1, m):
            dp[0] += x[r][0]
            for c in range(1, n):
                dp[c] = min(dp[c], dp[c - 1]) + x[r][c]
        return dp[-1]
    if pid == 71:
        # Simplify Path
        stack = []
        for part in x.split('/'):
            if part in ('', '.'):
                continue
            if part == '..':
                if stack:
                    stack.pop()
            else:
                stack.append(part)
        return '/' + '/'.join(stack)
    if pid == 72:
        # Edit Distance
        w1, w2 = x, a[1]
        dp = list(range(len(w2) + 1))
        for i, c1 in enumerate(w1):
            nxt = [i + 1] + [0] * len(w2)
            for j, c2 in enumerate(w2):
                if c1 == c2:
                    nxt[j + 1] = dp[j]
                else:
                    nxt[j + 1] = 1 + min(dp[j], dp[j + 1], nxt[j])
            dp = nxt
        return dp[-1]
    if pid == 73:
        # Set Matrix Zeroes (functional adapter)
        m, n = len(x), len(x[0])
        zero_rows = {r for r in range(m) for c in range(n) if x[r][c] == 0}
        zero_cols = {c for r in range(m) for c in range(n) if x[r][c] == 0}
        return [[0 if (r in zero_rows or c in zero_cols) else x[r][c] for c in range(n)] for r in range(m)]
    if pid == 74:
        # Search a 2D Matrix
        return any(a[1] in row for row in x)
    if pid == 75:
        # Sort Colors (functional adapter)
        return sorted(x)
    if pid == 76:
        # Minimum Window Substring
        s, t = x, a[1]
        t_counts = Counter(t)
        required = len(t_counts)
        l = 0
        formed = 0
        window = defaultdict(int)
        ans = (float('inf'), 0, 0)
        for r, ch in enumerate(s):
            window[ch] += 1
            if ch in t_counts and window[ch] == t_counts[ch]:
                formed += 1
            while l <= r and formed == required:
                if r - l + 1 < ans[0]:
                    ans = (r - l + 1, l, r)
                window[s[l]] -= 1
                if s[l] in t_counts and window[s[l]] < t_counts[s[l]]:
                    formed -= 1
                l += 1
        return '' if ans[0] == float('inf') else s[ans[1]:ans[2] + 1]
    if pid == 77:
        # Combinations
        return sorted(list(c) for c in combinations(range(1, x + 1), a[1]))
    if pid == 78:
        # Subsets
        res = []
        for r in range(len(x) + 1):
            for c in combinations(x, r):
                res.append(list(c))
        return sorted(res)
    if pid == 79:
        # Word Search
        board, word = x, a[1]
        m, n = len(board), len(board[0])
        def dfs(r, c, k, visited):
            if k == len(word):
                return True
            if r < 0 or r >= m or c < 0 or c >= n or (r, c) in visited or board[r][c] != word[k]:
                return False
            visited.add((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if dfs(r + dr, c + dc, k + 1, visited):
                    return True
            visited.remove((r, c))
            return False
        for r in range(m):
            for c in range(n):
                if dfs(r, c, 0, set()):
                    return True
        return False
    if pid == 80:
        # Remove Duplicates from Sorted Array II (functional adapter)
        res = []
        for v in x:
            if len(res) < 2 or res[-2] != v:
                res.append(v)
        return res
    if pid == 81:
        # Search in Rotated Sorted Array II
        return a[1] in x
    if pid == 84:
        # Largest Rectangle in Histogram
        stack = []
        max_area = 0
        h = x + [0]
        for i, val in enumerate(h):
            while stack and h[stack[-1]] > val:
                height = h[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                max_area = max(max_area, height * width)
            stack.append(i)
        return max_area
    if pid == 88:
        # Merge Sorted Array (functional adapter)
        nums1, m, nums2, n = x, a[1], a[2], a[3]
        return sorted(nums1[:m] + nums2[:n])
    if pid == 89:
        # Gray Code
        return [i ^ (i >> 1) for i in range(1 << x)]
    if pid == 90:
        # Subsets II
        nums = sorted(x)
        res = []
        def dfs(idx, cur):
            res.append(cur)
            for i in range(idx, len(nums)):
                if i > idx and nums[i] == nums[i - 1]:
                    continue
                dfs(i + 1, cur + [nums[i]])
        dfs(0, [])
        return sorted(res)
    if pid == 91:
        # Decode Ways
        s = x
        if not s or s[0] == '0':
            return 0
        dp = [0] * (len(s) + 1)
        dp[0] = 1
        dp[1] = 1
        for i in range(2, len(s) + 1):
            if s[i - 1] != '0':
                dp[i] += dp[i - 1]
            two = int(s[i - 2:i])
            if 10 <= two <= 26:
                dp[i] += dp[i - 2]
        return dp[-1]
    if pid == 93:
        # Restore IP Addresses
        s = x
        res = []
        def dfs(start, parts):
            if len(parts) == 4:
                if start == len(s):
                    res.append('.'.join(parts))
                return
            for length in range(1, 4):
                if start + length > len(s):
                    break
                part = s[start:start + length]
                if (part.startswith('0') and len(part) > 1) or int(part) > 255:
                    continue
                dfs(start + length, parts + [part])
        dfs(0, [])
        return sorted(res)
    if pid == 96:
        # Unique Binary Search Trees
        return math.comb(2 * x, x) // (x + 1)
    if pid == 97:
        # Interleaving String
        s1, s2, s3 = x, a[1], a[2]
        if len(s1) + len(s2) != len(s3):
            return False
        @lru_cache(None)
        def dfs(i, j):
            if i == len(s1) and j == len(s2):
                return True
            res = False
            if i < len(s1) and s1[i] == s3[i + j]:
                res = res or dfs(i + 1, j)
            if j < len(s2) and s2[j] == s3[i + j]:
                res = res or dfs(i, j + 1)
            return res
        return dfs(0, 0)
    if pid == 115:
        # Distinct Subsequences
        s, t = x, a[1]
        dp = [0] * (len(t) + 1)
        dp[0] = 1
        for sc in s:
            for tc_idx in range(len(t) - 1, -1, -1):
                if sc == t[tc_idx]:
                    dp[tc_idx + 1] += dp[tc_idx]
        return dp[-1]
    if pid == 120:
        # Triangle
        dp = list(x[-1])
        for r in range(len(x) - 2, -1, -1):
            for c in range(len(x[r])):
                dp[c] = x[r][c] + min(dp[c], dp[c + 1])
        return dp[0]
    if pid == 122:
        # Best Time to Buy and Sell Stock II
        return sum(max(0, x[i] - x[i - 1]) for i in range(1, len(x)))
    if pid == 123:
        # Best Time to Buy and Sell Stock III
        b1, s1 = -float('inf'), 0
        b2, s2 = -float('inf'), 0
        for p in x:
            b1 = max(b1, -p)
            s1 = max(s1, b1 + p)
            b2 = max(b2, s1 - p)
            s2 = max(s2, b2 + p)
        return s2
    if pid == 127:
        # Word Ladder
        begin, end, words = x, a[1], set(a[2])
        if end not in words:
            return 0
        queue = deque([(begin, 1)])
        seen = {begin}
        while queue:
            word, dist = queue.popleft()
            if word == end:
                return dist
            for i in range(len(word)):
                for ch in 'abcdefghijklmnopqrstuvwxyz':
                    cand = word[:i] + ch + word[i + 1:]
                    if cand in words and cand not in seen:
                        seen.add(cand)
                        queue.append((cand, dist + 1))
        return 0
    if pid == 128:
        # Longest Consecutive Sequence
        s = set(x)
        best = 0
        for v in s:
            if v - 1 not in s:
                cur = v
                cnt = 1
                while cur + 1 in s:
                    cur += 1
                    cnt += 1
                best = max(best, cnt)
        return best
    if pid == 130:
        # Surrounded Regions (functional adapter)
        board = [row[:] for row in x]
        m, n = len(board), len(board[0])
        def dfs(r, c):
            if r < 0 or r >= m or c < 0 or c >= n or board[r][c] != 'O':
                return
            board[r][c] = '#'
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                dfs(r + dr, c + dc)
        for r in range(m):
            dfs(r, 0)
            dfs(r, n - 1)
        for c in range(n):
            dfs(0, c)
            dfs(m - 1, c)
        for r in range(m):
            for c in range(n):
                if board[r][c] == '#':
                    board[r][c] = 'O'
                elif board[r][c] == 'O':
                    board[r][c] = 'X'
        return board
    if pid == 131:
        # Palindrome Partitioning
        s = x
        res = []
        def dfs(idx, cur):
            if idx == len(s):
                res.append(cur)
                return
            for j in range(idx + 1, len(s) + 1):
                sub = s[idx:j]
                if sub == sub[::-1]:
                    dfs(j, cur + [sub])
        dfs(0, [])
        return sorted(res)
    if pid == 134:
        # Gas Station
        gas, cost = x, a[1]
        if sum(gas) < sum(cost):
            return -1
        start = 0
        tank = 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:
                start = i + 1
                tank = 0
        return start
    if pid == 135:
        # Candy
        n = len(x)
        candies = [1] * n
        for i in range(1, n):
            if x[i] > x[i - 1]:
                candies[i] = candies[i - 1] + 1
        for i in range(n - 2, -1, -1):
            if x[i] > x[i + 1]:
                candies[i] = max(candies[i], candies[i + 1] + 1)
        return sum(candies)
    if pid == 136:
        # Single Number
        res = 0
        for v in x:
            res ^= v
        return res
    if pid == 137:
        # Single Number II
        ones, twos = 0, 0
        for v in x:
            ones = (ones ^ v) & ~twos
            twos = (twos ^ v) & ~ones
        ones &= 0xFFFFFFFF
        return ones if ones <= 0x7FFFFFFF else ones - 0x100000000
    if pid == 139:
        # Word Break
        s, words = x, set(a[1])
        dp = [True] + [False] * len(s)
        for i in range(1, len(s) + 1):
            for j in range(i):
                if dp[j] and s[j:i] in words:
                    dp[i] = True
                    break
        return dp[-1]
    if pid == 152:
        # Maximum Product Subarray
        max_p = min_p = best = x[0]
        for v in x[1:]:
            cands = (v, max_p * v, min_p * v)
            max_p = max(cands)
            min_p = min(cands)
            best = max(best, max_p)
        return best
    if pid == 154:
        # Find Minimum in Rotated Sorted Array II
        return min(x)
    if pid == 164:
        # Maximum Gap
        if len(x) < 2:
            return 0
        ordered = sorted(x)
        return max(ordered[i] - ordered[i - 1] for i in range(1, len(ordered)))
    if pid == 165:
        # Compare Version Numbers
        v1 = [int(p) for p in x.split('.')]
        v2 = [int(p) for p in a[1].split('.')]
        max_l = max(len(v1), len(v2))
        v1 += [0] * (max_l - len(v1))
        v2 += [0] * (max_l - len(v2))
        for a_val, b_val in zip(v1, v2):
            if a_val < b_val:
                return -1
            if a_val > b_val:
                return 1
        return 0
    if pid == 166:
        # Fraction to Recurring Decimal
        num, den = x, a[1]
        if num == 0:
            return '0'
        res = []
        if (num < 0) ^ (den < 0):
            res.append('-')
        num, den = abs(num), abs(den)
        res.append(str(num // den))
        rem = num % den
        if rem == 0:
            return ''.join(res)
        res.append('.')
        seen = {}
        while rem != 0:
            if rem in seen:
                res.insert(seen[rem], '(')
                res.append(')')
                break
            seen[rem] = len(res)
            rem *= 10
            res.append(str(rem // den))
            rem %= den
        return ''.join(res)
    if pid == 174:
        # Dungeon Game
        m, n = len(x), len(x[0])
        dp = [[float('inf')] * (n + 1) for _ in range(m + 1)]
        dp[m][n - 1] = dp[m - 1][n] = 1
        for r in range(m - 1, -1, -1):
            for c in range(n - 1, -1, -1):
                need = min(dp[r + 1][c], dp[r][c + 1]) - x[r][c]
                dp[r][c] = max(1, need)
        return dp[0][0]
    if pid == 186:
        # Reverse Words in a String II (functional adapter)
        chars = list(x)
        chars.reverse()
        start = 0
        for i in range(len(chars) + 1):
            if i == len(chars) or chars[i] == ' ':
                chars[start:i] = reversed(chars[start:i])
                start = i + 1
        return chars
    if pid == 187:
        # Repeated DNA Sequences
        seen, repeated = set(), set()
        for i in range(len(x) - 9):
            sub = x[i:i + 10]
            if sub in seen:
                repeated.add(sub)
            else:
                seen.add(sub)
        return sorted(list(repeated))
    if pid == 200:
        # Number of Islands
        grid = [row[:] for row in x]
        m, n = len(grid), len(grid[0])
        count = 0
        def dfs(r, c):
            if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] != '1':
                return
            grid[r][c] = '0'
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                dfs(r + dr, c + dc)
        for r in range(m):
            for c in range(n):
                if grid[r][c] == '1':
                    count += 1
                    dfs(r, c)
        return count
    if pid == 201:
        # Bitwise AND of Numbers Range
        left, right = x, a[1]
        shift = 0
        while left < right:
            left >>= 1
            right >>= 1
            shift += 1
        return left << shift
    if pid == 207:
        # Course Schedule
        n, prereqs = x, a[1]
        adj = defaultdict(list)
        indeg = [0] * n
        for dest, src in prereqs:
            adj[src].append(dest)
            indeg[dest] += 1
        queue = deque([i for i in range(n) if indeg[i] == 0])
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for nxt in adj[node]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        return visited == n
    if pid == 210:
        # Course Schedule II
        n, prereqs = x, a[1]
        adj = defaultdict(list)
        indeg = [0] * n
        for dest, src in prereqs:
            adj[src].append(dest)
            indeg[dest] += 1
        queue = deque([i for i in range(n) if indeg[i] == 0])
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for nxt in adj[node]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        return order if len(order) == n else []
    if pid == 216:
        # Combination Sum III
        k, target = x, a[1]
        res = []
        def dfs(start, cur, rem):
            if len(cur) == k:
                if rem == 0:
                    res.append(cur)
                return
            for v in range(start, 10):
                if v > rem:
                    break
                dfs(v + 1, cur + [v], rem - v)
        dfs(1, [], target)
        return sorted(res)
    if pid == 223:
        # Rectangle Area
        ax1, ay1, ax2, ay2, bx1, by1, bx2, by2 = a
        area1 = (ax2 - ax1) * (ay2 - ay1)
        area2 = (bx2 - bx1) * (by2 - by1)
        overlap_w = max(0, min(ax2, bx2) - max(ax1, bx1))
        overlap_h = max(0, min(ay2, by2) - max(ay1, by1))
        return area1 + area2 - overlap_w * overlap_h
    if pid == 227:
        # Basic Calculator II
        s = x + '+'
        stack = []
        num = 0
        op = '+'
        for ch in s:
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch != ' ':
                if op == '+':
                    stack.append(num)
                elif op == '-':
                    stack.append(-num)
                elif op == '*':
                    stack.append(stack.pop() * num)
                elif op == '/':
                    top = stack.pop()
                    stack.append(int(top / num))
                op = ch
                num = 0
        return sum(stack)
    if pid == 239:
        # Sliding Window Maximum
        nums, k = x, a[1]
        q = deque()
        res = []
        for i, v in enumerate(nums):
            while q and q[0] <= i - k:
                q.popleft()
            while q and nums[q[-1]] <= v:
                q.pop()
            q.append(i)
            if i >= k - 1:
                res.append(nums[q[0]])
        return res
    if pid == 241:
        # Different Ways to Add Parentheses
        @lru_cache(None)
        def compute(expr):
            res = []
            for i, ch in enumerate(expr):
                if ch in '+-*':
                    left = compute(expr[:i])
                    right = compute(expr[i + 1:])
                    for l in left:
                        for r in right:
                            if ch == '+':
                                res.append(l + r)
                            elif ch == '-':
                                res.append(l - r)
                            elif ch == '*':
                                res.append(l * r)
            if not res:
                res.append(int(expr))
            return res
        return sorted(compute(x))
    if pid == 310:
        # Minimum Height Trees
        n, edges = x, a[1]
        if n <= 2:
            return sorted(list(range(n)))
        adj = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        leaves = deque([i for i in range(n) if len(adj[i]) == 1])
        remaining = n
        while remaining > 2:
            count = len(leaves)
            remaining -= count
            for _ in range(count):
                leaf = leaves.popleft()
                neighbor = adj[leaf].pop()
                adj[neighbor].remove(leaf)
                if len(adj[neighbor]) == 1:
                    leaves.append(neighbor)
        return sorted(list(leaves))
    if pid == 331:
        # Verify Preorder Serialization of a Binary Tree
        nodes = x.split(',')
        slots = 1
        for node in nodes:
            slots -= 1
            if slots < 0:
                return False
            if node != '#':
                slots += 2
        return slots == 0
    if pid == 332:
        # Reconstruct Itinerary
        adj = defaultdict(list)
        for src, dest in sorted(x, reverse=True):
            adj[src].append(dest)
        itinerary = []
        def visit(airport):
            while adj[airport]:
                visit(adj[airport].pop())
            itinerary.append(airport)
        visit('JFK')
        return itinerary[::-1]
    if pid == 347:
        # Top K Frequent Elements
        counts = Counter(x)
        return sorted([val for val, _ in counts.most_common(a[1])])
    if pid == 373:
        # Find K Pairs with Smallest Sums
        nums1, nums2, k = x, a[1], a[2]
        if not nums1 or not nums2 or k == 0:
            return []
        h = []
        for i in range(min(k, len(nums1))):
            heapq.heappush(h, (nums1[i] + nums2[0], i, 0))
        res = []
        while h and len(res) < k:
            _, i, j = heapq.heappop(h)
            res.append([nums1[i], nums2[j]])
            if j + 1 < len(nums2):
                heapq.heappush(h, (nums1[i] + nums2[j + 1], i, j + 1))
        return res
    if pid == 375:
        # Guess Number Higher or Lower II
        n = x
        dp = [[0] * (n + 2) for _ in range(n + 2)]
        for length in range(2, n + 1):
            for i in range(1, n - length + 2):
                j = i + length - 1
                dp[i][j] = min(pivot + max(dp[i][pivot - 1], dp[pivot + 1][j]) for pivot in range(i, j + 1))
        return dp[1][n]
    if pid == 388:
        # Longest Absolute File Path
        paths = {0: 0}
        max_len = 0
        for line in x.split('\n'):
            name = line.lstrip('\t')
            depth = len(line) - len(name)
            if '.' in name:
                max_len = max(max_len, paths.get(depth, 0) + len(name))
            else:
                paths[depth + 1] = paths.get(depth, 0) + len(name) + 1
        return max_len
    if pid == 400:
        # Nth Digit
        n = x
        digits = 1
        count = 9
        start = 1
        while n > digits * count:
            n -= digits * count
            digits += 1
            count *= 10
            start *= 10
        num = start + (n - 1) // digits
        idx = (n - 1) % digits
        return int(str(num)[idx])
    raise ValueError(f'unregistered oracle {pid}')


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(exact(l, r) for l, r in zip(a, b))
    if type(a) is dict:
        return set(a) == set(b) and all(exact(a[k], b[k]) for k in a)
    return a == b


def _typed_key(value):
    """Sortable recursive JSON value identity, keeping bool/int/float distinct."""
    kind = type(value)
    if kind is list:
        return ('list', tuple(_typed_key(item) for item in value))
    if kind is dict:
        return ('dict', tuple(sorted((_typed_key(key), _typed_key(item))
                                     for key, item in value.items())))
    if kind in (bool, int, str) or value is None:
        return (kind.__name__, value)
    if kind is float and math.isfinite(value):
        return ('float', value)
    raise ValueError('unsupported typed result value')


def _unordered_equal(value, want, *, inner_unordered=False):
    if type(value) is not list or type(want) is not list:
        return False
    def key(item):
        if not inner_unordered:
            return _typed_key(item)
        if type(item) is not list:
            raise ValueError('nested result collection must be a list')
        return tuple(sorted(_typed_key(part) for part in item))
    try:
        return sorted(key(item) for item in value) == sorted(key(item) for item in want)
    except (ValueError, TypeError, RecursionError):
        return False


def _smallest_pairs(args, value):
    """Check legal index-pair multiplicity and the kth-sum threshold, not ties.

    Repeated value-pairs are legitimate only when distinct input index pairs
    supply them. Counting pairs below the largest selected sum checks that no
    strictly smaller pair was omitted, independently of a chosen oracle witness.
    """
    if type(args) is not list or len(args) != 3 or type(value) is not list:
        return False
    nums1, nums2, k = args
    if (type(nums1) is not list or type(nums2) is not list or type(k) is not int or k < 0
            or any(type(x) is not int for x in nums1 + nums2)
            or any(a > b for a, b in zip(nums1, nums1[1:]))
            or any(a > b for a, b in zip(nums2, nums2[1:]))):
        return False
    if len(value) != min(k, len(nums1) * len(nums2)):
        return False
    if not value:
        return True
    first, second = Counter(nums1), Counter(nums2)
    selected = Counter()
    sums = []
    for pair in value:
        if type(pair) is not list or len(pair) != 2 or any(type(x) is not int for x in pair):
            return False
        a, b = pair
        selected[a, b] += 1
        if selected[a, b] > first[a] * second[b]:
            return False
        sums.append(a + b)
    threshold = max(sums)
    available_below = sum(bisect_left(nums2, threshold - a) for a in nums1)
    return available_below == sum(total < threshold for total in sums)


def matches(pid, args, value, want):
    if pid in (15, 39, 40, 77, 78, 90, 216):
        # Collections of combinations / subsets / triplets
        return _unordered_equal(value, want, inner_unordered=True)
    if pid in (22, 46, 93, 131, 187):
        # Permutations or collections of strings / partitions
        return _unordered_equal(value, want)
    if pid == 49:
        # Group Anagrams
        return _unordered_equal(value, want, inner_unordered=True)
    if pid == 50:
        # Pow(x, n)
        if type(value) not in (int, float):
            return False
        return math.isclose(value, want, rel_tol=1e-5, abs_tol=1e-7)
    if pid in (56, 57):
        # Disjoint intervals
        return _unordered_equal(value, want)
    if pid == 89:
        # Gray Code sequence validity predicate
        if type(args) is not list or len(args) != 1 or type(value) is not list:
            return False
        n = args[0]
        # Bound the shift by the supplied result size before evaluating it.
        if type(n) is not int or n < 1 or n > len(value).bit_length():
            return False
        if len(value) != (1 << n) or any(type(v) is not int or not 0 <= v < (1 << n) for v in value):
            return False
        if not value or value[0] != 0:
            return False
        if len(set(value)) != len(value):
            return False
        for i in range(len(value)):
            nxt = value[(i + 1) % len(value)]
            diff = value[i] ^ nxt
            if diff <= 0 or (diff & (diff - 1)) != 0:
                return False
        return True
    if pid == 210:
        # Course Schedule II validity predicate
        n, prereqs = args[0], args[1]
        if type(value) is not list:
            return False
        if not want:
            return value == []
        if len(value) != n or set(value) != set(range(n)):
            return False
        pos = {c: i for i, c in enumerate(value)}
        for dest, src in prereqs:
            if pos[src] >= pos[dest]:
                return False
        return True
    if pid in (241, 310, 347):
        # Lists where elements can appear in any order
        return _unordered_equal(value, want)
    if pid == 373:
        # Find K Pairs with Smallest Sums
        return _smallest_pairs(args, value)
    return exact(value, want)


def compare(pid, args, want, record, language):
    if 'error' in record:
        return False, 'candidate_error'
    kind = float if pid == 50 else type(want)
    types = {
        'python': {list: 'list', int: 'int', float: 'float', bool: 'bool', str: 'str'},
        'javascript': {list: 'object', int: 'number', float: 'number', bool: 'boolean', str: 'string'}
    }
    expected_type = types[language].get(kind)
    if record.get('result_type') != expected_type:
        return False, 'result_type'
    if not matches(pid, args, record.get('result'), want):
        return False, 'result_value'
    if not exact(record.get('args_before'), args) or not exact(record.get('args_after'), args):
        return False, 'input_effects'
    if record.get('alias_edges') != []:
        return False, 'mutable_return_alias'
    return True, None
