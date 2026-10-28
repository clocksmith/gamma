"""576. Out of Boundary Paths (Medium).

Specification: https://leetcode.com/problems/out-of-boundary-paths/description/
"""


def solve(m: int, n: int, maxMove: int, startRow: int, startColumn: int) -> int:
    MOD = 1000000007
    dp = [[0] * n for _ in range(m)]
    dp[startRow][startColumn] = 1
    result = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for _step in range(maxMove):
        nxt = [[0] * n for _ in range(m)]
        for r in range(m):
            for c in range(n):
                if dp[r][c] == 0:
                    continue
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= m or nc < 0 or nc >= n:
                        result = (result + dp[r][c]) % MOD
                    else:
                        nxt[nr][nc] = (nxt[nr][nc] + dp[r][c]) % MOD
        dp = nxt
    return result


class Solution:
    def findPaths(self, m: int, n: int, maxMove: int, startRow: int, startColumn: int) -> int:
        return solve(m, n, maxMove, startRow, startColumn)
