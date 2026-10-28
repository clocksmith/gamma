"""122. Best Time to Buy and Sell Stock II (Medium).

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/description/
"""


def solve(prices: list[int]) -> int:
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            profit += prices[i] - prices[i - 1]
    return profit


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
