"""Hack2Hire 68523a801af0034b322764d9 (Find Optimal Commute, variant 1: single mode). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(grid, modes, times, costs):
    rows, cols = len(grid), len(grid[0])
    start = next((r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 'S')
    best = None
    for m in range(len(modes)):
        digit = str(m + 1)
        steps = {start: 0}
        frontier, head, found = [start], 0, -1
        while head < len(frontier) and found < 0:
            r, c = frontier[head]
            head += 1
            for x, y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= x < rows and 0 <= y < cols and (x, y) not in steps:
                    ch = grid[x][y]
                    if ch == 'D':
                        found = steps[(r, c)] + 1
                        break
                    if ch == digit:
                        steps[(x, y)] = steps[(r, c)] + 1
                        frontier.append((x, y))
        if found >= 0:
            charged = found - 1
            key = (charged * times[m], charged * costs[m], m)
            if best is None or key < best:
                best = key
    return '' if best is None else modes[best[2]]


class Solution:
    def optimalCommuteMode(self, grid, modes, times, costs):
        return solve(grid, modes, times, costs)
