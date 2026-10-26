"""2016. Maximum Difference Between Increasing Elements (Easy).

Specification: https://leetcode.com/problems/maximum-difference-between-increasing-elements/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; require a strictly larger later value; preserve nums."""
    smallest = nums[0]
    greatest_difference = -1
    for index in range(1, len(nums)):
        if nums[index] > smallest:
            greatest_difference = max(greatest_difference, nums[index] - smallest)
        smallest = min(smallest, nums[index])
    return greatest_difference


class Solution:
    def maximumDifference(self, nums: list[int]) -> int:
        return solve(nums)
