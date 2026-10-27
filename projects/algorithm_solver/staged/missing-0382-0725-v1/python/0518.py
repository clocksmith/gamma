"""518. Coin Change II. Count unordered coin combinations; exact internal counts and problem-bounded numeric return."""

def solve(amount: int, coins: list[int]) -> int:
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in coins:
        for subtotal in range(coin, amount + 1):
            dp[subtotal] += dp[subtotal - coin]
    return dp[amount]


class Solution:
    def change(self, amount: int, coins: list[int]) -> int:
        return solve(amount, coins)
