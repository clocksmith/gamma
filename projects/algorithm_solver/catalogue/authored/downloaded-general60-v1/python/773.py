"""773. Sliding Puzzle (Hard).

Specification: https://leetcode.com/problems/sliding-puzzle/description/
"""


def solve(board: list[list[int]]) -> int:
    start = "".join(str(v) for row in board for v in row)
    target = '123450'
    neighbors = [[1, 3], [0, 2, 4], [1, 5], [0, 4], [1, 3, 5], [2, 4]]
    queue = [start]
    visited = {start}
    steps = 0
    while queue:
        next_queue = []
        for current in queue:
            if current == target:
                return steps
            zero = current.index('0')
            for neighbor in neighbors[zero]:
                chars = list(current)
                chars[zero], chars[neighbor] = chars[neighbor], chars[zero]
                candidate = "".join(chars)
                if candidate not in visited:
                    visited.add(candidate)
                    next_queue.append(candidate)
        queue = next_queue
        steps += 1
    return -1


class Solution:
    def slidingPuzzle(self, board: list[list[int]]) -> int:
        return solve(board)
