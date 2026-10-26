"""1210. Minimum Moves to Reach Target with Rotations.

Breadth-first search over tail position and orientation; O(n^2) time and space. Inputs are preserved.
"""

from collections import deque


def solve(grid: list[list[int]]) -> int:
    n = len(grid)
    queue = deque([(0, 0, 0, 0)])
    seen = {(0, 0, 0)}
    while queue:
        row, column, vertical, distance = queue.popleft()
        if (row, column, vertical) == (n - 1, n - 2, 0):
            return distance
        following = []
        if vertical == 0:
            if column + 2 < n and grid[row][column + 2] == 0:
                following.append((row, column + 1, 0))
            if row + 1 < n and grid[row + 1][column] == grid[row + 1][column + 1] == 0:
                following.extend(((row + 1, column, 0), (row, column, 1)))
        else:
            if row + 2 < n and grid[row + 2][column] == 0:
                following.append((row + 1, column, 1))
            if column + 1 < n and grid[row][column + 1] == grid[row + 1][column + 1] == 0:
                following.extend(((row, column + 1, 1), (row, column, 0)))
        for state in following:
            if state not in seen:
                seen.add(state)
                queue.append((*state, distance + 1))
    return -1


class Solution:
    def minimumMoves(self, grid: list[list[int]]) -> int:
        return solve(grid)
