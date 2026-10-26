"""2258. Escape the Spreading Fire."""

from collections import deque


def solve(grid: list[list[int]]) -> int:
    """Fire-arrival BFS and binary search on the initial wait; O(R*C*log(10^9)) time, O(R*C) space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    count = rows * columns
    fire = [float('inf')] * count
    queue = deque()
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for row in range(rows):
        for column in range(columns):
            if grid[row][column] == 1:
                cell = row * columns + column
                fire[cell] = 0
                queue.append(cell)
    while queue:
        cell = queue.popleft()
        row, column = divmod(cell, columns)
        for dr, dc in directions:
            nr, nc = row + dr, column + dc
            if not (0 <= nr < rows and 0 <= nc < columns) or grid[nr][nc] == 2:
                continue
            target = nr * columns + nc
            if fire[target] == float('inf'):
                fire[target] = fire[cell] + 1
                queue.append(target)

    def feasible(wait):
        if wait >= fire[0]:
            return False
        arrival = [-1] * count
        arrival[0] = wait
        pending = deque([0])
        while pending:
            cell = pending.popleft()
            if cell == count - 1:
                return True
            row, column = divmod(cell, columns)
            following = arrival[cell] + 1
            for dr, dc in directions:
                nr, nc = row + dr, column + dc
                if not (0 <= nr < rows and 0 <= nc < columns) or grid[nr][nc] == 2:
                    continue
                target = nr * columns + nc
                if arrival[target] >= 0:
                    continue
                if target == count - 1:
                    if following > fire[target]:
                        continue
                elif following >= fire[target]:
                    continue
                arrival[target] = following
                pending.append(target)
        return False

    if not feasible(0):
        return -1
    left, right = 0, 1_000_000_000
    while left < right:
        middle = (left + right + 1) // 2
        if feasible(middle):
            left = middle
        else:
            right = middle - 1
    return left


class Solution:
    def maximumMinutes(self, grid: list[list[int]]) -> int:
        return solve(grid)
