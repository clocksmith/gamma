"""377. Combination Sum IV (Medium).

Specification: https://leetcode.com/problems/combination-sum-iv/description/
"""


def solve(nums: list[int], target: int) -> int:
    dp = [0] * (target + 1)
    dp[0] = 1
    for total in range(1, target + 1):
        for value in nums:
            if value <= total:
                dp[total] += dp[total - value]
    return dp[target]


class Solution:
    def combinationSum4(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
