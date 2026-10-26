"""2435. Paths in Matrix Whose Sum Is Divisible by K. Rolling residue-count dynamic programming."""


def solve(grid: list[list[int]], k: int) -> int:
    """O(m*n*k) time and O(n*k) space. Inputs are preserved."""
    modulus = 1_000_000_007
    columns = len(grid[0])
    counts = [[0] * k for _ in range(columns)]
    for row in range(len(grid)):
        for column in range(columns):
            current = [0] * k
            value = grid[row][column] % k
            if row == 0 and column == 0:
                current[value] = 1
            else:
                for remainder in range(k):
                    ways = counts[column][remainder]
                    if column > 0:
                        ways += counts[column - 1][remainder]
                    current[(remainder + value) % k] = ways % modulus
            counts[column] = current
    return counts[-1][0]


class Solution:
    def numberOfPaths(self, grid: list[list[int]], k: int) -> int:
        return solve(grid, k)
