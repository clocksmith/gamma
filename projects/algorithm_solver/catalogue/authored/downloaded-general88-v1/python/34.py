"""34. Find First and Last Position of Element in Sorted Array (Medium).

Specification: https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/description/
"""


def _bound(nums, target, first):
    left, right = 0, len(nums) - 1
    answer = -1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            answer = mid
            if first:
                right = mid - 1
            else:
                left = mid + 1
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return answer


def solve(nums: list[int], target: int) -> list[int]:
    return [_bound(nums, target, True), _bound(nums, target, False)]


class Solution:
    def searchRange(self, nums: list[int], target: int) -> list[int]:
        return solve(nums, target)
