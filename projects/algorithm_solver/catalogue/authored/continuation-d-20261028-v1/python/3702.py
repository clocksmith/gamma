"""Original development candidate for frontend 3702; qualification pending."""

def solve(nums):
    total = 0
    nonzero = False
    for value in nums:
        total ^= value
        nonzero |= value != 0
    return len(nums) if total else len(nums) - 1 if nonzero else 0


class Solution:
    def longestSubsequence(self, nums):
        return solve(nums)
