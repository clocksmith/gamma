"""Hack2Hire 6944670d867a3f9f539ff548 (Find Optimal Commute, variant 2: mode switching). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""
import heapq


def solve(grid, modes, times, costs):
    rows, cols = len(grid), len(grid[0])
    start = next((r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 'S')
    best = {start: (0, 0)}
    heap = [(0, 0, start[0], start[1])]
    while heap:
        time, cost, r, c = heapq.heappop(heap)
        if best.get((r, c)) != (time, cost):
            continue
        ch = grid[r][c]
        if ch == 'D':
            return [time, cost]
        step_time, step_cost = (0, 0) if ch == 'S' else (times[int(ch) - 1], costs[int(ch) - 1])
        candidate = (time + step_time, cost + step_cost)
        for x, y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= x < rows and 0 <= y < cols and grid[x][y] != 'X' and grid[x][y] != 'S':
                if (x, y) not in best or candidate < best[(x, y)]:
                    best[(x, y)] = candidate
                    heapq.heappush(heap, (candidate[0], candidate[1], x, y))
    return [-1, -1]


class Solution:
    def optimalCommuteCost(self, grid, modes, times, costs):
        return solve(grid, modes, times, costs)
