"""Original frontend 256 variant; qualification unknown."""


def solve(costs) -> int:
    r, b, g = 0, 0, 0
    for c0, c1, c2 in costs:
        r, b, g = c0 + min(b, g), c1 + min(r, g), c2 + min(r, b)
    return min(r, b, g)


minCost = solve


class Solution:
    def minCost(self, costs) -> int:
        return solve(costs)
