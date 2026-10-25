"""1800. Maximum Ascending Subarray Sum (Easy).

Specification: https://leetcode.com/problems/maximum-ascending-subarray-sum/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; preserve the positive input array."""
    current = nums[0]
    best = current
    for index in range(1, len(nums)):
        if nums[index] > nums[index - 1]:
            current += nums[index]
        else:
            current = nums[index]
        best = max(best, current)
    return best


class Solution:
    def maxAscendingSum(self, nums: list[int]) -> int:
        return solve(nums)
