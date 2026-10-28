"""309. Best Time to Buy and Sell Stock with Cooldown (Medium).

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/description/
"""


def solve(prices: list[int]) -> int:
    hold = float('-inf')
    sold = 0
    rest = 0
    for price in prices:
        previous_hold = hold
        hold = max(hold, rest - price)
        rest = max(rest, sold)
        sold = previous_hold + price
    return max(sold, rest)


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
