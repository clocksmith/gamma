"""35. Search Insert Position (Easy).

Specification: https://leetcode.com/problems/search-insert-position/description/
"""


def solve(nums: list[int], target: int) -> int:
    """O(log n) time, O(1) space; lower-bound search on a half-open interval."""
    left, right = 0, len(nums)
    while left < right:
        middle = left + (right - left) // 2
        if nums[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def searchInsert(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
