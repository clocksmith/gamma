"""121. Best Time to Buy and Sell Stock (Easy).

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock/description/
"""


def solve(prices: list[int]) -> int:
    """O(n) time, O(1) space; retain the cheapest earlier purchase and best profit."""
    cheapest = float('inf')
    profit = 0
    for price in prices:
        cheapest = min(cheapest, price)
        profit = max(profit, price - cheapest)
    return profit


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
