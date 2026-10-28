"""81. Search in Rotated Sorted Array II (Medium).

Specification: https://leetcode.com/problems/search-in-rotated-sorted-array-ii/description/
"""


def solve(nums: list[int], target: int) -> bool:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return True
        if nums[left] == nums[mid] == nums[right]:
            left += 1
            right -= 1
        elif nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return False


class Solution:
    def search(self, nums: list[int], target: int) -> bool:
        return solve(nums, target)
