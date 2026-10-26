"""2945. Find Maximum Non-decreasing Array Length.

Positive-prefix DP propagates the latest feasible previous split; O(n log n) time and O(n) space. Inputs are preserved.
"""

from bisect import bisect_left


def solve(nums: list[int]) -> int:
    n = len(nums)
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    previous = [0] * (n + 2)
    count = [0] * (n + 1)
    for end in range(1, n + 1):
        previous[end] = max(previous[end], previous[end - 1])
        start = previous[end]
        count[end] = count[start] + 1
        next_end = bisect_left(prefix, 2 * prefix[end] - prefix[start], end + 1)
        if next_end <= n:
            previous[next_end] = max(previous[next_end], end)
    return count[n]


class Solution:
    def findMaximumLength(self, nums: list[int]) -> int:
        return solve(nums)
