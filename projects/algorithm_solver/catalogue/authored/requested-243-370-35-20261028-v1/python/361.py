"""Original frontend 361 variant; qualification unknown."""


def solve(grid) -> int:
    m, n = len(grid), len(grid[0])
    row_hits = 0
    col_hits = [0] * n
    best = 0
    for r in range(m):
        for c in range(n):
            if c == 0 or grid[r][c - 1] == "W":
                row_hits = 0
                k = c
                while k < n and grid[r][k] != "W":
                    if grid[r][k] == "E":
                        row_hits += 1
                    k += 1
            if r == 0 or grid[r - 1][c] == "W":
                col_hits[c] = 0
                k = r
                while k < m and grid[k][c] != "W":
                    if grid[k][c] == "E":
                        col_hits[c] += 1
                    k += 1
            if grid[r][c] == "0":
                if row_hits + col_hits[c] > best:
                    best = row_hits + col_hits[c]
    return best


maxKilledEnemies = solve


class Solution:
    def maxKilledEnemies(self, grid) -> int:
        return solve(grid)
