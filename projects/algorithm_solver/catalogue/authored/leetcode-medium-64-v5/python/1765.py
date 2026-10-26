"""1765. Map of Highest Peak: assign every cell its shortest distance to any water cell."""
from collections import deque


def solve(isWater: list[list[int]]) -> list[list[int]]:
    """O(rows * columns) time and O(rows * columns) space; inputs are read-only."""
    rows, columns = len(isWater), len(isWater[0])
    height = [[-1] * columns for _ in range(rows)]
    queue = deque()
    for row in range(rows):
        for column in range(columns):
            if isWater[row][column] == 1:
                height[row][column] = 0
                queue.append((row, column))
    while queue:
        row, column = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and height[nr][nc] == -1:
                height[nr][nc] = height[row][column] + 1
                queue.append((nr, nc))
    return height


class Solution:
    def highestPeak(self, isWater: list[list[int]]) -> list[list[int]]:
        return solve(isWater)
