"""1150. Check If a Number Is Majority Element in a Sorted Array (Easy).

Specification: https://leetcode.com/problems/check-if-a-number-is-majority-element-in-a-sorted-array/description/
"""


def solve(nums: list[int], target: int) -> bool:
    """O(log n) time, O(1) space; locate the first target and check its strict-majority endpoint."""
    left = 0
    right = len(nums)
    while left < right:
        middle = left + (right - left) // 2
        if nums[middle] < target:
            left = middle + 1
        else:
            right = middle
    last_required = left + len(nums) // 2
    return last_required < len(nums) and nums[last_required] == target


class Solution:
    def isMajorityElement(self, nums: list[int], target: int) -> bool:
        return solve(nums, target)
