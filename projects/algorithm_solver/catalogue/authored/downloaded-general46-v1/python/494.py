"""494. Target Sum (Medium).

Specification: https://leetcode.com/problems/target-sum/description/
"""


def solve(nums: list[int], target: int) -> int:
    total = sum(nums)
    if abs(target) > total:
        return 0
    offset = total
    dp = [0] * (2 * total + 1)
    dp[offset] = 1
    for value in nums:
        nxt = [0] * (2 * total + 1)
        for s in range(-total, total + 1):
            if dp[s + offset] != 0:
                nxt[s + value + offset] += dp[s + offset]
                nxt[s - value + offset] += dp[s + offset]
        dp = nxt
    return dp[target + offset]


class Solution:
    def findTargetSumWays(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
