"""Original frontend 3347 variant; qualification unknown."""

import bisect
from collections import Counter


def solve(nums, k: int, numOperations: int) -> int:
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


maxFrequency = solve


class Solution:
    def maxFrequency(self, nums, k: int, numOperations: int) -> int:
        return solve(nums, k, numOperations)
