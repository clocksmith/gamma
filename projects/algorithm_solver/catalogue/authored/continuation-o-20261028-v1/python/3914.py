"""Original frontend 3914 variant; qualification unknown."""

def solve(nums):
    return sum(max(0, nums[i - 1] - nums[i]) for i in range(1, len(nums)))


class Solution:
    def minOperations(self, nums):
        return solve(nums)
