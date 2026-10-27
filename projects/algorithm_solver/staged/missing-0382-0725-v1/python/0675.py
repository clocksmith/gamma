"""675. Cut Off Trees for Golf Event. Visit trees by increasing height with shortest grid paths; input forest is preserved."""

from collections import deque

def solve(forest: list[list[int]]) -> int:
    rows, cols = len(forest), len(forest[0])
    trees = sorted((forest[r][c], r, c) for r in range(rows) for c in range(cols) if forest[r][c] > 1)
    if trees and forest[0][0] == 0:
        return -1
    def distance(source, target):
        queue = deque([(source[0], source[1], 0)])
        seen = {source}
        while queue:
            r, c, steps = queue.popleft()
            if (r, c) == target:
                return steps
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and forest[nr][nc] > 0 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    queue.append((nr, nc, steps + 1))
        return -1
    current, total = (0, 0), 0
    for _, row, col in trees:
        target = (row, col)
        steps = distance(current, target)
        if steps < 0:
            return -1
        total += steps
        current = target
    return total


class Solution:
    def cutOffTree(self, forest: list[list[int]]) -> int:
        return solve(forest)
