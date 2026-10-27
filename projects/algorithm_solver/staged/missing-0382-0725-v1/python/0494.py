"""494. Target Sum. Count positive-sign subsets; zero values correctly double the count."""

def solve(nums: list[int], target: int) -> int:
    total = sum(nums)
    if abs(target) > total or (total + target) % 2:
        return 0
    wanted = (total + target) // 2
    dp = [0] * (wanted + 1)
    dp[0] = 1
    for value in nums:
        for subtotal in range(wanted, value - 1, -1):
            dp[subtotal] += dp[subtotal - value]
    return dp[wanted]


class Solution:
    def findTargetSumWays(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
