"""213. House Robber II (Medium).

Specification: https://leetcode.com/problems/house-robber-ii/description/
"""


def _rob_linear(nums):
    previous = 0
    current = 0
    for value in nums:
        previous, current = current, max(current, previous + value)
    return current


def solve(nums: list[int]) -> int:
    if len(nums) == 1:
        return nums[0]
    return max(_rob_linear(nums[:-1]), _rob_linear(nums[1:]))


class Solution:
    def rob(self, nums: list[int]) -> int:
        return solve(nums)
