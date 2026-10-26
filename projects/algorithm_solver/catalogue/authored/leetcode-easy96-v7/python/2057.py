"""2057. Smallest Index With Equal Value (Easy).

Specification: https://leetcode.com/problems/smallest-index-with-equal-value/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; return the first matching index; preserve nums."""
    for index, value in enumerate(nums):
        if index % 10 == value:
            return index
    return -1


class Solution:
    def smallestEqual(self, nums: list[int]) -> int:
        return solve(nums)
