"""1561. Maximum Number of Coins You Can Get (Medium).

Specification: https://leetcode.com/problems/maximum-number-of-coins-you-can-get/description/
"""


def solve(piles: list[int]) -> int:
    ordered = sorted(piles, reverse=True)
    groups = len(ordered) // 3
    total = 0
    for group in range(groups):
        total += ordered[group * 2 + 1]
    return total


class Solution:
    def maxCoins(self, piles: list[int]) -> int:
        return solve(piles)
