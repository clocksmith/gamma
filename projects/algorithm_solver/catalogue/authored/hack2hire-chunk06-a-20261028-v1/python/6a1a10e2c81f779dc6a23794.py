"""Hack2Hire 6a1a10e2c81f779dc6a23794 (Factory Network Cost Minimization, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(costs):
    return sum(min(row) for row in costs)


class Solution:
    def minimumCost(self, costs):
        return solve(costs)
