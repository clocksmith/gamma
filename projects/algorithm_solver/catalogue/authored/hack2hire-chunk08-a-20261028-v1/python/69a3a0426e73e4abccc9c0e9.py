"""Hack2Hire 69a3a0426e73e4abccc9c0e9 (Reach End in Grid With Teleports) over an INFERRED spec; qualification unknown."""


def solve(grid, teleports):
    n, m = len(grid), len(grid[0])
    jump = {}
    for r1, c1, r2, c2 in teleports:
        jump[r1 * m + c1] = r2 * m + c2
    seen = bytearray(n * m)
    seen[0] = 1
    position, destination, moves = 0, n * m - 1, 0
    while position != destination:
        r, c = divmod(position, m)
        if c == m - 1 or grid[r][c + 1] == 1:
            return -1
        position = jump.get(position + 1, position + 1)
        moves += 1
        if seen[position]:
            return -1
        seen[position] = 1
    return moves


class Solution:
    def reachEnd(self, grid, teleports):
        return solve(grid, teleports)
