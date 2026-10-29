"""Original frontend 265 variant; qualification unknown."""


def solve(costs) -> int:
    k = len(costs[0])
    dp = list(costs[0])
    for row in costs[1:]:
        min1 = min2 = 10**18
        idx1 = -1
        for j, v in enumerate(dp):
            if v < min1:
                min2 = min1
                min1 = v
                idx1 = j
            elif v < min2:
                min2 = v
        dp = [row[j] + (min2 if j == idx1 else min1) for j in range(k)]
    return min(dp)


minCostII = solve


class Solution:
    def minCostII(self, costs) -> int:
        return solve(costs)
