"""Hack2Hire 69d414a379bf03c0074bcec2 (Cellular Infection Spreading, variant 2 of 5) over an INFERRED spec; qualification unknown."""


def _infection_days(grid, threshold):
    # multi-source breadth-first search by days with a counter of infected neighbours per healthy plant
    m = len(grid)
    n = len(grid[0])
    day = [[0 if v else -1 for v in row] for row in grid]
    count = [[0] * n for _ in range(m)]
    frontier = [(i, j) for i in range(m) for j in range(n) if grid[i][j]]
    current = 0
    last = 0
    while frontier:
        following = []
        for i, j in frontier:
            for a in range(i - 1 if i > 0 else 0, i + 2 if i + 2 <= m else m):
                day_row = day[a]
                count_row = count[a]
                for b in range(j - 1 if j > 0 else 0, j + 2 if j + 2 <= n else n):
                    if day_row[b] == -1:
                        count_row[b] += 1
                        if count_row[b] == threshold:
                            following.append((a, b))
        current += 1
        for a, b in following:
            day[a][b] = current
        if following:
            last = current
        frontier = following
    return day, last


def solve(grid, threshold):
    day, last = _infection_days(grid, threshold)
    for row in day:
        if -1 in row:
            return -1
    return last


class Solution:
    def daysToInfectAll(self, grid, threshold):
        return solve(grid, threshold)
