"""Hack2Hire 6a74eeddd713d873ca7a8195 (Minimum Device Procurement Cost) over an INFERRED spec; qualification unknown."""


def solve(x, y, edgeCost, inputCost, bundleCost):
    best = None
    for b in (0, min(x, y), max(x, y)):
        cost = b * bundleCost + (x - b if x > b else 0) * edgeCost + (y - b if y > b else 0) * inputCost
        if best is None or cost < best:
            best = cost
    return best


class Solution:
    def minimumCost(self, x, y, edgeCost, inputCost, bundleCost):
        return solve(x, y, edgeCost, inputCost, bundleCost)
