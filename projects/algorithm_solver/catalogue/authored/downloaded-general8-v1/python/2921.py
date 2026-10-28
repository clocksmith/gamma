"""2921. Maximum Profitable Triplets With Increasing Prices II (Hard).

Specification: https://leetcode.com/problems/maximum-profitable-triplets-with-increasing-prices-ii/description/
"""


def solve(prices, profits):
    # Same increasing-triplet rule as 2907; this version uses the O(n^2)
    # middle-element scan, which is correct but not the optimal Fenwick
    # version for the larger input limits of this problem.
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
