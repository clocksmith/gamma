"""309. Best Time to Buy and Sell Stock with Cooldown."""
def solve(prices: list[int]) -> int:
    hold = float('-inf')
    sold = rest = 0
    for price in prices:
        previous_sold = sold
        sold = hold + price
        hold = max(hold, rest - price)
        rest = max(rest, previous_sold)
    return max(sold, rest)

class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return solve(prices)
