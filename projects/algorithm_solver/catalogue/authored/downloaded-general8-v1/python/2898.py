"""2898. Maximum Linear Stock Score (Medium).

Specification: https://leetcode.com/problems/maximum-linear-stock-score/description/
"""


def solve(prices):
    sums = {}
    for i, p in enumerate(prices):
        key = p - (i + 1)
        sums[key] = sums.get(key, 0) + p
    return max(sums.values())


class Solution:
    def maximumScore(self, *args):
        return solve(*args)
