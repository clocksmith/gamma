"""Original frontend 3795 development variant; qualification unknown."""

def solve(nums, k):
    counts = {}
    total = left = 0
    best = len(nums) + 1
    for right, value in enumerate(nums):
        if counts.get(value, 0) == 0:
            total += value
        counts[value] = counts.get(value, 0) + 1
        while total >= k:
            best = min(best, right - left + 1)
            outgoing = nums[left]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                total -= outgoing
            left += 1
    return best if best <= len(nums) else -1


class Solution:
    def minLength(self, nums, k):
        return solve(nums, k)
