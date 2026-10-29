"""Hack2Hire 68dc5856dd5418be11109afb (Shortest Path with Gas Stations) over an INFERRED spec; qualification unknown."""


def solve(grid, fuelCapacity):
    m, n = len(grid), len(grid[0])
    start = next((r, row.index('S')) for r, row in enumerate(grid) if 'S' in row)
    best = [[-1] * n for _ in range(m)]
    best[start[0]][start[1]] = fuelCapacity
    frontier = [(start[0], start[1], fuelCapacity)]
    steps = 0
    while frontier:
        following = []
        for r, c, fuel in frontier:
            if grid[r][c] == 'D':
                return steps
            if fuel == 0:
                continue
            for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= rr < m and 0 <= cc < n and grid[rr][cc] != '#':
                    left = fuelCapacity if grid[rr][cc] == 'G' else fuel - 1
                    if left > best[rr][cc]:
                        best[rr][cc] = left
                        following.append((rr, cc, left))
        frontier = following
        steps += 1
    return -1


class Solution:
    def shortestPathWithFuel(self, grid, fuelCapacity):
        return solve(grid, fuelCapacity)
