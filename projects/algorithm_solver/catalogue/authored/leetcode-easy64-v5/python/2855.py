"""2855. Minimum Right Shifts to Sort the Array (Easy).

Specification: https://leetcode.com/problems/minimum-right-shifts-to-sort-the-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; inputs are distinct and remain unchanged."""
    pivot = -1
    for index in range(1, len(nums)):
        if nums[index] < nums[index - 1]:
            if pivot != -1:
                return -1
            pivot = index
    if pivot == -1:
        return 0
    if nums[-1] > nums[0]:
        return -1
    return len(nums) - pivot


class Solution:
    def minimumRightShifts(self, nums: list[int]) -> int:
        return solve(nums)
