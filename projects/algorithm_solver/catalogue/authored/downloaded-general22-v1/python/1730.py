"""1730. Shortest Path to Get Food (Medium).

Specification: https://leetcode.com/problems/shortest-path-to-get-food/description/
"""


def solve(grid: list[list[str]]) -> int:
    rows, cols = len(grid), len(grid[0])
    start = None
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '*':
                start = (r, c)
    queue = [(start[0], start[1], 0)]
    visited = {start}
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while queue:
        r, c, steps = queue.pop(0)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols or (nr, nc) in visited or grid[nr][nc] == 'X':
                continue
            if grid[nr][nc] == '#':
                return steps + 1
            visited.add((nr, nc))
            queue.append((nr, nc, steps + 1))
    return -1


class Solution:
    def getFood(self, grid: list[list[str]]) -> int:
        return solve(grid)
