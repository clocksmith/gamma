"""3880. Minimum Absolute Difference Between Two Values (Easy).

Specification: https://leetcode.com/problems/minimum-absolute-difference-between-two-values/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; minimize index distance between a 1 and a 2; preserve nums."""
    lastOne = -1
    lastTwo = -1
    shortest = len(nums)
    for index, value in enumerate(nums):
        if value == 1:
            lastOne = index
            if lastTwo != -1:
                shortest = min(shortest, index - lastTwo)
        elif value == 2:
            lastTwo = index
            if lastOne != -1:
                shortest = min(shortest, index - lastOne)
    return -1 if shortest == len(nums) else shortest


class Solution:
    def minAbsoluteDifference(self, nums: list[int]) -> int:
        return solve(nums)
