"""2733. Neither Minimum nor Maximum (Easy).

Specification: https://leetcode.com/problems/neither-minimum-nor-maximum/description/
"""


def solve(nums: list[int]) -> int:
    """O(1) time and space; return the median of the first three distinct values."""
    if len(nums) < 3:
        return -1
    first, second, third = nums[0], nums[1], nums[2]
    return first + second + third - min(first, second, third) - max(first, second, third)


class Solution:
    def findNonMinOrMax(self, nums: list[int]) -> int:
        return solve(nums)
