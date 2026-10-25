"""123. Best Time to Buy and Sell Stock III (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/description/
Canonical API: solve(prices); also exposes Solution.maxProfit.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(prices: list[int]) -> int:
    first_buy = float("-inf")
    first_sell = 0
    second_buy = float("-inf")
    second_sell = 0
    for price in prices:
        # Reverse order keeps every transition on the previous day's state.
        second_sell = max(second_sell, second_buy + price)
        second_buy = max(second_buy, first_sell - price)
        first_sell = max(first_sell, first_buy + price)
        first_buy = max(first_buy, -price)
    return second_sell

class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
