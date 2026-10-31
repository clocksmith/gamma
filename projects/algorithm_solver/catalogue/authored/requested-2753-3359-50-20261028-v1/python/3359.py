"""Original frontend 3359 variant; qualification unknown."""


def solve(grid, k: int) -> int:
    m, n = len(grid), len(grid[0])
    width = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            if grid[r][c] <= k:
                if c > 0 and grid[r][c - 1] <= k and grid[r][c - 1] >= grid[r][c]:
                    width[r][c] = width[r][c - 1] + 1
                else:
                    width[r][c] = 1
    total = 0
    for c in range(n):
        stack = []
        col_sum = 0
        for r in range(m):
            w = width[r][c]
            cnt = 1
            while stack and stack[-1][0] >= w:
                pw, pcnt = stack.pop()
                col_sum -= pw * pcnt
                cnt += pcnt
            stack.append((w, cnt))
            col_sum += w * cnt
            total += col_sum
    return total


countSubmatrices = solve


class Solution:
    def countSubmatrices(self, grid, k: int) -> int:
        return solve(grid, k)
