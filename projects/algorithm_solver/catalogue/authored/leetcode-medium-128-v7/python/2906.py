"""2906. Construct Product Matrix: combine exclusive prefix and suffix products without modular division."""


def solve(grid: list[list[int]]) -> list[list[int]]:
    """O(r * c) time and O(r * c) auxiliary space including the result; inputs are read-only."""
    modulus = 12345
    rows, columns = len(grid), len(grid[0])
    result = [[0] * columns for _ in range(rows)]
    prefix = 1
    for row in range(rows):
        for column in range(columns):
            result[row][column] = prefix
            prefix = prefix * (grid[row][column] % modulus) % modulus
    suffix = 1
    for row in range(rows - 1, -1, -1):
        for column in range(columns - 1, -1, -1):
            result[row][column] = result[row][column] * suffix % modulus
            suffix = suffix * (grid[row][column] % modulus) % modulus
    return result


class Solution:
    def constructProductMatrix(self, grid: list[list[int]]) -> list[list[int]]:
        return solve(grid)
