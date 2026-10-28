"""Original frontend 3862 variant; qualification unknown."""

def solve(nums):
    limit = sum(nums)
    suffix = [1] * (len(nums) + 1)
    for i in range(len(nums) - 1, -1, -1):
        suffix[i] = limit + 1 if suffix[i + 1] > limit // nums[i] else suffix[i + 1] * nums[i]
    left = 0
    for i, value in enumerate(nums):
        if left == suffix[i + 1]:
            return i
        left += value
    return -1


class Solution:
    def smallestBalancedIndex(self, nums):
        return solve(nums)
