"""1091. Shortest Path in Binary Matrix (Medium).

Specification: https://leetcode.com/problems/shortest-path-in-binary-matrix/description/
"""


def solve(grid: list[list[int]]) -> int:
    n = len(grid)
    if grid[0][0] != 0 or grid[n - 1][n - 1] != 0:
        return -1
    queue = [(0, 0, 1)]
    visited = {(0, 0)}
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    index = 0
    while index < len(queue):
        r, c, distance = queue[index]
        index += 1
        if r == n - 1 and c == n - 1:
            return distance
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0 and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, distance + 1))
    return -1


class Solution:
    def shortestPathBinaryMatrix(self, grid: list[list[int]]) -> int:
        return solve(grid)
