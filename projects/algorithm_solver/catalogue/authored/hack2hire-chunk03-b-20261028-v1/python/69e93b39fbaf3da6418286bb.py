"""Hack2Hire 69e93b39fbaf3da6418286bb (Purchase Optimization) over an INFERRED spec; qualification unknown."""
from bisect import bisect_right


def solve(prices, pos, amount):
    prefix = [0]
    for p in prices: prefix.append(prefix[-1] + p)
    return [bisect_right(prefix, prefix[p - 1] + a, p - 1) - p for p, a in zip(pos, amount)]


class Solution:
    def maxItems(self, prices, pos, amount):
        return solve(prices, pos, amount)
