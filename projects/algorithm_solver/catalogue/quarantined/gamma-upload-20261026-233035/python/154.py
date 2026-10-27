"""154. Find Minimum in Rotated Sorted Array II."""
def solve(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    while left < right:
        middle = (left + right) // 2
        if nums[middle] < nums[right]:
            right = middle
        elif nums[middle] > nums[right]:
            left = middle + 1
        else:
            right -= 1
    return nums[left]

class Solution:
    def findMin(self, nums: list[int]) -> int:
        return solve(nums)
