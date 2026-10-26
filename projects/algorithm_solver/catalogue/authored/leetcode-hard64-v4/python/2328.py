"""2328. Number of Increasing Paths in a Grid."""


def solve(grid: list[list[int]]) -> int:
    """Value-ordered path DP with no recursive depth; O(R*C log(R*C)) time and O(R*C) space. Inputs are preserved."""
    modulus = 1_000_000_007
    rows, columns = len(grid), len(grid[0])
    order = sorted(range(rows * columns), key=lambda cell: grid[cell // columns][cell % columns])
    ways = [0] * (rows * columns)
    answer = 0
    for cell in order:
        row, column = divmod(cell, columns)
        count = 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and grid[nr][nc] < grid[row][column]:
                count += ways[nr * columns + nc]
        ways[cell] = count % modulus
        answer = (answer + ways[cell]) % modulus
    return answer


class Solution:
    def countPaths(self, grid: list[list[int]]) -> int:
        return solve(grid)
