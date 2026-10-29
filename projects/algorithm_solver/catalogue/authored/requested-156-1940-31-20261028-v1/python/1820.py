"""Original frontend 1820 variant; qualification unknown."""


def solve(grid) -> int:
    m, n = len(grid), len(grid[0])
    match = [-1] * n

    def dfs(u: int, vis) -> bool:
        for v in range(n):
            if grid[u][v] and not vis[v]:
                vis[v] = True
                if match[v] == -1 or dfs(match[v], vis):
                    match[v] = u
                    return True
        return False

    ans = 0
    for u in range(m):
        if dfs(u, [False] * n):
            ans += 1
    return ans


maximumInvitations = solve


class Solution:
    def maximumInvitations(self, grid) -> int:
        return solve(grid)
