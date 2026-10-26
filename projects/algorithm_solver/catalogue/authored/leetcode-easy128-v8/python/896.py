"""896. Monotonic Array (Easy).

Specification: https://leetcode.com/problems/monotonic-array/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) time, O(1) space; equal neighbors do not determine the direction."""
    increasing = decreasing = False
    for index in range(1, len(nums)):
        if nums[index] > nums[index - 1]:
            increasing = True
        if nums[index] < nums[index - 1]:
            decreasing = True
        if increasing and decreasing:
            return False
    return True


class Solution:
    def isMonotonic(self, nums: list[int]) -> bool:
        return solve(nums)
