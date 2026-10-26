"""1824. Minimum Sideway Jumps: carry the cheapest reachable cost for each of the three lanes."""


def solve(obstacles: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    unreachable = len(obstacles) + 1
    costs = [1, 0, 1]
    for obstacle in obstacles:
        if obstacle:
            costs[obstacle - 1] = unreachable
        best = min(costs)
        for lane in range(3):
            if lane + 1 != obstacle:
                costs[lane] = min(costs[lane], best + 1)
    return min(costs)


class Solution:
    def minSideJumps(self, obstacles: list[int]) -> int:
        return solve(obstacles)
