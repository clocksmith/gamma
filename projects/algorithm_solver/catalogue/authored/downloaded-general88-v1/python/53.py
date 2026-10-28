"""53. Maximum Subarray (Medium).

Specification: https://leetcode.com/problems/maximum-subarray/description/
"""


def solve(nums: list[int]) -> int:
    best = nums[0]
    current = nums[0]
    for i in range(1, len(nums)):
        current = max(nums[i], current + nums[i])
        best = max(best, current)
    return best


class Solution:
    def maxSubArray(self, nums: list[int]) -> int:
        return solve(nums)
