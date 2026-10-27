"""162. Find Peak Element."""
def solve(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        middle = (left + right) // 2
        if nums[middle] > nums[middle + 1]:
            right = middle
        else:
            left = middle + 1
    return left

class Solution:
    def findPeakElement(self, nums: list[int]) -> int:
        return solve(nums)
