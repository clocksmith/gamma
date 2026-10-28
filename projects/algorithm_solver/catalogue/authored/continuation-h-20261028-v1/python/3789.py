"""Original frontend 3789 development variant; qualification unknown."""

def solve(cost1, cost2, costBoth, need1, need2):
    return min(count * costBoth + max(0, need1 - count) * cost1 + max(0, need2 - count) * cost2 for count in (0, min(need1, need2), max(need1, need2)))


class Solution:
    def minimumCost(self, cost1, cost2, costBoth, need1, need2):
        return solve(cost1, cost2, costBoth, need1, need2)
