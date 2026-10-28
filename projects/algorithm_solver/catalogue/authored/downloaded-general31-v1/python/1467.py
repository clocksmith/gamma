"""1467. Probability of a Two Boxes Having The Same Number of Distinct Balls (Hard).

Specification: https://leetcode.com/problems/probability-of-a-two-boxes-having-the-same-number-of-distinct-balls/description/
"""


import math


def solve(balls: list[int]) -> float:
    total = sum(balls)
    if total % 2 != 0:
        return 0.0
    half = total // 2
    favorable = 0.0

    def dfs(index, remaining, distinct1, distinct2, ways):
        nonlocal favorable
        if index == len(balls):
            if remaining == 0 and distinct1 == distinct2:
                favorable += ways
            return
        count = balls[index]
        for take in range(count + 1):
            if take > remaining:
                break
            d1 = distinct1 + (1 if take > 0 else 0)
            d2 = distinct2 + (1 if take < count else 0)
            dfs(index + 1, remaining - take, d1, d2, ways * math.comb(count, take))

    dfs(0, half, 0, 0, 1)
    return favorable / math.comb(total, half)


class Solution:
    def getProbability(self, balls: list[int]) -> float:
        return solve(balls)
