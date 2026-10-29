"""Hack2Hire 689bcb111126a03aace65e51 (Find Closest Dashmart). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(city, locations):
    rows, cols = len(city), len(city[0])
    dist = [-1] * (rows * cols)
    frontier = []
    for r in range(rows):
        for c in range(cols):
            if city[r][c] == 'D':
                dist[r * cols + c] = 0
                frontier.append(r * cols + c)
    head = 0
    while head < len(frontier):
        cell = frontier[head]
        head += 1
        r, c = divmod(cell, cols)
        for x, y in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= x < rows and 0 <= y < cols and dist[x * cols + y] < 0 and city[x][y] != 'X':
                dist[x * cols + y] = dist[cell] + 1
                frontier.append(x * cols + y)
    return [dist[r * cols + c] for r, c in locations]


class Solution:
    def closestDashmartDistances(self, city, locations):
        return solve(city, locations)
