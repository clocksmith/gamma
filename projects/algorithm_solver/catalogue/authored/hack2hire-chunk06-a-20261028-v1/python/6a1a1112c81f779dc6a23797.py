"""Hack2Hire 6a1a1112c81f779dc6a23797 (Factory Network Cost Minimization, variant 2 of 3) over an INFERRED spec; qualification unknown."""
INF = float('inf')


def solve(costs):
    best1, index1, best2 = 0, -1, 0
    for row in costs:
        b1, i1, b2 = INF, -1, INF
        for j, cost in enumerate(row):
            value = cost + (best2 if j == index1 else best1)
            if value < b1:
                b1, i1, b2 = value, j, b1
            elif value < b2:
                b2 = value
        best1, index1, best2 = b1, i1, b2
    return -1 if best1 == INF else best1


class Solution:
    def minimumCost(self, costs):
        return solve(costs)
