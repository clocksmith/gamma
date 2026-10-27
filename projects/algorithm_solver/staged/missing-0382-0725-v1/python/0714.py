"""714. Best Time to Buy and Sell Stock with Transaction Fee."""

def solve(prices: list[int], fee: int) -> int:
    if not prices:
        return 0
    cash, holding = 0, -prices[0]
    for price in prices[1:]:
        cash, holding = max(cash, holding + price - fee), max(holding, cash - price)
    return cash


class Solution:
    def maxProfit(self, prices: list[int], fee: int) -> int:
        return solve(prices, fee)
