"""188. Best Time to Buy and Sell Stock IV."""
def solve(k: int, prices: list[int]) -> int:
    if not prices or k == 0:
        return 0
    if k >= len(prices) // 2:
        return sum(max(0, right - left) for left, right in zip(prices, prices[1:]))
    buy = [float('-inf')] * (k + 1)
    sell = [0] * (k + 1)
    for price in prices:
        for transaction in range(1, k + 1):
            buy[transaction] = max(buy[transaction], sell[transaction - 1] - price)
            sell[transaction] = max(sell[transaction], buy[transaction] + price)
    return sell[k]

class Solution:
    def maxProfit(self, k: int, prices: list[int]) -> int:
        return solve(k, prices)
