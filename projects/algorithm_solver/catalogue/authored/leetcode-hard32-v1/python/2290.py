"""2290. Minimum Obstacle Removal to Reach Corner."""

from collections import deque


def solve(grid: list[list[int]]) -> int:
    """0-1 BFS: O(rows*cols) time and space; entering a cell pays its obstacle cost."""
    rows, cols = len(grid), len(grid[0])
    size = rows * cols
    distance = [size + 1] * size
    distance[0] = 0
    queue = deque([(0, 0)])
    while queue:
        node, cost = queue.popleft()
        if cost != distance[node]:
            continue
        if node == size - 1:
            return cost
        row, col = divmod(node, cols)
        for next_row, next_col in ((row - 1, col), (row + 1, col),
                                   (row, col - 1), (row, col + 1)):
            if not (0 <= next_row < rows and 0 <= next_col < cols):
                continue
            following = next_row * cols + next_col
            weight = grid[next_row][next_col]
            candidate = cost + weight
            if candidate >= distance[following]:
                continue
            distance[following] = candidate
            if weight:
                queue.append((following, candidate))
            else:
                queue.appendleft((following, candidate))
    return distance[-1]


class Solution:
    def minimumObstacles(self, grid: list[list[int]]) -> int:
        return solve(grid)
