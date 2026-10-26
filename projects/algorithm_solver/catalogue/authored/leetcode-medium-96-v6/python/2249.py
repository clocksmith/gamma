"""2249. Count Lattice Points Inside a Circle: enumerate bounded integer coordinates and deduplicate points satisfying a squared-radius check."""


def solve(circles: list[list[int]]) -> int:
    """O(sum(r^2)) time and O(U) auxiliary space for U distinct covered points; inputs are read-only."""
    covered = set()
    for x, y, radius in circles:
        squared = radius * radius
        for column in range(x - radius, x + radius + 1):
            for row in range(y - radius, y + radius + 1):
                if (column - x) ** 2 + (row - y) ** 2 <= squared:
                    covered.add((column, row))
    return len(covered)


class Solution:
    def countLatticePoints(self, circles: list[list[int]]) -> int:
        return solve(circles)
