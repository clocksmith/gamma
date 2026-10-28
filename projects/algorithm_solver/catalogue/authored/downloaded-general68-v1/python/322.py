"""322. Coin Change (Medium).

Specification: https://leetcode.com/problems/coin-change/description/
"""


def solve(coins: list[int], amount: int) -> int:
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] == float('inf') else dp[amount]


class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        return solve(coins, amount)
