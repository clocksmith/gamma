"""3550. Smallest Index With Digit Sum Equal to Index (Easy).

Specification: https://leetcode.com/problems/smallest-index-with-digit-sum-equal-to-index/description/
"""


def solve(nums: list[int]) -> int:
    """O(n * d) time, O(1) space; d is the maximum digit count; preserve nums."""
    for index, value in enumerate(nums):
        remaining = value
        digitSum = 0
        while remaining > 0:
            digitSum += remaining % 10
            remaining //= 10
        if digitSum == index:
            return index
    return -1


class Solution:
    def smallestIndex(self, nums: list[int]) -> int:
        return solve(nums)
