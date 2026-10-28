"""3364. Minimum Positive Sum Subarray (Easy).

Specification: https://leetcode.com/problems/minimum-positive-sum-subarray/description/
"""


def solve(nums: list[int], l: int, r: int) -> int:
    best = float('inf')
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            if j - i + 1 > r:
                break
            total += nums[j]
            if j - i + 1 >= l and total > 0:
                best = min(best, total)
    return -1 if best == float('inf') else best


class Solution:
    def minimumSumSubarray(self, nums: list[int], l: int, r: int) -> int:
        return solve(nums, l, r)
