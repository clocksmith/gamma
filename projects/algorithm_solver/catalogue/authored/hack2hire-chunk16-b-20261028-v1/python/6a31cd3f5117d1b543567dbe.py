"""Hack2Hire 6a31cd3f5117d1b543567dbe (Minimum Redistribution Cost) over an INFERRED spec; qualification unknown."""


def solve(products):
    n = len(products)
    average = sum(products) // n
    prefix = 0
    total = 0
    low = None
    high = None
    for v in products:
        prefix += v - average
        total += prefix
        if low is None or prefix < low:
            low = prefix
        if high is None or prefix > high:
            high = prefix
    clockwise = total - n * low
    counterclockwise = n * high - total
    return clockwise if clockwise < counterclockwise else counterclockwise


class Solution:
    def minRedistributionCost(self, products):
        return solve(products)
