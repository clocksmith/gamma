"""2579. Count Total Number of Colored Cells: sum the successive diamond boundaries around the first cell."""


def solve(n: int) -> int:
    """O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    return 1 + 2 * n * (n - 1)


class Solution:
    def coloredCells(self, n: int) -> int:
        return solve(n)
