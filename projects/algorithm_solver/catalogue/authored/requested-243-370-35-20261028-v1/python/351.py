"""Original frontend 351 variant; qualification unknown."""


def solve(m: int, n: int) -> int:
    skip = [[0] * 10 for _ in range(10)]
    skip[1][3] = skip[3][1] = 2
    skip[1][7] = skip[7][1] = 4
    skip[3][9] = skip[9][3] = 6
    skip[7][9] = skip[9][7] = 8
    skip[1][9] = skip[9][1] = skip[2][8] = skip[8][2] = skip[3][7] = skip[7][3] = skip[4][6] = skip[6][4] = 5

    def dfs(vis: int, cur: int, rem: int) -> int:
        if rem == 0:
            return 1
        vis |= 1 << cur
        total = 0
        for nxt in range(1, 10):
            mid = skip[cur][nxt]
            if not ((vis >> nxt) & 1) and (mid == 0 or ((vis >> mid) & 1)):
                total += dfs(vis, nxt, rem - 1)
        return total

    ans = 0
    for length in range(m, n + 1):
        ans += dfs(0, 1, length - 1) * 4
        ans += dfs(0, 2, length - 1) * 4
        ans += dfs(0, 5, length - 1)
    return ans


numberOfPatterns = solve


class Solution:
    def numberOfPatterns(self, m: int, n: int) -> int:
        return solve(m, n)
