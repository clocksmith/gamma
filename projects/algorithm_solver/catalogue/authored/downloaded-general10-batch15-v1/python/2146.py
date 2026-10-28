"""2146. K Highest Ranked Items Within a Price Range (Medium).

Specification: https://leetcode.com/problems/k-highest-ranked-items-within-a-price-range/description/
"""

from collections import deque


def solve(grid: list[list[int]], pricing: list[int], start: list[int], k: int) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    low, high = pricing
    visited = [[False] * cols for _ in range(rows)]
    queue = deque([(start[0], start[1], 0)])
    visited[start[0]][start[1]] = True
    items = []
    while queue:
        r, c, dist = queue.popleft()
        price = grid[r][c]
        if low <= price <= high:
            items.append((dist, price, r, c))
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if visited[nr][nc] or grid[nr][nc] == 0:
                continue
            visited[nr][nc] = True
            queue.append((nr, nc, dist + 1))
    items.sort()
    return [[r, c] for _, _, r, c in items[:k]]


class Solution:
    def highestRankedKItems(self, grid: list[list[int]], pricing: list[int], start: list[int], k: int) -> list[list[int]]:
        return solve(grid, pricing, start, k)
