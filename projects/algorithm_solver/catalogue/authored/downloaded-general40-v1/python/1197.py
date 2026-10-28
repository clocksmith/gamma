"""1197. Minimum Knight Moves (Medium).

Specification: https://leetcode.com/problems/minimum-knight-moves/description/
"""


def solve(x: int, y: int) -> int:
    target_x, target_y = abs(x), abs(y)
    queue = [(0, 0, 0)]
    visited = {(0, 0)}
    moves = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    head = 0
    while head < len(queue):
        cx, cy, steps = queue[head]
        head += 1
        if cx == target_x and cy == target_y:
            return steps
        for dx, dy in moves:
            nx, ny = cx + dx, cy + dy
            if nx < -2 or ny < -2 or nx > target_x + 2 or ny > target_y + 2:
                continue
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, steps + 1))
    return -1


class Solution:
    def minKnightMoves(self, x: int, y: int) -> int:
        return solve(x, y)
