"""1263. Minimum Moves to Move a Box to Their Target Location: BFS over pushes with player reachability; O((rows*columns)^2) time and O(rows*columns) space."""

from collections import deque


def solve(grid: list[list[str]]) -> int:
    rows, columns = len(grid), len(grid[0])
    cells = rows * columns
    player = box = target = -1
    for row in range(rows):
        for column in range(columns):
            cell = row * columns + column
            if grid[row][column] == 'S':
                player = cell
            elif grid[row][column] == 'B':
                box = cell
            elif grid[row][column] == 'T':
                target = cell
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def step(cell: int, dr: int, dc: int) -> int:
        row, column = divmod(cell, columns)
        row += dr
        column += dc
        if 0 <= row < rows and 0 <= column < columns and grid[row][column] != '#':
            return row * columns + column
        return -1

    queue = deque([(box, player, 0)])
    seen = {box * cells + player}
    while queue:
        current_box, current_player, pushes = queue.popleft()
        if current_box == target:
            return pushes
        reachable = {current_player}
        walking = deque([current_player])
        while walking:
            position = walking.popleft()
            for dr, dc in directions:
                neighbor = step(position, dr, dc)
                if neighbor != -1 and neighbor != current_box and neighbor not in reachable:
                    reachable.add(neighbor)
                    walking.append(neighbor)
        for dr, dc in directions:
            destination = step(current_box, dr, dc)
            standing = step(current_box, -dr, -dc)
            if destination == -1 or standing not in reachable:
                continue
            key = destination * cells + current_box
            if key not in seen:
                seen.add(key)
                queue.append((destination, current_box, pushes + 1))
    return -1


class Solution:
    def minPushBox(self, grid: list[list[str]]) -> int:
        return solve(grid)
