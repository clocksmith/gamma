"""153. Find Minimum in Rotated Sorted Array (Medium).

Specification: https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/description/
"""


def solve(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    return nums[left]


class Solution:
    def findMin(self, nums: list[int]) -> int:
        return solve(nums)
