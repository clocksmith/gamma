"""1909. Remove One Element to Make the Array Strictly Increasing (Easy).

Specification: https://leetcode.com/problems/remove-one-element-to-make-the-array-strictly-increasing/description/
"""


def solve(nums: list[int]) -> bool:
    removed = False
    for i in range(1, len(nums)):
        if nums[i] <= nums[i - 1]:
            if removed:
                return False
            removed = True
            if (i > 1 and i + 1 < len(nums)
                    and nums[i] <= nums[i - 2] and nums[i + 1] <= nums[i - 1]):
                return False
    return True


class Solution:
    def canBeIncreasing(self, nums: list[int]) -> bool:
        return solve(nums)
