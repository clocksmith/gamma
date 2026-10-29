"""Hack2Hire 69bef61921f6ab4226963c5a (Maximum Throughput) over an INFERRED spec; qualification unknown."""


def solve(throughput, scalingCost, budget):
    def feasible(target):
        spent = 0
        for t, c in zip(throughput, scalingCost):
            if t < target:
                upgrades = (target + t - 1) // t - 1
                if upgrades > budget: return False
                spent += upgrades * c
                if spent > budget: return False
        return True

    lo = min(throughput)
    hi = min(t * (1 + budget // c) for t, c in zip(throughput, scalingCost))
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid): lo = mid
        else: hi = mid - 1
    return lo


class Solution:
    def maximumThroughput(self, throughput, scalingCost, budget):
        return solve(throughput, scalingCost, budget)
