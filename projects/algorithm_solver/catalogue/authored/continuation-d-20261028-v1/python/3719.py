"""Original development candidate for frontend 3719; qualification pending."""

def solve(nums):
    best = 0
    for left in range(len(nums)):
        seen = set()
        balance = 0
        for right in range(left, len(nums)):
            value = nums[right]
            if value not in seen:
                seen.add(value)
                balance += 1 if value % 2 == 0 else -1
            if balance == 0:
                best = max(best, right - left + 1)
    return best


class Solution:
    def longestBalanced(self, nums):
        return solve(nums)
