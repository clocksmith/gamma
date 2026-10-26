"""1277. Count Square Submatrices with All Ones: roll square-size dynamic programming through one row."""


def solve(matrix: list[list[int]]) -> int:
    """O(r * c) time and O(c) auxiliary space; inputs are read-only."""
    sizes = [0] * (len(matrix[0]) + 1)
    total = 0
    for row in matrix:
        diagonal = 0
        for col, value in enumerate(row, 1):
            above = sizes[col]
            sizes[col] = 1 + min(above, sizes[col - 1], diagonal) if value else 0
            total += sizes[col]
            diagonal = above
    return total


class Solution:
    def countSquares(self, matrix: list[list[int]]) -> int:
        return solve(matrix)
