"""Original development candidate for frontend 3708; qualification pending."""

def solve(nums):
    best = run = 2
    for i in range(2, len(nums)):
        run = run + 1 if nums[i] == nums[i - 1] + nums[i - 2] else 2
        best = max(best, run)
    return best


class Solution:
    def longestSubarray(self, nums):
        return solve(nums)
