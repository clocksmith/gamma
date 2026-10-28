"""2907. Maximum Profitable Triplets With Increasing Prices I (Medium).

Specification: https://leetcode.com/problems/maximum-profitable-triplets-with-increasing-prices-i/description/
"""


def solve(prices, profits):
    n = len(prices)
    ans = -1
    for j in range(n):
        left = -1
        right = -1
        for i in range(j):
            if prices[i] < prices[j]:
                left = max(left, profits[i])
        for k in range(j + 1, n):
            if prices[k] > prices[j]:
                right = max(right, profits[k])
        if left >= 0 and right >= 0:
            ans = max(ans, left + profits[j] + right)
    return ans


class Solution:
    def maxProfit(self, *args):
        return solve(*args)
