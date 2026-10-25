"""1921. Eliminate Maximum Number of Monsters: shoot in increasing integer deadline order."""


def solve(dist: list[int], speed: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    deadlines = sorted((distance - 1) // velocity for distance, velocity in zip(dist, speed))
    for minute, deadline in enumerate(deadlines):
        if deadline < minute:
            return minute
    return len(deadlines)


class Solution:
    def eliminateMaximum(self, dist: list[int], speed: list[int]) -> int:
        return solve(dist, speed)
