"""Hack2Hire 67873a44e20f8f324213c29a (Make Power Non-decreasing) over an INFERRED spec; qualification unknown."""


def solve(power):
    total = 0
    for i in range(1, len(power)):
        if power[i - 1] > power[i]:
            total += power[i - 1] - power[i]
    return total


class Solution:
    def minimalIncreaseSum(self, power):
        return solve(power)
