"""123. Best Time to Buy and Sell Stock III (Hard).

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/description/
"""


def solve(prices: list[int]) -> int:
    buy1 = float('-inf')
    sell1 = 0
    buy2 = float('-inf')
    sell2 = 0
    for price in prices:
        buy1 = max(buy1, -price)
        sell1 = max(sell1, buy1 + price)
        buy2 = max(buy2, sell1 - price)
        sell2 = max(sell2, buy2 + price)
    return sell2


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
