"""910. Smallest Range II (Medium).

Specification: https://leetcode.com/problems/smallest-range-ii/description/
"""


def solve(nums: list[int], k: int) -> int:
    ordered = sorted(nums)
    best = ordered[-1] - ordered[0]
    for i in range(len(ordered) - 1):
        low = min(ordered[0] + k, ordered[i + 1] - k)
        high = max(ordered[-1] - k, ordered[i] + k)
        best = min(best, high - low)
    return best


class Solution:
    def smallestRangeII(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
