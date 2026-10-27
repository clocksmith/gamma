"""259. 3Sum Smaller."""
def solve(nums: list[int], target: int) -> int:
    nums = sorted(nums)
    total = 0
    for index in range(len(nums) - 2):
        left, right = index + 1, len(nums) - 1
        while left < right:
            if nums[index] + nums[left] + nums[right] < target:
                total += right - left
                left += 1
            else:
                right -= 1
    return total

class Solution:
    def threeSumSmaller(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
