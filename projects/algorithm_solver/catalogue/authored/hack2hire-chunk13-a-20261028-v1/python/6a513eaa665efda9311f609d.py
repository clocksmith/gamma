"""Hack2Hire 6a513eaa665efda9311f609d (Optimal Stock Price Subsequence) over an INFERRED spec; qualification unknown."""


def solve(stockPrice):
    n = len(stockPrice)
    keys = sorted({stockPrice[i] + i for i in range(n)})
    rank = {k: i + 1 for i, k in enumerate(keys)}
    m = len(keys)
    tree = [0] * (m + 1)  # prefix maximum of non-negative dp values by key
    best = None
    for i in range(n):
        k = rank[stockPrice[i] + i]
        j, base = k, 0
        while j > 0:
            if tree[j] > base:
                base = tree[j]
            j -= j & -j
        value = stockPrice[i] + base
        if best is None or value > best:
            best = value
        j = k
        while j <= m:
            if tree[j] < value:
                tree[j] = value
            j += j & -j
    return best


class Solution:
    def maxBalancedSum(self, stockPrice):
        return solve(stockPrice)
