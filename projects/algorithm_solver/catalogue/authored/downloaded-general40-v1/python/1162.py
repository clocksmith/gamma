"""1162. As Far from Land as Possible (Medium).

Specification: https://leetcode.com/problems/as-far-from-land-as-possible/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    queue = []
    dist = [[0 if value == 1 else -1 for value in row] for row in grid]
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                queue.append((r, c))
            else:
                dist[r][c] = -1
    if not queue or len(queue) == rows * cols:
        return -1
    best = 0
    head = 0
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while head < len(queue):
        r, c = queue[head]
        head += 1
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                best = max(best, dist[nr][nc])
                queue.append((nr, nc))
    return best


class Solution:
    def maxDistance(self, grid: list[list[int]]) -> int:
        return solve(grid)
