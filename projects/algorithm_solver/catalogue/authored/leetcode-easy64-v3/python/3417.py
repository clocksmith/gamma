"""3417. Zigzag Grid Traversal With Skip (Easy).

Specification: https://leetcode.com/problems/zigzag-grid-traversal-with-skip/description/
"""


def solve(grid: list[list[int]]) -> list[int]:
    """O(rows * columns) time and output space; skipping continues across row boundaries."""
    result = []
    columns = len(grid[0])
    take = True
    for row in range(len(grid)):
        for offset in range(columns):
            column = offset if row % 2 == 0 else columns - 1 - offset
            if take:
                result.append(grid[row][column])
            take = not take
    return result


class Solution:
    def zigzagTraversal(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
