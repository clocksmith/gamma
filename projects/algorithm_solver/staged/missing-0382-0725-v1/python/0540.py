"""540. Single Element in a Sorted Array."""

def solve(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        middle = (left + right) // 2
        middle -= middle % 2
        if nums[middle] == nums[middle + 1]:
            left = middle + 2
        else:
            right = middle
    return nums[left]


class Solution:
    def singleNonDuplicate(self, nums: list[int]) -> int:
        return solve(nums)
