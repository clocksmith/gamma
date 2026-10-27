"""209. Minimum Size Subarray Sum."""
def solve(target: int, nums: list[int]) -> int:
    left = total = 0
    best = len(nums) + 1
    for right, value in enumerate(nums):
        total += value
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    return 0 if best > len(nums) else best

class Solution:
    def minSubArrayLen(self, target: int, nums: list[int]) -> int:
        return solve(target, nums)
