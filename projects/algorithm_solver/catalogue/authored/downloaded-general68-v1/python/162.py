"""162. Find Peak Element (Medium).

Specification: https://leetcode.com/problems/find-peak-element/description/
"""


def solve(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < nums[mid + 1]:
            left = mid + 1
        else:
            right = mid
    return left


class Solution:
    def findPeakElement(self, nums: list[int]) -> int:
        return solve(nums)
