"""778. Swim in Rising Water (Hard).

Specification: https://leetcode.com/problems/swim-in-rising-water/description/
"""


def solve(grid: list[list[int]]) -> int:
    n = len(grid)
    dist = [[float('inf')] * n for _ in range(n)]
    dist[0][0] = grid[0][0]
    visited = set()
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for _step in range(n * n):
        best = float('inf')
        br = bc = -1
        for r in range(n):
            for c in range(n):
                if (r, c) not in visited and dist[r][c] < best:
                    best = dist[r][c]
                    br, bc = r, c
        if br == -1:
            break
        visited.add((br, bc))
        if br == n - 1 and bc == n - 1:
            break
        for dr, dc in directions:
            nr, nc = br + dr, bc + dc
            if 0 <= nr < n and 0 <= nc < n:
                dist[nr][nc] = min(dist[nr][nc], max(dist[br][bc], grid[nr][nc]))
    return dist[n - 1][n - 1]


class Solution:
    def swimInWater(self, grid: list[list[int]]) -> int:
        return solve(grid)
