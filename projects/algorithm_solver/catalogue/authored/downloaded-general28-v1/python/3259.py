"""3259. Maximum Energy Boost From Two Drinks (Medium).

Specification: https://leetcode.com/problems/maximum-energy-boost-from-two-drinks/description/
"""


def solve(energyDrinkA: list[int], energyDrinkB: list[int]) -> int:
    n = len(energyDrinkA)
    a, b, c = energyDrinkA[0], energyDrinkB[0], 0
    for i in range(1, n):
        na = energyDrinkA[i] + max(a, c)
        nb = energyDrinkB[i] + max(b, c)
        nc = max(a, b, c)
        a, b, c = na, nb, nc
    return max(a, b, c)


class Solution:
    def maxEnergyBoost(self, energyDrinkA: list[int], energyDrinkB: list[int]) -> int:
        return solve(energyDrinkA, energyDrinkB)
