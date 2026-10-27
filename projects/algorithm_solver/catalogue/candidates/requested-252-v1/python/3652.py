"""3652. Best Time to Buy and Sell Stock using Strategy.

Specification: https://leetcode.com/problems/best-time-to-buy-and-sell-stock-using-strategy/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) time and space; k is even, and changing a segment is optional.
Inputs are not modified.
"""

def solve(prices, strategy, k):
    size = len(prices)
    original = [0]
    price_sum = [0]
    for price, action in zip(prices, strategy):
        original.append(original[-1] + price * action)
        price_sum.append(price_sum[-1] + price)
    best_gain = 0
    for start in range(size - k + 1):
        end = start + k
        replaced = price_sum[end] - price_sum[start + k // 2]
        prior = original[end] - original[start]
        best_gain = max(best_gain, replaced - prior)
    return original[-1] + best_gain


class Solution:
    def maxProfit(self, prices, strategy, k):
        return solve(prices, strategy, k)
