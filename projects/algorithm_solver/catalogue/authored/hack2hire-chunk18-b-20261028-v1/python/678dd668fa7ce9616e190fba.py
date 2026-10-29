"""Hack2Hire 678dd668fa7ce9616e190fba (Sum of Islands Max) over an INFERRED spec; qualification unknown."""


def solve(grid):
    m = len(grid)
    n = len(grid[0])
    seen = [[False] * n for _ in range(m)]
    best = 0
    for si in range(m):
        for sj in range(n):
            if grid[si][sj] <= 0 or seen[si][sj]:
                continue
            seen[si][sj] = True
            stack = [(si, sj)]
            total = 0
            while stack:
                i, j = stack.pop()
                total += grid[i][j]
                for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                    if 0 <= a < m and 0 <= b < n and not seen[a][b] and grid[a][b] > 0:
                        seen[a][b] = True
                        stack.append((a, b))
            if total > best:
                best = total
    return best


class Solution:
    def maxIslandSum(self, grid):
        return solve(grid)
