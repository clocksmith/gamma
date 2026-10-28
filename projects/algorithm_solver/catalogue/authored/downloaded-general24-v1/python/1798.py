"""1798. Maximum Number of Consecutive Values You Can Make (Medium).

Specification: https://leetcode.com/problems/maximum-number-of-consecutive-values-you-can-make/description/
"""


def solve(coins: list[int]) -> int:
    ordered = sorted(coins)
    reachable = 0
    for coin in ordered:
        if coin > reachable + 1:
            break
        reachable += coin
    return reachable + 1


class Solution:
    def getMaximumConsecutive(self, coins: list[int]) -> int:
        return solve(coins)
