"""2965. Find Missing and Repeated Values (Easy).

Specification: https://leetcode.com/problems/find-missing-and-repeated-values/description/
"""


def solve(grid: list[list[int]]) -> list[int]:
    """O(n^2) time and space; return repeated then missing; preserve grid and row identities."""
    count = len(grid) * len(grid)
    seen = [False] * (count + 1)
    repeated = -1
    for row in grid:
        for value in row:
            if seen[value]:
                repeated = value
            seen[value] = True
    for value in range(1, count + 1):
        if not seen[value]:
            return [repeated, value]
    return [-1, -1]


class Solution:
    def findMissingAndRepeatedValues(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
