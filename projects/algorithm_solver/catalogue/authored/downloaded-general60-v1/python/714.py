"""714. Best Time to Buy and Sell Stock with Transaction Fee (Medium).

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/description/
"""


def solve(prices: list[int], fee: int) -> int:
    cash = 0
    hold = float('-inf')
    for price in prices:
        previous_cash = cash
        cash = max(cash, hold + price - fee)
        hold = max(hold, previous_cash - price)
    return cash


class Solution:
    def maxProfit(self, prices: list[int], fee: int) -> int:
        return solve(prices, fee)
