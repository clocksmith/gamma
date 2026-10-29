"""Hack2Hire 69e933bdfbaf3da641828694 (Maximize Portfolio Floor Value) over an INFERRED spec; qualification unknown."""

def solve(values, costs, totalCost):
    assets = sorted(zip(values, costs))

    def affordable(target):
        spent = 0
        for v, c in assets:
            if v >= target:
                break
            spent += (target - v) * c
            if spent > totalCost:
                return False
        return True

    lo, hi = assets[0][0], assets[0][0] + totalCost
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if affordable(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


class Solution:
    def maxPortfolioFloor(self, values, costs, totalCost):
        return solve(values, costs, totalCost)
