"""198. House Robber (Medium).

Specification: https://leetcode.com/problems/house-robber/description/
"""


def solve(nums: list[int]) -> int:
    previous = 0
    current = 0
    for value in nums:
        previous, current = current, max(current, previous + value)
    return current


class Solution:
    def rob(self, nums: list[int]) -> int:
        return solve(nums)
