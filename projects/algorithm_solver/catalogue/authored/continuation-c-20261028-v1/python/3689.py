def solve(nums, k):
    return (max(nums)-min(nums))*k

class Solution:
    def maxTotalValue(self, nums, k):
        return solve(nums, k)
