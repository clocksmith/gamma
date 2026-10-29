"""Original LeetCode 675 candidate; qualification unknown."""

from collections import deque

def solve(forest):
    rows, cols = len(forest), len(forest[0])
    trees = sorted((forest[r][c], r, c) for r in range(rows) for c in range(cols) if forest[r][c] > 1)
    def distance(start, target):
        if not forest[start[0]][start[1]]: return -1
        queue, seen = deque([(start[0], start[1], 0)]), {start}
        while queue:
            r, c, steps = queue.popleft()
            if (r, c) == target: return steps
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0 <= nr < rows and 0 <= nc < cols and forest[nr][nc] and (nr,nc) not in seen:
                    seen.add((nr,nc)); queue.append((nr,nc,steps+1))
        return -1
    current, total = (0,0), 0
    for _, r, c in trees:
        steps = distance(current, (r,c))
        if steps < 0: return -1
        total += steps; current = (r,c)
    return total


class Solution:
    def cutOffTree(self, forest):
        return solve(forest)
