# 518 — Coin Change II. Original implementation; authored candidate, not independently qualified.
def solve(amount, coins):
    dp = [1] + [0] * amount
    # Coin-first iteration counts combinations, never orderings of a combination.
    for coin in coins:
        for value in range(coin, amount + 1):
            dp[value] += dp[value - coin]
    return dp[amount]

change = solve

class Solution:
    change = staticmethod(solve)
