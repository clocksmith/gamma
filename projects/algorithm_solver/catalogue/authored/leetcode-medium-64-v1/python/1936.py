"""1936. Add Minimum Number of Rungs: fill each consecutive height gap with the minimum number of intermediate rungs."""


def solve(rungs: list[int], dist: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    previous = answer = 0
    for height in rungs:
        answer += (height - previous - 1) // dist
        previous = height
    return answer


class Solution:
    def addRungs(self, rungs: list[int], dist: int) -> int:
        return solve(rungs, dist)
