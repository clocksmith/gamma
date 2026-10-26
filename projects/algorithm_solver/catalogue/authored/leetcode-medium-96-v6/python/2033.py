"""2033. Minimum Operations to Make a Uni-Value Grid: check the common residue and minimize distances to a median."""


def solve(grid: list[list[int]], x: int) -> int:
    """O(N log N) time and O(N) auxiliary space for N cells; inputs are read-only."""
    values = sorted(value for row in grid for value in row)
    residue = values[0] % x
    if any(value % x != residue for value in values):
        return -1
    median = values[len(values) // 2]
    return sum(abs(value - median) // x for value in values)


class Solution:
    def minOperations(self, grid: list[list[int]], x: int) -> int:
        return solve(grid, x)
