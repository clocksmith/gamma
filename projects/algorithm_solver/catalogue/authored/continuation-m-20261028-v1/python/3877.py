def solve(nums, target):
    dp = [-1] * 16384
    dp[0] = 0
    for x in nums:
        following = dp[:]
        for value, length in enumerate(dp):
            if length >= 0:
                following[value ^ x] = max(following[value ^ x], length + 1)
        dp = following
    return -1 if dp[target] < 0 else len(nums) - dp[target]


class Solution:
    def minRemovals(self, nums, target):
        return solve(nums, target)
