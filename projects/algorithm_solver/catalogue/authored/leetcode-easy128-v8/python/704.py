"""704. Binary Search (Easy).

Specification: https://leetcode.com/problems/binary-search/description/
"""


def solve(nums: list[int], target: int) -> int:
    """O(log n) time, O(1) space; narrow an inclusive sorted interval."""
    left, right = 0, len(nums) - 1
    while left <= right:
        middle = left + (right - left) // 2
        if nums[middle] == target:
            return middle
        if nums[middle] < target:
            left = middle + 1
        else:
            right = middle - 1
    return -1


class Solution:
    def search(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
