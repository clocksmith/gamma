"""Original frontend 3904 variant; qualification unknown."""

def solve(nums, k):
    suffix = [0] * len(nums)
    suffix[-1] = nums[-1]
    for i in range(len(nums) - 2, -1, -1):
        suffix[i] = min(nums[i], suffix[i + 1])
    maximum = 0
    for i, value in enumerate(nums):
        maximum = max(maximum, value)
        if maximum - suffix[i] <= k:
            return i
    return -1


class Solution:
    def firstStableIndex(self, nums, k):
        return solve(nums, k)
