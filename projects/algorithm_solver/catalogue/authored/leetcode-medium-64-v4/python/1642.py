"""1642. Furthest Building You Can Reach: reserve ladders for the largest climbs seen and pay bricks for smaller climbs."""
from heapq import heappop, heappush


def solve(heights: list[int], bricks: int, ladders: int) -> int:
    """O(n log(ladders + 2)) time and O(min(n, ladders + 1)) auxiliary space; inputs are read-only."""
    climbs = []
    remaining = bricks
    for index in range(len(heights) - 1):
        climb = heights[index + 1] - heights[index]
        if climb <= 0:
            continue
        heappush(climbs, climb)
        if len(climbs) > ladders:
            remaining -= heappop(climbs)
        if remaining < 0:
            return index
    return len(heights) - 1


class Solution:
    def furthestBuilding(self, heights: list[int], bricks: int, ladders: int) -> int:
        return solve(heights, bricks, ladders)
