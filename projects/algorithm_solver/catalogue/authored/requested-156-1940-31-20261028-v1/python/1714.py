"""Original frontend 1714 variant; qualification unknown."""

import math

MOD = 10**9 + 7


def solve(nums, queries):
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


class Solution:
    def solve(self, nums, queries):
        return solve(nums, queries)
