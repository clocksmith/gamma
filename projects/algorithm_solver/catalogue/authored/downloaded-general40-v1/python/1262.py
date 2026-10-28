"""1262. Greatest Sum Divisible by Three (Medium).

Specification: https://leetcode.com/problems/greatest-sum-divisible-by-three/description/
"""


def solve(nums: list[int]) -> int:
    dp = [0, float('-inf'), float('-inf')]
    for value in nums:
        nxt = dp[:]
        for remainder in range(3):
            new_remainder = (remainder + value) % 3
            nxt[new_remainder] = max(nxt[new_remainder], dp[remainder] + value)
        dp = nxt
    return dp[0]


class Solution:
    def maxSumDivThree(self, nums: list[int]) -> int:
        return solve(nums)
