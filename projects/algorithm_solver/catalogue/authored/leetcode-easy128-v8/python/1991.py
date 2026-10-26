"""1991. Find the Middle Index in Array (Easy).

Specification: https://leetcode.com/problems/find-the-middle-index-in-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; return the first index whose excluded left and right sums agree."""
    total = sum(nums)
    left = 0
    for index, value in enumerate(nums):
        if left == total - left - value:
            return index
        left += value
    return -1


class Solution:
    def findMiddleIndex(self, nums: list[int]) -> int:
        return solve(nums)
